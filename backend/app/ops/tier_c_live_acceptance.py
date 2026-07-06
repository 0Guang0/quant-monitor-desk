"""Tier C live acceptance harness (M-DATA-03 AC-7 · validation_fetch)."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml

from backend.app.config import PROJECT_ROOT
from backend.app.datasources.live_tier_router import TIER_C_SOURCES
from backend.app.datasources.product_live_gate import is_product_live_fetch_allowed
from backend.app.ops.sandbox_clean_write.path_utils import resolve_sandbox_path
from backend.app.ops.tier_a_live_acceptance import (
    canonical_main_db_paths,
    ensure_isolated_db,
    is_canonical_main_data_root,
    is_canonical_main_db_path,
)
from backend.app.ops.tier_a_live_status import live_acceptance_mock_env_enabled
from backend.app.ops.tier_c_live_validation_dispatch import (
    PASS_FETCH_STATUSES,
    LiveValidationOutcome,
    run_tier_c_live_validation,
)

M_DATA_03_SANDBOX_SEGMENT = "m-data-03"
TIER_C_SANDBOX_SEGMENT = "tier-c"
DEFAULT_SANDBOX_ROOT = (
    PROJECT_ROOT / ".audit-sandbox" / M_DATA_03_SANDBOX_SEGMENT / TIER_C_SANDBOX_SEGMENT
)

QUICK_SOURCE_IDS: tuple[str, ...] = ("kalshi", "polymarket")

SOURCE_API_KEY_ENV: dict[str, str] = {}

EVIDENCE_CONTRACT_PATH = PROJECT_ROOT / "specs/contracts/live_tier_c_evidence_v1.yaml"
MANIFEST_FILENAME = "live_tier_c_evidence_manifest.json"
SCHEMA_VERSION = "live_tier_c_evidence_v1"
REPORT_FAILURE_TO_MANIFEST: dict[str, str] = {
    "PASS": "none",
    "FAIL_FIXABLE": "fixable_technical",
    "FAIL_EXTERNAL": "external_environment",
}
_FETCH_STATUS_TO_MANIFEST: dict[str, str] = {
    "SUCCESS": "SUCCESS",
    "OK": "SUCCESS",
    "EMPTY_RESPONSE": "EMPTY_RESPONSE",
    "FAILED": "FAILED",
    "RATE_LIMITED": "RATE_LIMITED",
    "NETWORK_ERROR": "NETWORK_ERROR",
    "NOT_PUBLISHED_YET": "NOT_PUBLISHED_YET",
    "DISABLED_SOURCE": "DISABLED_SOURCE",
    "AUTH_FAILED": "AUTH_FAILED",
}
_EXTERNAL_FETCH_STATUSES = frozenset(
    {"RATE_LIMITED", "NETWORK_ERROR", "NOT_PUBLISHED_YET", "DISABLED_SOURCE", "AUTH_FAILED"}
)


def fail_external_adr_ref() -> str:
    """ADR slug for FAIL_EXTERNAL rows — SSOT: live_tier_c_evidence_v1 authoritative_docs."""
    for doc in _load_evidence_contract().get("authoritative_docs") or []:
        match = re.search(r"ADR-\d+", str(doc))
        if match:
            return match.group(0)
    raise RuntimeError("live_tier_c_evidence_v1: no ADR in authoritative_docs")


class TierCLiveEnvError(RuntimeError):
    """Invalid live acceptance environment (CLI exit 2)."""

    def __init__(self, message: str, *, code: str = "INVALID_LIVE_ENV") -> None:
        super().__init__(message)
        self.code = code


def assert_isolated_live_data_root(data_root: Path | str) -> Path:
    """Reject canonical main DB; require `.audit-sandbox/m-data-03/tier-c`."""
    resolved = resolve_sandbox_path(data_root).resolve()
    if is_canonical_main_db_path(resolved) or is_canonical_main_data_root(resolved):
        raise TierCLiveEnvError(
            f"canonical main DB/data root rejected for live acceptance: {resolved}",
            code="CANONICAL_MAIN_DB_REJECTED",
        )
    posix = resolved.as_posix()
    if (
        ".audit-sandbox" not in posix
        or M_DATA_03_SANDBOX_SEGMENT not in posix
        or TIER_C_SANDBOX_SEGMENT not in posix
    ):
        raise TierCLiveEnvError(
            f"DATA_ROOT must be under .audit-sandbox/{M_DATA_03_SANDBOX_SEGMENT}/{TIER_C_SANDBOX_SEGMENT}: {resolved}",
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
        if not str(raw).strip():
            missing.append(f"{env_name} (required for {sid})")
    return missing


def validate_live_acceptance_env(
    *,
    data_root: Path | str | None = None,
    source_ids: tuple[str, ...] | None = None,
) -> Path:
    """Validate env for Tier C validation_fetch acceptance."""
    if live_acceptance_mock_env_enabled():
        raise TierCLiveEnvError(
            "QMD_FRED_INCREMENTAL_USE_MOCK forbidden in live acceptance (ADR-008/034)",
            code="MOCK_FORBIDDEN_IN_LIVE_ACCEPTANCE",
        )
    if not is_product_live_fetch_allowed():
        raise TierCLiveEnvError(
            "QMD_ALLOW_LIVE_FETCH not set to opt-in value (ADR-008)",
            code="LIVE_FETCH_NOT_OPTED_IN",
        )
    resolved_root = resolve_live_data_root(data_root)
    os.environ["QMD_DATA_ROOT"] = str(resolved_root)
    targets = source_ids or tuple(sorted(TIER_C_SOURCES))
    missing = missing_api_keys_for_sources(targets)
    if missing:
        raise TierCLiveEnvError(
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
        if source_id not in TIER_C_SOURCES:
            raise TierCLiveEnvError(f"unknown Tier C source_id: {source_id!r}")
        return (source_id,)
    if quick:
        return QUICK_SOURCE_IDS
    return tuple(sorted(TIER_C_SOURCES))


def _f0_applicable(source_id: str) -> bool:
    binding = source_bindings()[source_id]
    return bool(binding.get("f0_applicable", True))


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
        rel = candidate.resolve().relative_to(data_root.resolve()).as_posix()
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
    """Run F0 data health on latest raw evidence when binding marks f0_applicable."""
    if not _f0_applicable(source_id):
        return "NOT_APPLICABLE", "f0 not applicable for validation_fetch binding"

    from backend.app.ops.data_health import DataHealthLoadError
    from backend.app.ops.data_health_profiles import run_data_health_profile

    binding = source_bindings()[source_id]
    health_domain = str(binding["health_domain"])
    health_profile_id = str(binding["health_profile_id"])
    if health_profile_id == "not_applicable":
        return "NOT_APPLICABLE", "no health profile for binding"

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
            live_acceptance=True,
        )
    except DataHealthLoadError as exc:
        return "FAIL", f"F0 evidence unloadable: {exc}"

    status = str(report.overall_status)
    detail = report.gate_rationale or status
    if status in {"FAIL", "BLOCKED"}:
        return "FAIL", f"data-health {status}: {detail}"
    return status, detail


@dataclass(frozen=True)
class SourceAcceptanceResult:
    source_id: str
    status: Literal["pass", "fail"]
    detail: str = ""
    failure_class: str = "PASS"
    adr_ref: str | None = None


@dataclass(frozen=True)
class _SourcePipelineResult:
    source_id: str
    outcome: LiveValidationOutcome
    f0_status: str
    f0_detail: str
    disposition: Literal["pass", "fail"]
    failure_class: str
    adr_ref: str | None
    detail: str


def classify_source_report_failure(
    outcome: LiveValidationOutcome,
) -> tuple[Literal["pass", "fail"], str, str | None]:
    """Return (disposition, report failure_class, adr_ref)."""
    fetch = outcome.fetch_status.upper()
    if fetch in _EXTERNAL_FETCH_STATUSES:
        return "fail", "FAIL_EXTERNAL", fail_external_adr_ref()
    if fetch not in PASS_FETCH_STATUSES:
        return "fail", "FAIL_FIXABLE", None
    if outcome.row_count < 1:
        return "fail", "FAIL_FIXABLE", None
    return "pass", "PASS", None


def _append_provenance_detail(detail: str, outcome: LiveValidationOutcome) -> str:
    prov = outcome.fetch_provenance or "unknown"
    if f"provenance={prov}" in detail:
        return detail
    return f"{detail}; fetch_provenance={prov}"


def _run_source_acceptance_pipeline(
    source_id: str,
    *,
    data_root: Path,
    db_path: Path | None = None,
) -> _SourcePipelineResult:
    resolved_db = db_path if db_path is not None else ensure_isolated_db(data_root)
    outcome = run_tier_c_live_validation(source_id, data_root)
    f0_status, f0_detail = _run_f0_data_health(
        source_id, data_root=data_root, db_path=resolved_db
    )
    disposition, failure_class, adr_ref = classify_source_report_failure(outcome)
    if failure_class != "FAIL_EXTERNAL" and f0_status in {"FAIL", "BLOCKED"}:
        disposition = "fail"
        failure_class = "FAIL_FIXABLE"
        adr_ref = None

    detail = outcome.detail
    if disposition == "fail":
        if failure_class == "FAIL_EXTERNAL":
            detail = f"fetch={outcome.fetch_status} external: {outcome.detail}"
        elif f0_status in {"FAIL", "BLOCKED"}:
            detail = f"data-health {f0_status}: {f0_detail}"
        elif outcome.fetch_status not in PASS_FETCH_STATUSES:
            detail = f"fetch failed: {outcome.detail}"
        elif outcome.row_count < 1:
            detail = "validation_fetch zero rows"
    else:
        detail = (
            f"fetch={outcome.fetch_status} health={f0_status} rows={outcome.row_count}"
        )
    detail = _append_provenance_detail(detail, outcome)

    return _SourcePipelineResult(
        source_id=source_id,
        outcome=outcome,
        f0_status=f0_status,
        f0_detail=f0_detail,
        disposition=disposition,
        failure_class=failure_class,
        adr_ref=adr_ref,
        detail=detail,
    )


def _cli_status_from_pipeline(pipeline: _SourcePipelineResult) -> Literal["pass", "fail"]:
    if pipeline.disposition == "pass":
        return "pass"
    if pipeline.failure_class == "FAIL_EXTERNAL" and pipeline.adr_ref:
        return "pass"
    return "fail"


def run_source_live_acceptance(source_id: str, *, data_root: Path) -> SourceAcceptanceResult:
    """Run validation_fetch→raw→F0 for one Tier C source."""
    resolved = assert_isolated_live_data_root(data_root)
    os.environ["QMD_DATA_ROOT"] = str(resolved)
    try:
        pipeline = _run_source_acceptance_pipeline(source_id, data_root=resolved)
    except Exception as exc:
        return SourceAcceptanceResult(source_id=source_id, status="fail", detail=str(exc))
    return SourceAcceptanceResult(
        source_id=source_id,
        status=_cli_status_from_pipeline(pipeline),
        detail=pipeline.detail,
        failure_class=pipeline.failure_class,
        adr_ref=pipeline.adr_ref,
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
    except TierCLiveEnvError as exc:
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


def _manifest_fetch_status(fetch_status: str) -> str:
    return _FETCH_STATUS_TO_MANIFEST.get(fetch_status.upper(), "FAILED")


def _resolve_fetch_schema_hash(
    source_id: str,
    *,
    data_root: Path,
    raw_paths: list[str],
    binding: dict[str, Any],
) -> str:
    from backend.app.datasources.normalizers.evidence_bundle import schema_hash_for_version

    for rel in reversed(raw_paths):
        path = data_root / rel.replace("/", os.sep)
        if path.suffix != ".json" or not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if raw_hash := payload.get("schema_hash"):
            return str(raw_hash)
        if schema_version := payload.get("schema_version"):
            return schema_hash_for_version(str(schema_version))
    health_profile_id = binding.get("health_profile_id")
    if health_profile_id and health_profile_id != "not_applicable":
        return schema_hash_for_version(str(health_profile_id))
    return schema_hash_for_version(str(binding.get("data_domain", source_id)))


def _build_fetch_block(
    source_id: str,
    *,
    data_root: Path,
    outcome: LiveValidationOutcome,
    raw_paths: list[str],
) -> dict[str, Any]:
    now = datetime.now(UTC).isoformat()
    fingerprint = "|".join(raw_paths) if raw_paths else outcome.detail
    binding = source_bindings()[source_id]
    schema_hash = _resolve_fetch_schema_hash(
        source_id, data_root=data_root, raw_paths=raw_paths, binding=binding
    )
    return {
        "source_id": source_id,
        "status": _manifest_fetch_status(outcome.fetch_status),
        "content_hash": hashlib.sha256(fingerprint.encode()).hexdigest(),
        "schema_hash": schema_hash,
        "row_count": outcome.row_count,
        "fetch_time": now,
        "as_of_timestamp": now,
    }


def build_live_tier_c_evidence_manifest(
    *,
    source_id: str,
    data_root: Path,
    run_id: str,
    job_id: str,
    outcome: LiveValidationOutcome,
    report_failure_class: str,
    f0_health_status: str = "pending",
    b2_validation_status: str = "NOT_APPLICABLE",
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
        "fetch": _build_fetch_block(
            source_id, data_root=data_root, outcome=outcome, raw_paths=raw_paths
        ),
        "evidence": {
            "raw_relative_paths": raw_paths,
            "evidence_dir_relative": _relative_to_data_root(data_root, evidence_dir),
        },
        "acceptance": {
            "disposition": disposition,
            "failure_class": manifest_failure_class(report_failure_class),
            "e2_inspect_status": outcome.inspect_status,
            "f0_health_status": f0_health_status,
            "b2_validation_status": b2_validation_status,
            "clean_table": binding["clean_table"],
            "rule_set_id": binding["rule_set_id"],
            "health_domain": binding["health_domain"],
            "health_profile_id": binding["health_profile_id"],
        },
    }


def write_live_tier_c_evidence_manifest(
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


def _process_source_for_report(
    source_id: str,
    *,
    data_root: Path,
    run_id: str,
    db_path: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    pipeline = _run_source_acceptance_pipeline(
        source_id, data_root=data_root, db_path=db_path
    )
    job_id = f"{run_id}:{source_id}"
    binding = source_bindings()[source_id]
    manifest = build_live_tier_c_evidence_manifest(
        source_id=source_id,
        data_root=data_root,
        run_id=run_id,
        job_id=job_id,
        outcome=pipeline.outcome,
        report_failure_class=pipeline.failure_class,
        f0_health_status=pipeline.f0_status,
    )
    manifest_path = write_live_tier_c_evidence_manifest(manifest, data_root=data_root)
    detail = pipeline.detail
    if pipeline.f0_detail and pipeline.failure_class == "PASS":
        detail = f"{detail}; f0={pipeline.f0_detail}"
    row = {
        "source_id": source_id,
        "disposition": pipeline.disposition,
        "failure_class": pipeline.failure_class,
        "failure_detail": detail,
        "adr_ref": pipeline.adr_ref,
        "fetch_status": pipeline.outcome.fetch_status,
        "e2_inspect_status": pipeline.outcome.inspect_status,
        "f0_health_status": pipeline.f0_status,
        "b2_validation_status": "NOT_APPLICABLE",
        "health_domain": binding["health_domain"],
        "health_profile_id": binding["health_profile_id"],
        "rule_set_id": binding["rule_set_id"],
        "clean_table": binding["clean_table"],
        "evidence_manifest_path": _relative_to_data_root(data_root, manifest_path),
        "fetch_provenance": pipeline.outcome.fetch_provenance,
    }
    return row, manifest


def _acceptance_report_exit_code(
    rows: list[dict[str, Any]], summary: dict[str, int]
) -> int:
    if summary["failed_fixable"] > 0:
        return 1
    if summary["failed_external"] > 0:
        externals = [r for r in rows if r.get("failure_class") == "FAIL_EXTERNAL"]
        if externals and all(r.get("adr_ref") for r in externals):
            return 0
        return 1
    return 0


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
    out = Path(report_path).parent / f"tier_c_live_acceptance_failure_{run_id}.json"
    out.write_text(json.dumps(artifact, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def run_acceptance_report(
    report_path: Path | str,
    *,
    source_id: str | None = None,
    quick: bool = False,
    data_root: Path | str | None = None,
) -> int:
    """Write TierCLiveAcceptanceReport JSON and per-source evidence manifests."""
    try:
        sources = select_source_ids(source_id=source_id, quick=quick)
        resolved_root = validate_live_acceptance_env(data_root=data_root, source_ids=sources)
    except TierCLiveEnvError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    run_id = uuid.uuid4().hex
    db_path = ensure_isolated_db(resolved_root)
    rows: list[dict[str, Any]] = []
    summary = {"total": 0, "passed": 0, "failed_fixable": 0, "failed_external": 0}
    for sid in sources:
        row, _manifest = _process_source_for_report(
            sid, data_root=resolved_root, run_id=run_id, db_path=db_path
        )
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
        "command": "tier_c_live_acceptance --report",
        "schema_version": SCHEMA_VERSION,
        "data_root": str(resolved_root),
        "generated_at": datetime.now(UTC).isoformat(),
        "sources": rows,
        "summary": summary,
    }
    out = Path(report_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    exit_code = _acceptance_report_exit_code(rows, summary)
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
    "TIER_C_SANDBOX_SEGMENT",
    "SourceAcceptanceResult",
    "TierCLiveEnvError",
    "assert_isolated_live_data_root",
    "build_live_tier_c_evidence_manifest",
    "classify_source_report_failure",
    "manifest_failure_class",
    "missing_api_keys_for_sources",
    "resolve_live_data_root",
    "run_acceptance",
    "run_acceptance_report",
    "run_source_live_acceptance",
    "select_source_ids",
    "source_bindings",
    "validate_live_acceptance_env",
    "write_acceptance_failure_artifact",
    "write_live_tier_c_evidence_manifest",
]
