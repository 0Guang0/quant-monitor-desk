"""R3G-03 limited production clean-write entry — capped promote with gate chain."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from backend.app.config import DATA_ROOT, PROJECT_ROOT
from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.db.sql_identifiers import quote_ident
from backend.app.db.validation_gate import DbValidationGate
from backend.app.db.write_manager import WriteManager, WriteRequest
from backend.app.datasources.service import DataSourceService
from backend.app.ops.mutation_proof import key_table_row_counts
from backend.app.ops.staged_pilot import DEFAULT_PRODUCTION_DB
from backend.app.ops.sandbox_clean_write.approval_contract import (
    ApprovalCandidate,
    ApprovalContractError,
    validate_approval_contract,
)
from backend.app.ops.sandbox_clean_write.gates import (
    REQUIRED_GATES,
    assert_data_health_admission,
    coverage_ratio,
    preview_route_for_candidate,
    run_source_data_health,
    validation_status_from_dh,
)
from backend.app.ops.sandbox_clean_write.path_utils import resolve_sandbox_path, utc_now_iso
from backend.app.ops.sandbox_clean_write.rehearsal_loader import (
    load_rehearsal_bundle,
    populate_staging_from_bundle,
)
from backend.app.ops.sandbox_clean_write.rehearsal_plan import (
    RehearsalCandidate,
    validate_fred_authorization,
)
from backend.app.ops.sandbox_clean_write.rehearsal_runner import (
    _ensure_validation_report,
)
from backend.app.ops.sandbox_clean_write.rollback_plan import (
    RollbackPlanError,
    dry_run_identify_affected_keys,
    load_rollback_plan,
    validate_rollback_plan,
)

PROMOTE_ID = "r3g03-limited-production-entry"
REQUIRED_BEFORE_FIELDS = (
    "production_db_path",
    "target_table",
    "target_table_row_count",
    "affected_key_range_count",
    "target_schema_hash",
    "latest_write_operation_id",
    "backup_or_snapshot_pointer",
    "resource_guard_decision",
)
REQUIRED_AFTER_FIELDS = (
    "inserted_updated_row_count",
    "unchanged_non_target_row_count",
    "validation_status",
    "source_fetch_id_coverage",
    "content_hash_coverage",
    "schema_hash_coverage",
    "write_manager_operation_id",
    "rollback_plan_id",
    "data_health_status",
)

_BLOCK_IF_ERROR_CODES: tuple[tuple[str, str], ...] = (
    ("missing_", "MISSING_ARTIFACT"),
    ("approval_audit_mismatch", "APPROVAL_AUDIT_MISMATCH"),
    ("audit_decision_not_allowing_entry", "AUDIT_DECISION_NOT_ALLOWING"),
    ("no_agent_triggered_write", "AGENT_WRITE_PATH_REJECTED"),
    ("cap_expansion", "CAP_EXPANSION"),
    ("ResourceGuard blocked", "RESOURCE_GUARD_BLOCKED"),
    ("production_db_path outside", "PRODUCTION_DB_PATH_REJECTED"),
    ("backup_or_snapshot_pointer", "MISSING_BACKUP_POINTER"),
    ("invalid target_table", "INVALID_TARGET_TABLE"),
    ("allow_live_fetch", "LIVE_FETCH_REJECTED"),
    ("dry_run mutated", "DRY_RUN_MUTATION"),
)


class LimitedProductionEntryError(RuntimeError):
    """Promote orchestration failed fail-closed gate."""

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code or _error_code_from_message(message)


def _error_code_from_message(message: str) -> str:
    for prefix, code in _BLOCK_IF_ERROR_CODES:
        if prefix in message:
            return code
    return "INVALID_INPUT"


@dataclass(frozen=True)
class PromoteRequest:
    approval_file: Path
    audit_decision: Path
    before_proof: Path | None
    after_proof: Path | None
    rollback_plan: Path | None
    evidence_dir: Path | None = None
    dry_run: bool = True
    execute: bool = False
    allow_live_fetch: bool = False
    fred_authorization: Path | None = None


def _assert_production_db_allowed(
    production_db: Path,
    *,
    mkdir_if_missing: bool = True,
) -> Path:
    """Promote target must be explicit production_db_path from approval; refuse canonical main DB."""
    resolved = resolve_sandbox_path(production_db)
    prod = DEFAULT_PRODUCTION_DB.resolve()
    from backend.app import config as app_config

    default_prod = (app_config.DATA_ROOT / "duckdb" / "quant_monitor.duckdb").resolve()
    canonical_prod = (PROJECT_ROOT / "data" / "duckdb" / "quant_monitor.duckdb").resolve()
    if resolved in {prod, default_prod, canonical_prod}:
        raise LimitedProductionEntryError(
            "canonical production DB path refused for R3G-03 promote; use isolated pilot DB",
            code="PRODUCTION_DB_PATH_REJECTED",
        )
    if mkdir_if_missing:
        resolved.parent.mkdir(parents=True, exist_ok=True)
    elif not resolved.is_file() and not resolved.parent.is_dir():
        raise LimitedProductionEntryError(
            f"production_db parent must exist before execute: {resolved.parent}",
            code="PRODUCTION_DB_PATH_REJECTED",
        )
    return resolved


def _assert_within_data_root(db_path: Path) -> None:
    """Fail-closed: refuse paths outside approved DATA_ROOT tree unless under .audit-sandbox."""
    resolved = resolve_sandbox_path(db_path)
    data_root = DATA_ROOT.resolve()
    audit_sandbox = (PROJECT_ROOT / ".audit-sandbox").resolve()
    if resolved.is_relative_to(data_root) or resolved.is_relative_to(audit_sandbox):
        return
    raise LimitedProductionEntryError(
        f"production_db_path outside DATA_ROOT or .audit-sandbox: {resolved}",
        code="PRODUCTION_DB_PATH_REJECTED",
    )


def _assert_validation_source_isolated_db(source_id: str, production_db: Path) -> None:
    """validation_only contract sources may only promote to pilot or audit-sandbox DBs."""
    from backend.app.ops.sandbox_clean_write.approval_contract import _load_contract_caps

    caps = _load_contract_caps().get(source_id) or {}
    if not caps.get("validation_only"):
        return
    resolved = resolve_sandbox_path(production_db)
    audit_sandbox = (PROJECT_ROOT / ".audit-sandbox").resolve()
    if resolved.is_relative_to(audit_sandbox) or "r3g03_pilot" in resolved.name:
        return
    raise LimitedProductionEntryError(
        f"validation_only source {source_id} requires r3g03_pilot or .audit-sandbox DB",
        code="PRODUCTION_DB_PATH_REJECTED",
    )


def _quoted_table(table: str) -> str:
    try:
        return quote_ident(table)
    except ValueError as exc:
        raise LimitedProductionEntryError(
            f"invalid target_table: {exc}",
            code="INVALID_TARGET_TABLE",
        ) from exc


def _table_schema_hash(con, table: str) -> str:
    rows = con.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'main' AND table_name = ?
        ORDER BY ordinal_position
        """,
        [table],
    ).fetchall()
    if not rows:
        return "table-absent"
    payload = "|".join(f"{name}:{dtype}" for name, dtype in rows)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _target_table_row_count(con, table: str) -> int:
    tables = {
        row[0]
        for row in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
    }
    if table not in tables:
        return 0
    quoted = _quoted_table(table)
    return int(con.execute(f"SELECT COUNT(*) FROM {quoted}").fetchone()[0])


