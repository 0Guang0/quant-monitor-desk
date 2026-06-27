"""R3G-01 rehearsal report builder — contract required_report_fields."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from backend.app.config import PROJECT_ROOT
from backend.app.ops.data_health import DataHealthReport

CONTRACT_PATH = PROJECT_ROOT / "specs/contracts/sandbox_clean_write_contract.yaml"


def required_report_fields() -> tuple[str, ...]:
    if not CONTRACT_PATH.is_file():
        raise FileNotFoundError(CONTRACT_PATH)
    raw = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8")) or {}
    fields = (raw.get("r3g01_rehearsal") or {}).get("required_report_fields") or []
    return tuple(str(f) for f in fields)


def build_data_health_summary(report: DataHealthReport) -> dict[str, Any]:
    """Nested DH summary with pass/warn/fail counts (not free text)."""
    pass_count = sum(1 for c in report.checks if c.status == "PASS")
    warn_count = sum(1 for c in report.checks if c.status == "WARN")
    fail_count = sum(1 for c in report.checks if c.status == "FAIL")
    duplicate_pk = sum(
        1 for c in report.checks if c.rule_id == "DUPLICATE_PRIMARY_KEY" and c.status == "FAIL"
    )
    ohlc_violations = sum(
        1
        for c in report.checks
        if c.rule_id in {"INVALID_OHLC", "NON_POSITIVE_PRICE"} and c.status == "FAIL"
    )
    calendar_violations = sum(
        1
        for c in report.checks
        if c.rule_id in {"MISSING_TRADING_DAY", "INSUFFICIENT_HISTORY"} and c.status == "FAIL"
    )
    return {
        "overall_status": report.overall_status,
        "validation_pass_count": pass_count,
        "validation_warn_count": warn_count,
        "validation_fail_count": fail_count,
        "duplicate_primary_key_count": duplicate_pk,
        "ohlc_violation_count": ohlc_violations,
        "calendar_gap_violation_count": calendar_violations,
        "sandbox_clean_write_gate_ready": report.sandbox_clean_write_gate_ready,
        "gate_rationale": report.gate_rationale,
    }


def build_rehearsal_report(
    *,
    candidate_set: str,
    source_id: str,
    domain: str,
    bundle_rows: dict[str, int],
    window_start: str,
    window_end: str,
    validation_status: str,
    data_health_status: str,
    data_health_summary: dict[str, Any],
    source_fetch_id_coverage: float,
    content_hash_coverage: float,
    schema_hash_coverage: float,
    write_manager_operation_id: str,
    rollback_artifact_path: str,
    symbol_or_series_count: int,
    production_mutation_allowed: bool = False,
) -> dict[str, Any]:
    """Build contract-shaped rehearsal report JSON payload."""
    report = {
        "candidate_set": candidate_set,
        "source_id": source_id,
        "domain": domain,
        "symbol_or_series_count": symbol_or_series_count,
        "window_start": window_start,
        "window_end": window_end,
        "raw_row_count": bundle_rows.get("raw", 0),
        "staged_row_count": bundle_rows.get("staged", 0),
        "sandbox_clean_row_count": bundle_rows.get("clean", 0),
        "validation_status": validation_status,
        "data_health_status": data_health_status,
        "data_health_summary": data_health_summary,
        "source_fetch_id_coverage": source_fetch_id_coverage,
        "content_hash_coverage": content_hash_coverage,
        "schema_hash_coverage": schema_hash_coverage,
        "write_manager_operation_id": write_manager_operation_id,
        "rollback_artifact_path": rollback_artifact_path,
        "production_mutation_allowed": production_mutation_allowed,
        "sandbox_only": True,
        "production_live_claim": False,
    }
    missing = [field for field in required_report_fields() if field not in report]
    if missing:
        raise ValueError(f"rehearsal report missing required fields: {missing}")
    return report


def write_rehearsal_report(path: Path, payload: dict[str, Any]) -> Path:
    import json

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
