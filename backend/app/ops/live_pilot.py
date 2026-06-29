"""Batch 2.75 controlled live pilot orchestration (fail-closed, sandbox-first).

``REHEARSAL_ONLY`` — not R3H-08 product live SSOT; see ``backend.app.ops.rehearsal_boundary``.
"""

from __future__ import annotations

from backend.app.ops.live_pilot_auth import (
    assert_pilot_ready_before_fetch,
    approved_pilot_requests,
    validate_authorization,
)
from backend.app.ops.live_pilot_phase2 import require_hitl_confirmation
from backend.app.ops.live_pilot_closeout import derive_pilot_closeout_outcome
from backend.app.ops.live_pilot_constants import *  # noqa: F403
from backend.app.ops.live_pilot_phase1 import (
    build_phase1_capability_snapshot,
    capture_phase1_baseline,
    capture_task_phase1_baseline_evidence,
)
from backend.app.ops.live_pilot_phase2 import (
    capture_phase2_route_matrix,
    capture_task_phase2_route_evidence,
    preview_live_pilot,
)
from backend.app.ops.live_pilot_phase3 import (
    _assert_live_fetch_port,
    capture_phase3_raw_evidence,
    capture_task_phase3_raw_evidence,
    run_live_pilot_raw_only,
)
from backend.app.ops.live_pilot_phase4 import (
    capture_phase4_validation,
    capture_task_phase4_validation_evidence,
)
from backend.app.ops.live_pilot_types import (
    LivePilotAuthorizationError,
    LivePilotDisabledSourceError,
    LivePilotFixtureForbiddenError,
    LivePilotOutcome,
    LivePilotRequest,
    LivePilotRouteNotReadyError,
)

__all__ = [
    "APPROVED_PILOT_REQUESTS",
    "APPROVED_PILOT_REQUEST_ENVELOPES",
    "DEFAULT_AUTHORIZATION_PATH",
    "DEFAULT_PRODUCTION_DB",
    "DEFAULT_SANDBOX_ROOT",
    "DISABLED_PILOT_SOURCE_IDS",
    "EASTMONEY_VERDICT_MD",
    "FRED_PRIMARY_DEFERRED_NOTE",
    "HITL_CONFIRMATION_MD",
    "LivePilotAuthorizationError",
    "LivePilotDisabledSourceError",
    "LivePilotFixtureForbiddenError",
    "LivePilotOutcome",
    "LivePilotRequest",
    "LivePilotRouteNotReadyError",
    "MAX_PILOT_ROW_CAP",
    "ORIGINAL_REQUEST2_ENDPOINT_HOST",
    "ORIGINAL_REQUEST2_VENDOR_API",
    "PHASE1_BASELINE_JSON",
    "PHASE1_BASELINE_MD",
    "PHASE1_CAPABILITY_JSON",
    "PHASE1_NO_MUTATION_MD",
    "PHASE2_ROUTE_MATRIX_JSON",
    "PHASE3_NO_PRODUCTION_MUTATION_MD",
    "PHASE3_RAW_EVIDENCE_JSON",
    "PHASE3_REQUEST2_RECONCILIATION_MD",
    "PHASE45_PERF_BUDGET_JSON",
    "PHASE4_CONFLICT_INSPECT_TXT",
    "PHASE4_NO_PRODUCTION_MUTATION_MD",
    "PHASE4_VALIDATION_REPORT_JSON",
    "SIDECAR_REQUEST2_ENDPOINT_HOST",
    "SIDECAR_REQUEST2_VENDOR_API",
    "approved_pilot_requests",
    "assert_pilot_ready_before_fetch",
    "build_phase1_capability_snapshot",
    "capture_phase1_baseline",
    "capture_phase2_route_matrix",
    "capture_phase3_raw_evidence",
    "capture_phase4_validation",
    "capture_task_phase1_baseline_evidence",
    "capture_task_phase2_route_evidence",
    "capture_task_phase3_raw_evidence",
    "capture_task_phase4_validation_evidence",
    "derive_pilot_closeout_outcome",
    "preview_live_pilot",
    "require_hitl_confirmation",
    "run_live_pilot_raw_only",
    "validate_authorization",
    "_assert_live_fetch_port",
]