def _non_target_row_count(con, table: str, approved_symbols: tuple[str, ...]) -> int:
    """Count rows in target table outside approved symbol set (execute after-proof)."""
    tables = {
        row[0]
        for row in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
    }
    if table not in tables:
        return 0
    quoted = _quoted_table(table)
    if not approved_symbols:
        return int(con.execute(f"SELECT COUNT(*) FROM {quoted}").fetchone()[0])
    placeholders = ", ".join("?" for _ in approved_symbols)
    sql = f"SELECT COUNT(*) FROM {quoted} WHERE instrument_id NOT IN ({placeholders})"
    return int(con.execute(sql, list(approved_symbols)).fetchone()[0])


def _latest_write_operation_id(con) -> str | None:
    tables = {
        row[0]
        for row in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
    }
    if "write_audit_log" not in tables:
        return None
    row = con.execute(
        "SELECT write_id FROM write_audit_log ORDER BY finished_at DESC NULLS LAST LIMIT 1"
    ).fetchone()
    return str(row[0]) if row else None


def _resource_guard_decision() -> str:
    guard_decision, _guard_reason = ResourceGuard().check()
    if guard_decision in {Decision.HARD_STOP, Decision.PAUSE}:
        raise LimitedProductionEntryError(
            f"ResourceGuard blocked: {guard_decision.value}",
            code="RESOURCE_GUARD_BLOCKED",
        )
    return guard_decision.value


