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
    candidates: list[SourceRouteCandidate] = field(default_factory=list)
    quality_flags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    @classmethod
    def new_id(cls) -> str:
        return str(uuid.uuid4())

    def to_payload_dict(self) -> dict[str, Any]:
        return {
            "route_plan_id": self.route_plan_id,
            "run_id": self.run_id,
            "job_id": self.job_id,
            "route_status": self.route_status,
            "selected_source_id": self.selected_source_id,
            "data_domain": self.data_domain,
            "operation": self.operation,
            "quality_flags": list(self.quality_flags),
            "candidates": [asdict(c) for c in self.candidates],
            "created_at": self.created_at,
        }
