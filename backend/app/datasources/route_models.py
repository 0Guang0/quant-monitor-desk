"""SourceRoutePlan models (Round2.6 Phase C)."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class SourceRouteCandidate:
    source_id: str
    role: str
    enabled: bool
    allowed_domain: str
    capability_declared: bool
    disabled_reason: str | None = None
    skip_reason: str | None = None


@dataclass
class SourceRoutePlan:
    route_plan_id: str
    run_id: str
    job_id: str
    data_domain: str
    operation: str
    route_status: str
    selected_source_id: str | None
    route_grade: str | None = None
    candidates: list[SourceRouteCandidate] = field(default_factory=list)
    quality_flags: list[str] = field(default_factory=list)
    requested_source_id: str | None = None
    # ADR-018 / task-02: activation_overlay_revision 可观察字段（附加，不改义既有字段）
    overlay_revision: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def __post_init__(self) -> None:
        if self.route_grade is None:
            self.route_grade = infer_route_grade(self.route_status, self.quality_flags)

    @classmethod
    def new_id(cls) -> str:
        return str(uuid.uuid4())

    def to_payload_dict(self) -> dict[str, Any]:
        return {
            "route_plan_id": self.route_plan_id,
            "run_id": self.run_id,
            "job_id": self.job_id,
            "route_status": self.route_status,
            "route_grade": self.route_grade,
            "selected_source_id": self.selected_source_id,
            "requested_source_id": self.requested_source_id,
            "data_domain": self.data_domain,
            "operation": self.operation,
            "quality_flags": list(self.quality_flags),
            "candidates": [asdict(c) for c in self.candidates],
            "overlay_revision": self.overlay_revision,
            "created_at": self.created_at,
        }


def infer_route_grade(route_status: str, quality_flags: list[str]) -> str:
    if route_status != "READY":
        return "blocked"
    if "SOURCE_FALLBACK_USED" in quality_flags or "VALIDATION_SOURCE_USED" in quality_flags:
        return "degraded"
    return "primary"
