"""Live pilot — phase2 (split from live_pilot.py, OP-01)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.app.core.resource_guard import Decision
from backend.app.datasources.service import DataSourceService
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.ops.live_pilot_auth import (
    _pilot_request_to_dict,
    assert_pilot_ready_before_fetch,
    validate_authorization,
)
from backend.app.ops.live_pilot_constants import (
    DEFAULT_AUTHORIZATION_PATH,
    DEFAULT_PRODUCTION_DB,
    DISABLED_PILOT_SOURCE_IDS,
    FRED_PRIMARY_DEFERRED_NOTE,
    HITL_CONFIRMATION_MD,
    PHASE2_ROUTE_MATRIX_JSON,
)
from backend.app.ops.live_pilot_phase1 import _utc_now_iso
from backend.app.ops.live_pilot_types import LivePilotAuthorizationError, LivePilotRequest

def _explicit_source_route_status(
    *,
    source_id: str,
    candidates: list[Any],
) -> str:
    candidate = next((c for c in candidates if c.source_id == source_id), None)
    if candidate is None:
        return "NO_AVAILABLE_SOURCE"
    if candidate.enabled:
        return "READY"
    reason = candidate.skip_reason or candidate.disabled_reason or ""
    if "user_authorization" in reason or reason.startswith("missing_env:"):
        return "USER_AUTH_REQUIRED"
    if reason == "capability_missing":
        return "CAPABILITY_MISSING"
    if source_id == "qmt_xtdata" and reason:
        return "DISABLED_SOURCE"
    return "DISABLED_SOURCE"


def preview_live_pilot(
    request: LivePilotRequest,
    *,
    service: DataSourceService | None = None,
    pilot_request_id: str = "pilot-req",
) -> dict[str, Any]:
    """Dry-run route preview for one authorized pilot request (no fetch)."""
    validate_authorization(request)
    if not request.dry_run:
        raise LivePilotAuthorizationError("Phase 2 route preview requires dry_run=true")

    svc = service or DataSourceService()
    guard_decision, guard_reason = svc.check_resource_guard()
    if guard_decision == Decision.HARD_STOP:
        raise RuntimeError(f"ResourceGuard HARD_STOP: {guard_reason}")

    route_plan = svc.preview_route(
        data_domain=request.data_domain,
        operation=request.operation,
        run_id=f"{pilot_request_id}-preview",
        job_id="batch275-live-pilot-phase2",
    )
    explicit_status = _explicit_source_route_status(
        source_id=request.source_id,
        candidates=route_plan.candidates,
    )

    return {
        "pilot_request_id": pilot_request_id,
        "request": _pilot_request_to_dict(request),
        "authorization_evidence": request.authorization_evidence,
        "dry_run": True,
        "route_plan": route_plan.to_payload_dict(),
        "explicit_source_route_status": explicit_status,
        "resource_guard_decision": guard_decision.value,
        "resource_guard_reason": guard_reason,
    }


def capture_phase2_route_matrix(
    *,
    requests: tuple[LivePilotRequest, ...],
    evidence_dir: Path,
    db_path: Path | None = None,
    service: DataSourceService | None = None,
) -> dict[str, Any]:
    """Phase 2 route preview matrix for authorized requests — zero fetch, optional DB proof."""
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    target_db = db_path or DEFAULT_PRODUCTION_DB
    before_counts = _key_table_row_counts(target_db) if target_db.is_file() else {}
    before_bytes = target_db.read_bytes() if target_db.is_file() else None

    svc = service or DataSourceService()
    previews: list[dict[str, Any]] = []
    for index, request in enumerate(requests, start=1):
        preview = preview_live_pilot(
            request,
            service=svc,
            pilot_request_id=f"pilot-req-{index}",
        )
        previews.append(preview)

    after_counts = _key_table_row_counts(target_db) if target_db.is_file() else {}
    after_bytes = target_db.read_bytes() if target_db.is_file() else None

    generated_at = _utc_now_iso()
    payload: dict[str, Any] = {
        "generated_at": generated_at,
        "phase": "phase2_route_preview",
        "dry_run": True,
        "authorization_evidence": requests[0].authorization_evidence if requests else None,
        "fred_primary_deferred": True,
        "fred_primary_deferred_note": FRED_PRIMARY_DEFERRED_NOTE,
        "previews": previews,
        "mutation_proof": {
            "generated_at": generated_at,
            "db_path": str(target_db),
            "db_file_hash_unchanged": before_bytes == after_bytes,
            "before_key_table_counts": before_counts,
            "after_key_table_counts": after_counts,
            "row_counts_unchanged": before_counts == after_counts,
            "phase2_zero_mutation": before_counts == after_counts and before_bytes == after_bytes,
        },
    }

    (evidence_dir / PHASE2_ROUTE_MATRIX_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def capture_task_phase2_route_evidence(
    evidence_dir: Path | str,
    *,
    db_path: Path | None = None,
) -> dict[str, Any]:
    """Execute helper: persist Phase 2 matrix for three authorized requests."""
    return capture_phase2_route_matrix(
        requests=approved_pilot_requests(),
        evidence_dir=Path(evidence_dir),
        db_path=db_path or DEFAULT_PRODUCTION_DB,
    )


def _resolve_hitl_path(evidence_dir: Path | None = None) -> Path:
    if evidence_dir is not None:
        return Path(evidence_dir) / HITL_CONFIRMATION_MD
    return (
        PROJECT_ROOT
        / ".trellis/tasks/06-21-round3-batch2-75-live-pilot/execute-evidence"
        / HITL_CONFIRMATION_MD
    )


def require_hitl_confirmation(*, evidence_dir: Path | None = None) -> Path:
    """Phase 3 HITL gate — user confirmation file must exist before network fetch."""
    hitl_path = _resolve_hitl_path(evidence_dir)
    if not hitl_path.is_file():
        raise LivePilotAuthorizationError(
            f"HITL confirmation required: {HITL_CONFIRMATION_MD} missing"
        )
    text = hitl_path.read_text(encoding="utf-8")
    if "User confirmation" not in text and "用户" not in text:
        raise LivePilotAuthorizationError("HITL file missing user confirmation marker")
    return hitl_path
