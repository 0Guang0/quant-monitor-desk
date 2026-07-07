"""Bridge tier A/B/C live harness to source-route matrix spine (TD-17)."""

from __future__ import annotations

from pathlib import Path

from backend.app.ops.source_route_db_acceptance import SourceRouteDbAcceptanceSpine
from backend.app.ops.source_route_db_acceptance_matrix import (
    iter_matrix_targets,
    matrix_target_key,
)


def matrix_target_for_source(source_id: str):
    for target in iter_matrix_targets():
        if target.request.source_id == source_id:
            return target
    return None


def run_matrix_spine_for_source(
    source_id: str,
    *,
    data_root: Path,
    live_authorized: bool = True,
) -> dict[str, object] | None:
    """Run documented matrix spine row when source_id is in DOCUMENTED_SOURCE_MATRIX."""
    target = matrix_target_for_source(source_id)
    if target is None:
        return None
    spine = SourceRouteDbAcceptanceSpine()
    report = spine.execute(
        target.request,
        data_root=data_root,
        live_authorized=live_authorized,
        persist_route_evidence=live_authorized,
    )
    return {
        "target": matrix_target_key(target),
        "source_id": source_id,
        "status": report.status,
        "failure_class": report.failure_class,
        "implementation_mode": report.implementation_mode,
        "errors": list(report.errors),
    }


def try_delegate_tier_acceptance(
    source_id: str,
    *,
    data_root: Path,
) -> tuple[bool, str, str | None]:
    """Return (delegated, status, detail) when tier runner should use matrix spine."""
    target = matrix_target_for_source(source_id)
    if target is None:
        return False, "skip", None
    outcome = run_matrix_spine_for_source(source_id, data_root=data_root, live_authorized=True)
    if outcome is None:
        return False, "skip", None
    status = "pass" if outcome["status"] == "PASS" and outcome["failure_class"] == "NONE" else "fail"
    detail = "; ".join(outcome.get("errors") or []) or str(outcome["failure_class"])
    return True, status, detail
