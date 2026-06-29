"""`qmd data` command implementations (R3F-CLI-01)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from backend.app.cli.errors import CliFailure, error_for_route_status
from backend.app.config import DATA_ROOT
from backend.app.core.resource_guard import ResourceGuard
from backend.app.datasources.service import DataSourceService
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations


def _default_operation(data_domain: str) -> str:
    return {
        "market_bar_1d": "fetch_daily_bar",
        "announcement": "fetch_announcement_index",
        "macro_series": "fetch_macro_series",
    }.get(data_domain, "fetch_daily_bar")


def _service() -> DataSourceService:
    return DataSourceService(staged_fixture_mode=False)


def route_preview(
    *,
    data_domain: str,
    operation: str | None = None,
    market_id: str | None = None,
    use_fallback: bool = False,
) -> dict[str, Any]:
    op = operation or _default_operation(data_domain)
    plan = _service().preview_route(
        data_domain=data_domain,
        operation=op,
        market_id=market_id,
        use_fallback=use_fallback,
    )
    guard_decision, guard_reason = _service().check_resource_guard()
    return {
        "command": "route-preview",
        "dry_run": True,
        "side_effects_allowed": False,
        "data_domain": data_domain,
        "operation": op,
        "route_status": plan.route_status,
        "selected_source_id": plan.selected_source_id,
        "resource_guard_decision": guard_decision.value,
        "resource_guard_reason": guard_reason,
        "route_plan": plan.to_payload_dict(),
    }


def sync_plan(
    *,
    data_domain: str,
    source_id: str | None = None,
    operation: str | None = None,
    dry_run: bool = True,
    start: str | None = None,
    end: str | None = None,
    since: str | None = None,
    series_ids: tuple[str, ...] | None = None,
    instrument_id: str | None = None,
) -> dict[str, Any]:
    if data_domain == "cn_equity_daily_bar":
        return sync_baostock_incremental(
            dry_run=dry_run,
            instrument_id=instrument_id,
            end=end,
            since=since,
            empty_table_lookback_days=30,
        )
    op = operation or _default_operation(data_domain)
    if dry_run:
        if data_domain == "macro_series" and source_id == "fred":
            from backend.app.ops.fred_incremental_run import build_fred_incremental_preview_service

            preview_svc = build_fred_incremental_preview_service()
            plan = preview_svc.preview_route(data_domain=data_domain, operation=op)
            guard_decision, guard_reason = ResourceGuard().check()
            preview = {
                "route_status": plan.route_status,
                "selected_source_id": plan.selected_source_id,
            }
        else:
            preview = route_preview(data_domain=data_domain, operation=op)
            guard_decision, guard_reason = ResourceGuard().check()
        if guard_decision.value != "OK":
            raise CliFailure(
                error_code="RESOURCE_GUARD_PAUSED",
                message=guard_reason or "resource guard paused",
                docs_anchor="docs/ops/ERROR_CODE_GUIDE.md#resource-guard-paused",
                retryable=True,
            )
        if preview["route_status"] != "READY":
            raise error_for_route_status(
                preview["route_status"],
                detail=f"sync dry-run blocked for domain={data_domain!r}",
            )
        payload: dict[str, Any] = {
            "command": "sync",
            "dry_run": True,
            "product_live": False,
            "data_domain": data_domain,
            "operation": op,
            "window": {"start": start, "end": end, "since": since},
            "route_status": preview["route_status"],
            "selected_source_id": preview["selected_source_id"],
            "resource_guard_decision": guard_decision.value,
            "message": "dry-run only; no fetch or DB writes performed",
        }
        if source_id is not None:
            payload["source_id"] = source_id
        return payload

    if data_domain == "macro_series" and source_id == "fred":
        return _sync_fred_macro_incremental(
            operation=op,
            since=since,
            series_ids=series_ids,
        )

    raise CliFailure(
        error_code="USER_AUTH_REQUIRED",
        message=(
            "qmd data sync without --dry-run requires explicit operator "
            "confirmation (not enabled by default)"
        ),
        docs_anchor="docs/ops/data_sync_quick_reference.md",
        manual_confirmation_required=True,
    )


def _sync_fred_macro_incremental(
    *,
    operation: str,
    since: str | None,
    series_ids: tuple[str, ...] | None,
) -> dict[str, Any]:
    """Execute fred macro incremental via gold path (R3-DCP-02 S02-05).

    L1: DataSourceService + run_incremental (reference-adoption-dcp02.md §2).
    L2: --source-id fred + watermark since map (execute-reference-read-evidence.md R1).
    forbidden: EasyXT silent fallback (reference-adoption-dcp02.md §0).
    """
    import os

    from backend.app.datasources.fetch_ports.fred_port import P0_SERIES_WHITELIST, create_fred_fetch_port
    from backend.app.datasources.product_live_gate import (
        ProductLiveGateError,
        assert_product_live_allowed,
    )
    from backend.app.ops.fred_incremental_run import (
        build_fred_incremental_service,
        run_fred_macro_incremental,
    )
    from backend.app.ops.fred_incremental_watermark import (
        read_since_dates_for_series,
    )
    from backend.app.ops.sandbox_clean_write.rehearsal_runner import (
        RehearsalRunnerError,
        assert_sandbox_db_allowed,
    )
    from backend.app.sync.orchestrator import DataSyncOrchestrator

    try:
        assert_product_live_allowed(source_id="fred", operation=operation)
    except ProductLiveGateError as exc:
        raise CliFailure(
            error_code=exc.code,
            message=str(exc),
            docs_anchor="docs/decisions/ADR-027-r3h08-product-live-env-gate.md",
        ) from exc

    guard_decision, guard_reason = ResourceGuard().check()
    if guard_decision.value != "OK":
        raise CliFailure(
            error_code="RESOURCE_GUARD_PAUSED",
            message=guard_reason or "resource guard paused",
            docs_anchor="docs/ops/ERROR_CODE_GUIDE.md#resource-guard-paused",
            retryable=True,
        )

    selected = series_ids or tuple(sorted(P0_SERIES_WHITELIST))[:1]
    use_mock = os.environ.get("QMD_FRED_INCREMENTAL_USE_MOCK", "0") != "0"
    if not use_mock and not os.environ.get("FRED_API_KEY"):
        raise CliFailure(
            error_code="USER_AUTH_REQUIRED",
            message="FRED_API_KEY missing for live fred incremental sync",
            docs_anchor="docs/ops/ERROR_CODE_GUIDE.md#user-auth-required",
        )

    from backend.app.config import PROJECT_ROOT, _path_env

    data_root = _path_env("QMD_DATA_ROOT", PROJECT_ROOT / "data")
    db = data_root / "duckdb" / "quant_monitor.duckdb"
    try:
        assert_sandbox_db_allowed(db, no_production_mutation=True)
    except RehearsalRunnerError as exc:
        raise CliFailure(
            error_code="INVALID_INPUT",
            message=str(exc),
            docs_anchor="docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3_DCP_02_FRED_INCREMENTAL.md",
        ) from exc
    db.parent.mkdir(parents=True, exist_ok=True)
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
        since_map = read_since_dates_for_series(con, selected)
    if since:
        since_map = {sid: since for sid in selected}

    raw_root = data_root / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    port = create_fred_fetch_port(
        series_ids=selected,
        max_rows=3,
        use_mock=use_mock,
    )
    orch = DataSyncOrchestrator(cm)
    service = build_fred_incremental_service(
        data_root=raw_root,
        fetch_port=port,
        since_by_series=since_map,
        job_events=orch._jobs,
    )
    report = run_fred_macro_incremental(
        orch,
        service=service,
        series_ids=selected,
        use_mock=use_mock,
    )
    if report.overall_status == "PARTIAL_FAILURE":
        failed = [r for r in report.series_results if r["status"] not in {"COMPLETED", "EMPTY_RESPONSE"}]
        raise CliFailure(
            error_code="SYNC_PARTIAL_FAILURE",
            message=f"fred macro incremental partial failure: {failed}",
            docs_anchor="docs/ops/ERROR_CODE_GUIDE.md#sync-partial-failure",
            retryable=True,
        )
    if report.overall_status == "FAILED":
        raise CliFailure(
            error_code="SYNC_FAILED",
            message=f"fred macro incremental failed: {list(report.series_results)}",
            docs_anchor="docs/ops/ERROR_CODE_GUIDE.md#sync-failed",
            retryable=True,
        )
    message = (
        "fred macro incremental sync completed"
        if report.overall_status == "COMPLETED"
        else "fred macro incremental sync completed (no new observations)"
    )
    return {
        "command": "sync",
        "dry_run": False,
        "product_live": not use_mock,
        "data_domain": "macro_series",
        "source_id": "fred",
        "operation": operation,
        "series_ids": list(selected),
        "since_by_series": since_map,
        "resource_guard_decision": guard_decision.value,
        "series_results": list(report.series_results),
        "total_rows_written": report.total_rows_written,
        "overall_status": report.overall_status,
        "message": message,
    }


def _parse_sync_date(value: str, *, field: str) -> date:
    try:
        return date.fromisoformat(value[:10])
    except ValueError as exc:
        raise CliFailure(
            error_code="INVALID_INPUT",
            message=f"invalid {field} date: {value!r}",
            docs_anchor="docs/ops/data_sync_quick_reference.md",
        ) from exc


def _require_baostock_sync_operator_or_sandbox(data_root: Path) -> None:
    if ".audit-sandbox" not in str(data_root.resolve()):
        raise CliFailure(
            error_code="USER_AUTH_REQUIRED",
            message=(
                "qmd data sync without --dry-run requires explicit operator "
                "confirmation or QMD_DATA_ROOT under .audit-sandbox"
            ),
            docs_anchor="docs/ops/data_sync_quick_reference.md",
            manual_confirmation_required=True,
        )


def sync_baostock_incremental(
    *,
    dry_run: bool = True,
    instrument_id: str | None = None,
    end: str | None = None,
    since: str | None = None,
    empty_table_lookback_days: int = 30,
) -> dict[str, Any]:
    """``qmd data sync --domain cn_equity_daily_bar`` — watermark + orchestrator gold path."""
    from datetime import UTC, date, datetime

    import uuid

    from backend.app.datasources.fetch_ports.baostock_port import create_baostock_fetch_port
    from backend.app.ops.sandbox_clean_write.clean_write_targets import resolve_clean_write_target
    from backend.app.ops.sandbox_clean_write.rehearsal_runner import (
        RehearsalRunnerError,
        assert_sandbox_db_allowed,
    )
    from backend.app.sync.jobs import SyncJobSpec
    from backend.app.sync.orchestrator import DataSyncOrchestrator
    from backend.app.sync.watermark import (
        IncrementalWindow,
        compute_incremental_window,
        incremental_window_is_empty,
        read_bar_trade_date_watermark,
    )

    data_domain = "cn_equity_daily_bar"
    op = "fetch_daily_bar"
    preview = route_preview(data_domain=data_domain, operation=op)
    guard_decision, guard_reason = ResourceGuard().check()
    symbol = instrument_id or "sh.600519"
    db = DATA_ROOT / "duckdb" / "quant_monitor.duckdb"

    if not dry_run:
        _require_baostock_sync_operator_or_sandbox(DATA_ROOT)
        try:
            assert_sandbox_db_allowed(db, no_production_mutation=True)
        except RehearsalRunnerError as exc:
            raise CliFailure(
                error_code="INVALID_INPUT",
                message=str(exc),
                docs_anchor="docs/ops/data_sync_quick_reference.md",
            ) from exc

    if end is not None:
        end_date = _parse_sync_date(end, field="end")
    else:
        end_date = datetime.now(UTC).date()

    watermark: date | None = None
    if db.is_file():
        with ConnectionManager(db_path=db).reader() as con:
            watermark = read_bar_trade_date_watermark(con, instrument_id=symbol)

    try:
        window = compute_incremental_window(
            watermark,
            end=end_date,
            empty_table_lookback_days=empty_table_lookback_days,
        )
    except ValueError as exc:
        raise CliFailure(
            error_code="INVALID_INPUT",
            message=str(exc),
            docs_anchor="docs/ops/data_sync_quick_reference.md",
        ) from exc

    if since is not None:
        since_date = _parse_sync_date(since, field="since")
        window = IncrementalWindow(
            date_start=since_date,
            date_end=window.date_end,
            watermark=window.watermark,
        )

    target = resolve_clean_write_target(data_domain)
    caught_up = incremental_window_is_empty(window)
    payload: dict[str, Any] = {
        "command": "sync",
        "dry_run": dry_run,
        "product_live": False,
        "data_domain": data_domain,
        "operation": op,
        "instrument_id": symbol,
        "watermark": watermark.isoformat() if watermark else None,
        "window": {
            "date_start": window.date_start.isoformat(),
            "date_end": window.date_end.isoformat(),
            "since": since,
            "end": end,
        },
        "route_status": preview["route_status"],
        "selected_source_id": preview["selected_source_id"],
        "resource_guard_decision": guard_decision.value,
        "clean_table": target.target_table,
        "write_mode": target.write_mode,
        "caught_up": caught_up,
    }
    if dry_run:
        payload["message"] = "dry-run only; watermark window computed, no fetch or DB writes"
        return payload

    if guard_decision.value != "OK":
        raise CliFailure(
            error_code="RESOURCE_GUARD_PAUSED",
            message=guard_reason or "resource guard paused",
            docs_anchor="docs/ops/ERROR_CODE_GUIDE.md#resource-guard-paused",
            retryable=True,
        )
    if preview["route_status"] != "READY":
        raise error_for_route_status(
            preview["route_status"],
            detail=f"sync blocked for domain={data_domain!r}",
        )

    if caught_up:
        payload["job_status"] = "COMPLETED"
        payload["message"] = "caught-up: empty incremental window; no fetch or DB writes"
        return payload

    db.parent.mkdir(parents=True, exist_ok=True)
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)

    port = create_baostock_fetch_port(symbols=(symbol,), max_rows=500, use_mock=True)
    raw_root = DATA_ROOT / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    orch = DataSyncOrchestrator(cm)
    service = DataSourceService(
        data_root=raw_root,
        fetch_port=port,
        job_events=orch._jobs,
    )
    job_id = f"qmd-baostock-sync-{uuid.uuid4().hex[:10]}"
    spec = SyncJobSpec(
        run_id=job_id,
        job_id=job_id,
        job_type="incremental",
        data_domain=data_domain,
        market_id="CN_A",
        source_id="baostock",
        adapter_id="baostock",
        date_start=window.date_start,
        date_end=window.date_end,
        instrument_id=symbol,
        partition_key=None,
        trigger_reason="qmd_data_sync",
    )
    result = orch.run_incremental(
        spec,
        datasource_service=service,
        clean_table=target.target_table,
        write_mode=target.write_mode,
        primary_keys=target.primary_keys,
    )
    payload["job_status"] = result.status
    payload["job_id"] = result.job_id
    payload["message"] = "baostock incremental sync completed via DataSourceService gold path"
    return payload


def live_fetch(
    *,
    source_id: str,
    data_domain: str,
    operation: str | None = None,
    instrument_id: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """``qmd data live-fetch`` — product live route preview + optional fetch (R3H-08 S08-05)."""
    from backend.app.datasources.fetch_result import FetchRequest
    from backend.app.datasources.product_live_gate import (
        ProductLiveGateError,
        assert_product_live_allowed,
    )
    from backend.app.datasources.product_live_ports import build_product_live_service

    op = operation or _default_operation(data_domain)
    try:
        assert_product_live_allowed(source_id=source_id, operation=op)
    except ProductLiveGateError as exc:
        raise CliFailure(
            error_code=exc.code,
            message=str(exc),
            docs_anchor="docs/decisions/ADR-027-r3h08-product-live-env-gate.md",
        ) from exc

    preview_service = _service()
    plan = preview_service.preview_route(data_domain=data_domain, operation=op)
    guard_decision, guard_reason = preview_service.check_resource_guard()
    payload: dict[str, Any] = {
        "command": "live-fetch",
        "dry_run": dry_run,
        "product_live": True,
        "source_id": source_id,
        "data_domain": data_domain,
        "operation": op,
        "route_status": plan.route_status,
        "selected_source_id": plan.selected_source_id,
        "resource_guard_decision": guard_decision.value,
        "resource_guard_reason": guard_reason,
    }
    if dry_run:
        payload["message"] = "dry-run only; set dry_run=false for product live fetch"
        return payload

    if guard_decision.value != "OK":
        raise CliFailure(
            error_code="RESOURCE_GUARD_PAUSED",
            message=guard_reason or "resource guard paused",
            docs_anchor="docs/ops/ERROR_CODE_GUIDE.md#resource-guard-paused",
            retryable=True,
        )
    if plan.route_status != "READY":
        raise error_for_route_status(
            plan.route_status,
            detail=f"live-fetch blocked for domain={data_domain!r}",
        )

    live_service = build_product_live_service(
        source_id=source_id,
        data_domain=data_domain,
        data_root=DATA_ROOT / "raw",
        operation=op,
    )
    db = DATA_ROOT / "duckdb" / "quant_monitor.duckdb"
    cm = ConnectionManager(db_path=db)
    req = FetchRequest(
        run_id="qmd-live-fetch",
        source_id=source_id,
        data_domain=data_domain,
        instrument_id=instrument_id,
    )
    with cm.writer() as con:
        result = live_service.fetch(req, con=con, job_id="qmd-live-fetch", operation=op)
    payload["row_count"] = result.row_count
    payload["fetch_status"] = result.status
    payload["message"] = "product live fetch completed via DataSourceService gold path"
    return payload


def init_basic(*, dry_run: bool = True, db_path: Path | None = None) -> dict[str, Any]:
    target = db_path or (DATA_ROOT / "duckdb" / "quant_monitor.duckdb")
    payload: dict[str, Any] = {
        "command": "init-basic",
        "dry_run": dry_run,
        "db_path": str(target),
        "steps": ["apply_migrations", "sync_registry"],
    }
    if dry_run:
        payload["message"] = (
            "dry-run only; use qmd-init-db --sync-registry for migrations + registry"
        )
        return payload
    target.parent.mkdir(parents=True, exist_ok=True)
    cm = ConnectionManager(target)
    registry_rows: int | None = None
    with cm.writer() as con:
        applied = apply_migrations(con)
        registry = SourceRegistry()
        registry.load()
        registry_rows = registry.sync_to_db(con, tombstone_missing=True)
    payload["migrations_applied"] = applied or "none (up to date)"
    payload["registry_rows"] = registry_rows
    return payload


_HEALTH_FORBIDDEN_FLAGS: tuple[tuple[str, str], ...] = (
    ("allow_network", "live fetch not allowed for qmd data health"),
    ("clean_write", "clean write not allowed for read-only health"),
    ("full_market_scan", "full-market scan forbidden; use bounded window"),
    ("full_history", "full-history default scan forbidden; set --start/--end"),
)


def health_check(
    *,
    data_domain: str,
    profile: str,
    evidence_dir: Path | None = None,
    db_path: Path | None = None,
    start: str | None = None,
    end: str | None = None,
    max_rows: int = 1000,
    allow_network: bool = False,
    clean_write: bool = False,
    full_market_scan: bool = False,
    full_history: bool = False,
) -> dict[str, Any]:
    """``qmd data health`` CLI entry — delegates to ``run_data_health_profile`` (R3FR-06).

    Canonical read-only runner: ``backend.app.ops.data_health_profiles``.
    """
    from backend.app.ops.data_health import DataHealthLoadError
    from backend.app.ops.data_health_profiles import (
        DataHealthIngestLimitError,
        UnsupportedProfileError,
        cli_envelope_from_report,
        run_data_health_profile,
    )

    flag_values = {
        "allow_network": allow_network,
        "clean_write": clean_write,
        "full_market_scan": full_market_scan,
        "full_history": full_history,
    }
    for flag, message in _HEALTH_FORBIDDEN_FLAGS:
        if flag_values[flag]:
            raise CliFailure(
                error_code="CAPABILITY_MISSING",
                message=message,
                docs_anchor="docs/ops/data_health_cli.md",
            )
    if not data_domain or not profile:
        raise CliFailure(
            error_code="INVALID_INPUT",
            message="--domain and --profile are required",
            docs_anchor="docs/ops/data_health_cli.md",
        )
    if evidence_dir is None:
        raise CliFailure(
            error_code="INVALID_INPUT",
            message="--evidence-dir required for supported profiles in this slice",
            docs_anchor="docs/ops/data_health_cli.md",
        )

    try:
        report, limitations, hash_coverage, schema_coverage, window = run_data_health_profile(
            profile_id=profile,
            domain=data_domain,
            evidence_path=evidence_dir,
            db_path=db_path,
            start_date=start,
            end_date=end,
            max_rows=max_rows,
        )
    except UnsupportedProfileError as exc:
        raise CliFailure(
            error_code="CAPABILITY_MISSING",
            message=str(exc),
            docs_anchor="docs/ops/data_health_cli.md",
        ) from exc
    except (DataHealthLoadError, DataHealthIngestLimitError) as exc:
        raise CliFailure(
            error_code="INVALID_INPUT",
            message=str(exc),
            docs_anchor="docs/ops/data_health_cli.md",
        ) from exc

    source_ids: list[str] = []
    for check in report.checks:
        if check.source_id and check.source_id not in source_ids:
            source_ids.append(check.source_id)

    return cli_envelope_from_report(
        report,
        domain=data_domain,
        profile=profile,
        window=window,
        source_ids=source_ids,
        limitations=limitations,
        content_hash_coverage=hash_coverage,
        schema_hash_coverage=schema_coverage,
    )


def emit_payload(payload: dict[str, Any], *, fmt: str = "json") -> str:
    if fmt == "json":
        return json.dumps(payload, indent=2)
    lines = [f"{key}={value}" for key, value in payload.items() if key != "route_plan"]
    if "route_plan" in payload:
        lines.append("route_plan=" + json.dumps(payload["route_plan"], sort_keys=True))
    return "\n".join(lines) + "\n"


def emit_failure(err: CliFailure, *, fmt: str = "json") -> str:
    if fmt == "json":
        return err.format_json()
    return err.format_text()


def sandbox_clean_write_rehearse(
    *,
    candidate_set: str,
    sandbox_db: Path,
    evidence_dir: Path,
    report: Path,
    no_production_mutation: bool = False,
    dry_run: bool = True,
    allow_live_fetch: bool = False,
    fred_authorization: Path | None = None,
) -> dict[str, Any]:
    """``qmd data sandbox-clean-write rehearse`` — R3G-01 sandbox rehearsal CLI."""
    from backend.app.ops.sandbox_clean_write.rehearsal_runner import (
        RehearsalRequest,
        RehearsalRunnerError,
        run_sandbox_clean_write_rehearsal,
    )

    if not no_production_mutation:
        raise CliFailure(
            error_code="USER_AUTH_REQUIRED",
            message="--no-production-mutation is required for sandbox clean-write rehearsal",
            docs_anchor="docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_01_SANDBOX_CLEAN_WRITE_REHEARSAL.md",
            manual_confirmation_required=True,
        )
    try:
        return run_sandbox_clean_write_rehearsal(
            RehearsalRequest(
                candidate_set=candidate_set,
                sandbox_db=sandbox_db,
                evidence_dir=evidence_dir,
                report_path=report,
                no_production_mutation=no_production_mutation,
                dry_run=dry_run,
                allow_live_fetch=allow_live_fetch,
                fred_authorization=fred_authorization,
            )
        )
    except RehearsalRunnerError as exc:
        raise CliFailure(
            error_code="INVALID_INPUT",
            message=str(exc),
            docs_anchor="docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_01_SANDBOX_CLEAN_WRITE_REHEARSAL.md",
        ) from exc


def sandbox_clean_write_audit(
    *,
    rehearsal_report: Path,
    sandbox_db: Path,
    evidence_dir: Path,
    decision_report: Path,
) -> dict[str, Any]:
    """``qmd data sandbox-clean-write audit`` — R3G-02 adversarial audit CLI."""
    from backend.app.ops.sandbox_clean_write.adversarial_audit import (
        AdversarialAuditRequest,
        run_adversarial_audit,
    )
    from backend.app.ops.sandbox_clean_write.audit_decision import write_audit_decision
    from backend.app.ops.sandbox_clean_write.rehearsal_runner import (
        RehearsalRunnerError,
        assert_sandbox_db_allowed,
    )

    try:
        assert_sandbox_db_allowed(sandbox_db, no_production_mutation=True)
    except RehearsalRunnerError as exc:
        raise CliFailure(
            error_code="INVALID_INPUT",
            message=str(exc),
            docs_anchor="docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_02_PRE_PRODUCTION_ADVERSARIAL_AUDIT.md",
        ) from exc

    result = run_adversarial_audit(
        AdversarialAuditRequest(
            rehearsal_report=rehearsal_report,
            sandbox_db=sandbox_db,
            evidence_dir=evidence_dir,
        )
    )
    write_audit_decision(decision_report, result)
    payload = result.serialize()
    payload["decision_report_path"] = str(decision_report)
    return payload


def sandbox_clean_write_promote(
    *,
    approval_file: Path,
    audit_decision: Path,
    before_proof: Path,
    after_proof: Path,
    rollback_plan: Path,
    evidence_dir: Path | None = None,
    dry_run: bool = True,
    execute: bool = False,
    allow_live_fetch: bool = False,
    fred_authorization: Path | None = None,
) -> dict[str, Any]:
    """``qmd data sandbox-clean-write promote`` — R3G-03 limited production entry CLI."""
    from backend.app.ops.sandbox_clean_write.limited_production_entry import (
        LimitedProductionEntryError,
        PromoteRequest,
        run_limited_production_entry,
    )

    if execute and dry_run:
        raise CliFailure(
            error_code="INVALID_INPUT",
            message="--execute requires --no-dry-run",
            docs_anchor="docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_03_LIMITED_PRODUCTION_CLEAN_WRITE.md",
        )
    if not approval_file.is_file():
        raise CliFailure(
            error_code="INVALID_INPUT",
            message=f"missing approval file: {approval_file}",
            docs_anchor="docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_03_LIMITED_PRODUCTION_CLEAN_WRITE.md",
        )
    if not audit_decision.is_file():
        raise CliFailure(
            error_code="INVALID_INPUT",
            message=f"missing audit decision: {audit_decision}",
            docs_anchor="docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_03_LIMITED_PRODUCTION_CLEAN_WRITE.md",
        )
    if not before_proof.is_file():
        raise CliFailure(
            error_code="INVALID_INPUT",
            message=f"missing before proof: {before_proof}",
            docs_anchor="docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_03_LIMITED_PRODUCTION_CLEAN_WRITE.md",
        )
    if not rollback_plan.is_file():
        raise CliFailure(
            error_code="INVALID_INPUT",
            message=f"missing rollback plan: {rollback_plan}",
            docs_anchor="docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_03_LIMITED_PRODUCTION_CLEAN_WRITE.md",
        )
    try:
        return run_limited_production_entry(
            PromoteRequest(
                approval_file=approval_file,
                audit_decision=audit_decision,
                before_proof=before_proof,
                after_proof=after_proof,
                rollback_plan=rollback_plan,
                evidence_dir=evidence_dir,
                dry_run=dry_run,
                execute=execute,
                allow_live_fetch=allow_live_fetch,
                fred_authorization=fred_authorization,
            )
        )
    except LimitedProductionEntryError as exc:
        raise CliFailure(
            error_code=getattr(exc, "code", None) or "INVALID_INPUT",
            message=str(exc),
            docs_anchor="docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_03_LIMITED_PRODUCTION_CLEAN_WRITE.md",
        ) from exc
