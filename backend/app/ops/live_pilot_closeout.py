"""Live pilot — closeout (split from live_pilot.py, OP-01)."""

from __future__ import annotations

from typing import Any

from backend.app.ops.live_pilot_types import LivePilotOutcome

def derive_pilot_closeout_outcome(phase4_payload: dict[str, Any]) -> LivePilotOutcome:
    """Map per-request validation to a single PILOT_* closeout state."""
    statuses = {
        item["pilot_request_id"]: item.get("status")
        for item in phase4_payload.get("validations", [])
    }
    req2 = next(
        (
            item
            for item in phase4_payload.get("validations", [])
            if item.get("pilot_request_id") == "pilot-req-2"
        ),
        {},
    )
    original_req2_failed = req2.get("status") == "SOURCE_ENDPOINT_FAILURE"
    req1_ok = statuses.get("pilot-req-1") == "PASSED"
    req3_ok = statuses.get("pilot-req-3") == "PASSED"
    if original_req2_failed:
        return LivePilotOutcome.PILOT_FAIL_SOURCE
    if not req1_ok or not req3_ok:
        validation_failed = any(status == "FAILED" for status in statuses.values())
        return (
            LivePilotOutcome.PILOT_FAIL_VALIDATION
            if validation_failed
            else LivePilotOutcome.PILOT_FAIL_SOURCE
        )
    if phase4_payload.get("allow_clean_write"):
        return LivePilotOutcome.PILOT_PASS_SANDBOX_CLEAN
    return LivePilotOutcome.PILOT_PASS_RAW_ONLY