_BACKUP_POINTER_RE = re.compile(r"^[\w./\\:-]+$")


def _validate_backup_pointer(pointer: Any) -> None:
    if pointer is None:
        return
    text = str(pointer).strip()
    if not text:
        raise LimitedProductionEntryError(
            "backup_or_snapshot_pointer must be non-empty when provided",
            code="MISSING_BACKUP_POINTER",
        )
    if not _BACKUP_POINTER_RE.fullmatch(text):
        raise LimitedProductionEntryError(
            f"invalid backup_or_snapshot_pointer format: {text!r}",
            code="MISSING_BACKUP_POINTER",
        )


def build_before_proof(
    production_db: Path,
    candidate: ApprovalCandidate,
    *,
    backup_or_snapshot_pointer: str | None = None,
) -> dict[str, Any]:
    """Build §7 before proof from production DB (read-only)."""
    db_path = _assert_production_db_allowed(production_db)
    _assert_within_data_root(db_path)
    if backup_or_snapshot_pointer is not None:
        _validate_backup_pointer(backup_or_snapshot_pointer)
    rg_decision = _resource_guard_decision()

    if not db_path.is_file():
        return {
            "production_db_path": str(db_path),
            "target_table": candidate.target_table,
            "target_table_row_count": 0,
            "affected_key_range_count": 0,
            "target_schema_hash": "db-absent",
            "latest_write_operation_id": None,
            "backup_or_snapshot_pointer": backup_or_snapshot_pointer,
            "resource_guard_decision": rg_decision,
            "key_table_row_counts": {},
            "source_id": candidate.source_id,
            "domain": candidate.domain,
            "symbols": list(candidate.symbols),
            "start_date": candidate.start_date,
            "end_date": candidate.end_date,
            "max_rows": candidate.max_rows,
            "generated_at": utc_now_iso(),
        }

    cm = ConnectionManager(db_path, profile="eco")
    with cm.reader() as con:
        apply_migrations(con)
        row_count = _target_table_row_count(con, candidate.target_table)
        schema_hash = _table_schema_hash(con, candidate.target_table)
        latest_op = _latest_write_operation_id(con)

    return {
        "production_db_path": str(db_path),
        "target_table": candidate.target_table,
        "target_table_row_count": row_count,
        "affected_key_range_count": len(candidate.symbols),
        "target_schema_hash": schema_hash,
        "latest_write_operation_id": latest_op,
        "backup_or_snapshot_pointer": backup_or_snapshot_pointer,
        "resource_guard_decision": rg_decision,
        "key_table_row_counts": key_table_row_counts(db_path),
        "source_id": candidate.source_id,
        "domain": candidate.domain,
        "symbols": list(candidate.symbols),
        "start_date": candidate.start_date,
        "end_date": candidate.end_date,
        "max_rows": candidate.max_rows,
        "generated_at": utc_now_iso(),
    }


