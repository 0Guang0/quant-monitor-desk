"""R3G-03 rollback plan — identify-only dry-run (no production deletes)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from backend.app.ops.sandbox_clean_write.approval_contract import ApprovalCandidate, ApprovalContract
from backend.app.ops.sandbox_clean_write.path_utils import resolve_sandbox_path, utc_now_iso

ROLLBACK_PLAN_VERSION = "r3g03-rollback-v1"


class RollbackPlanError(RuntimeError):
    """Rollback plan validation or build failed fail-closed."""


def _plan_id(approval_id: str, candidate: ApprovalCandidate) -> str:
    digest = hashlib.sha256(
        f"{approval_id}:{candidate.source_id}:{candidate.symbols}".encode()
    ).hexdigest()[:12]
    return f"r3g03-rollback-{digest}"


def build_rollback_plan(
    contract: ApprovalContract,
    candidate: ApprovalCandidate,
    *,
    before_proof: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build identify-only rollback plan from approval + optional before proof."""
    prod_path = resolve_sandbox_path(contract.production_db_path)
    affected_keys = [
        {
            "symbol": symbol,
            "start_date": candidate.start_date,
            "end_date": candidate.end_date,
        }
        for symbol in candidate.symbols
    ]
    return {
        "rollback_plan_id": _plan_id(contract.approval_id, candidate),
        "rollback_plan_version": ROLLBACK_PLAN_VERSION,
        "generated_at": utc_now_iso(),
        "dry_run_only": True,
        "identify_only": True,
        "production_db_path": str(prod_path),
        "target_table": candidate.target_table,
        "source_id": candidate.source_id,
        "domain": candidate.domain,
        "affected_keys": affected_keys,
        "non_target_keys_untouched": True,
        "before_proof_row_count": (before_proof or {}).get("target_table_row_count"),
        "note": "identify-only dry-run; no production DELETE executed",
    }


def write_rollback_plan(path: Path | str, plan: dict[str, Any]) -> Path:
    resolved = resolve_sandbox_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return resolved


def load_rollback_plan(path: Path | str) -> dict[str, Any]:
    resolved = resolve_sandbox_path(path)
    if not resolved.is_file():
        raise RollbackPlanError(f"missing_rollback_plan: {resolved}")
    return json.loads(resolved.read_text(encoding="utf-8"))


def validate_rollback_plan(
    plan: dict[str, Any],
    *,
    candidate: ApprovalCandidate,
    production_db_path: Path,
) -> None:
    """Ensure rollback plan is identify-only and scoped to approved keys."""
    if not plan.get("dry_run_only"):
        raise RollbackPlanError("rollback plan must set dry_run_only=true")
    if not plan.get("identify_only"):
        raise RollbackPlanError("rollback plan must set identify_only=true")
    if not plan.get("non_target_keys_untouched"):
        raise RollbackPlanError("rollback plan must assert non_target_keys_untouched")

    plan_prod = resolve_sandbox_path(str(plan.get("production_db_path") or ""))
    if plan_prod != resolve_sandbox_path(production_db_path):
        raise RollbackPlanError("rollback plan production_db_path mismatch")

    if plan.get("target_table") != candidate.target_table:
        raise RollbackPlanError("rollback plan target_table mismatch")

    affected = plan.get("affected_keys") or []
    expected_symbols = set(candidate.symbols)
    plan_symbols = {item.get("symbol") for item in affected}
    if plan_symbols != expected_symbols:
        raise RollbackPlanError("rollback plan affected_keys symbol mismatch")


def dry_run_identify_affected_keys(plan: dict[str, Any]) -> list[dict[str, str]]:
    """Return affected key identifiers only — never mutates production DB."""
    if not plan.get("identify_only"):
        raise RollbackPlanError("dry_run_identify requires identify_only=true")
    return list(plan.get("affected_keys") or [])
