"""R3G-03 limited production promote — approval YAML + audit_decision.json validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from backend.app.db.sql_identifiers import quote_ident
from backend.app.ops.sandbox_clean_write.audit_decision import AuditDecision, AuditResult
from backend.app.ops.sandbox_clean_write.path_utils import resolve_sandbox_path
from backend.app.ops.sandbox_clean_write.rehearsal_plan import (
    CONTRACT_PATH,
    validate_contract_source_caps,
)

ALLOWING_DECISIONS = frozenset(
    {
        AuditDecision.PASS_ALLOW_LIMITED_PROD_WRITE,
        AuditDecision.WARN_ALLOW_WITH_MANUAL_APPROVAL,
    }
)


class ApprovalContractError(RuntimeError):
    """Approval or audit decision failed fail-closed promote gate."""


@dataclass(frozen=True)
class ApprovalCandidate:
    source_id: str
    domain: str
    symbols: tuple[str, ...]
    start_date: str
    end_date: str
    max_rows: int
    target_table: str
    metadata_only: bool = False
    live_fetch_authorized: bool = False

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ApprovalCandidate:
        symbols_raw = raw.get("symbols") or raw.get("series") or []
        target_table = str(raw.get("target_table") or "")
        _validate_target_table(target_table)
        return cls(
            source_id=str(raw["source_id"]),
            domain=str(raw["domain"]),
            symbols=tuple(str(s) for s in symbols_raw),
            start_date=str(raw["start_date"]),
            end_date=str(raw["end_date"]),
            max_rows=int(raw.get("max_rows") or 0),
            target_table=target_table,
            metadata_only=bool(raw.get("metadata_only", False)),
            live_fetch_authorized=bool(raw.get("live_fetch_authorized", False)),
        )


@dataclass(frozen=True)
class ApprovalContract:
    approval_id: str
    approver: str
    approved_at: str
    audit_decision_file: str
    source_candidates: tuple[ApprovalCandidate, ...]
    production_db_path: str
    rollback_plan_path: str
    rollback_required: bool
    no_agent_triggered_write: bool
    no_cap_expansion: bool

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ApprovalContract:
        candidates = tuple(
            ApprovalCandidate.from_dict(item)
            for item in (raw.get("source_candidates") or [])
        )
        return cls(
            approval_id=str(raw.get("approval_id") or ""),
            approver=str(raw.get("approver") or ""),
            approved_at=str(raw.get("approved_at") or ""),
            audit_decision_file=str(raw.get("audit_decision_file") or ""),
            source_candidates=candidates,
            production_db_path=str(raw.get("production_db_path") or ""),
            rollback_plan_path=str(raw.get("rollback_plan_path") or ""),
            rollback_required=bool(raw.get("rollback_required", True)),
            no_agent_triggered_write=bool(raw.get("no_agent_triggered_write", False)),
            no_cap_expansion=bool(raw.get("no_cap_expansion", False)),
        )


def _validate_target_table(table: str) -> None:
    if not table:
        raise ApprovalContractError("target_table is required")
    try:
        quote_ident(table)
    except ValueError as exc:
        raise ApprovalContractError(f"invalid target_table: {exc}") from exc


def _load_contract_caps() -> dict[str, Any]:
    if not CONTRACT_PATH.is_file():
        raise ApprovalContractError(f"missing contract: {CONTRACT_PATH}")
    raw = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8")) or {}
    return raw.get("candidate_caps") or {}


def _window_days(start: str, end: str) -> int:
    start_d = date.fromisoformat(start)
    end_d = date.fromisoformat(end)
    if end_d < start_d:
        raise ApprovalContractError(f"end_date {end!r} before start_date {start!r}")
    return (end_d - start_d).days + 1


def validate_r3g03_source_caps(candidate: ApprovalCandidate) -> None:
    """Hard-reject candidates exceeding contract r3g03 caps."""
    validate_contract_source_caps(
        source_id=candidate.source_id,
        domain=candidate.domain,
        symbols=candidate.symbols,
        window_days=_window_days(candidate.start_date, candidate.end_date),
        metadata_only=candidate.metadata_only,
        profile="r3g03",
        error_cls=ApprovalContractError,
    )


def load_approval_contract(path: Path | str) -> ApprovalContract:
    resolved = resolve_sandbox_path(path)
    if not resolved.is_file():
        raise ApprovalContractError(f"missing_approval_file: {resolved}")
    raw = yaml.safe_load(resolved.read_text(encoding="utf-8")) or {}
    contract = ApprovalContract.from_dict(raw)
    if not contract.approval_id:
        raise ApprovalContractError("approval_id is required")
    if not contract.approver:
        raise ApprovalContractError("approver is required")
    if not contract.source_candidates:
        raise ApprovalContractError("source_candidates must be non-empty")
    if len(contract.source_candidates) > 3:
        raise ApprovalContractError("max 3 source candidates per r3g03 cap")
    return contract


def load_audit_decision_payload(path: Path | str) -> dict[str, Any]:
    resolved = resolve_sandbox_path(path)
    if not resolved.is_file():
        raise ApprovalContractError(f"missing audit decision file: {resolved}")
    return json.loads(resolved.read_text(encoding="utf-8"))


def _audit_promote_fields(payload: dict[str, Any]) -> dict[str, Any]:
    symbols = payload.get("symbols") or payload.get("series") or []
    target_table = str(payload.get("target_table") or "")
    _validate_target_table(target_table)
    return {
        "source_id": str(payload.get("source_id") or ""),
        "domain": str(payload.get("domain") or ""),
        "symbols": tuple(str(s) for s in symbols),
        "start_date": str(payload.get("start_date") or ""),
        "end_date": str(payload.get("end_date") or ""),
        "max_rows": int(payload.get("max_rows") or 0),
        "target_table": target_table,
        "production_db_path": str(payload.get("production_db_path") or ""),
    }


def _candidate_promote_fields(candidate: ApprovalCandidate) -> dict[str, Any]:
    return {
        "source_id": candidate.source_id,
        "domain": candidate.domain,
        "symbols": candidate.symbols,
        "start_date": candidate.start_date,
        "end_date": candidate.end_date,
        "max_rows": candidate.max_rows,
        "target_table": candidate.target_table,
        "production_db_path": "",  # filled by caller
    }


def _mismatched_field(
    approval_fields: dict[str, Any],
    audit_fields: dict[str, Any],
) -> str | None:
    keys = (
        "source_id",
        "domain",
        "symbols",
        "start_date",
        "end_date",
        "max_rows",
        "target_table",
        "production_db_path",
    )
    for key in keys:
        if approval_fields.get(key) != audit_fields.get(key):
            return key
    return None


def validate_approval_contract(
    approval_path: Path | str,
    audit_decision_path: Path | str,
    *,
    rollback_plan_path: Path | str | None = None,
) -> tuple[ApprovalContract, AuditResult, ApprovalCandidate]:
    """Fail-closed quadruple-lock gate — approval YAML must align with audit_decision.json."""
    contract = load_approval_contract(approval_path)
    audit_path = resolve_sandbox_path(audit_decision_path)
    audit_payload = load_audit_decision_payload(audit_path)

    if contract.audit_decision_file:
        expected_audit = resolve_sandbox_path(contract.audit_decision_file)
        if expected_audit != audit_path:
            raise ApprovalContractError("approval_audit_mismatch: audit_decision_file")

    if rollback_plan_path is not None and contract.rollback_plan_path:
        expected_rollback = resolve_sandbox_path(contract.rollback_plan_path)
        if expected_rollback != resolve_sandbox_path(rollback_plan_path):
            raise ApprovalContractError("approval_audit_mismatch: rollback_plan_path")

    try:
        audit_result = AuditResult.from_dict(audit_payload)
    except ValueError as exc:
        raise ApprovalContractError(f"audit_decision_not_allowing_entry: {exc}") from exc

    if audit_result.decision not in ALLOWING_DECISIONS:
        raise ApprovalContractError(
            f"audit_decision_not_allowing_entry: {audit_result.decision.value}"
        )

    if not contract.no_agent_triggered_write:
        raise ApprovalContractError("agent_triggered_write_path: no_agent_triggered_write must be true")

    if not contract.no_cap_expansion:
        raise ApprovalContractError("cap_expansion: no_cap_expansion must be true")

    if not contract.rollback_required:
        raise ApprovalContractError("rollback_required must be true")

    prod_path = resolve_sandbox_path(contract.production_db_path)
    audit_prod = audit_payload.get("production_db_path")
    if audit_prod and resolve_sandbox_path(str(audit_prod)) != prod_path:
        raise ApprovalContractError("approval_audit_mismatch: production_db_path")

    # ponytail: R3G-03 pilot supports single-candidate promote; multi-source needs explicit extension
    if len(contract.source_candidates) != 1:
        raise ApprovalContractError("r3g03 pilot supports exactly one source candidate per promote run")

    candidate = contract.source_candidates[0]
    validate_r3g03_source_caps(candidate)

    approval_fields = _candidate_promote_fields(candidate)
    approval_fields["production_db_path"] = str(prod_path)
    audit_fields = _audit_promote_fields(audit_payload)
    if audit_fields["production_db_path"]:
        audit_fields["production_db_path"] = str(resolve_sandbox_path(audit_fields["production_db_path"]))

    mismatch = _mismatched_field(approval_fields, audit_fields)
    if mismatch:
        raise ApprovalContractError(f"approval_audit_mismatch: {mismatch}")

    if candidate.max_rows <= 0:
        raise ApprovalContractError("max_rows must be positive")

    return contract, audit_result, candidate