def _validate_before_proof_payload(
    proof: dict[str, Any],
    *,
    candidate: ApprovalCandidate,
    production_db: Path,
    require_backup: bool = False,
) -> None:
    for field in REQUIRED_BEFORE_FIELDS:
        if field not in proof:
            raise LimitedProductionEntryError(
                f"missing_before_proof field: {field}",
                code="MISSING_ARTIFACT",
            )
    if resolve_sandbox_path(str(proof.get("production_db_path"))) != resolve_sandbox_path(production_db):
        raise LimitedProductionEntryError(
            "before_proof production_db_path mismatch",
            code="APPROVAL_AUDIT_MISMATCH",
        )
    if proof.get("target_table") != candidate.target_table:
        raise LimitedProductionEntryError(
            "before_proof target_table mismatch",
            code="APPROVAL_AUDIT_MISMATCH",
        )
    _validate_backup_pointer(proof.get("backup_or_snapshot_pointer"))
    if require_backup:
        pointer = proof.get("backup_or_snapshot_pointer")
        if not pointer or not str(pointer).strip():
            raise LimitedProductionEntryError(
                "backup_or_snapshot_pointer required before execute",
                code="MISSING_BACKUP_POINTER",
            )


def write_before_proof(path: Path | str, proof: dict[str, Any]) -> Path:
    resolved = resolve_sandbox_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return resolved


def load_before_proof(path: Path | str) -> dict[str, Any]:
    resolved = resolve_sandbox_path(path)
    if not resolved.is_file():
        raise LimitedProductionEntryError(
            f"missing_before_proof: {resolved}",
            code="MISSING_ARTIFACT",
        )
    return json.loads(resolved.read_text(encoding="utf-8"))


def build_after_proof(
    *,
    before_proof: dict[str, Any],
    candidate: ApprovalCandidate,
    write_manager_operation_id: str | None,
    rollback_plan_id: str,
    validation_status: str,
    data_health_status: str,
    bundle_metrics: dict[str, Any],
    dry_run: bool,
    unchanged_non_target_row_count: int | None = None,
) -> dict[str, Any]:
    """Build §7 after proof — dry_run uses zero inserted rows."""
    before_count = int(before_proof.get("target_table_row_count") or 0)
    inserted = 0 if dry_run else int(bundle_metrics.get("clean_rows") or 0)
    non_target = (
        before_count
        if dry_run
        else (
            unchanged_non_target_row_count
            if unchanged_non_target_row_count is not None
            else int(bundle_metrics.get("unchanged_non_target_row_count") or before_count)
        )
    )
    return {
        "production_db_path": before_proof.get("production_db_path"),
        "target_table": candidate.target_table,
        "inserted_updated_row_count": inserted,
        "unchanged_non_target_row_count": non_target,
        "validation_status": validation_status,
        "source_fetch_id_coverage": bundle_metrics.get("source_fetch_id_coverage", 0.0),
        "content_hash_coverage": bundle_metrics.get("content_hash_coverage", 0.0),
        "schema_hash_coverage": bundle_metrics.get("schema_hash_coverage", 0.0),
        "write_manager_operation_id": write_manager_operation_id,
        "rollback_plan_id": rollback_plan_id,
        "data_health_status": data_health_status,
        "dry_run": dry_run,
        "production_mutation_allowed": not dry_run,
        "generated_at": utc_now_iso(),
    }


def _validate_after_proof_payload(proof: dict[str, Any], *, dry_run: bool) -> None:
    for field in REQUIRED_AFTER_FIELDS:
        if field not in proof:
            raise LimitedProductionEntryError(
                f"missing_after_proof field: {field}",
                code="MISSING_ARTIFACT",
            )
    if dry_run and proof.get("production_mutation_allowed"):
        raise LimitedProductionEntryError(
            "after_proof production_mutation_allowed must be false during dry_run",
            code="DRY_RUN_MUTATION",
        )


