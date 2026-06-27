"""R3G-01 sandbox clean-write rehearsal runner — composes QMD gates (sandbox only)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.app.config import DATA_ROOT, PROJECT_ROOT
from backend.app.ops.sandbox_clean_write.path_utils import resolve_sandbox_path, utc_now_iso
from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.datasources.service import DataSourceService
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.db.validation_gate import DbValidationGate
from backend.app.db.write_manager import WriteManager, WriteRequest
from backend.app.ops.data_health import DataHealthReport, DataHealthService
from backend.app.ops.data_health_profiles import run_data_health_profile
from backend.app.ops.mutation_proof import build_production_mutation_proof
from backend.app.ops.mutation_proof import key_table_row_counts as _key_table_row_counts
from backend.app.ops.sandbox_clean_write.rehearsal_loader import (
    load_rehearsal_bundle,
    populate_staging_from_bundle,
)
from backend.app.ops.sandbox_clean_write.rehearsal_plan import (
    RehearsalCandidate,
    RehearsalPlanError,
    load_candidate_set,
    validate_candidate_set,
)
from backend.app.ops.sandbox_clean_write.rehearsal_report import (
    build_data_health_summary,
    build_rehearsal_report,
    write_rehearsal_report,
)
from backend.app.ops.staged_pilot import DEFAULT_PRODUCTION_DB, _staged_conflict_check_summary

REHEARSAL_ID = "r3g01-sandbox-rehearsal-20260627"
VALIDATION_REPORT_ID = "r3g01-rehearsal-clean-write"
CONFLICT_CHECK_JSON = "conflict_check_summary.json"
NO_MUTATION_MD = "production_db_no_mutation_proof.md"
REHEARSAL_SYNTHETIC_QUALITY_FLAG = "r3g01_rehearsal_synthetic_admission"

_DH_TO_VALIDATION_STATUS = {
    "PASS": "PASSED",
    "WARN": "WARNING",
    "FAIL": "FAILED",
    "BLOCKED": "BLOCKED",
}

REQUIRED_GATES = (
    "DataSourceService",
    "SourceRoutePlanner",
    "ResourceGuard",
    "DbValidationGate",
    "WriteManager",
    "QMD-owned data-health profiles",
)


class RehearsalRunnerError(RuntimeError):
    """Rehearsal orchestration failed fail-closed gate."""


@dataclass(frozen=True)
class RehearsalRequest:
    candidate_set: str
    sandbox_db: Path
    evidence_dir: Path
    report_path: Path
    no_production_mutation: bool = True
    dry_run: bool = True
    allow_live_fetch: bool = False
    fred_authorization: Path | None = None


def assert_sandbox_db_allowed(sandbox_db: Path, *, no_production_mutation: bool) -> Path:
    if not no_production_mutation:
        raise RehearsalRunnerError("--no-production-mutation is required for R3G-01")
    resolved = resolve_sandbox_path(sandbox_db)
    prod = DEFAULT_PRODUCTION_DB.resolve()
    # ponytail: read DATA_ROOT at call time — tests may monkeypatch config.DATA_ROOT
    from backend.app import config as app_config

    default_prod = (app_config.DATA_ROOT / "duckdb" / "quant_monitor.duckdb").resolve()
    canonical_prod = (PROJECT_ROOT / "data" / "duckdb" / "quant_monitor.duckdb").resolve()
    if resolved in {prod, default_prod, canonical_prod}:
        raise RehearsalRunnerError("production DB path refused for sandbox rehearsal")
    return resolved


def _coverage_ratio(present: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(min(1.0, present / total), 4)


def _run_source_data_health(
    candidate: RehearsalCandidate,
    evidence_dir: Path,
    *,
    max_rows: int = 1000,
):
    if candidate.source_id in {"baostock", "akshare", "yahoo_finance"}:
        report, *_ = run_data_health_profile(
            profile_id="market_bar_p0",
            domain="market_bar_1d",
            evidence_path=evidence_dir,
            db_path=None,
            start_date=None,
            end_date=None,
            max_rows=max_rows,
        )
        return report
    service = DataHealthService()
    profile = "staged_pilot_v3" if candidate.source_id == "cninfo" else "fred_sandbox_pilot"
    return service.check_evidence_dir(evidence_dir, profile=profile)


def _preview_route(candidate: RehearsalCandidate, service: DataSourceService) -> dict[str, Any]:
    plan = service.preview_route(
        data_domain=candidate.domain,
        operation=candidate.operation,
        run_id=f"{REHEARSAL_ID}-{candidate.source_id}",
        job_id="r3g01-rehearsal-route",
    )
    return plan.to_payload_dict()


def _validation_report_id_for_source(source_id: str) -> str:
    return f"{VALIDATION_REPORT_ID}-{source_id}"


def _rollback_artifact_name(source_id: str) -> str:
    return f"rollback_artifact_{source_id}.json"


def _validation_status_from_dh(dh_report: DataHealthReport) -> str:
    return _DH_TO_VALIDATION_STATUS.get(
        dh_report.overall_status, str(dh_report.overall_status)
    )


def _assert_data_health_admission(dh_report: DataHealthReport, source_id: str) -> None:
    if dh_report.overall_status in {"FAIL", "BLOCKED"}:
        raise RehearsalRunnerError(
            f"data-health overall_status={dh_report.overall_status} blocks write for "
            f"{source_id}: {dh_report.gate_rationale}"
        )
    if not dh_report.sandbox_clean_write_gate_ready:
        raise RehearsalRunnerError(
            f"data-health sandbox_clean_write_gate_ready=false for {source_id}: "
            f"{dh_report.gate_rationale}"
        )


def _db_validation_status_from_dh(dh_report: DataHealthReport) -> str:
    mapped = _validation_status_from_dh(dh_report)
    if mapped in {"PASSED", "WARNING"}:
        return mapped
    return "FAILED"


def _ensure_clean_table(con) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS security_bar_smoke_clean AS
        SELECT * FROM stg_foundation_smoke WHERE 1=0
        """
    )


