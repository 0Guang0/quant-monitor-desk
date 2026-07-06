"""Source route and DB acceptance spine contract models."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any, Literal

from backend.app.config import DATA_ROOT, PROJECT_ROOT
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations

ImplementationMode = Literal["live", "mock", "replay", "dry_run", "not_implemented"]
RouteGrade = Literal["primary", "degraded", "blocked", "not_planned"]
WriteGrade = Literal["primary_grade_clean", "degraded_clean", "blocked", "not_written"]
FailureClass = Literal["NONE", "BLOCKED", "FAIL_EXTERNAL", "NOT_IMPLEMENTED", "CONTRACT_VIOLATION"]
ACCEPTANCE_DUCKDB_NAME = "quant_monitor.duckdb"

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


def acceptance_report_json(report: AcceptanceReport) -> str:
    return json.dumps(report.to_dict(), indent=2)


def write_acceptance_report(report: AcceptanceReport, path: Path) -> str:
    output = acceptance_report_json(report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(output, encoding="utf-8")
    return output


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

    @classmethod
    def contract_violation(cls, request: AcceptanceRequest, error: str) -> AcceptanceReport:
        return cls(
            source_id=request.source_id,
            data_domain=request.data_domain,
            operation=request.operation,
            route_plan_id=None,
            route_grade="blocked",
            implementation_mode="not_implemented",
            write_grade="blocked",
            source_used=None,
            source_role=None,
            source_switched=False,
            failure_class="CONTRACT_VIOLATION",
            status="FAIL",
            errors=(error,),
        )

    @classmethod
    def from_route_payload(
        cls,
        request: AcceptanceRequest,
        route_payload: dict[str, Any],
    ) -> AcceptanceReport:
        route_grade = _route_grade_from_payload(route_payload)
        source_used = _optional_str(route_payload.get("selected_source_id"))
        quality_flags = tuple(str(flag) for flag in route_payload.get("quality_flags") or ())
        return cls(
            source_id=request.source_id,
            data_domain=request.data_domain,
            operation=request.operation,
            route_plan_id=_optional_str(route_payload.get("route_plan_id")),
            route_grade=route_grade,
            implementation_mode="not_implemented",
            write_grade="not_written" if route_grade != "blocked" else "blocked",
            source_used=source_used,
            source_role=_source_role_from_payload(route_payload, source_used),
            source_switched=_source_switched(route_payload, source_used, route_grade),
            quality_flags=quality_flags,
            failure_class="BLOCKED" if route_grade == "blocked" else "NOT_IMPLEMENTED",
            status="FAIL",
            errors=("Route evidence normalized; downstream acceptance is not implemented yet",),
        )

    @classmethod
    def blocked_from_route_payload(
        cls,
        request: AcceptanceRequest,
        route_payload: dict[str, Any],
        error: str,
    ) -> AcceptanceReport:
        report = cls.from_route_payload(request, route_payload)
        return replace(
            report,
            write_grade="blocked",
            failure_class="BLOCKED",
            status="FAIL",
            errors=(error,),
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
        _ = live_authorized
        resolved_root = Path(data_root).expanduser().resolve()
        if _is_canonical_main_data_root(resolved_root):
            return AcceptanceReport.contract_violation(
                request,
                f"canonical main data root rejected for acceptance: {resolved_root}",
            )
        _bootstrap_acceptance_db(resolved_root)
        if _is_fred_macro_series_request(request):
            route_payload = _fred_macro_route_payload(request)
            if not live_authorized:
                return AcceptanceReport.blocked_from_route_payload(
                    request,
                    route_payload,
                    "live authorization missing for macro_series:fred:fetch_macro_series",
                )
            if not _fred_live_credentials_available():
                return AcceptanceReport.blocked_from_route_payload(
                    request,
                    route_payload,
                    "FRED_API_KEY missing for macro_series:fred:fetch_macro_series",
                )
            return AcceptanceReport.from_route_payload(request, route_payload)
        return AcceptanceReport.not_implemented(request)


def _acceptance_db_path(data_root: Path) -> Path:
    return data_root / "duckdb" / ACCEPTANCE_DUCKDB_NAME


def _bootstrap_acceptance_db(data_root: Path) -> ConnectionManager:
    db_path = _acceptance_db_path(data_root)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    cm = ConnectionManager(db_path=db_path)
    with cm.writer() as con:
        apply_migrations(con)
    return cm


def _is_fred_macro_series_request(request: AcceptanceRequest) -> bool:
    return (
        request.data_domain == "macro_series"
        and request.source_id == "fred"
        and request.operation == "fetch_macro_series"
    )


def _fred_macro_route_payload(request: AcceptanceRequest) -> dict[str, Any]:
    from backend.app.ops.fred_incremental_run import build_fred_incremental_preview_service

    plan = build_fred_incremental_preview_service().preview_route(
        data_domain=request.data_domain,
        operation=request.operation,
        market_id=request.market_id,
        run_id="acceptance-preview",
        job_id="acceptance-preview",
    )
    return plan.to_payload_dict()


def _fred_live_credentials_available() -> bool:
    return bool(os.environ.get("FRED_API_KEY"))


def _is_canonical_main_data_root(data_root: Path) -> bool:
    canonical_roots = {Path(PROJECT_ROOT / "data").resolve(), Path(DATA_ROOT).resolve()}
    if data_root in canonical_roots:
        return True
    canonical_db_paths = {root / "duckdb" / "quant_monitor.duckdb" for root in canonical_roots}
    return data_root / "duckdb" / "quant_monitor.duckdb" in canonical_db_paths


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _route_grade_from_payload(route_payload: dict[str, Any]) -> RouteGrade:
    explicit = _optional_str(route_payload.get("route_grade"))
    if explicit in {"primary", "degraded", "blocked"}:
        return explicit  # type: ignore[return-value]
    route_status = _optional_str(route_payload.get("route_status"))
    quality_flags = set(str(flag) for flag in route_payload.get("quality_flags") or ())
    if route_status != "READY":
        return "blocked"
    if quality_flags & {"SOURCE_FALLBACK_USED", "VALIDATION_SOURCE_USED"}:
        return "degraded"
    return "primary"


def _source_role_from_payload(route_payload: dict[str, Any], source_used: str | None) -> str | None:
    if source_used is None:
        return None
    for candidate in route_payload.get("candidates") or ():
        if not isinstance(candidate, dict) or candidate.get("source_id") != source_used:
            continue
        role = _optional_str(candidate.get("role"))
        if role == "FallbackPolicy":
            return "fallback"
        return role.lower() if role else None
    return None


def _source_switched(
    route_payload: dict[str, Any],
    source_used: str | None,
    route_grade: RouteGrade,
) -> bool:
    requested = _optional_str(route_payload.get("requested_source_id"))
    return route_grade == "degraded" or bool(requested and source_used and requested != source_used)