def write_after_proof(path: Path | str, proof: dict[str, Any]) -> Path:
    resolved = resolve_sandbox_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return resolved


def load_after_proof(path: Path | str) -> dict[str, Any]:
    resolved = resolve_sandbox_path(path)
    if not resolved.is_file():
        raise LimitedProductionEntryError(
            f"missing_after_proof: {resolved}",
            code="MISSING_ARTIFACT",
        )
    return json.loads(resolved.read_text(encoding="utf-8"))


def _to_rehearsal_candidate(candidate: ApprovalCandidate) -> RehearsalCandidate:
    start = date.fromisoformat(candidate.start_date)
    end = date.fromisoformat(candidate.end_date)
    window_days = (end - start).days + 1
    op_map = {
        "baostock": "fetch_daily_bar",
        "akshare": "fetch_daily_bar_validation",
        "yahoo_finance": "fetch_daily_bar_validation",
        "cninfo": "fetch_announcement_index",
        "fred": "fetch_macro_series",
    }
    return RehearsalCandidate(
        source_id=candidate.source_id,
        domain=candidate.domain,
        operation=op_map.get(candidate.source_id, "fetch_daily_bar"),
        symbols_or_series=candidate.symbols,
        window_days=window_days,
        metadata_only=candidate.metadata_only,
    )


def _enforce_live_fetch_gates(request: PromoteRequest, candidate: ApprovalCandidate) -> None:
    if request.allow_live_fetch and request.dry_run:
        raise LimitedProductionEntryError(
            "allow_live_fetch requires --execute --no-dry-run",
            code="LIVE_FETCH_REJECTED",
        )
    wants_live = request.allow_live_fetch or candidate.live_fetch_authorized
    if not wants_live:
        return
    if candidate.source_id != "fred":
        raise LimitedProductionEntryError(
            "allow_live_fetch only supported for fred source",
            code="LIVE_FETCH_REJECTED",
        )
    try:
        validate_fred_authorization(
            request.fred_authorization,
            series_ids=candidate.symbols,
            require_live_credentials=True,
        )
    except Exception as exc:
        raise LimitedProductionEntryError(
            f"fred authorization failed: {exc}",
            code="LIVE_FETCH_REJECTED",
        ) from exc


def _production_clean_write(
    *,
    production_db: Path,
    candidate: ApprovalCandidate,
    rehearsal: RehearsalCandidate,
    bundle,
    run_id: str,
    dh_report,
    dry_run: bool,
    allow_fixture_window_fallback: bool,
) -> tuple[str | None, int, int]:
    """Write bundle evidence rows through staging → WriteManager on approved DB.

    ponytail: staging via populate_staging_from_bundle; WriteManager orchestration
    mirrored from rehearsal_runner._sandbox_clean_write — upgrade path: gates.compose_clean_write_gates().
    """
    if dry_run:
        return None, 0, 0

    production_db.parent.mkdir(parents=True, exist_ok=True)
    cm = ConnectionManager(production_db)
    with cm.writer() as con:
        apply_migrations(con)
        before_non_target = _non_target_row_count(con, candidate.target_table, candidate.symbols)
        validation_report_id = _ensure_validation_report(con, rehearsal, run_id, dh_report)
        staged_count = populate_staging_from_bundle(
            con,
            bundle,
            batch_id=PROMOTE_ID,
            max_rows=candidate.max_rows,
            start_date=candidate.start_date,
            end_date=candidate.end_date,
            allow_window_fallback=allow_fixture_window_fallback,
        )
        if staged_count <= 0:
            raise LimitedProductionEntryError("bundle produced zero staging rows")
        quoted_target = _quoted_table(candidate.target_table)
        tables = {
            row[0]
            for row in con.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
            ).fetchall()
        }
        if candidate.target_table not in tables:
            con.execute(
                f"CREATE TABLE {quoted_target} AS SELECT * FROM stg_foundation_smoke WHERE 1=0"
            )
        gate = DbValidationGate(cm)
        wm = WriteManager(cm, gate)
        req = WriteRequest(
            run_id=run_id,
            job_id="r3g03-clean-write",
            target_table=candidate.target_table,
            staging_table="stg_foundation_smoke",
            write_mode="append_only",
            primary_keys=("instrument_id", "trade_date"),
            validation_report_id=validation_report_id,
            source_used=candidate.source_id,
            data_domain=candidate.domain,
        )
        result = wm.write(req, con=con, own_transaction=True)
        if result.status != "SUCCESS":
            raise LimitedProductionEntryError(result.error_message or "production clean write failed")
        rows_inserted = int(result.rows_inserted)
        after_non_target = _non_target_row_count(con, candidate.target_table, candidate.symbols)
        if after_non_target != before_non_target:
            raise LimitedProductionEntryError(
                "execute mutated non-target key rows",
                code="DRY_RUN_MUTATION",
            )
        return result.write_id, rows_inserted, after_non_target


