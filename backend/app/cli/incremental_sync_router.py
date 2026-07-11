"""Incremental sync CLI router for ``qmd data sync --source-id``."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from backend.app.cli.errors import (
    CliFailure,
    DOCS_ANCHOR_DATA_SYNC_CLI,
    DOCS_ANCHOR_RESOURCE_GUARD_PAUSED,
    error_for_route_status,
    raise_if_ready_selected_mismatch,
)
from backend.app.core.resource_guard import ResourceGuard
from backend.app.db.connection import ConnectionManager
from backend.app.ops.sandbox_clean_write.clean_write_targets import resolve_clean_write_target
from backend.app.sync.incremental_source_registry import (
    UnknownIncrementalGoldPathSourceError,
    resolve_incremental_gold_path,
)
from backend.app.sync.watermark import compute_incremental_window, read_bar_trade_date_watermark


def _data_root_and_db():
    from backend.app.config import PROJECT_ROOT, _path_env

    data_root = _path_env("QMD_DATA_ROOT", PROJECT_ROOT / "data")
    db = data_root / "duckdb" / "quant_monitor.duckdb"
    return data_root, db


def _require_audit_sandbox_data_root(data_root) -> None:
    from pathlib import Path

    from backend.app.datasources.incremental_route_activation import (
        is_audit_sandbox_data_root,
    )

    resolved = Path(data_root)
    if not is_audit_sandbox_data_root(resolved):
        raise CliFailure(
            error_code="INVALID_INPUT",
            message="Incremental sync dry-run requires QMD_DATA_ROOT under .audit-sandbox",
            docs_anchor=DOCS_ANCHOR_DATA_SYNC_CLI,
        )
    if "user-live" in resolved.parts:
        raise CliFailure(
            error_code="INVALID_INPUT",
            message="user-live audit path refused for incremental sync dry-run",
            docs_anchor=DOCS_ANCHOR_DATA_SYNC_CLI,
        )


def _sandbox_db_readable(data_root) -> bool:
    from backend.app.datasources.incremental_route_activation import (
        is_audit_sandbox_data_root,
    )

    return is_audit_sandbox_data_root(data_root)


def _parse_end(end: str | None) -> date:
    from backend.app.cli.data_commands import _parse_sync_date

    if end is not None:
        return _parse_sync_date(end, field="end")
    return datetime.now(UTC).date()


def _sandbox_preview_binding(source_id: str):
    """沙箱 duckdb 存在时传入 con + 平台矩阵，供 ask_activation 读 overlay（ADR-018）。"""
    from contextlib import contextmanager
    from pathlib import Path

    @contextmanager
    def _ctx():
        data_root, db = _data_root_and_db()
        matrix = Path(data_root) / "platform-matrix" / f"platform-matrix-{source_id}.yaml"
        matrix_path = matrix if matrix.is_file() else None
        if _sandbox_db_readable(data_root) and db.is_file():
            with ConnectionManager(db_path=db).reader() as con:
                yield con, matrix_path
        else:
            yield None, matrix_path

    return _ctx()


def _incremental_route_preview(
    *,
    source_id: str,
    data_domain: str,
    operation: str,
    con=None,
    platform_matrix_path=None,
):
    from backend.app.datasources.incremental_route_activation import (
        plan_with_preferred_primary,
    )

    plan = plan_with_preferred_primary(
        source_id=source_id,
        data_domain=data_domain,
        operation=operation,
        con=con,
        platform_matrix_path=platform_matrix_path,
    )
    guard_decision, guard_reason = ResourceGuard().check()
    return plan, guard_decision, guard_reason


def _dry_run_shell(
    *,
    source_id: str,
    data_domain: str,
    operation: str,
    clean_table: str,
    write_mode: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    with _sandbox_preview_binding(source_id) as (preview_con, matrix_path):
        plan, guard_decision, guard_reason = _incremental_route_preview(
            source_id=source_id,
            data_domain=data_domain,
            operation=operation,
            con=preview_con,
            platform_matrix_path=matrix_path,
        )
    if guard_decision.value != "OK":
        raise CliFailure(
            error_code="RESOURCE_GUARD_PAUSED",
            message=guard_reason or "resource guard paused",
            docs_anchor=DOCS_ANCHOR_RESOURCE_GUARD_PAUSED,
            retryable=True,
        )
    route_status = plan.route_status
    selected_source_id = plan.selected_source_id
    raise_if_ready_selected_mismatch(
        route_status=route_status,
        selected_source_id=selected_source_id,
        requested_source_id=source_id,
        job_kind="sync dry-run",
    )
    if route_status != "READY":
        raise error_for_route_status(
            route_status,
            detail=f"sync dry-run blocked for source_id={source_id!r}",
        )
    message = "dry-run only; watermark/window computed, no fetch or DB writes"
    payload: dict[str, Any] = {
        "command": "sync",
        "dry_run": True,
        "source_id": source_id,
        "data_domain": data_domain,
        "operation": operation,
        "route_status": route_status,
        "selected_source_id": selected_source_id,
        "resource_guard_decision": guard_decision.value,
        "clean_table": clean_table,
        "write_mode": write_mode,
        "message": message,
    }
    if extra:
        payload.update(extra)
    from backend.app.cli.phase1_acceptance import (
        dry_run_envelope_for_plan,
        merge_payload_with_envelope,
        resolve_cli_data_root,
    )

    envelope = dry_run_envelope_for_plan(
        job_kind="sync",
        trigger=f"qmd-data data sync --source-id {source_id}",
        data_root=resolve_cli_data_root(),
        route_payload={
            "data_domain": data_domain,
            "selected_source_id": selected_source_id,
            "operation": operation,
            "route_status": route_status,
        },
    )
    return merge_payload_with_envelope(payload, envelope)


def _macro_dry_run(
    *,
    source_id: str,
    data_domain: str,
    operation: str,
    instrument_ids: tuple[str, ...],
    advance_days: int = 1,
    end: str | None = None,
) -> dict[str, Any]:
    from backend.app.ops.macro_incremental_common import (
        compute_since_date,
        read_since_dates_for_instruments,
    )

    data_root, db = _data_root_and_db()
    if _sandbox_db_readable(data_root) and db.is_file():
        with ConnectionManager(db_path=db).reader() as con:
            since_map = read_since_dates_for_instruments(
                con, instrument_ids, advance_days=advance_days
            )
    else:
        since_map = {
            iid: compute_since_date(None, advance_days=advance_days).isoformat()
            for iid in instrument_ids
        }
    target = resolve_clean_write_target(data_domain)
    return _dry_run_shell(
        source_id=source_id,
        data_domain=data_domain,
        operation=operation,
        clean_table=target.target_table,
        write_mode=target.write_mode,
        extra={
            "since_by_instrument": since_map,
            "window": {"end": end, "since_by_instrument": since_map},
        },
    )


def _bar_dry_run(
    *,
    source_id: str,
    data_domain: str,
    instrument_id: str,
    end: str | None,
    empty_table_lookback_days: int = 30,
) -> dict[str, Any]:
    from backend.app.sync.watermark import incremental_window_is_empty

    end_date = _parse_end(end)
    data_root, db = _data_root_and_db()
    watermark: date | None = None
    if _sandbox_db_readable(data_root) and db.is_file():
        with ConnectionManager(db_path=db).reader() as con:
            watermark = read_bar_trade_date_watermark(con, instrument_id=instrument_id)
    window = compute_incremental_window(
        watermark, end=end_date, empty_table_lookback_days=empty_table_lookback_days
    )
    target = resolve_clean_write_target(data_domain)
    return _dry_run_shell(
        source_id=source_id,
        data_domain=data_domain,
        operation="fetch_daily_bar",
        clean_table=target.target_table,
        write_mode=target.write_mode,
        extra={
            "instrument_id": instrument_id,
            "watermark": watermark.isoformat() if watermark else None,
            "window": {
                "date_start": window.date_start.isoformat(),
                "date_end": window.date_end.isoformat(),
                "end": end,
            },
            "caught_up": incremental_window_is_empty(window),
        },
    )


def sync_incremental_by_source_id(
    *,
    source_id: str,
    dry_run: bool = True,
    data_domain: str | None = None,
    operation: str | None = None,
    instrument_id: str | None = None,
    end: str | None = None,
    since: str | None = None,
    series_ids: tuple[str, ...] | None = None,
    start: str | None = None,
) -> dict[str, Any]:
    """Route ``qmd data sync --source-id`` to per-source incremental handlers (ADR-009)."""
    try:
        entry = resolve_incremental_gold_path(source_id)
    except UnknownIncrementalGoldPathSourceError as exc:
        raise CliFailure(
            error_code="INVALID_INPUT",
            message=str(exc),
            docs_anchor=DOCS_ANCHOR_DATA_SYNC_CLI,
        ) from exc

    if data_domain is not None and data_domain != entry.canonical_domain:
        raise CliFailure(
            error_code="INVALID_INPUT",
            message=(
                f"domain mismatch for source_id={source_id!r}: "
                f"got {data_domain!r}, expected {entry.canonical_domain!r}"
            ),
            docs_anchor=DOCS_ANCHOR_DATA_SYNC_CLI,
        )

    canonical = entry.canonical_domain
    from backend.app.cli import data_commands

    if dry_run:
        data_root, _ = _data_root_and_db()
        _require_audit_sandbox_data_root(data_root)

    if not dry_run:
        from backend.app.cli.phase1_acceptance import (
            is_production_equivalent_acceptance_root,
            require_phase1_data_root_for_live,
            resolve_cli_data_root,
            run_phase1_sync_live,
        )

        data_root = resolve_cli_data_root()
        if not is_production_equivalent_acceptance_root(data_root):
            require_phase1_data_root_for_live(data_root)
        return run_phase1_sync_live(
            source_id=source_id,
            data_domain=canonical,
            data_root=data_root,
            end=end,
            instrument_id=instrument_id,
        )

    if source_id == "baostock":
        return data_commands.sync_baostock_incremental(
            dry_run=True,
            instrument_id=instrument_id,
            end=end,
            since=since,
        )
    if source_id == "mootdx":
        return data_commands.sync_mootdx_incremental(
            dry_run=True,
            instrument_id=instrument_id,
            end=end,
            since=since,
        )
    if source_id == "fred":
        from backend.app.datasources.fetch_ports.fred_port import P0_SERIES_WHITELIST
        from backend.app.ops.fred_incremental_run import build_fred_incremental_preview_service
        from backend.app.ops.fred_incremental_watermark import read_since_dates_for_series

        op = operation or "fetch_macro_series"
        selected = series_ids or tuple(sorted(P0_SERIES_WHITELIST))[:1]
        since_map: dict[str, str] = {}
        with _sandbox_preview_binding(source_id) as (preview_con, matrix_path):
            preview_svc = build_fred_incremental_preview_service(
                platform_matrix_path=matrix_path,
            )
            plan = preview_svc.preview_route(
                data_domain=canonical,
                operation=op,
                con=preview_con,
            )
            if preview_con is not None:
                since_map = read_since_dates_for_series(preview_con, selected)
        guard_decision, guard_reason = ResourceGuard().check()
        if guard_decision.value != "OK":
            raise CliFailure(
                error_code="RESOURCE_GUARD_PAUSED",
                message=guard_reason or "resource guard paused",
                docs_anchor=DOCS_ANCHOR_RESOURCE_GUARD_PAUSED,
                retryable=True,
            )
        if plan.route_status != "READY":
            raise error_for_route_status(
                plan.route_status,
                detail=f"sync dry-run blocked for source_id={source_id!r}",
            )
        if since:
            since_map = {sid: since for sid in selected}
        target = resolve_clean_write_target(canonical)
        payload = {
            "command": "sync",
            "dry_run": True,
            "source_id": source_id,
            "data_domain": canonical,
            "operation": op,
            "series_ids": list(selected),
            "since_by_series": since_map,
            "route_status": plan.route_status,
            "selected_source_id": plan.selected_source_id,
            "resource_guard_decision": guard_decision.value,
            "clean_table": target.target_table,
            "write_mode": target.write_mode,
            "message": "dry-run only; no fetch or DB writes performed",
        }
        from backend.app.cli.phase1_acceptance import (
            build_incremental_evidence,
            dry_run_envelope_for_plan,
            merge_payload_with_envelope,
            resolve_cli_data_root,
        )
        from backend.app.ops.macro_incremental_common import compute_since_date

        end_date = _parse_end(end)
        window_start = (
            min(since_map.values())
            if since_map
            else compute_since_date(None).isoformat()
        )
        envelope = dry_run_envelope_for_plan(
            job_kind="sync",
            trigger=f"qmd-data data sync --source-id {source_id}",
            data_root=resolve_cli_data_root(),
            route_payload={
                "data_domain": canonical,
                "selected_source_id": plan.selected_source_id,
                "operation": op,
                "route_status": plan.route_status,
                "route_plan_id": plan.route_plan_id,
            },
            extra={
                "incremental_evidence": build_incremental_evidence(
                    watermark_before=None,
                    window_date_start=window_start,
                    window_date_end=end_date.isoformat(),
                ),
            },
        )
        return merge_payload_with_envelope(payload, envelope)
    if source_id == "us_treasury":
        from backend.app.ops.us_treasury_incremental_run import DEFAULT_TENORS

        return _macro_dry_run(
            source_id=source_id,
            data_domain=canonical,
            operation="fetch_yield_curve",
            instrument_ids=DEFAULT_TENORS,
            end=end,
        )
    if source_id == "bis":
        from backend.app.ops.bis_incremental_run import DEFAULT_COUNTRIES

        return _macro_dry_run(
            source_id=source_id,
            data_domain=canonical,
            operation="fetch_policy_rate",
            instrument_ids=DEFAULT_COUNTRIES,
            end=end,
        )
    if source_id == "world_bank":
        from backend.app.ops.world_bank_incremental_run import (
            DEFAULT_COUNTRIES,
            DEFAULT_INDICATOR,
        )

        return _macro_dry_run(
            source_id=source_id,
            data_domain=canonical,
            operation="fetch_development_indicator",
            instrument_ids=(f"{DEFAULT_COUNTRIES[0]}:{DEFAULT_INDICATOR}",),
            end=end,
        )
    if source_id == "cftc_cot":
        from backend.app.ops.cftc_incremental_run import DEFAULT_MARKETS

        return _macro_dry_run(
            source_id=source_id,
            data_domain=canonical,
            operation="fetch_cot_report",
            instrument_ids=DEFAULT_MARKETS,
            advance_days=7,
            end=end,
        )
    if source_id == "alpha_vantage":
        symbol = instrument_id or "AAPL"
        return _bar_dry_run(
            source_id=source_id,
            data_domain=canonical,
            instrument_id=symbol,
            end=end,
        )
    if source_id == "cninfo":
        from backend.app.ops.cninfo_incremental_watermark import read_since_date_for_instrument

        symbol = instrument_id or "sh.600519"
        data_root, db = _data_root_and_db()
        since_date = None
        if _sandbox_db_readable(data_root) and db.is_file():
            with ConnectionManager(db_path=db).reader() as con:
                since_date = read_since_date_for_instrument(con, symbol)
        target = resolve_clean_write_target(canonical)
        return _dry_run_shell(
            source_id=source_id,
            data_domain=canonical,
            operation="fetch_announcement_index",
            clean_table=target.target_table,
            write_mode=target.write_mode,
            extra={
                "instrument_id": symbol,
                "window": {"since": since_date, "end": end},
            },
        )
    if source_id == "sec_edgar":
        from backend.app.ops.sec_edgar_incremental_watermark import read_since_date_for_cik

        cik = instrument_id or "0000320193"
        data_root, db = _data_root_and_db()
        since_date = None
        if _sandbox_db_readable(data_root) and db.is_file():
            with ConnectionManager(db_path=db).reader() as con:
                since_date = read_since_date_for_cik(con, cik)
        target = resolve_clean_write_target(canonical)
        return _dry_run_shell(
            source_id=source_id,
            data_domain=canonical,
            operation="fetch_company_filings",
            clean_table=target.target_table,
            write_mode=target.write_mode,
            extra={"cik": cik, "window": {"since": since_date, "end": end}},
        )
    if source_id == "deribit":
        from backend.app.ops.deribit_incremental_watermark import read_since_date_for_instrument

        instrument = instrument_id or "BTC-28JUN24-65000-C"
        data_root, db = _data_root_and_db()
        since_date = None
        if _sandbox_db_readable(data_root) and db.is_file():
            with ConnectionManager(db_path=db).reader() as con:
                since_date = read_since_date_for_instrument(con, instrument)
        target = resolve_clean_write_target(canonical)
        return _dry_run_shell(
            source_id=source_id,
            data_domain=canonical,
            operation="fetch_options_surface",
            clean_table=target.target_table,
            write_mode=target.write_mode,
            extra={
                "instrument_name": instrument,
                "window": {"since": since_date, "end": end},
            },
        )

    raise CliFailure(
        error_code="INVALID_INPUT",
        message=f"no incremental sync handler for source_id={source_id!r}",
        docs_anchor=DOCS_ANCHOR_DATA_SYNC_CLI,
    )