def _ensure_validation_report(
    con,
    candidate: RehearsalCandidate,
    run_id: str,
    dh_report: DataHealthReport,
) -> str:
    validation_report_id = _validation_report_id_for_source(candidate.source_id)
    db_status = _db_validation_status_from_dh(dh_report)
    fail_count = sum(1 for c in dh_report.checks if c.status == "FAIL")
    warn_count = sum(1 for c in dh_report.checks if c.status == "WARN")
    con.execute(
        """
        INSERT OR REPLACE INTO validation_report (
            validation_report_id, run_id, job_id, data_domain, staging_table,
            source_id, status, checked_rows, failed_rows, warning_rows,
            quality_flags, stale_reason, can_write_clean, needs_manual_review,
            rule_set_id, rule_version, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            validation_report_id,
            run_id,
            "r3g01-clean-write",
            candidate.domain,
            "stg_foundation_smoke",
            candidate.source_id,
            db_status,
            1,
            fail_count,
            warn_count,
            REHEARSAL_SYNTHETIC_QUALITY_FLAG,
            None,
            dh_report.sandbox_clean_write_gate_ready,
            False,
            "r3g01_rehearsal",
            "r3g01_rehearsal",
            datetime.now(UTC),
        ],
    )
    return validation_report_id


def _sandbox_clean_write(
    *,
    sandbox_db: Path,
    candidate: RehearsalCandidate,
    bundle,
    run_id: str,
    dh_report: DataHealthReport,
) -> tuple[str, int]:
    sandbox_db.parent.mkdir(parents=True, exist_ok=True)
    cm = ConnectionManager(sandbox_db)
    with cm.writer() as con:
        apply_migrations(con)
        _ensure_clean_table(con)
        validation_report_id = _ensure_validation_report(con, candidate, run_id, dh_report)
        populate_staging_from_bundle(
            con,
            bundle,
            batch_id=REHEARSAL_ID,
            max_rows=max(1, bundle.staged_row_count),
            start_date=bundle.window_start if bundle.window_start != "unknown" else None,
            end_date=bundle.window_end if bundle.window_end != "unknown" else None,
            allow_window_fallback=True,
        )
        gate = DbValidationGate(cm)
        wm = WriteManager(cm, gate)
        req = WriteRequest(
            run_id=run_id,
            job_id="r3g01-clean-write",
            target_table="security_bar_smoke_clean",
            staging_table="stg_foundation_smoke",
            write_mode="append_only",
            primary_keys=("instrument_id", "trade_date"),
            validation_report_id=validation_report_id,
            source_used=candidate.source_id,
            data_domain=candidate.domain,
        )
        result = wm.write(req, con=con, own_transaction=True)
        if result.status != "SUCCESS":
            raise RehearsalRunnerError(result.error_message or "sandbox clean write failed")
        clean_count = con.execute("SELECT COUNT(*) FROM security_bar_smoke_clean").fetchone()[0]
        return result.write_id, int(clean_count)


def _write_rollback_artifact(
    evidence_dir: Path,
    *,
    write_id: str,
    candidate: RehearsalCandidate,
    sandbox_db: Path,
) -> Path:
    payload = {
        "rehearsal_id": REHEARSAL_ID,
        "generated_at": utc_now_iso(),
        "write_manager_operation_id": write_id,
        "source_id": candidate.source_id,
        "domain": candidate.domain,
        "sandbox_db": str(sandbox_db),
        "rollback_plan": "DELETE FROM security_bar_smoke_clean WHERE batch_id = ?",
        "rollback_params": [REHEARSAL_ID],
        "dry_run_note": "sandbox rehearsal rollback artifact for audit only",
    }
    path = evidence_dir / _rollback_artifact_name(candidate.source_id)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_conflict_summary(evidence_dir: Path) -> dict[str, Any]:
    payload = _staged_conflict_check_summary()
    (evidence_dir / CONFLICT_CHECK_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def _write_mutation_proof(
    evidence_dir: Path,
    *,
    before_counts: dict[str, int | None],
    before_bytes: bytes | None,
) -> dict[str, Any]:
    proof = build_production_mutation_proof(
        DEFAULT_PRODUCTION_DB,
        before_counts=before_counts,
        before_bytes=before_bytes,
    )
    lines = [
        "# Production DB — No Mutation Proof (R3G-01)",
        "",
        f"- **Rehearsal ID:** {REHEARSAL_ID}",
        f"- **Generated at:** {utc_now_iso()}",
        f"- **Production DB:** `{DEFAULT_PRODUCTION_DB}`",
        f"- **proof_status:** {proof.get('proof_status')}",
        f"- **production_mutation_allowed:** false",
    ]
    (evidence_dir / NO_MUTATION_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return proof


def _write_route_plan(evidence_dir: Path, source_id: str, route_plan: dict[str, Any]) -> Path:
    source_dir = evidence_dir / source_id
    source_dir.mkdir(parents=True, exist_ok=True)
    path = source_dir / "route_plan.json"
    path.write_text(json.dumps(route_plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _process_candidate(
    candidate: RehearsalCandidate,
    *,
    request: RehearsalRequest,
    service: DataSourceService,
    run_id: str,
) -> dict[str, Any]:
    evidence_subdir = request.evidence_dir / candidate.source_id
    bundle = load_rehearsal_bundle(
        candidate,
        evidence_dir=evidence_subdir if evidence_subdir.is_dir() else None,
        dry_run=request.dry_run,
    )
    route_plan = _preview_route(candidate, service)
    _write_route_plan(request.evidence_dir, candidate.source_id, route_plan)
    dh_report = _run_source_data_health(candidate, bundle.evidence_dir)
    _assert_data_health_admission(dh_report, candidate.source_id)
    dh_summary = build_data_health_summary(dh_report)
    write_id, clean_rows = _sandbox_clean_write(
        sandbox_db=request.sandbox_db,
        candidate=candidate,
        bundle=bundle,
        run_id=run_id,
        dh_report=dh_report,
    )
    rollback_path = _write_rollback_artifact(
        request.evidence_dir,
        write_id=write_id,
        candidate=candidate,
        sandbox_db=request.sandbox_db,
    )
    fetch_cov = _coverage_ratio(len(bundle.source_fetch_ids), max(1, bundle.raw_row_count))
    content_cov = _coverage_ratio(len(bundle.content_hashes), max(1, bundle.raw_row_count))
    schema_cov = _coverage_ratio(len(bundle.schema_hashes), max(1, bundle.raw_row_count))
    report = build_rehearsal_report(
        candidate_set=request.candidate_set,
        source_id=candidate.source_id,
        domain=candidate.domain,
        bundle_rows={
            "raw": bundle.raw_row_count,
            "staged": bundle.staged_row_count,
            "clean": clean_rows,
        },
        window_start=bundle.window_start,
        window_end=bundle.window_end,
        validation_status=_validation_status_from_dh(dh_report),
        data_health_status=dh_report.overall_status,
        data_health_summary=dh_summary,
        source_fetch_id_coverage=fetch_cov,
        content_hash_coverage=content_cov,
        schema_hash_coverage=schema_cov,
        write_manager_operation_id=write_id,
        rollback_artifact_path=str(rollback_path.relative_to(PROJECT_ROOT))
        if rollback_path.is_relative_to(PROJECT_ROOT)
        else str(rollback_path),
        symbol_or_series_count=len(candidate.symbols_or_series),
        production_mutation_allowed=False,
    )
    report["synthetic_admission"] = True
    report["route_plan"] = route_plan
    report["staging_semantics"] = "smoke_only_bar_table"
    return report


def run_sandbox_clean_write_rehearsal(request: RehearsalRequest) -> dict[str, Any]:
    """End-to-end sandbox rehearsal — compose gates, sandbox clean write, evidence."""
    sandbox_db = assert_sandbox_db_allowed(
        request.sandbox_db,
        no_production_mutation=request.no_production_mutation,
    )
    evidence_dir = resolve_sandbox_path(request.evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    report_path = resolve_sandbox_path(request.report_path)

    if request.allow_live_fetch and request.dry_run:
        raise RehearsalRunnerError("allow_live_fetch requires dry_run=false")

    try:
        validate_candidate_set(
            request.candidate_set,
            fred_authorization=request.fred_authorization,
            require_live_credentials=request.allow_live_fetch and not request.dry_run,
        )
    except RehearsalPlanError as exc:
        raise RehearsalRunnerError(str(exc)) from exc

    prod_before_counts = _key_table_row_counts(DEFAULT_PRODUCTION_DB)
    prod_before_bytes = (
        DEFAULT_PRODUCTION_DB.read_bytes() if DEFAULT_PRODUCTION_DB.is_file() else None
    )

    guard = ResourceGuard()
    guard_decision, guard_reason = guard.check()
    if guard_decision == Decision.HARD_STOP:
        raise RehearsalRunnerError(f"ResourceGuard HARD_STOP: {guard_reason}")

    service = DataSourceService(staged_fixture_mode=request.dry_run and not request.allow_live_fetch)
    run_id = f"{REHEARSAL_ID}-{utc_now_iso()}"

    per_source: list[dict[str, Any]] = []
    candidates = list(load_candidate_set(request.candidate_set))
    for candidate in candidates:
        per_source.append(
            _process_candidate(
                candidate,
                request=RehearsalRequest(
                    candidate_set=request.candidate_set,
                    sandbox_db=sandbox_db,
                    evidence_dir=evidence_dir,
                    report_path=report_path,
                    no_production_mutation=request.no_production_mutation,
                    dry_run=request.dry_run,
                    allow_live_fetch=request.allow_live_fetch,
                    fred_authorization=request.fred_authorization,
                ),
                service=service,
                run_id=run_id,
            )
        )

    conflict = _write_conflict_summary(evidence_dir)
    mutation_proof = _write_mutation_proof(
        evidence_dir,
        before_counts=prod_before_counts,
        before_bytes=prod_before_bytes,
    )

    payload = {
        "rehearsal_id": REHEARSAL_ID,
        "generated_at": utc_now_iso(),
        "candidate_set": request.candidate_set,
        "sandbox_db": str(sandbox_db),
        "production_mutation_allowed": False,
        "sandbox_only": True,
        "dry_run": request.dry_run,
        "allow_live_fetch": request.allow_live_fetch,
        "resource_guard_decision": guard_decision.value,
        "resource_guard_reason": guard_reason,
        "required_gates": list(REQUIRED_GATES),
        "conflict_check_summary": conflict,
        "mutation_proof": mutation_proof,
        "per_source_reports": per_source,
    }
    write_rehearsal_report(report_path, payload)
    return payload
