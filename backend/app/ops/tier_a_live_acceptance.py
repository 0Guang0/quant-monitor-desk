"""Tier A live acceptance harness (M-DATA-03 S00-INFRA · ADR-034)."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml

from backend.app.config import DATA_ROOT, PROJECT_ROOT
from backend.app.datasources.live_tier_router import TIER_A_SOURCES
from backend.app.datasources.product_live_gate import is_product_live_fetch_allowed
from backend.app.ops.sandbox_clean_write.path_utils import resolve_sandbox_path
from backend.app.ops.tier_a_live_status import (
    PASS_SYNC_STATUSES,
    live_acceptance_mock_env_enabled,
    validate_sec_edgar_user_agent,
)
from backend.app.sync.incremental_source_registry import iter_tier_a_incremental_sources

M_DATA_03_SANDBOX_SEGMENT = "m-data-03"
DEFAULT_SANDBOX_ROOT = PROJECT_ROOT / ".audit-sandbox" / M_DATA_03_SANDBOX_SEGMENT

QUICK_SOURCE_IDS: tuple[str, ...] = ("fred", "baostock")

SOURCE_API_KEY_ENV: dict[str, str] = {
    "fred": "FRED_API_KEY",
    "alpha_vantage": "ALPHA_VANTAGE_API_KEY",
    "sec_edgar": "SEC_EDGAR_USER_AGENT",
}

EVIDENCE_CONTRACT_PATH = PROJECT_ROOT / "specs/contracts/live_tier_a_evidence_v1.yaml"
MANIFEST_FILENAME = "live_tier_a_evidence_manifest.json"
SCHEMA_VERSION = "live_tier_a_evidence_v1"
REPORT_FAILURE_TO_MANIFEST: dict[str, str] = {
    "PASS": "none",
    "FAIL_FIXABLE": "fixable_technical",
    "FAIL_EXTERNAL": "external_environment",
}
_FETCH_STATUS_FROM_SYNC: dict[str, str] = {
    "COMPLETED": "SUCCESS",
    "OK": "SUCCESS",
    "SUCCESS": "SUCCESS",
    "PLANNED": "SUCCESS",
    "EMPTY_RESPONSE": "EMPTY_RESPONSE",
    "FAILED": "FAILED",
}


class TierALiveEnvError(RuntimeError):
    """Invalid live acceptance environment (CLI exit 2)."""

    def __init__(self, message: str, *, code: str = "INVALID_LIVE_ENV") -> None:
        super().__init__(message)
        self.code = code


def canonical_main_db_paths() -> frozenset[Path]:
    return frozenset(
        {
            (PROJECT_ROOT / "data" / "duckdb" / "quant_monitor.duckdb").resolve(),
            (DATA_ROOT / "duckdb" / "quant_monitor.duckdb").resolve(),
        }
    )


def is_canonical_main_db_path(path: Path | str) -> bool:
    return resolve_sandbox_path(path).resolve() in canonical_main_db_paths()


def is_canonical_main_data_root(data_root: Path | str) -> bool:
    resolved = resolve_sandbox_path(data_root).resolve()
    if resolved == (PROJECT_ROOT / "data").resolve():
        return True
    return is_canonical_main_db_path(resolved / "duckdb" / "quant_monitor.duckdb")


def assert_isolated_live_data_root(data_root: Path | str) -> Path:
    """Reject canonical main DB paths; require `.audit-sandbox/m-data-03`."""
    resolved = resolve_sandbox_path(data_root).resolve()
    if is_canonical_main_db_path(resolved) or is_canonical_main_data_root(resolved):
        raise TierALiveEnvError(
            f"canonical main DB/data root rejected for live acceptance: {resolved}",
            code="CANONICAL_MAIN_DB_REJECTED",
        )
    posix = resolved.as_posix()
    if ".audit-sandbox" not in posix or M_DATA_03_SANDBOX_SEGMENT not in posix:
        raise TierALiveEnvError(
            f"DATA_ROOT must be under .audit-sandbox/{M_DATA_03_SANDBOX_SEGMENT}: {resolved}",
            code="ISOLATED_ROOT_REQUIRED",
        )
    return resolved


def resolve_live_data_root(data_root: Path | str | None = None) -> Path:
    raw = data_root
    if raw is None:
        raw = os.environ.get("QMD_DATA_ROOT") or os.environ.get("DATA_ROOT")
    if raw is None or str(raw).strip() == "":
        return DEFAULT_SANDBOX_ROOT
    return assert_isolated_live_data_root(Path(raw))


def missing_api_keys_for_sources(source_ids: tuple[str, ...]) -> list[str]:
    missing: list[str] = []
    for sid in source_ids:
        env_name = SOURCE_API_KEY_ENV.get(sid)
        if env_name is None:
            continue
        raw = os.environ.get(env_name, "")
        if sid == "sec_edgar":
            if validate_sec_edgar_user_agent(raw) is None:
                missing.append(
                    f"{env_name} missing or lacks contact identity (required for {sid})"
                )
            continue
        if not str(raw).strip():
            missing.append(f"{env_name} (required for {sid})")
    return missing


def validate_live_acceptance_env(
    *,
    data_root: Path | str | None = None,
    source_ids: tuple[str, ...] | None = None,
) -> Path:
    """Validate env for live acceptance; raise TierALiveEnvError on failure."""
    if not is_product_live_fetch_allowed():
        raise TierALiveEnvError(
            "QMD_ALLOW_LIVE_FETCH not set to opt-in value (ADR-027)",
            code="LIVE_FETCH_NOT_OPTED_IN",
        )
    if live_acceptance_mock_env_enabled():
        raise TierALiveEnvError(
            "QMD_FRED_INCREMENTAL_USE_MOCK forbidden in live acceptance (ADR-027/034)",
            code="MOCK_FORBIDDEN_IN_LIVE_ACCEPTANCE",
        )
    resolved_root = resolve_live_data_root(data_root)
    os.environ["QMD_DATA_ROOT"] = str(resolved_root)
    targets = source_ids or tuple(iter_tier_a_incremental_sources())
    missing = missing_api_keys_for_sources(targets)
    if missing:
        raise TierALiveEnvError(
            "missing API keys: " + "; ".join(missing),
            code="MISSING_API_KEYS",
        )
    return resolved_root


def select_source_ids(
    *,
    source_id: str | None = None,
    quick: bool = False,
) -> tuple[str, ...]:
    if source_id is not None:
        if source_id not in TIER_A_SOURCES:
            raise TierALiveEnvError(f"unknown Tier A source_id: {source_id!r}")
        return (source_id,)
    if quick:
        return QUICK_SOURCE_IDS
    return tuple(iter_tier_a_incremental_sources())


def ensure_isolated_db(data_root: Path) -> Path:
    """Create isolated DuckDB under data_root; apply migrations + registry sync."""
    import duckdb

    from backend.app.datasources.source_registry import SourceRegistry
    from backend.app.db.connection import ConnectionManager
    from backend.app.db.migrate import apply_migrations

    db = data_root / "duckdb" / "quant_monitor.duckdb"
    db.parent.mkdir(parents=True, exist_ok=True)
    if not db.is_file():
        con = duckdb.connect(str(db))
        try:
            apply_migrations(con)
        finally:
            con.close()
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
        registry = SourceRegistry()
        registry.load()
        registry.sync_to_db(con, tombstone_missing=True)
    return db


def _raw_path_belongs_to_source(rel_posix: str, source_id: str) -> bool:
    needle = f"raw/{source_id}/"
    return rel_posix.startswith(needle) or f"/{needle}" in rel_posix


def _iter_source_raw_files(data_root: Path, source_id: str) -> list[Path]:
    raw_base = data_root / "raw"
    if not raw_base.is_dir():
        return []
    files: list[Path] = []
    for candidate in raw_base.rglob("*"):
        if not candidate.is_file():
            continue
        rel = _relative_to_data_root(data_root, candidate).replace("\\", "/")
        if _raw_path_belongs_to_source(rel, source_id):
            files.append(candidate)
    return sorted(files)


def _latest_raw_evidence_dir(data_root: Path, source_id: str) -> Path | None:
    json_files = [
        path for path in _iter_source_raw_files(data_root, source_id) if path.suffix == ".json"
    ]
    if not json_files:
        return None
    return max(json_files, key=lambda path: path.stat().st_mtime).parent


def _run_f0_data_health(
    source_id: str, *, data_root: Path, db_path: Path
) -> tuple[str, str]:
    """Run F0 data health on latest raw evidence; return (status, detail)."""
    from backend.app.ops.data_health import DataHealthLoadError
    from backend.app.ops.data_health_profiles import run_data_health_profile

    binding = source_bindings()[source_id]
    health_domain = str(binding["health_domain"])
    health_profile_id = str(binding["health_profile_id"])

    evidence_dir = _latest_raw_evidence_dir(data_root, source_id)
    if evidence_dir is None:
        return "FAIL", "no raw evidence for F0 data health"

    try:
        report, *_ = run_data_health_profile(
            profile_id=health_profile_id,
            domain=health_domain,
            evidence_path=evidence_dir,
            db_path=db_path if db_path.is_file() else None,
            start_date=None,
            end_date=None,
            max_rows=1000,
        )
    except DataHealthLoadError as exc:
        return "FAIL", f"F0 evidence unloadable: {exc}"

    status = str(report.overall_status)
    detail = report.gate_rationale or status
    if status in {"FAIL", "BLOCKED"}:
        return "FAIL", f"data-health {status}: {detail}"
    return status, detail


def _run_b2_data_validation(
    source_id: str,
    *,
    db_path: Path,
    run_id: str,
    job_id: str,
) -> tuple[str, str]:
    """Run B2 validate_table on the source clean table per source_bindings."""
    from backend.app.validation.data_quality_validator import run_b2_validate_table

    binding = source_bindings()[source_id]
    return run_b2_validate_table(
        source_id,
        binding=binding,
        db_path=db_path,
        run_id=run_id,
        job_id=job_id,
    )


@dataclass(frozen=True)
class SourceAcceptanceResult:
    source_id: str
    status: Literal["pass", "fail"]
    detail: str = ""


def run_tier_a_live_incremental(source_id: str, data_root: Path) -> "LiveIncrementalOutcome":
    """Delegate to dispatch; exposed for acceptance/report and test monkeypatch."""
    from backend.app.ops.tier_a_live_incremental_dispatch import (
        LiveIncrementalOutcome,
        run_tier_a_live_incremental as _dispatch_run,
    )

    return _dispatch_run(source_id, data_root)


def run_source_live_acceptance(source_id: str, *, data_root: Path) -> SourceAcceptanceResult:
    """Run sync→clean→inspect→data health for one Tier A source (S-ACCEPT)."""
    resolved = assert_isolated_live_data_root(data_root)
    os.environ["QMD_DATA_ROOT"] = str(resolved)
    db_path = ensure_isolated_db(resolved)
    try:
        outcome = run_tier_a_live_incremental(source_id, resolved)
    except Exception as exc:
        return SourceAcceptanceResult(source_id=source_id, status="fail", detail=str(exc))

    health_status, health_detail = _run_f0_data_health(
        source_id, data_root=resolved, db_path=db_path
    )
    if health_status in {"FAIL", "BLOCKED"}:
        return SourceAcceptanceResult(
            source_id=source_id,
            status="fail",
            detail=f"data-health {health_status}: {health_detail}",
        )

    b2_status, b2_detail = _run_b2_data_validation(
        source_id,
        db_path=db_path,
        run_id=f"accept-{source_id}",
        job_id=f"accept-{source_id}",
    )
    if b2_status == "FAILED":
        return SourceAcceptanceResult(
            source_id=source_id,
            status="fail",
            detail=f"b2 validation FAILED: {b2_detail}",
        )

    if outcome.inspect_status == "FAIL":
        return SourceAcceptanceResult(
            source_id=source_id,
            status="fail",
            detail=f"db-inspect FAIL: {outcome.detail}",
        )
    if outcome.sync_status not in PASS_SYNC_STATUSES:
        return SourceAcceptanceResult(
            source_id=source_id,
            status="fail",
            detail=f"sync failed: {outcome.detail}",
        )
    if outcome.sync_status in {"COMPLETED", "PLANNED"} and outcome.clean_row_count < 1:
        raw_dir = resolved / "raw" / source_id
        fred_raw = resolved / "raw"
        has_raw = (raw_dir.is_dir() and any(raw_dir.rglob("*"))) or (
            source_id == "fred" and fred_raw.is_dir() and any(fred_raw.rglob("*"))
        )
        if not has_raw:
            return SourceAcceptanceResult(
                source_id=source_id,
                status="fail",
                detail=(
                    f"{outcome.sync_status} but {outcome.clean_table} empty: "
                    f"{outcome.detail}"
                ),
            )
    return SourceAcceptanceResult(
        source_id=source_id,
        status="pass",
        detail=(
            f"sync={outcome.sync_status} inspect={outcome.inspect_status} "
            f"health={health_status} b2={b2_status} "
            f"{outcome.clean_table}={outcome.clean_row_count}"
        ),
    )


def run_acceptance(
    *,
    source_id: str | None = None,
    quick: bool = False,
    data_root: Path | str | None = None,
) -> int:
    """Return CLI exit code: 0 pass · 1 source failure · 2 invalid env."""
    try:
        sources = select_source_ids(source_id=source_id, quick=quick)
        resolved_root = validate_live_acceptance_env(data_root=data_root, source_ids=sources)
    except TierALiveEnvError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    failures: list[SourceAcceptanceResult] = []
    for sid in sources:
        outcome = run_source_live_acceptance(sid, data_root=resolved_root)
        if outcome.status != "pass":
            failures.append(outcome)

    if failures:
        for item in failures:
            print(f"{item.source_id}: {item.detail}")
        return 1
    return 0


@lru_cache(maxsize=1)
def _load_evidence_contract() -> dict[str, Any]:
    return yaml.safe_load(EVIDENCE_CONTRACT_PATH.read_text(encoding="utf-8")) or {}


def source_bindings() -> dict[str, dict[str, Any]]:
    return _load_evidence_contract()["source_bindings"]


def manifest_failure_class(report_failure_class: str) -> str:
    try:
        return REPORT_FAILURE_TO_MANIFEST[report_failure_class]
    except KeyError as exc:
        raise ValueError(f"unknown report failure_class: {report_failure_class!r}") from exc


def _relative_to_data_root(data_root: Path, path: Path) -> str:
    return path.resolve().relative_to(data_root.resolve()).as_posix()


def _collect_raw_evidence_paths(data_root: Path, source_id: str) -> tuple[Path, list[str]]:
    evidence_dir = data_root / "evidence" / source_id
    evidence_dir.mkdir(parents=True, exist_ok=True)
    raw_paths = [
        _relative_to_data_root(data_root, path)
        for path in _iter_source_raw_files(data_root, source_id)
    ]
    return evidence_dir, raw_paths


def _manifest_fetch_status(sync_status: str) -> str:
    return _FETCH_STATUS_FROM_SYNC.get(sync_status.upper(), "FAILED")


def _build_fetch_block(
    source_id: str,
    *,
    outcome: "LiveIncrementalOutcome",
    raw_paths: list[str],
) -> dict[str, Any]:
    now = datetime.now(UTC).isoformat()
    fingerprint = "|".join(raw_paths) if raw_paths else outcome.detail
    return {
        "source_id": source_id,
        "status": _manifest_fetch_status(outcome.sync_status),
        "content_hash": hashlib.sha256(fingerprint.encode()).hexdigest(),
        "schema_hash": hashlib.sha256(source_id.encode()).hexdigest(),
        "row_count": outcome.clean_row_count,
        "fetch_time": now,
        "as_of_timestamp": now,
    }


def _health_status_for_manifest(health_status: str) -> str:
    return health_status


def build_live_tier_a_evidence_manifest(
    *,
    source_id: str,
    data_root: Path,
    run_id: str,
    job_id: str,
    outcome: "LiveIncrementalOutcome",
    report_failure_class: str,
    f0_health_status: str = "pending",
    b2_validation_status: str = "pending",
) -> dict[str, Any]:
    binding = source_bindings()[source_id]
    evidence_dir, raw_paths = _collect_raw_evidence_paths(data_root, source_id)
    disposition = "pass" if report_failure_class == "PASS" else "fail"
    return {
        "schema_version": SCHEMA_VERSION,
        "source_id": source_id,
        "run_id": run_id,
        "job_id": job_id,
        "data_domain": binding["data_domain"],
        "data_root": str(data_root.resolve()),
        "generated_at": datetime.now(UTC).isoformat(),
        "fetch": _build_fetch_block(source_id, outcome=outcome, raw_paths=raw_paths),
        "evidence": {
            "raw_relative_paths": raw_paths,
            "evidence_dir_relative": _relative_to_data_root(data_root, evidence_dir),
        },
        "acceptance": {
            "disposition": disposition,
            "failure_class": manifest_failure_class(report_failure_class),
            "e2_inspect_status": outcome.inspect_status,
            "f0_health_status": _health_status_for_manifest(f0_health_status),
            "b2_validation_status": b2_validation_status,
            "clean_table": binding["clean_table"],
            "rule_set_id": binding["rule_set_id"],
            "health_domain": binding["health_domain"],
            "health_profile_id": binding["health_profile_id"],
        },
    }


def write_live_tier_a_evidence_manifest(
    manifest: dict[str, Any], *, data_root: Path
) -> Path:
    evidence_rel = manifest["evidence"]["evidence_dir_relative"]
    evidence_dir = data_root / evidence_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    path = evidence_dir / MANIFEST_FILENAME
    path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def classify_source_report_failure(
    outcome: "LiveIncrementalOutcome",
) -> tuple[str, str]:
    """Return (disposition, report failure_class)."""
    if outcome.inspect_status == "FAIL":
        return "fail", "FAIL_FIXABLE"
    if outcome.sync_status not in PASS_SYNC_STATUSES:
        return "fail", "FAIL_FIXABLE"
    return "pass", "PASS"


def _process_source_for_report(
    source_id: str,
    *,
    data_root: Path,
    run_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    db_path = ensure_isolated_db(data_root)
    outcome = run_tier_a_live_incremental(source_id, data_root)
    disposition, report_failure_class = classify_source_report_failure(outcome)
    f0_status, f0_detail = _run_f0_data_health(source_id, data_root=data_root, db_path=db_path)
    if f0_status in {"FAIL", "BLOCKED"}:
        disposition = "fail"
        report_failure_class = "FAIL_FIXABLE"
    job_id = f"{run_id}:{source_id}"
    b2_status, b2_detail = _run_b2_data_validation(
        source_id,
        db_path=db_path,
        run_id=run_id,
        job_id=job_id,
    )
    if b2_status == "FAILED":
        disposition = "fail"
        report_failure_class = "FAIL_FIXABLE"
    binding = source_bindings()[source_id]
    manifest = build_live_tier_a_evidence_manifest(
        source_id=source_id,
        data_root=data_root,
        run_id=run_id,
        job_id=job_id,
        outcome=outcome,
        report_failure_class=report_failure_class,
        f0_health_status=f0_status,
        b2_validation_status=b2_status,
    )
    manifest_path = write_live_tier_a_evidence_manifest(manifest, data_root=data_root)
    detail = outcome.detail
    if f0_detail:
        detail = f"{detail}; f0={f0_detail}"
    if b2_detail:
        detail = f"{detail}; b2={b2_detail}"
    row = {
        "source_id": source_id,
        "disposition": disposition,
        "failure_class": report_failure_class,
        "failure_detail": detail,
        "adr_ref": None,
        "sync_status": outcome.sync_status,
        "e2_inspect_status": outcome.inspect_status,
        "f0_health_status": _health_status_for_manifest(f0_status),
        "b2_validation_status": b2_status,
        "health_domain": binding["health_domain"],
        "health_profile_id": binding["health_profile_id"],
        "rule_set_id": binding["rule_set_id"],
        "clean_table": binding["clean_table"],
        "evidence_manifest_path": _relative_to_data_root(data_root, manifest_path),
    }
    return row, manifest


def write_acceptance_failure_artifact(
    report_path: Path | str,
    *,
    run_id: str,
    report: dict[str, Any],
    exit_code: int,
) -> Path:
    """Write contract failure_artifact next to the acceptance report."""
    first_failure = next(
        (row for row in report["sources"] if row.get("disposition") == "fail"),
        None,
    )
    artifact = {
        "command": report["command"],
        "schema_version": report["schema_version"],
        "data_root": report["data_root"],
        "generated_at": report["generated_at"],
        "exit_code": exit_code,
        "sources": report["sources"],
        "summary": report["summary"],
        "first_failure_source_id": first_failure["source_id"] if first_failure else None,
        "failure_detail": first_failure.get("failure_detail") if first_failure else None,
    }
    out = Path(report_path).parent / f"tier_a_live_acceptance_failure_{run_id}.json"
    out.write_text(json.dumps(artifact, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def run_acceptance_report(
    report_path: Path | str,
    *,
    source_id: str | None = None,
    quick: bool = False,
    data_root: Path | str | None = None,
) -> int:
    """Write TierALiveAcceptanceReport JSON and per-source evidence manifests."""
    try:
        sources = select_source_ids(source_id=source_id, quick=quick)
        resolved_root = validate_live_acceptance_env(data_root=data_root, source_ids=sources)
    except TierALiveEnvError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    run_id = uuid.uuid4().hex
    rows: list[dict[str, Any]] = []
    summary = {"total": 0, "passed": 0, "failed_fixable": 0, "failed_external": 0}
    for sid in sources:
        row, _manifest = _process_source_for_report(sid, data_root=resolved_root, run_id=run_id)
        rows.append(row)
        summary["total"] += 1
        failure_class = row["failure_class"]
        if failure_class == "PASS":
            summary["passed"] += 1
        elif failure_class == "FAIL_FIXABLE":
            summary["failed_fixable"] += 1
        elif failure_class == "FAIL_EXTERNAL":
            summary["failed_external"] += 1

    report = {
        "command": "tier_a_live_acceptance --report",
        "schema_version": SCHEMA_VERSION,
        "data_root": str(resolved_root),
        "generated_at": datetime.now(UTC).isoformat(),
        "sources": rows,
        "summary": summary,
    }
    out = Path(report_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    exit_code = 0
    if summary["failed_fixable"] > 0 or summary["failed_external"] > 0:
        exit_code = 1
    if exit_code != 0:
        write_acceptance_failure_artifact(
            out, run_id=run_id, report=report, exit_code=exit_code
        )
    return exit_code


__all__ = [
    "DEFAULT_SANDBOX_ROOT",
    "EVIDENCE_CONTRACT_PATH",
    "MANIFEST_FILENAME",
    "M_DATA_03_SANDBOX_SEGMENT",
    "QUICK_SOURCE_IDS",
    "SCHEMA_VERSION",
    "SOURCE_API_KEY_ENV",
    "SourceAcceptanceResult",
    "TierALiveEnvError",
    "assert_isolated_live_data_root",
    "build_live_tier_a_evidence_manifest",
    "canonical_main_db_paths",
    "classify_source_report_failure",
    "ensure_isolated_db",
    "is_canonical_main_data_root",
    "is_canonical_main_db_path",
    "manifest_failure_class",
    "missing_api_keys_for_sources",
    "resolve_live_data_root",
    "run_acceptance",
    "run_acceptance_report",
    "run_source_live_acceptance",
    "run_tier_a_live_incremental",
    "select_source_ids",
    "source_bindings",
    "validate_live_acceptance_env",
    "write_acceptance_failure_artifact",
    "write_live_tier_a_evidence_manifest",
]
