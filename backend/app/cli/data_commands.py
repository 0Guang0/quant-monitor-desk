"""`qmd data` command implementations (R3F-CLI-01)."""

from __future__ import annotations

import json
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
    operation: str | None = None,
    dry_run: bool = True,
    start: str | None = None,
    end: str | None = None,
    since: str | None = None,
) -> dict[str, Any]:
    if not dry_run:
        raise CliFailure(
            error_code="USER_AUTH_REQUIRED",
            message=(
                "qmd data sync without --dry-run requires explicit operator "
                "confirmation (not enabled by default)"
            ),
            docs_anchor="docs/ops/data_sync_quick_reference.md",
            manual_confirmation_required=True,
        )
    op = operation or _default_operation(data_domain)
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
    return {
        "command": "sync",
        "dry_run": True,
        "data_domain": data_domain,
        "operation": op,
        "window": {"start": start, "end": end, "since": since},
        "route_status": preview["route_status"],
        "selected_source_id": preview["selected_source_id"],
        "resource_guard_decision": guard_decision.value,
        "message": "dry-run only; no fetch or DB writes performed",
    }


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


def health_check(*, data_domain: str | None = None) -> dict[str, Any]:
    return {
        "command": "health",
        "dry_run": True,
        "side_effects_allowed": False,
        "data_domain": data_domain,
        "status": "not_implemented_phase_c",
        "message": "read-only health checks ship in Batch 6 Phase C; use qmd-ops db-inspect for v1",
        "docs_anchor": "docs/ops/data_health_cli.md",
    }


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
