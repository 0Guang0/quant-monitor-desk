"""Live pilot — phase4 (split from live_pilot.py, OP-01)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.app.config import DATA_ROOT, PROJECT_ROOT
from backend.app.db.connection import ConnectionManager
from backend.app.ops.live_pilot_constants import (
    DEFAULT_PRODUCTION_DB,
    DEFAULT_SANDBOX_ROOT,
    EASTMONEY_VERDICT_MD,
    ORIGINAL_REQUEST2_ENDPOINT_HOST,
    ORIGINAL_REQUEST2_VENDOR_API,
    PHASE3_RAW_EVIDENCE_JSON,
    PHASE3_REQUEST2_RECONCILIATION_MD,
    PHASE4_CONFLICT_INSPECT_TXT,
    PHASE4_NO_PRODUCTION_MUTATION_MD,
    PHASE4_VALIDATION_REPORT_JSON,
    SIDECAR_REQUEST2_ENDPOINT_HOST,
    SIDECAR_REQUEST2_VENDOR_API,
)
from backend.app.ops.live_pilot_phase3 import _ensure_sandbox_db
from backend.app.ops.live_pilot_phase1 import _utc_now_iso
from backend.app.ops.live_pilot_types import LivePilotAuthorizationError, LivePilotRequest
from backend.app.ops.mutation_proof import key_table_row_counts as _key_table_row_counts

def _load_raw_json_payload(raw_path: Path) -> dict[str, Any]:
    return json.loads(raw_path.read_text(encoding="utf-8"))


def _equity_bar_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        return []
    first = rows[0]
    if isinstance(first, dict):
        return [row for row in rows if isinstance(row, dict)]
    if isinstance(first, list):
        normalized: list[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, list) or len(row) < 7:
                continue
            normalized.append(
                {
                    "date": row[0],
                    "code": row[1],
                    "open": row[2],
                    "high": row[3],
                    "low": row[4],
                    "close": row[5],
                    "volume": row[6],
                }
            )
        return normalized
    return []


def _validate_equity_raw_structure(rows: list[dict[str, Any]]) -> dict[str, Any]:
    required = ("date", "open", "high", "low", "close")
    findings: list[str] = []
    if not rows:
        findings.append("EMPTY_ROWS")
        return {"status": "FAILED", "checked_rows": 0, "findings": findings}
    for index, row in enumerate(rows):
        missing = [field for field in required if field not in row or row[field] in (None, "")]
        if missing:
            findings.append(f"ROW_{index}_MISSING_FIELDS:{','.join(missing)}")
        try:
            high = float(row.get("high"))
            low = float(row.get("low"))
            if high < low:
                findings.append(f"ROW_{index}_HIGH_LT_LOW")
        except (TypeError, ValueError):
            findings.append(f"ROW_{index}_NON_NUMERIC_OHLC")
    status = "FAILED" if findings else "PASSED"
    return {"status": status, "checked_rows": len(rows), "findings": findings}


def _validate_macro_raw_structure(rows: list[dict[str, Any]]) -> dict[str, Any]:
    findings: list[str] = []
    if not rows:
        findings.append("EMPTY_ROWS")
        return {"status": "FAILED", "checked_rows": 0, "findings": findings}
    if not any("日期" in row or "date" in row for row in rows):
        findings.append("MISSING_DATE_COLUMN")
    status = "FAILED" if findings else "PASSED"
    return {"status": status, "checked_rows": len(rows), "findings": findings}


def _classify_request2_endpoint(
    *,
    raw_payload: dict[str, Any] | None,
    verdict_unavailable: bool,
) -> dict[str, Any]:
    vendor_api = str(raw_payload.get("vendor_api", "")) if raw_payload else ""
    sidecar_present = vendor_api == SIDECAR_REQUEST2_VENDOR_API
    original_present = vendor_api == ORIGINAL_REQUEST2_VENDOR_API
    if verdict_unavailable and not original_present:
        original_status = "SOURCE_ENDPOINT_FAILURE"
    elif original_present:
        original_status = "RAW_PRESENT"
    else:
        original_status = "SOURCE_ENDPOINT_FAILURE"
    sidecar_status = "SIDECAR_STRUCTURE_OK" if sidecar_present and raw_payload else "NOT_PRESENT"
    return {
        "original_endpoint_expected": (
            f"{ORIGINAL_REQUEST2_VENDOR_API} / {ORIGINAL_REQUEST2_ENDPOINT_HOST}"
        ),
        "sidecar_endpoint_observed": (
            f"{SIDECAR_REQUEST2_VENDOR_API} / {SIDECAR_REQUEST2_ENDPOINT_HOST}"
            if sidecar_present
            else None
        ),
        "vendor_api_observed": vendor_api or None,
        "original_semantics_status": original_status,
        "sidecar_classification": "candidate_only" if sidecar_present else None,
        "sidecar_validation_status": sidecar_status,
        "closes_original_request2": False,
        "supports_pilot_pass_raw_only": False,
    }


def _compare_equity_sidecar_conflict(
    *,
    primary_rows: list[dict[str, Any]],
    sidecar_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Informational baostock vs Sina sidecar comparison — not authoritative for Request 2."""
    primary_by_date = {
        str(row.get("date")): row for row in primary_rows if row.get("date") is not None
    }
    sidecar_by_date = {
        str(row.get("date")): row for row in sidecar_rows if row.get("date") is not None
    }
    findings: list[dict[str, Any]] = []
    for trade_date in sorted(set(primary_by_date) & set(sidecar_by_date)):
        primary_close = primary_by_date[trade_date].get("close")
        sidecar_close = sidecar_by_date[trade_date].get("close")
        try:
            p_close = float(primary_close)
            s_close = float(sidecar_close)
            rel_diff = abs(p_close - s_close) / p_close if p_close else None
        except (TypeError, ValueError):
            rel_diff = None
        findings.append(
            {
                "trade_date": trade_date,
                "primary_source": "baostock",
                "sidecar_source": "akshare",
                "sidecar_vendor_api": SIDECAR_REQUEST2_VENDOR_API,
                "primary_close": primary_close,
                "sidecar_close": sidecar_close,
                "relative_close_diff": rel_diff,
                "informational_only": True,
            }
        )
    return findings


