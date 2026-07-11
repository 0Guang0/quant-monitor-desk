"""CLI failure envelope aligned with docs/ops/design/ERROR_CODE_GUIDE.md."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

# User-visible failure doc anchors — SSOT under **/design/** or retained ADR only.
# ponytail: staging docs/ops/*.md (non-design) are not authoritative anchors.
DOCS_ANCHOR_ERROR_CODE_GUIDE = "docs/ops/design/ERROR_CODE_GUIDE.md"
DOCS_ANCHOR_INCIDENT_PLAYBOOK = "docs/ops/design/incident_playbook.md"
DOCS_ANCHOR_RESOURCE_GUARD_PAUSED = f"{DOCS_ANCHOR_INCIDENT_PLAYBOOK}#inc-002-resource_guard_paused"
DOCS_ANCHOR_INCIDENT_DISABLED_SOURCE = f"{DOCS_ANCHOR_INCIDENT_PLAYBOOK}#inc-001-disabled_source"
DOCS_ANCHOR_INCIDENT_USER_AUTH = f"{DOCS_ANCHOR_INCIDENT_PLAYBOOK}#inc-004-user_auth_required"
DOCS_ANCHOR_DATA_SYNC_CLI = "docs/modules/design/data_sync_orchestrator.md#137-cli-设计"
DOCS_ANCHOR_DATA_VALIDATION = "docs/modules/design/data_validation_and_conflict.md"
DOCS_ANCHOR_BACKFILL_CAP = "docs/decisions/ADR-011-bounded-backfill-cap-and-ci-nightly.md"
DOCS_ANCHOR_LIVE_ENV_GATE = "docs/decisions/ADR-015-live-acceptance-sandbox-dual-track.md"
DOCS_ANCHOR_ORCHESTRATOR = "docs/modules/design/data_sync_orchestrator.md"
DOCS_ANCHOR_ORCHESTRATOR_FULL_LOAD = f"{DOCS_ANCHOR_ORCHESTRATOR}#1341-fullloadjob"
DOCS_ANCHOR_ORCHESTRATOR_SCHEDULER = f"{DOCS_ANCHOR_ORCHESTRATOR}#136-调度计划"
DOCS_ANCHOR_ORCHESTRATOR_CLI = f"{DOCS_ANCHOR_ORCHESTRATOR}#137-cli-设计"
DOCS_ANCHOR_LAYER1_INDICATOR_BINDING = "docs/modules/design/layer1_global_regime_panel.md"

# Back-compat alias (same design anchor; quick_reference.md is staging only).
DOCS_ANCHOR_DATA_SYNC_QUICK_REF = DOCS_ANCHOR_DATA_SYNC_CLI
DOCS_ANCHOR_DATA_HEALTH_CLI = DOCS_ANCHOR_DATA_VALIDATION


@dataclass(frozen=True)
class CliFailure(RuntimeError):
    error_code: str
    message: str
    docs_anchor: str
    retryable: bool = False
    manual_confirmation_required: bool = False

    def __str__(self) -> str:
        return self.message

    def exit_code(self) -> int:
        return 2

    def format_text(self) -> str:
        return (
            f"error_code={self.error_code}\n"
            f"message={self.message}\n"
            f"docs_anchor={self.docs_anchor}\n"
            f"retryable={str(self.retryable).lower()}\n"
            f"manual_confirmation_required={str(self.manual_confirmation_required).lower()}\n"
        )

    def format_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


_ROUTE_STATUS_TO_ERROR: dict[str, str] = {
    "DISABLED_SOURCE": "DISABLED_SOURCE",
    "NO_AVAILABLE_SOURCE": "NO_AVAILABLE_SOURCE",
    "CAPABILITY_MISSING": "CAPABILITY_MISSING",
    "USER_AUTH_REQUIRED": "USER_AUTH_REQUIRED",
    "VALIDATION_ONLY_BLOCKED": "DISABLED_SOURCE",
}


def error_for_route_status(route_status: str, *, detail: str) -> CliFailure:
    code = _ROUTE_STATUS_TO_ERROR.get(route_status, "NO_AVAILABLE_SOURCE")
    anchor = {
        "DISABLED_SOURCE": DOCS_ANCHOR_INCIDENT_DISABLED_SOURCE,
        "CAPABILITY_MISSING": DOCS_ANCHOR_ERROR_CODE_GUIDE,
        "USER_AUTH_REQUIRED": DOCS_ANCHOR_INCIDENT_USER_AUTH,
    }.get(code, DOCS_ANCHOR_ERROR_CODE_GUIDE)
    return CliFailure(
        error_code=code,
        message=detail,
        docs_anchor=anchor,
        manual_confirmation_required=code in {"DISABLED_SOURCE", "USER_AUTH_REQUIRED"},
    )


def raise_if_ready_selected_mismatch(
    *,
    route_status: str,
    selected_source_id: str | None,
    requested_source_id: str,
    job_kind: str,
) -> None:
    """READY 时 selected 必须等于 CLI 请求源（禁止用请求 id 粉饰选源）。"""
    if route_status != "READY":
        return
    if selected_source_id == requested_source_id:
        return
    raise CliFailure(
        error_code="INVALID_INPUT",
        message=(
            f"{job_kind} selected {selected_source_id!r} "
            f"but requested {requested_source_id!r}"
        ),
        docs_anchor=DOCS_ANCHOR_DATA_SYNC_CLI,
    )
