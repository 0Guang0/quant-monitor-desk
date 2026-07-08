"""`qmd data` command implementations (R3F-CLI-01)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from backend.app.cli.errors import CliFailure, error_for_route_status
from backend.app.config import DATA_ROOT
from backend.app.core.resource_guard import Decision, ResourceGuard
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
    if source_id is not None:
        from backend.app.cli.incremental_sync_router import sync_incremental_by_source_id

        return sync_incremental_by_source_id(
            source_id=source_id,
            dry_run=dry_run,
            data_domain=data_domain,
            operation=operation,
            instrument_id=instrument_id,
            end=end,
            since=since,
            series_ids=series_ids,
            start=start,
        )
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
        from backend.app.cli.phase1_acceptance import (
            dry_run_envelope_for_plan,
            merge_payload_with_envelope,
            resolve_cli_data_root,
        )

        envelope = dry_run_envelope_for_plan(
            job_kind="sync",
            trigger="qmd-data data sync",
            data_root=resolve_cli_data_root(),
            route_payload={
                "data_domain": data_domain,
                "selected_source_id": preview["selected_source_id"],
                "operation": op,
                "route_status": preview["route_status"],
                "route_plan_id": preview.get("route_plan", {}).get("route_plan_id"),
            },
        )
        return merge_payload_with_envelope(payload, envelope)

    raise CliFailure(
        error_code="USER_AUTH_REQUIRED",
        message=(
            "qmd data sync without --dry-run requires explicit operator "
            "confirmation (not enabled by default)"
        ),
        docs_anchor="docs/ops/data_sync_quick_reference.md",
        manual_confirmation_required=True,
    )


def _parse_sync_date(value: str, *, field: str) -> date:
    try:
        return date.fromisoformat(value[:10])
    except ValueError as exc:
        raise CliFailure(
            error_code="INVALID_INPUT",
            message=f"invalid {field} date: {value!r}",
            docs_anchor="docs/ops/data_sync_quick_reference.md",
        ) from exc


def _require_phase1_live_data_root(data_root: Path) -> None:
    from backend.app.cli.phase1_acceptance import require_phase1_data_root_for_live

    require_phase1_data_root_for_live(data_root)


def sync_baostock_incremental(
    *,
    dry_run: bool = True,
    instrument_id: str | None = None,
    end: str | None = None,
    since: str | None = None,
    empty_table_lookback_days: int = 30,
) -> dict[str, Any]:
    """``qmd data sync --domain cn_equity_daily_bar`` — watermark + orchestrator gold path."""
    from datetime import UTC, datetime

    from backend.app.ops.baostock_incremental_run import resolve_baostock_incremental_use_mock
    from backend.app.ops.sandbox_clean_write.clean_write_targets import resolve_clean_write_target
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
    from backend.app.config import PROJECT_ROOT, _path_env

    symbol = instrument_id or "sh.600519"
    data_root = _path_env("QMD_DATA_ROOT", PROJECT_ROOT / "data")
    db = data_root / "duckdb" / "quant_monitor.duckdb"

    if not dry_run:
        from backend.app.cli.phase1_acceptance import (
            require_phase1_data_root_for_live,
            run_phase1_sync_live,
        )

        require_phase1_data_root_for_live(data_root)
        return run_phase1_sync_live(
            source_id="baostock",
            data_domain=data_domain,
            data_root=data_root,
            end=end,
            instrument_id=symbol,
        )

    from backend.app.cli.incremental_sync_router import (
        _require_audit_sandbox_data_root,
        _sandbox_db_readable,
    )

    _require_audit_sandbox_data_root(data_root)

    end_date = _parse_sync_date(end, field="end") if end else datetime.now(UTC).date()
    watermark: date | None = None
    if _sandbox_db_readable(data_root) and db.is_file():
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
    product_live = not resolve_baostock_incremental_use_mock()
    payload: dict[str, Any] = {
        "command": "sync",
        "dry_run": True,
        "source_id": "baostock",
        "product_live": product_live,
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
    payload["message"] = "dry-run only; watermark window computed, no fetch or DB writes"
    return payload


def _tier_a_backfill_route_preview(
    *, source_id: str, data_domain: str, operation: str
):
    """Route preview with runtime source enable (ADR-009 dry-run parity)."""
    from backend.app.datasources.capability_registry import SourceCapabilityRegistry
    from backend.app.datasources.route_planner import SourceRoutePlanner
    from backend.app.datasources.service import DataSourceService
    from backend.app.ops.macro_incremental_common import enabled_source_registry

    if source_id == "fred" and data_domain == "macro_series":
        from backend.app.ops.fred_incremental_run import build_fred_incremental_preview_service

        preview_svc = build_fred_incremental_preview_service()
        plan = preview_svc.preview_route(data_domain=data_domain, operation=operation)
    else:
        registry = enabled_source_registry(source_id=source_id, data_domain=data_domain)
        caps = SourceCapabilityRegistry()
        caps.load()
        planner = SourceRoutePlanner(source_registry=registry, capability_registry=caps)
        planner._platform_allows = lambda _sid: (True, None)
        service = DataSourceService(
            staged_fixture_mode=False,
            source_registry=registry,
            capability_registry=caps,
            route_planner=planner,
        )
        plan = service.preview_route(data_domain=data_domain, operation=operation)
    guard_decision, guard_reason = ResourceGuard().check()
    return plan, guard_decision, guard_reason


def backfill_plan(
    *,
    data_domain: str,
    source_id: str,
    start: str,
    end: str,
    max_shards: int | None = None,
    truncate_to_cap: bool = False,
    dry_run: bool = True,
    instrument_id: str | None = None,
    trigger_reason: str = "eco_catchup",
    resume_job_id: str | None = None,
) -> dict[str, Any]:
    """``qmd data backfill`` — bounded shard plan + orchestrator gold path (R3-DCP-09)."""
    from backend.app.config import PROJECT_ROOT, _path_env
    from backend.app.ops.baostock_incremental_run import (
        build_baostock_incremental_service,
        resolve_baostock_incremental_use_mock,
        run_baostock_bar_backfill,
    )
    from backend.app.ops.sandbox_clean_write.clean_write_targets import resolve_clean_write_target
    from backend.app.ops.sandbox_clean_write.rehearsal_runner import (
        RehearsalRunnerError,
        assert_sandbox_db_allowed,
    )
    from backend.app.sync.incremental_source_registry import (
        UnknownTierAIncrementalSourceError,
        resolve_tier_a_incremental,
    )
    from backend.app.sync.jobs import (
        ABSOLUTE_MAX_BACKFILL_SHARDS,
        DEFAULT_MAX_BACKFILL_SHARDS,
        BackfillShardCapExceededError,
        plan_backfill_shards,
    )
    from backend.app.sync.orchestrator import DataSyncOrchestrator

    tier_a_operations = {
        "cn_equity_daily_bar": "fetch_daily_bar",
        "macro_series": "fetch_macro_series",
        "us_treasury_yield_curve": "fetch_yield_curve",
        "central_bank_policy": "fetch_policy_rate",
        "development_indicator": "fetch_development_indicator",
        "cot_positioning": "fetch_cot_report",
        "cn_announcements": "fetch_announcement_index",
        "us_filings": "fetch_company_filings",
        "us_equity_daily_bar": "fetch_daily_bar",
        "crypto_options_surface": "fetch_options_surface",
    }

    try:
        entry = resolve_tier_a_incremental(source_id)
    except UnknownTierAIncrementalSourceError as exc:
        raise CliFailure(
            error_code="INVALID_INPUT",
            message=str(exc),
            docs_anchor="docs/ops/data_sync_quick_reference.md",
        ) from exc
    if data_domain != entry.canonical_domain:
        raise CliFailure(
            error_code="INVALID_INPUT",
            message=(
                f"domain mismatch for source_id={source_id!r}: "
                f"got {data_domain!r}, expected {entry.canonical_domain!r}"
            ),
            docs_anchor="docs/ops/data_sync_quick_reference.md",
        )
    op = tier_a_operations.get(data_domain)
    if op is None:
        raise CliFailure(
            error_code="CAPABILITY_MISSING",
            message=f"no backfill operation for data_domain={data_domain!r}",
            docs_anchor="docs/decisions/ADR-011-bounded-backfill-cap-and-ci-nightly.md",
        )

    resolved_max = DEFAULT_MAX_BACKFILL_SHARDS if max_shards is None else max_shards
    if resolved_max < 1 or resolved_max > ABSOLUTE_MAX_BACKFILL_SHARDS:
        raise CliFailure(
            error_code="INVALID_INPUT",
            message=(
                f"max_shards must be between 1 and {ABSOLUTE_MAX_BACKFILL_SHARDS}; "
                f"got {resolved_max}"
            ),
            docs_anchor="docs/decisions/ADR-011-bounded-backfill-cap-and-ci-nightly.md",
        )

    date_start = _parse_sync_date(start, field="start")
    date_end = _parse_sync_date(end, field="end")
    if date_end < date_start:
        raise CliFailure(
            error_code="INVALID_INPUT",
            message="end must be on or after start",
            docs_anchor="docs/ops/data_sync_quick_reference.md",
        )

    try:
        shards = plan_backfill_shards(
            date_start,
            date_end,
            max_shards=resolved_max,
            truncate_to_cap=truncate_to_cap,
        )
    except BackfillShardCapExceededError as exc:
        raise CliFailure(
            error_code="BACKFILL_CAP_EXCEEDED",
            message=str(exc),
            docs_anchor="docs/decisions/ADR-011-bounded-backfill-cap-and-ci-nightly.md",
            retryable=False,
        ) from exc

    effective_end = shards[-1][2] if shards else date_end
    plan, guard_decision, guard_reason = _tier_a_backfill_route_preview(
        source_id=source_id,
        data_domain=data_domain,
        operation=op,
    )
    symbol = instrument_id or (
        "DGS10" if data_domain == "macro_series" else "sh.600519"
    )
    data_root = _path_env("QMD_DATA_ROOT", PROJECT_ROOT / "data")
    db = data_root / "duckdb" / "quant_monitor.duckdb"
    use_mock = (
        resolve_baostock_incremental_use_mock()
        if source_id == "baostock"
        else True
    )
    product_live = not use_mock
    target = resolve_clean_write_target(data_domain)

    shard_plan = [
        {"task_id": task_id, "date_start": s.isoformat(), "date_end": e.isoformat()}
        for task_id, s, e in shards
    ]
    payload: dict[str, Any] = {
        "command": "backfill",
        "dry_run": dry_run,
        "source_id": source_id,
        "product_live": product_live,
        "data_domain": data_domain,
        "operation": op,
        "instrument_id": symbol,
        "window": {
            "date_start": date_start.isoformat(),
            "date_end": date_end.isoformat(),
            "effective_date_end": effective_end.isoformat(),
        },
        "max_shards": resolved_max,
        "truncate_to_cap": truncate_to_cap,
        "shard_count": len(shards),
        "shards": shard_plan,
        "route_status": plan.route_status,
        "selected_source_id": plan.selected_source_id or source_id,
        "resource_guard_decision": guard_decision.value,
        "clean_table": target.target_table,
        "write_mode": target.write_mode,
    }

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
            detail=f"backfill blocked for domain={data_domain!r}",
        )

    if dry_run:
        from backend.app.cli.phase1_acceptance import (
            build_backfill_evidence,
            dry_run_envelope_for_plan,
            merge_payload_with_envelope,
        )
        from backend.app.cli.incremental_sync_router import _require_audit_sandbox_data_root

        _require_audit_sandbox_data_root(data_root)
        payload["message"] = "dry-run only; shard plan computed, no fetch or DB writes"
        envelope = dry_run_envelope_for_plan(
            job_kind="backfill",
            trigger=f"qmd-data data backfill --source-id {source_id}",
            data_root=data_root,
            route_payload={
                "data_domain": data_domain,
                "selected_source_id": plan.selected_source_id or source_id,
                "operation": op,
                "route_status": plan.route_status,
                "route_plan_id": getattr(plan, "route_plan_id", None),
            },
            extra={
                "backfill_evidence": build_backfill_evidence(
                    trigger_reason=trigger_reason,
                    shard_plan=shard_plan,
                ),
            },
        )
        return merge_payload_with_envelope(payload, envelope)

    from backend.app.cli.phase1_acceptance import (
        is_production_equivalent_acceptance_root,
        run_phase1_backfill_live,
    )

    if is_production_equivalent_acceptance_root(data_root):
        return run_phase1_backfill_live(
            source_id=source_id,
            data_domain=data_domain,
            data_root=data_root,
            date_start=date_start,
            date_end=effective_end,
            instrument_id=instrument_id,
            shard_plan=shard_plan,
            trigger_reason=trigger_reason,
            resume_job_id=resume_job_id,
        )

    from backend.app.cli.phase1_acceptance import require_phase1_data_root_for_live

    require_phase1_data_root_for_live(data_root)
    raise AssertionError("unreachable")


def full_load_plan(
    *,
    data_domain: str,
    source_id: str,
    start: str,
    end: str | None = None,
    max_shards: int | None = None,
    truncate_to_cap: bool = False,
    dry_run: bool = True,
    instrument_id: str | None = None,
) -> dict[str, Any]:
    """``qmd data full-load`` — §13.4.1 shard plan + orchestrator run_full_load gold path."""
    import uuid
    from datetime import UTC, datetime

    from backend.app.cli.phase1_acceptance import tier_a_fetch_operation
    from backend.app.config import PROJECT_ROOT, _path_env
    from backend.app.ops.baostock_incremental_run import (
        build_baostock_incremental_service,
        resolve_baostock_incremental_use_mock,
    )
    from backend.app.ops.sandbox_clean_write.clean_write_targets import resolve_clean_write_target
    from backend.app.ops.sandbox_clean_write.rehearsal_runner import (
        RehearsalRunnerError,
        assert_sandbox_db_allowed,
    )
    from backend.app.sync.incremental_source_registry import (
        UnknownTierAIncrementalSourceError,
        resolve_tier_a_incremental,
    )
    from backend.app.sync.jobs import (
        ABSOLUTE_MAX_BACKFILL_SHARDS,
        DEFAULT_MAX_BACKFILL_SHARDS,
        BackfillShardCapExceededError,
        SyncJobSpec,
        plan_backfill_shards,
    )
    from backend.app.sync.orchestrator import DataSyncOrchestrator

    try:
        tier_entry = resolve_tier_a_incremental(source_id)
    except UnknownTierAIncrementalSourceError as exc:
        raise CliFailure(
            error_code="CAPABILITY_MISSING",
            message=str(exc),
            docs_anchor="docs/modules/data_sync_orchestrator.md#1341-fullloadjob",
            retryable=False,
        ) from exc
    if data_domain != tier_entry.canonical_domain:
        raise CliFailure(
            error_code="INVALID_INPUT",
            message=(
                f"domain mismatch for source_id={source_id!r}: "
                f"got {data_domain!r}, expected {tier_entry.canonical_domain!r}"
            ),
            docs_anchor="docs/modules/data_sync_orchestrator.md#1341-fullloadjob",
        )

    resolved_max = DEFAULT_MAX_BACKFILL_SHARDS if max_shards is None else max_shards
    if resolved_max < 1 or resolved_max > ABSOLUTE_MAX_BACKFILL_SHARDS:
        raise CliFailure(
            error_code="INVALID_INPUT",
            message=(
                f"max_shards must be between 1 and {ABSOLUTE_MAX_BACKFILL_SHARDS}; "
                f"got {resolved_max}"
            ),
            docs_anchor="docs/modules/data_sync_orchestrator.md#1341-fullloadjob",
        )

    date_start = _parse_sync_date(start, field="start")
    date_end = _parse_sync_date(end, field="end") if end else datetime.now(UTC).date()
    if date_end < date_start:
        raise CliFailure(
            error_code="INVALID_INPUT",
            message="end must be on or after start",
            docs_anchor="docs/ops/data_sync_quick_reference.md",
        )

    try:
        shards = plan_backfill_shards(
            date_start,
            date_end,
            max_shards=resolved_max,
            truncate_to_cap=truncate_to_cap,
        )
    except BackfillShardCapExceededError as exc:
        raise CliFailure(
            error_code="BACKFILL_CAP_EXCEEDED",
            message=str(exc),
            docs_anchor="docs/decisions/ADR-011-bounded-backfill-cap-and-ci-nightly.md",
            retryable=False,
        ) from exc

    effective_end = shards[-1][2] if shards else date_end
    op = tier_a_fetch_operation(data_domain)
    symbol = instrument_id or (
        "DGS10" if data_domain == "macro_series" else "sh.600519"
    )
    data_root = _path_env("QMD_DATA_ROOT", PROJECT_ROOT / "data")
    shard_plan = [
        {"task_id": task_id, "date_start": s.isoformat(), "date_end": e.isoformat()}
        for task_id, s, e in shards
    ]

    from backend.app.cli.phase1_acceptance import (
        is_production_equivalent_acceptance_root,
        run_phase1_full_load_live,
    )

    if not dry_run and is_production_equivalent_acceptance_root(data_root):
        import uuid

        fl_run_id = f"p1-fl-{uuid.uuid4().hex[:12]}"
        return run_phase1_full_load_live(
            source_id=source_id,
            data_domain=data_domain,
            data_root=data_root,
            date_start=date_start,
            date_end=effective_end,
            instrument_id=symbol,
            shard_plan=shard_plan,
            run_id=fl_run_id,
        )

    preview = route_preview(data_domain=data_domain, operation=op)
    guard_decision, guard_reason = ResourceGuard().check()
    use_mock = resolve_baostock_incremental_use_mock()
    product_live = not use_mock
    target = resolve_clean_write_target(data_domain)

    payload: dict[str, Any] = {
        "command": "full-load",
        "dry_run": dry_run,
        "source_id": source_id,
        "product_live": product_live,
        "data_domain": data_domain,
        "operation": op,
        "instrument_id": symbol,
        "window": {
            "date_start": date_start.isoformat(),
            "date_end": date_end.isoformat(),
            "effective_date_end": effective_end.isoformat(),
        },
        "max_shards": resolved_max,
        "truncate_to_cap": truncate_to_cap,
        "shard_count": len(shards),
        "shards": shard_plan,
        "route_status": preview["route_status"],
        "selected_source_id": preview["selected_source_id"],
        "resource_guard_decision": guard_decision.value,
        "clean_table": target.target_table,
        "write_mode": target.write_mode,
    }

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
            detail=f"full-load blocked for domain={data_domain!r}",
        )

    if dry_run:
        import uuid

        from backend.app.cli.phase1_acceptance import (
            build_full_load_evidence,
            dry_run_envelope_for_plan,
            merge_payload_with_envelope,
        )
        from backend.app.cli.incremental_sync_router import _require_audit_sandbox_data_root

        _require_audit_sandbox_data_root(data_root)
        fl_run_id = f"p1-fl-{uuid.uuid4().hex[:12]}"
        payload["message"] = "dry-run only; full-load shard plan computed, no fetch or DB writes"
        envelope = dry_run_envelope_for_plan(
            job_kind="full-load",
            trigger=f"qmd-data data full-load --source-id {source_id}",
            data_root=data_root,
            run_id=fl_run_id,
            route_payload={
                "data_domain": data_domain,
                "selected_source_id": preview["selected_source_id"],
                "operation": op,
                "route_status": preview["route_status"],
                "route_plan_id": preview.get("route_plan", {}).get("route_plan_id"),
            },
            extra={
                "full_load_evidence": build_full_load_evidence(
                    run_id=fl_run_id,
                    shard_plan=shard_plan,
                ),
            },
        )
        return merge_payload_with_envelope(payload, envelope)

    from backend.app.cli.phase1_acceptance import require_phase1_data_root_for_live

    require_phase1_data_root_for_live(data_root)
    raise AssertionError("unreachable")


def sync_mootdx_incremental(
    *,
    dry_run: bool = True,
    instrument_id: str | None = None,
    end: str | None = None,
    since: str | None = None,
    empty_table_lookback_days: int = 30,
) -> dict[str, Any]:
    """``qmd data sync --source-id mootdx`` — watermark + orchestrator gold path."""
    from datetime import UTC, datetime

    from backend.app.ops.mootdx_incremental_run import resolve_mootdx_incremental_use_mock
    from backend.app.ops.sandbox_clean_write.clean_write_targets import resolve_clean_write_target
    from backend.app.sync.watermark import (
        IncrementalWindow,
        compute_incremental_window,
        incremental_window_is_empty,
        read_bar_trade_date_watermark,
    )

    data_domain = "cn_equity_daily_bar"
    op = "fetch_daily_bar"
    from backend.app.datasources.service import DataSourceService
    from backend.app.ops.macro_incremental_common import enabled_source_registry

    mootdx_registry = enabled_source_registry(source_id="mootdx", data_domain=data_domain)
    preview_svc = DataSourceService(
        staged_fixture_mode=False, source_registry=mootdx_registry
    )
    plan = preview_svc.preview_route(data_domain=data_domain, operation=op)
    guard_decision, guard_reason = ResourceGuard().check()
    preview = {
        "route_status": plan.route_status,
        "selected_source_id": plan.selected_source_id,
    }
    from backend.app.config import PROJECT_ROOT, _path_env

    symbol = instrument_id or "sh.600519"
    data_root = _path_env("QMD_DATA_ROOT", PROJECT_ROOT / "data")
    db = data_root / "duckdb" / "quant_monitor.duckdb"

    if not dry_run:
        from backend.app.cli.phase1_acceptance import (
            require_phase1_data_root_for_live,
            run_phase1_sync_live,
        )

        require_phase1_data_root_for_live(data_root)
        return run_phase1_sync_live(
            source_id="mootdx",
            data_domain=data_domain,
            data_root=data_root,
            end=end,
            instrument_id=symbol,
        )

    from backend.app.cli.incremental_sync_router import (
        _require_audit_sandbox_data_root,
        _sandbox_db_readable,
    )

    _require_audit_sandbox_data_root(data_root)

    end_date = _parse_sync_date(end, field="end") if end else datetime.now(UTC).date()
    watermark: date | None = None
    if _sandbox_db_readable(data_root) and db.is_file():
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
    product_live = not resolve_mootdx_incremental_use_mock()
    payload: dict[str, Any] = {
        "command": "sync",
        "dry_run": True,
        "source_id": "mootdx",
        "product_live": product_live,
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
    payload["message"] = "dry-run only; watermark window computed, no fetch or DB writes"
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
            docs_anchor="docs/decisions/ADR-008-product-live-env-gate.md",
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


def scheduler_run(
    *,
    profile: str,
    dry_run: bool = True,
    job_type_filter: str | None = None,
) -> dict[str, Any]:
    """``qmd data scheduler run`` — §13.6 profile → registry → execute_binding."""
    from backend.app.config import PROJECT_ROOT, _path_env
    from backend.app.db.connection import ConnectionManager
    from backend.app.db.migrate import apply_migrations
    from backend.app.sync.scheduler import run_profile

    guard_decision, guard_reason = ResourceGuard().check()
    if guard_decision == Decision.HARD_STOP and not dry_run:
        raise CliFailure(
            error_code="RESOURCE_GUARD_PAUSED",
            message=guard_reason or "resource guard paused",
            docs_anchor="docs/ops/ERROR_CODE_GUIDE.md#resource-guard-paused",
            retryable=True,
        )

    data_root = _path_env("QMD_DATA_ROOT", PROJECT_ROOT / "data")
    db = data_root / "duckdb" / "quant_monitor.duckdb"
    if dry_run:
        from backend.app.cli.incremental_sync_router import _require_audit_sandbox_data_root

        _require_audit_sandbox_data_root(data_root)
        cm = None
    else:
        from backend.app.cli.phase1_acceptance import require_phase1_data_root_for_live

        require_phase1_data_root_for_live(data_root)
        db.parent.mkdir(parents=True, exist_ok=True)
        cm = ConnectionManager(db_path=db)
        with cm.writer() as con:
            apply_migrations(con)

    try:
        from backend.app.cli.phase1_acceptance import _build_datasource_service

        datasource_service = None if dry_run else _build_datasource_service()
        run = run_profile(
            profile,
            dry_run=dry_run,
            job_type_filter=job_type_filter,
            connection_manager=cm,
            datasource_service=datasource_service,
        )
    except KeyError as exc:
        raise CliFailure(
            error_code="INVALID_INPUT",
            message=str(exc),
            docs_anchor="docs/modules/data_sync_orchestrator.md#136-调度计划",
        ) from exc

    from backend.app.cli.phase1_acceptance import (
        aggregate_scheduler_parent_report,
        build_acceptance_envelope,
        build_scheduler_child_live_envelope,
        dry_run_envelope_for_plan,
        is_production_equivalent_acceptance_root,
        merge_payload_with_envelope,
        resolve_cli_data_root,
    )

    resolved_root = resolve_cli_data_root()
    child_envelopes: list[dict[str, Any]] = []
    for job in run.results:
        child_payload: dict[str, Any] = {
            "job_type": job.job_type,
            "domain": job.domain,
            "source_id": job.source_id,
            "status": job.status,
            "binding_ids": list(job.binding_ids),
            "message": job.message,
            "job_id": job.job_id,
            "required": job.job_type in {"incremental", "backfill", "full_load"},
        }
        if job.window is not None:
            child_payload["window"] = job.window
        if job.domain and job.source_id:
            if dry_run:
                child_env = dry_run_envelope_for_plan(
                    job_kind="scheduler",
                    trigger=f"scheduler:{profile}:{job.job_type}",
                    data_root=resolved_root,
                    source_id=job.source_id,
                    data_domain=job.domain,
                )
            else:
                if job.acceptance_report is not None and job.domain and job.source_id:
                    child_env = build_scheduler_child_live_envelope(
                        profile=profile,
                        job_type=job.job_type,
                        source_id=job.source_id,
                        data_domain=job.domain,
                        data_root=resolved_root,
                        acceptance_report=job.acceptance_report,
                        acceptance_extra=job.acceptance_extra,
                        guard_decision=guard_decision.value,
                    )
                else:
                    from backend.app.ops.source_route_db_acceptance import AcceptanceReport

                    child_status = job.status
                    if child_status in {"COMPLETED", "PASS"}:
                        child_status = "PASS"
                    elif child_status == "SKIPPED":
                        child_status = "SKIPPED"
                    elif child_status not in {
                        "BLOCKED",
                        "FAIL_EXTERNAL",
                        "CONTRACT_VIOLATION",
                        "FAIL",
                        "FAILED_FINAL",
                        "FAILED_RETRYABLE",
                    }:
                        child_status = "FAIL"
                    child_failure = job.acceptance_report.failure_class if job.acceptance_report else (
                        "NONE" if child_status == "PASS" else child_status
                    )
                    if child_failure not in {
                        "NONE",
                        "BLOCKED",
                        "FAIL_EXTERNAL",
                        "CONTRACT_VIOLATION",
                    }:
                        child_failure = "FAIL"
                    child_env = build_acceptance_envelope(
                        AcceptanceReport(
                            source_id=job.source_id or profile,
                            data_domain=job.domain or "scheduler",
                            operation=job.job_type,
                            route_plan_id=None,
                            route_grade="primary",
                            implementation_mode="live",
                            write_grade="not_written",
                            source_used=job.source_id or profile,
                            source_role="primary",
                            source_switched=False,
                            failure_class=child_failure,
                            status=child_status,
                            errors=() if child_status == "PASS" else (job.message or "",),
                        ),
                        job_kind="scheduler",
                        trigger=f"scheduler:{profile}:{job.job_type}",
                        data_root=resolved_root,
                        dry_run=False,
                        extra={
                            "sync_job_id": job.job_id,
                            "resource_guard_decision": guard_decision.value,
                        },
                    )
            child_payload.update(child_env)
        child_payload["status"] = job.status
        child_envelopes.append(child_payload)

    parent = aggregate_scheduler_parent_report(
        profile=profile,
        data_root=resolved_root,
        dry_run=dry_run,
        child_envelopes=child_envelopes,
        skipped_non_core=run.skipped_non_core,
        resource_guard_decision=guard_decision.value,
    )
    if is_production_equivalent_acceptance_root(resolved_root) and not dry_run:
        from backend.app.ops.source_route_db_acceptance import AcceptanceReport as SpineReport
        from backend.app.ops.source_route_db_acceptance import write_acceptance_report

        parent_report = SpineReport(
            source_id=profile,
            data_domain="scheduler",
            operation="run_profile",
            route_plan_id=None,
            route_grade="primary",
            implementation_mode="live",
            write_grade="not_written",
            source_used=profile,
            source_role="primary",
            source_switched=False,
            failure_class=parent["failure_class"],
            status=parent["status"],
            errors=(),
        )
        report_path = resolved_root / "reports" / f"scheduler-{profile}.json"
        write_acceptance_report(parent_report, report_path)
        parent["acceptance_report_path"] = str(report_path)

    payload: dict[str, Any] = {
        "command": "scheduler",
        "subcommand": "run",
        "profile": run.profile,
        "dry_run": run.dry_run,
        "skipped_non_core": run.skipped_non_core,
        "resource_guard_decision": guard_decision.value,
        "jobs": child_envelopes,
        "message": (
            "dry-run only; profile expanded via binding registry"
            if dry_run
            else "scheduler run completed"
        ),
    }
    return merge_payload_with_envelope(payload, parent)


def incremental_profile_plan(*, profile: str, dry_run: bool = True) -> dict[str, Any]:
    """``qmd data incremental --profile`` — incremental jobs only from scheduler profile."""
    payload = scheduler_run(profile=profile, dry_run=dry_run)
    payload["command"] = "incremental"
    payload["jobs"] = [j for j in payload["jobs"] if j["job_type"] == "incremental"]
    return payload


def revision_audit_plan(
    *,
    data_domain: str,
    market_id: str,
    lookback_days: int = 90,
    dry_run: bool = True,
) -> dict[str, Any]:
    """``qmd data revision-audit`` — §13.7 revision audit runner."""
    import uuid

    from backend.app.config import PROJECT_ROOT, _path_env
    from backend.app.db.connection import ConnectionManager
    from backend.app.db.migrate import apply_migrations
    from backend.app.sync.jobs import SyncJobSpec
    from backend.app.sync.orchestrator import DataSyncOrchestrator

    guard_decision, guard_reason = ResourceGuard().check()
    if guard_decision.value != "OK":
        raise CliFailure(
            error_code="RESOURCE_GUARD_PAUSED",
            message=guard_reason or "resource guard paused",
            docs_anchor="docs/ops/ERROR_CODE_GUIDE.md#resource-guard-paused",
            retryable=True,
        )

    suffix = uuid.uuid4().hex[:8]
    payload: dict[str, Any] = {
        "command": "revision-audit",
        "dry_run": dry_run,
        "data_domain": data_domain,
        "market_id": market_id,
        "lookback_days": lookback_days,
        "resource_guard_decision": guard_decision.value,
    }
    if dry_run:
        from backend.app.cli.incremental_sync_router import _require_audit_sandbox_data_root

        data_root = _path_env("QMD_DATA_ROOT", PROJECT_ROOT / "data")
        _require_audit_sandbox_data_root(data_root)
        payload["message"] = "dry-run only; revision audit plan, no DB writes"
        return payload

    data_root = _path_env("QMD_DATA_ROOT", PROJECT_ROOT / "data")
    _require_phase1_live_data_root(data_root)
    db = data_root / "duckdb" / "quant_monitor.duckdb"
    db.parent.mkdir(parents=True, exist_ok=True)
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    orch = DataSyncOrchestrator(cm)
    spec = SyncJobSpec(
        run_id=f"rev-audit-{suffix}",
        job_id=f"job-rev-audit-{suffix}",
        job_type="revision_audit",
        data_domain=data_domain,
        market_id=market_id,
        source_id="fred",
        adapter_id=None,
        date_start=None,
        date_end=None,
        instrument_id=None,
        partition_key=None,
        trigger_reason=f"revision_audit:{lookback_days}d",
    )
    result = orch.run_revision_audit(spec)
    payload["job_id"] = result.job_id
    payload["job_status"] = result.status
    payload["message"] = result.message or "revision audit completed"
    return payload


def reconcile_plan(*, conflict_id: str, dry_run: bool = True) -> dict[str, Any]:
    """``qmd data reconcile`` — §13.7 conflict reconcile."""
    from backend.app.config import PROJECT_ROOT, _path_env
    from backend.app.db.connection import ConnectionManager
    from backend.app.db.migrate import apply_migrations

    if not conflict_id:
        raise CliFailure(
            error_code="INVALID_INPUT",
            message="--conflict-id is required",
            docs_anchor="docs/modules/data_sync_orchestrator.md#137-cli-设计",
        )

    data_root = _path_env("QMD_DATA_ROOT", PROJECT_ROOT / "data")
    db = data_root / "duckdb" / "quant_monitor.duckdb"
    payload: dict[str, Any] = {
        "command": "reconcile",
        "dry_run": dry_run,
        "conflict_id": conflict_id,
    }
    if dry_run:
        from backend.app.cli.incremental_sync_router import _require_audit_sandbox_data_root

        _require_audit_sandbox_data_root(data_root)
        payload["message"] = "dry-run only; reconcile plan, no refetch"
        return payload

    _require_phase1_live_data_root(data_root)
    db.parent.mkdir(parents=True, exist_ok=True)
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
        row = con.execute(
            "SELECT conflict_id, reconcile_status FROM source_conflict WHERE conflict_id = ?",
            [conflict_id],
        ).fetchone()
    if row is None:
        raise CliFailure(
            error_code="INVALID_INPUT",
            message=f"unknown conflict_id={conflict_id!r}",
            docs_anchor="docs/modules/data_sync_orchestrator.md#137-cli-设计",
        )
    raise CliFailure(
        error_code="USER_AUTH_REQUIRED",
        message=(
            "qmd data reconcile without --dry-run requires datasource_service= gold path; "
            "use orchestrator API with explicit operator confirmation"
        ),
        docs_anchor="docs/decisions/ADR-006-sync-datasource-service-fail-closed.md",
        manual_confirmation_required=True,
    )


def quality_check_plan(
    *,
    data_domain: str,
    check_date: str,
    dry_run: bool = True,
) -> dict[str, Any]:
    """``qmd data quality-check`` — §13.7 data quality runner."""
    import uuid

    from backend.app.config import PROJECT_ROOT, _path_env
    from backend.app.db.connection import ConnectionManager
    from backend.app.db.migrate import apply_migrations
    from backend.app.sync.jobs import SyncJobSpec
    from backend.app.sync.orchestrator import DataSyncOrchestrator

    _parse_sync_date(check_date, field="date")
    guard_decision, guard_reason = ResourceGuard().check()
    if guard_decision.value != "OK":
        raise CliFailure(
            error_code="RESOURCE_GUARD_PAUSED",
            message=guard_reason or "resource guard paused",
            docs_anchor="docs/ops/ERROR_CODE_GUIDE.md#resource-guard-paused",
            retryable=True,
        )

    suffix = uuid.uuid4().hex[:8]
    payload: dict[str, Any] = {
        "command": "quality-check",
        "dry_run": dry_run,
        "data_domain": data_domain,
        "check_date": check_date,
        "resource_guard_decision": guard_decision.value,
    }
    if dry_run:
        from backend.app.cli.incremental_sync_router import _require_audit_sandbox_data_root

        data_root = _path_env("QMD_DATA_ROOT", PROJECT_ROOT / "data")
        _require_audit_sandbox_data_root(data_root)
        payload["message"] = "dry-run only; quality-check plan, no validation writes"
        return payload

    data_root = _path_env("QMD_DATA_ROOT", PROJECT_ROOT / "data")
    _require_phase1_live_data_root(data_root)
    db = data_root / "duckdb" / "quant_monitor.duckdb"
    db.parent.mkdir(parents=True, exist_ok=True)
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    orch = DataSyncOrchestrator(cm)
    spec = SyncJobSpec(
        run_id=f"dq-{suffix}",
        job_id=f"job-dq-{suffix}",
        job_type="data_quality",
        data_domain=data_domain,
        market_id="GLOBAL",
        source_id="fred",
        adapter_id=None,
        date_start=None,
        date_end=None,
        instrument_id=None,
        partition_key=None,
        trigger_reason=f"quality_check:{check_date}",
    )
    result = orch.run_data_quality(spec)
    payload["job_id"] = result.job_id
    payload["job_status"] = result.status
    payload["message"] = result.message or "data quality check completed"
    return payload


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