def _phase4_declared_validator_contract_refs() -> dict[str, Any]:
    """Freeze declared validator/conflict paths used to gate any clean write."""
    from backend.app.db.validation_gate import DbValidationGate
    from backend.app.validators.data_quality import DataQualityValidator
    from backend.app.validators.source_conflict import SourceConflictValidator

    return {
        "data_quality_validator": (
            f"{DataQualityValidator.__module__}.{DataQualityValidator.__name__}"
        ),
        "source_conflict_validator": (
            f"{SourceConflictValidator.__module__}.{SourceConflictValidator.__name__}"
        ),
        "clean_write_gate": f"{DbValidationGate.__module__}.{DbValidationGate.__name__}",
        "data_quality_rules": "specs/contracts/data_quality_rules.yaml",
        "source_conflict_rules": "specs/contracts/source_conflict_rules.yaml",
        "write_contract": "specs/contracts/write_contract.yaml",
        "freeze_note": (
            "Batch 2.75 Phase 4 remains raw/sandbox validation only. Any future clean write "
            "must pass DataQualityValidator, SourceConflictValidator, and DbValidationGate; "
            "local raw structure checks cannot independently authorize clean writes."
        ),
    }


def _format_phase4_conflict_inspect(
    *,
    conflict_rows: list[dict[str, Any]],
    request2_classification: dict[str, Any],
) -> str:
    lines = [
        "# Phase 4 — Source Conflict Inspect (Batch 2.75)",
        "",
        "## Scope",
        "",
        "- Validation covers Request 1 (baostock primary) and Request 3 (akshare macro shape).",
        "- Request 2 original endpoint (`stock_zh_a_hist` / Eastmoney push2his) is recorded as "
        "source/endpoint failure per reconciliation evidence.",
        "- Any baostock vs Sina sidecar rows below are **informational candidate comparison only** "
        "and do **not** close original Request 2.",
        "",
        "- **Request 2 original semantics:** "
        f"{request2_classification['original_semantics_status']}",
        f"- **Sidecar classification:** {request2_classification.get('sidecar_classification')}",
        "",
    ]
    if not conflict_rows:
        lines.extend(
            [
                "## Result",
                "",
                "NO_CONFLICT_INSPECT_REQUIRED_FOR_CLOSEOUT",
                "",
                "Sidecar comparison skipped or produced zero overlapping trade dates.",
                "",
            ]
        )
    else:
        lines.extend(["## Informational sidecar close diffs", ""])
        for row in conflict_rows:
            lines.append(
                f"- {row['trade_date']}: baostock close={row['primary_close']} vs "
                f"Sina sidecar close={row['sidecar_close']} "
                f"(rel_diff={row['relative_close_diff']}) [informational_only]"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def _require_request2_phase4_prerequisites(evidence_dir: Path) -> bool:
    reconciliation_path = evidence_dir / PHASE3_REQUEST2_RECONCILIATION_MD
    verdict_path = evidence_dir / EASTMONEY_VERDICT_MD
    missing = [
        name
        for name, path in (
            (PHASE3_REQUEST2_RECONCILIATION_MD, reconciliation_path),
            (EASTMONEY_VERDICT_MD, verdict_path),
        )
        if not path.is_file()
    ]
    if missing:
        raise LivePilotAuthorizationError(
            f"Request 2 Phase 4 prerequisites missing: {', '.join(missing)}"
        )

    reconciliation = reconciliation_path.read_text(encoding="utf-8")
    required_reconciliation_markers = (
        "stock_zh_a_hist",
        ORIGINAL_REQUEST2_ENDPOINT_HOST,
        "sidecar",
    )
    for marker in required_reconciliation_markers:
        if marker not in reconciliation:
            raise LivePilotAuthorizationError(f"Request 2 reconciliation missing marker: {marker}")

    verdict = verdict_path.read_text(encoding="utf-8")
    if (
        "不可用" not in verdict
        and "unreachable" not in verdict.lower()
        and "failure" not in verdict.lower()
    ):
        raise LivePilotAuthorizationError(
            "Request 2 verdict must record original endpoint failure/unavailability"
        )
    return "不可用" in verdict or "unreachable" in verdict.lower() or "failure" in verdict.lower()


def capture_phase4_validation(
    *,
    evidence_dir: Path,
    phase3_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Phase 4 raw validation + conflict inspect — default no clean write."""
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    if phase3_payload is None:
        phase3_path = evidence_dir / PHASE3_RAW_EVIDENCE_JSON
        if not phase3_path.is_file():
            raise FileNotFoundError(f"missing phase3 evidence: {phase3_path}")
        phase3_payload = json.loads(phase3_path.read_text(encoding="utf-8"))

    verdict_unavailable = _require_request2_phase4_prerequisites(evidence_dir)

    prod_before_counts = _key_table_row_counts(DEFAULT_PRODUCTION_DB)
    prod_before_hash = (
        DEFAULT_PRODUCTION_DB.read_bytes() if DEFAULT_PRODUCTION_DB.is_file() else None
    )

    fetches_by_id = {item["pilot_request_id"]: item for item in phase3_payload.get("fetches", [])}
    validations: list[dict[str, Any]] = []
    primary_equity_rows: list[dict[str, Any]] = []
    sidecar_equity_rows: list[dict[str, Any]] = []
    request2_classification: dict[str, Any] = {}

    for pilot_request_id in ("pilot-req-1", "pilot-req-2", "pilot-req-3"):
        fetch_item = fetches_by_id.get(pilot_request_id)
        if fetch_item is None:
            validations.append(
                {
                    "pilot_request_id": pilot_request_id,
                    "validation_scope": "missing_phase3_fetch",
                    "status": "FAILED",
                }
            )
            continue

        fetch_result = fetch_item["fetch_result"]
        raw_paths = fetch_result.get("raw_file_paths") or []
        raw_payload = None
        if raw_paths:
            raw_payload = _load_raw_json_payload(Path(raw_paths[0]))

        if pilot_request_id == "pilot-req-1":
            rows = _equity_bar_rows(raw_payload or {})
            structure = _validate_equity_raw_structure(rows)
            primary_equity_rows = rows
            validations.append(
                {
                    "pilot_request_id": pilot_request_id,
                    "validation_scope": "original_approved_semantics",
                    "data_domain": "cn_equity_daily_bar",
                    "source_id": "baostock",
                    "operation": "fetch_daily_bar",
                    "fetch_status": fetch_result.get("status"),
                    "structure_validation": structure,
                    "status": structure["status"],
                    "allow_clean_write": False,
                }
            )
        elif pilot_request_id == "pilot-req-2":
            request2_classification = _classify_request2_endpoint(
                raw_payload=raw_payload,
                verdict_unavailable=verdict_unavailable,
            )
            sidecar_structure = None
            if raw_payload and request2_classification["sidecar_classification"]:
                sidecar_rows = _equity_bar_rows(raw_payload)
                sidecar_equity_rows = sidecar_rows
                sidecar_structure = _validate_equity_raw_structure(sidecar_rows)
            validations.append(
                {
                    "pilot_request_id": pilot_request_id,
                    "validation_scope": "original_approved_semantics",
                    "data_domain": "cn_equity_daily_bar",
                    "source_id": "akshare",
                    "operation": "fetch_daily_bar_validation",
                    "fetch_status": fetch_result.get("status"),
                    "request2_endpoint_classification": request2_classification,
                    "sidecar_structure_validation": sidecar_structure,
                    "status": request2_classification["original_semantics_status"],
                    "allow_clean_write": False,
                }
            )
        else:
            macro_rows = (raw_payload or {}).get("rows", [])
            structure = _validate_macro_raw_structure(
                macro_rows if isinstance(macro_rows, list) else []
            )
            validations.append(
                {
                    "pilot_request_id": pilot_request_id,
                    "validation_scope": "original_approved_semantics",
                    "data_domain": "macro_supplementary",
                    "source_id": "akshare",
                    "operation": "fetch_macro_series",
                    "fetch_status": fetch_result.get("status"),
                    "structure_validation": structure,
                    "fred_primary_deferred": True,
                    "status": structure["status"],
                    "allow_clean_write": False,
                }
            )

    conflict_rows = _compare_equity_sidecar_conflict(
        primary_rows=primary_equity_rows,
        sidecar_rows=sidecar_equity_rows,
    )
    severe_findings = [
        {
            "pilot_request_id": item["pilot_request_id"],
            "status": item.get("status"),
            "validation_scope": item.get("validation_scope"),
        }
        for item in validations
        if item.get("status") in {"FAILED", "SOURCE_ENDPOINT_FAILURE"}
    ]
    severe_findings_block_clean_write = bool(severe_findings)

    prod_after_counts = _key_table_row_counts(DEFAULT_PRODUCTION_DB)
    prod_after_hash = (
        DEFAULT_PRODUCTION_DB.read_bytes() if DEFAULT_PRODUCTION_DB.is_file() else None
    )

    generated_at = _utc_now_iso()
    payload: dict[str, Any] = {
        "generated_at": generated_at,
        "phase": "phase4_validation",
        "allow_clean_write": False,
        "can_write_clean": False,
        "clean_write_performed": False,
        "clean_write_block_reasons": tuple(
            reason
            for reason in (
                "ALLOW_CLEAN_WRITE_FALSE_DEFAULT",
                "SEVERE_FINDINGS_PRESENT" if severe_findings_block_clean_write else None,
            )
            if reason is not None
        ),
        "declared_validation_conflict_paths": _phase4_declared_validator_contract_refs(),
        "severe_findings_block_clean_write": severe_findings_block_clean_write,
        "severe_findings": severe_findings,
        "request2_reconciliation_ref": PHASE3_REQUEST2_RECONCILIATION_MD,
        "eastmoney_verdict_ref": EASTMONEY_VERDICT_MD,
        "validation_scope_note": (
            "Request 1 and Request 3 validated under original approved semantics; "
            "Request 2 original endpoint failure recorded separately from Sina sidecar rows."
        ),
        "validations": validations,
        "production_mutation_proof": {
            "production_db_path": str(DEFAULT_PRODUCTION_DB),
            "db_hash_unchanged": prod_before_hash == prod_after_hash,
            "before_key_table_counts": prod_before_counts,
            "after_key_table_counts": prod_after_counts,
            "row_counts_unchanged": prod_before_counts == prod_after_counts,
        },
    }

    conflict_text = _format_phase4_conflict_inspect(
        conflict_rows=conflict_rows,
        request2_classification=request2_classification
        or _classify_request2_endpoint(raw_payload=None, verdict_unavailable=verdict_unavailable),
    )

    proof_lines = [
        "# Phase 4 — No Production Mutation Proof",
        "",
        f"- **Generated at:** {generated_at}",
        f"- **Production DB:** `{DEFAULT_PRODUCTION_DB}`",
        "- **allow_clean_write:** false",
        "- **can_write_clean:** false",
        "- **clean_write_performed:** false",
        f"- **clean_write_block_reasons:** {payload['clean_write_block_reasons']}",
        "- **declared_validation_conflict_paths:** "
        f"{payload['declared_validation_conflict_paths']}",
        f"- **severe_findings_block_clean_write:** {severe_findings_block_clean_write}",
        f"- **db_hash_unchanged:** {prod_before_hash == prod_after_hash}",
        f"- **row_counts_unchanged:** {prod_before_counts == prod_after_counts}",
        "",
    ]

    (evidence_dir / PHASE4_VALIDATION_REPORT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / PHASE4_CONFLICT_INSPECT_TXT).write_text(conflict_text, encoding="utf-8")
    (evidence_dir / PHASE4_NO_PRODUCTION_MUTATION_MD).write_text(
        "\n".join(proof_lines) + "\n",
        encoding="utf-8",
    )
    return payload


def capture_task_phase4_validation_evidence(evidence_dir: Path | str) -> dict[str, Any]:
    """Execute helper: Phase 4 validation on existing phase3 raw evidence."""
    return capture_phase4_validation(evidence_dir=Path(evidence_dir))