def run_limited_production_entry(request: PromoteRequest) -> dict[str, Any]:
    """End-to-end limited production promote — default dry_run, explicit execute for mutation."""
    if request.execute and request.dry_run:
        raise LimitedProductionEntryError("cannot set both execute and dry_run")
    if request.before_proof is None:
        raise LimitedProductionEntryError("missing_before_proof", code="MISSING_ARTIFACT")
    if request.rollback_plan is None:
        raise LimitedProductionEntryError("missing_rollback_plan", code="MISSING_ARTIFACT")
    if request.after_proof is None:
        raise LimitedProductionEntryError(
            "missing_after_proof path required for promote",
            code="MISSING_ARTIFACT",
        )

    production_mutation_allowed = request.execute and not request.dry_run

    try:
        contract, _audit, candidate = validate_approval_contract(
            request.approval_file,
            request.audit_decision,
            rollback_plan_path=request.rollback_plan,
        )
    except ApprovalContractError as exc:
        raise LimitedProductionEntryError(str(exc)) from exc

    _enforce_live_fetch_gates(request, candidate)

    production_db = _assert_production_db_allowed(
        contract.production_db_path,
        mkdir_if_missing=not production_mutation_allowed,
    )
    _assert_within_data_root(production_db)
    _assert_validation_source_isolated_db(candidate.source_id, production_db)

    if candidate.source_id == "fred":
        try:
            validate_fred_authorization(
                request.fred_authorization,
                series_ids=candidate.symbols,
                require_live_credentials=bool(request.allow_live_fetch),
            )
        except Exception as exc:
            raise LimitedProductionEntryError(
                f"fred authorization failed: {exc}",
                code="LIVE_FETCH_REJECTED",
            ) from exc

    before_proof = load_before_proof(request.before_proof)
    _validate_before_proof_payload(
        before_proof,
        candidate=candidate,
        production_db=production_db,
        require_backup=production_mutation_allowed,
    )

    rollback_plan = load_rollback_plan(request.rollback_plan)

    try:
        validate_rollback_plan(
            rollback_plan,
            candidate=candidate,
            production_db_path=production_db,
        )
    except RollbackPlanError as exc:
        raise LimitedProductionEntryError(str(exc)) from exc

    identified = dry_run_identify_affected_keys(rollback_plan)

    rehearsal = _to_rehearsal_candidate(candidate)
    evidence_dir = resolve_sandbox_path(request.evidence_dir) if request.evidence_dir else (
        PROJECT_ROOT / ".audit-sandbox" / "round3g" / "r3g03_promote"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_subdir = evidence_dir / candidate.source_id

    service = DataSourceService(
        staged_fixture_mode=not production_mutation_allowed and not request.allow_live_fetch
    )
    bundle = load_rehearsal_bundle(
        rehearsal,
        evidence_dir=evidence_subdir if evidence_subdir.is_dir() else None,
        dry_run=request.dry_run or not production_mutation_allowed,
        cap_profile="r3g03",
    )
    route_plan = preview_route_for_candidate(rehearsal, service)
    dh_report = run_source_data_health(
        rehearsal,
        bundle.evidence_dir,
        max_rows=candidate.max_rows,
    )
    assert_data_health_admission(dh_report, candidate.source_id)

    run_id = f"{PROMOTE_ID}-{candidate.source_id}"
    evidence_is_fixture = "tests/fixtures" in str(bundle.evidence_dir).replace("\\", "/")
    allow_fixture_window_fallback = evidence_is_fixture or not production_mutation_allowed
    write_id, clean_rows, non_target_count = _production_clean_write(
        production_db=production_db,
        candidate=candidate,
        rehearsal=rehearsal,
        bundle=bundle,
        run_id=run_id,
        dh_report=dh_report,
        dry_run=not production_mutation_allowed,
        allow_fixture_window_fallback=allow_fixture_window_fallback,
    )

    fetch_cov = coverage_ratio(len(bundle.source_fetch_ids), max(1, bundle.raw_row_count))
    content_cov = coverage_ratio(len(bundle.content_hashes), max(1, bundle.raw_row_count))
    schema_cov = coverage_ratio(len(bundle.schema_hashes), max(1, bundle.raw_row_count))

    after_proof = build_after_proof(
        before_proof=before_proof,
        candidate=candidate,
        write_manager_operation_id=write_id,
        rollback_plan_id=str(rollback_plan.get("rollback_plan_id") or ""),
        validation_status=validation_status_from_dh(dh_report),
        data_health_status=dh_report.overall_status,
        bundle_metrics={
            "clean_rows": clean_rows,
            "source_fetch_id_coverage": fetch_cov,
            "content_hash_coverage": content_cov,
            "schema_hash_coverage": schema_cov,
            "unchanged_non_target_row_count": non_target_count,
        },
        dry_run=not production_mutation_allowed,
        unchanged_non_target_row_count=non_target_count if production_mutation_allowed else None,
    )

    _validate_after_proof_payload(after_proof, dry_run=not production_mutation_allowed)
    write_after_proof(request.after_proof, after_proof)

    if not production_mutation_allowed:
        before_counts = before_proof.get("key_table_row_counts") or {}
        after_counts = key_table_row_counts(production_db) if production_db.is_file() else {}
        if after_counts != before_counts and production_db.is_file():
            raise LimitedProductionEntryError(
                "dry_run mutated production key tables",
                code="DRY_RUN_MUTATION",
            )

    report = {
        "promote_id": PROMOTE_ID,
        "generated_at": utc_now_iso(),
        "approval_id": contract.approval_id,
        "source_id": candidate.source_id,
        "domain": candidate.domain,
        "symbols": list(candidate.symbols),
        "window_start": candidate.start_date,
        "window_end": candidate.end_date,
        "production_db_path": str(production_db),
        "production_mutation_allowed": production_mutation_allowed,
        "dry_run": not production_mutation_allowed,
        "required_gates": list(REQUIRED_GATES),
        "route_plan": route_plan,
        "before_proof": before_proof,
        "after_proof": after_proof,
        "rollback_plan_id": rollback_plan.get("rollback_plan_id"),
        "rollback_affected_keys": identified,
        "write_manager_operation_id": write_id,
        "validation_status": after_proof["validation_status"],
        "data_health_status": after_proof["data_health_status"],
    }

    if report["dry_run"] and report["production_mutation_allowed"]:
        raise LimitedProductionEntryError(
            "promote report cannot claim production_mutation_allowed during dry_run",
            code="DRY_RUN_MUTATION",
        )

    return report
