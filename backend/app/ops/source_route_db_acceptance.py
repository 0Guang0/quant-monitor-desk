"""Source route and DB acceptance spine contract models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

ImplementationMode = Literal["live", "mock", "replay", "dry_run", "not_implemented"]
RouteGrade = Literal["primary", "degraded", "blocked", "not_planned"]
WriteGrade = Literal["primary_grade_clean", "degraded_clean", "blocked", "not_written"]
FailureClass = Literal["NONE", "BLOCKED", "FAIL_EXTERNAL", "NOT_IMPLEMENTED", "CONTRACT_VIOLATION"]

REQUIRED_ACCEPTANCE_REPORT_FIELDS: tuple[str, ...] = (
    "source_id",
    "data_domain",
    "operation",
    "route_plan_id",
    "route_grade",
    "implementation_mode",
    "write_grade",
    "source_used",
    "source_role",
    "source_switched",
    "quality_flags",
    "stale_reason",
    "fallback_reason",
    "schema_hash",
    "content_hash",
    "validation_status",
    "conflict_status",
    "failure_class",
    "downstream_layer_read_status",
    "status",
    "errors",
)


@dataclass(frozen=True, kw_only=True)
class AcceptanceRequest:
    data_domain: str
    source_id: str
    operation: str
    market_id: str | None = None
    start: str | None = None
    end: str | None = None

    @classmethod
    def from_target(cls, target: str) -> AcceptanceRequest:
        parts = [part.strip() for part in target.split(":")]
        if len(parts) != 3 or any(not part for part in parts):
            raise ValueError("target must be data_domain:source_id:operation")
        return cls(data_domain=parts[0], source_id=parts[1], operation=parts[2])

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, kw_only=True)
class AcceptancePreview:
    request: AcceptanceRequest
    route_grade: RouteGrade
    implementation_mode: ImplementationMode
    status: str
    reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, kw_only=True)
class AcceptanceReport:
    source_id: str
    data_domain: str
    operation: str
    route_plan_id: str | None
    route_grade: RouteGrade
    implementation_mode: ImplementationMode
    write_grade: WriteGrade
    source_used: str | None
    source_role: str | None
    source_switched: bool
    quality_flags: tuple[str, ...] = field(default_factory=tuple)
    stale_reason: str | None = None
    fallback_reason: str | None = None
    schema_hash: str | None = None
    content_hash: str | None = None
    validation_status: str = "NOT_RUN"
    conflict_status: str = "NOT_RUN"
    failure_class: FailureClass = "NOT_IMPLEMENTED"
    downstream_layer_read_status: str = "NOT_RUN"
    status: str = "FAIL"
    errors: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def not_implemented(cls, request: AcceptanceRequest) -> AcceptanceReport:
        return cls(
            source_id=request.source_id,
            data_domain=request.data_domain,
            operation=request.operation,
            route_plan_id=None,
            route_grade="not_planned",
            implementation_mode="not_implemented",
            write_grade="not_written",
            source_used=None,
            source_role=None,
            source_switched=False,
            failure_class="NOT_IMPLEMENTED",
            status="FAIL",
            errors=("SourceRouteDbAcceptanceSpine execution is not implemented yet",),
        )

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["quality_flags"] = list(self.quality_flags)
        payload["errors"] = list(self.errors)
        return payload


class SourceRouteDbAcceptanceSpine:
    """Deep Module seam for production-equivalent source-route DB acceptance."""

    def preview(self, request: AcceptanceRequest) -> AcceptancePreview:
        return AcceptancePreview(
            request=request,
            route_grade="not_planned",
            implementation_mode="not_implemented",
            status="FAIL",
            reason="SourceRouteDbAcceptanceSpine preview is not implemented yet",
        )

    def execute(
        self,
        request: AcceptanceRequest,
        *,
        data_root,
        live_authorized: bool,
    ) -> AcceptanceReport:
        _ = (data_root, live_authorized)
        return AcceptanceReport.not_implemented(request)
