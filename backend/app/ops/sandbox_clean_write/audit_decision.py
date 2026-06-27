"""R3G-02 adversarial audit decision types — contract r3g02_audit.decision_enum."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml

from backend.app.config import PROJECT_ROOT

CONTRACT_PATH = PROJECT_ROOT / "specs/contracts/sandbox_clean_write_contract.yaml"


class AuditDecision(StrEnum):
    PASS_ALLOW_LIMITED_PROD_WRITE = "PASS_ALLOW_LIMITED_PROD_WRITE"
    WARN_ALLOW_WITH_MANUAL_APPROVAL = "WARN_ALLOW_WITH_MANUAL_APPROVAL"
    BLOCK_PRODUCTION_WRITE = "BLOCK_PRODUCTION_WRITE"


@dataclass(frozen=True)
class AuditFinding:
    code: str
    message: str
    evidence_paths: tuple[str, ...] = ()

    def serialize(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "evidence_paths": list(self.evidence_paths),
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> AuditFinding:
        return cls(
            code=str(raw.get("code", "")),
            message=str(raw.get("message", "")),
            evidence_paths=tuple(str(p) for p in (raw.get("evidence_paths") or [])),
        )


@dataclass(frozen=True)
class AuditResult:
    decision: AuditDecision
    blocking_reasons: tuple[AuditFinding, ...]
    warning_reasons: tuple[AuditFinding, ...]
    evidence_paths: tuple[str, ...]
    production_mutation_allowed: bool = False

    def serialize(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "blocking_reasons": [f.serialize() for f in self.blocking_reasons],
            "warning_reasons": [f.serialize() for f in self.warning_reasons],
            "evidence_paths": list(self.evidence_paths),
            "production_mutation_allowed": self.production_mutation_allowed,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> AuditResult:
        decision_raw = raw.get("decision")
        try:
            decision = AuditDecision(str(decision_raw))
        except ValueError as exc:
            raise ValueError(f"unknown audit decision: {decision_raw!r}") from exc
        contract_values = set(_contract_decision_enum())
        if decision.value not in contract_values:
            raise ValueError(f"unknown audit decision: {decision_raw!r}")
        return cls(
            decision=decision,
            blocking_reasons=tuple(
                AuditFinding.from_dict(item) for item in (raw.get("blocking_reasons") or [])
            ),
            warning_reasons=tuple(
                AuditFinding.from_dict(item) for item in (raw.get("warning_reasons") or [])
            ),
            evidence_paths=tuple(str(p) for p in (raw.get("evidence_paths") or [])),
            production_mutation_allowed=bool(raw.get("production_mutation_allowed", False)),
        )


def _contract_decision_enum() -> tuple[str, ...]:
    if not CONTRACT_PATH.is_file():
        raise FileNotFoundError(CONTRACT_PATH)
    raw = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8")) or {}
    values = (raw.get("r3g02_audit") or {}).get("decision_enum") or []
    return tuple(str(v) for v in values)


def write_audit_decision(path: Path, result: AuditResult) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.serialize(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
