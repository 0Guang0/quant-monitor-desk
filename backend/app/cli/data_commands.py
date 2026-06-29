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
        "product_live": False,
        "data_domain": data_domain,
        "operation": op,
        "window": {"start": start, "end": end, "since": since},
        "route_status": preview["route_status"],
        "selected_source_id": preview["selected_source_id"],
        "resource_guard_decision": guard_decision.value,
        "message": "dry-run only; no fetch or DB writes performed",
    }


def live_fetch(
    *,
    source_id: str,
    data_domain: str,
    operation: str | None = None,
    instrument_id: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """``qmd data live-fetch`` — product live route preview + optional fetch (R3H-08 S08-05)."""
    from backend.app.datasources.product_live_gate import (
        ProductLiveGateError,
        assert_product_live_allowed,
    )
    from backend.app.datasources.product_live_ports import create_product_live_fetch_port
    from backend.app.datasources.fetch_result import FetchRequest

    op = operation or _default_operation(data_domain)
    try:
        assert_product_live_allowed(source_id=source_id, operation=op)
    except ProductLiveGateError as exc:
        raise CliFailure(
            error_code=exc.code,
            message=str(exc),
            docs_anchor="docs/decisions/ADR-027-r3h08-product-live-env-gate.md",
        ) from exc

    service = _service()
    plan = service.preview_route(data_domain=data_domain, operation=op)
    guard_decision, guard_reason = service.check_resource_guard()
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

    port = create_product_live_fetch_port(
        source_id=source_id,
        data_domain=data_domain,
        operation=op,
    )
    req = FetchRequest(
        run_id="qmd-live-fetch",
        source_id=source_id,
        data_domain=data_domain,
        instrument_id=instrument_id,
    )
    body = port.fetch_payload(req)
    payload["row_count"] = body.row_count
    payload["file_type"] = body.file_type
    payload["message"] = "product live fetch completed via DataSourceService gold path port"
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
