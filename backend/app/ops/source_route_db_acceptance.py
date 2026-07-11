"""Source route and DB acceptance spine contract models."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any, Literal

from backend.app.db.connection import ConnectionManager
from backend.app.db.sql_identifiers import quote_ident
from backend.app.ops.acceptance_isolation import AcceptanceIsolationError

ImplementationMode = Literal["live", "mock", "replay", "dry_run", "not_implemented"]
RouteGrade = Literal["primary", "degraded", "blocked", "not_planned"]
WriteGrade = Literal["primary_grade_clean", "degraded_clean", "blocked", "not_written"]
FailureClass = Literal["NONE", "BLOCKED", "FAIL_EXTERNAL", "NOT_IMPLEMENTED", "CONTRACT_VIOLATION"]
ACCEPTANCE_DUCKDB_NAME = "quant_monitor.duckdb"
FRED_ACCEPTANCE_SERIES_ID = "DGS10"
FRED_ACCEPTANCE_SPEC_INDICATOR_ID = "ENV-E1-DGS10"

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
    missing_prerequisites: tuple[str, ...] = ()
    live_ready: bool = True

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["missing_prerequisites"] = list(self.missing_prerequisites)
        return payload


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
            implementation_mode="live",
            write_grade="blocked",
            failure_class="BLOCKED",
            status="FAIL",
            errors=(error,),
        )

    @classmethod
    def qualified_non_primary_from_route_payload(
        cls,
        request: AcceptanceRequest,
        route_payload: dict[str, Any],
        *,
        positioning: str,
        expected_write_grade: str,
        downstream_expectation: str,
    ) -> AcceptanceReport:
        report = cls.from_route_payload(request, route_payload)
        validation_status = {
            "validation": "VALIDATION_POSITION_CONFIRMED",
            "manual_review_only": "MANUAL_REVIEW_POSITION_CONFIRMED",
            "licensed_validation": "LICENSED_VALIDATION_POSITION_CONFIRMED",
        }.get(positioning, "NON_PRIMARY_POSITION_CONFIRMED")
        write_grade: WriteGrade = (
            expected_write_grade
            if expected_write_grade in {"primary_grade_clean", "degraded_clean", "blocked", "not_written"}
            else "blocked"
        )
        return replace(
            report,
            implementation_mode="live",
            write_grade=write_grade,
            failure_class="NONE",
            status="PASS",
            validation_status=validation_status,
            conflict_status="NOT_APPLICABLE",
            downstream_layer_read_status=downstream_expectation,
            errors=(),
        )

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["quality_flags"] = list(self.quality_flags)
        payload["errors"] = list(self.errors)
        return payload


class SourceRouteDbAcceptanceSpine:
    """Deep Module seam for production-equivalent source-route DB acceptance."""

    def preview(self, request: AcceptanceRequest) -> AcceptancePreview:
        from backend.app.ops.source_route_db_acceptance_matrix import (
            build_matrix_preview,
            find_matrix_target,
            preview_route_payload,
        )

        matrix_target = find_matrix_target(request)
        if matrix_target is not None:
            route_payload = preview_route_payload(request)
            return build_matrix_preview(request, matrix_target, route_payload)
        return AcceptancePreview(
            request=request,
            route_grade="not_planned",
            implementation_mode="not_implemented",
            status="FAIL",
            reason="SourceRouteDbAcceptanceSpine preview is not implemented yet",
            missing_prerequisites=(),
            live_ready=False,
        )

    def execute(
        self,
        request: AcceptanceRequest,
        *,
        data_root,
        live_authorized: bool,
        cm: ConnectionManager | None = None,
        persist_route_evidence: bool = True,
        skip_data_root_validation: bool = False,
    ) -> AcceptanceReport:
        from backend.app.ops.source_route_db_acceptance_matrix import (
            find_matrix_target,
            resolve_matrix_data_root,
        )

        try:
            if skip_data_root_validation:
                resolved_root = Path(data_root).expanduser().resolve()
            else:
                resolved_root = resolve_matrix_data_root(data_root)
        except AcceptanceIsolationError as exc:
            return AcceptanceReport.contract_violation(request, str(exc))
        connection = cm if cm is not None else _bootstrap_acceptance_db(resolved_root)
        matrix_target = find_matrix_target(request)
        if matrix_target is not None:
            return _execute_matrix_target(
                request,
                matrix_target,
                connection,
                resolved_root,
                live_authorized=live_authorized,
                persist_route_evidence=persist_route_evidence,
            )
        return AcceptanceReport.not_implemented(request)


def _acceptance_db_path(data_root: Path) -> Path:
    return data_root / "duckdb" / ACCEPTANCE_DUCKDB_NAME


def _bootstrap_acceptance_db(data_root: Path) -> ConnectionManager:
    from backend.app.ops.acceptance_isolation import ensure_isolated_db

    db_path = ensure_isolated_db(data_root)
    return ConnectionManager(db_path=db_path)


def _persist_route_evidence(cm: ConnectionManager, route_payload: dict[str, Any]) -> None:
    from backend.app.sync.event_payload import build_event_payload

    payload = build_event_payload(**route_payload, decision="route_plan")
    route_status = _optional_str(route_payload.get("route_status")) or "UNKNOWN"
    with cm.writer() as con:
        con.execute(
            """
            INSERT INTO job_event_log (
                event_id, run_id, job_id, event_type, message, payload_json, created_at
            ) VALUES (uuid(), ?, ?, 'ROUTE_PLAN', ?, ?, CURRENT_TIMESTAMP)
            """,
            [
                _optional_str(route_payload.get("run_id")),
                _optional_str(route_payload.get("job_id")),
                f"route_status={route_status}",
                payload,
            ],
        )


def _execute_matrix_target(
    request: AcceptanceRequest,
    matrix_target,
    cm: ConnectionManager,
    data_root: Path,
    *,
    live_authorized: bool,
    persist_route_evidence: bool = True,
) -> AcceptanceReport:
    from backend.app.datasources.product_live_gate import (
        ProductLiveGateError,
        is_product_live_fetch_allowed,
    )
    from backend.app.ops.source_route_db_acceptance_matrix import (
        QUALIFICATION_DEFERRED_SOURCE_IDS,
        is_non_primary_positioning,
        matrix_target_key,
        missing_gate_errors,
        preview_route_payload,
        validate_qualification_credentials,
    )

    route_payload = preview_route_payload(request)
    if persist_route_evidence:
        _persist_route_evidence(cm, route_payload)
    target_key = matrix_target_key(matrix_target)
    gate_errors = missing_gate_errors(matrix_target)
    if not live_authorized:
        blocked_errors: list[str] = [f"live authorization missing for {target_key}"]
        if gate_errors:
            blocked_errors.extend(f"diagnostic:{item}" for item in gate_errors)
        report = AcceptanceReport.blocked_from_route_payload(
            request,
            route_payload,
            "; ".join(blocked_errors),
        )
        return replace(report, implementation_mode="dry_run")
    if gate_errors:
        return AcceptanceReport.blocked_from_route_payload(
            request,
            route_payload,
            "; ".join(gate_errors),
        )
    qualification_errors = validate_qualification_credentials(matrix_target)
    if qualification_errors:
        return AcceptanceReport.blocked_from_route_payload(
            request,
            route_payload,
            "; ".join(qualification_errors),
        )
    if is_non_primary_positioning(matrix_target):
        if matrix_target.request.source_id in QUALIFICATION_DEFERRED_SOURCE_IDS:
            pass
        elif matrix_target.positioning == "validation":
            from backend.app.ops.matrix_live_handlers import execute_validation_matrix_probe

            return execute_validation_matrix_probe(
                request,
                matrix_target,
                cm,
                data_root,
                route_payload,
            )
        else:
            return AcceptanceReport.qualified_non_primary_from_route_payload(
                request,
                route_payload,
                positioning=matrix_target.positioning,
                expected_write_grade=matrix_target.expected_write_grade,
                downstream_expectation=matrix_target.downstream_expectation,
            )
    if not is_product_live_fetch_allowed():
        return AcceptanceReport.blocked_from_route_payload(
            request,
            route_payload,
            "QMD_ALLOW_LIVE_FETCH missing for live matrix acceptance",
        )
    try:
        return _execute_primary_matrix_live(
            request,
            matrix_target,
            cm,
            data_root,
            route_payload,
        )
    except ProductLiveGateError as exc:
        return AcceptanceReport.blocked_from_route_payload(request, route_payload, str(exc))


def _execute_primary_matrix_live(
    request: AcceptanceRequest,
    matrix_target,
    cm: ConnectionManager,
    data_root: Path,
    route_payload: dict[str, Any],
) -> AcceptanceReport:
    from backend.app.ops.matrix_live_handlers import execute_primary_matrix_live

    return execute_primary_matrix_live(
        request,
        matrix_target,
        cm,
        data_root,
        route_payload,
    )


def _matrix_incremental_live_report(
    request: AcceptanceRequest,
    route_payload: dict[str, Any],
    cm: ConnectionManager,
    *,
    matrix_target,
    sync_status: str,
    rows_written: int,
    job_id: str | None,
) -> AcceptanceReport:
    route_report = AcceptanceReport.from_route_payload(request, route_payload)
    validation_status, conflict_status = _acceptance_job_statuses(cm, job_id)
    downstream = (
        matrix_target.downstream_expectation
        if rows_written > 0
        else "NO_CLEAN_ROWS"
    )
    pass_status = (
        route_report.route_plan_id is not None
        and sync_status in {"COMPLETED", "PASS", "EMPTY_RESPONSE"}
        and rows_written > 0
    )
    errors: tuple[str, ...] = ()
    if not pass_status:
        errors = (
            f"live acceptance incomplete: sync_status={sync_status}; rows_written={rows_written}",
        )
    return replace(
        route_report,
        implementation_mode="live",
        write_grade=matrix_target.expected_write_grade if rows_written > 0 else "not_written",
        validation_status=validation_status,
        conflict_status=conflict_status,
        failure_class="NONE" if pass_status else "FAIL_EXTERNAL",
        downstream_layer_read_status=downstream,
        status="PASS" if pass_status else "FAIL",
        errors=errors,
    )


def _matrix_evidence_fetch_live_report(
    request: AcceptanceRequest,
    route_payload: dict[str, Any],
    cm: ConnectionManager,
    *,
    matrix_target,
    sync_status: str,
    data_root: Path,
) -> AcceptanceReport:
    route_report = AcceptanceReport.from_route_payload(request, route_payload)
    validation_status, conflict_status = _acceptance_job_statuses(cm, None)
    raw_source = data_root / "raw" / request.source_id
    raw_exists = raw_source.is_dir() and any(raw_source.rglob("*"))
    pass_status = route_report.route_plan_id is not None and sync_status in {
        "COMPLETED",
        "PASS",
        "SUCCESS",
        "OK",
    } and raw_exists
    downstream = matrix_target.downstream_expectation if pass_status else "NO_EVIDENCE"
    errors: tuple[str, ...] = ()
    if not pass_status:
        detail = f"sync_status={sync_status}; raw_exists={raw_exists}"
        errors = (f"evidence fetch incomplete: {detail}",)
    return replace(
        route_report,
        implementation_mode="live",
        write_grade="not_written",
        validation_status=validation_status,
        conflict_status=conflict_status,
        failure_class="NONE" if pass_status else "FAIL_EXTERNAL",
        downstream_layer_read_status=downstream,
        status="PASS" if pass_status else "FAIL",
        errors=errors,
    )


def _count_clean_rows(
    cm: ConnectionManager,
    data_domain: str,
    *,
    source_id: str | None = None,
) -> int:
    from backend.app.ops.sandbox_clean_write.clean_write_targets import resolve_clean_write_target

    target = resolve_clean_write_target(data_domain)
    table = quote_ident(target.target_table)
    with cm.writer() as con:
        if source_id:
            row = con.execute(
                f"SELECT COUNT(*) FROM {table} WHERE source_used = ?",
                [source_id],
            ).fetchone()
        else:
            row = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    return int(row[0]) if row else 0


def _run_fred_macro_live_sync(cm: ConnectionManager, data_root: Path):
    from backend.app.datasources.fetch_ports.fred_port import create_fred_fetch_port
    from backend.app.datasources.incremental_route_activation import (
        build_activation_route_planner,
        ensure_sandbox_route_activation,
    )
    from backend.app.ops.fred_incremental_run import (
        build_fred_incremental_service,
        run_fred_macro_incremental,
    )
    from backend.app.ops.fred_incremental_watermark import read_since_dates_for_series
    from backend.app.sync.orchestrator import DataSyncOrchestrator

    series_ids = (FRED_ACCEPTANCE_SERIES_ID,)
    raw_root = data_root / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    with cm.writer() as con:
        matrix_path = ensure_sandbox_route_activation(
            con,
            data_root=data_root,
            source_id="fred",
            data_domain="macro_series",
            operation="fetch_macro_series",
        )
        since_map = read_since_dates_for_series(con, series_ids)
    planner = build_activation_route_planner(
        platform_matrix_path=matrix_path,
    )
    port = create_fred_fetch_port(series_ids=series_ids, max_rows=3, use_mock=False)
    orch = DataSyncOrchestrator(cm)
    service = build_fred_incremental_service(
        data_root=raw_root,
        fetch_port=port,
        since_by_series=since_map,
        job_events=orch._jobs,
        source_registry=planner.source_registry,
        route_planner=planner,
    )
    return run_fred_macro_incremental(
        orch,
        service=service,
        series_ids=series_ids,
        use_mock=False,
        source_registry=planner.source_registry,
    )


def _acceptance_job_statuses(
    cm: ConnectionManager,
    job_id: str | None,
) -> tuple[str, str]:
    if job_id is None:
        return "NOT_RUN", "NOT_RUN"
    with cm.reader() as con:
        row = con.execute(
            """
            SELECT status, validation_report_id, conflict_report_id
            FROM data_sync_job
            WHERE job_id = ?
            """,
            [job_id],
        ).fetchone()
    if row is None:
        return "NOT_RUN", "NOT_RUN"
    status = str(row[0])
    if status == "COMPLETED":
        validation_status = "PASSED_PRIMARY" if row[1] else "NOT_RUN"
        conflict_status = "PASSED" if row[2] else "NOT_RUN"
    elif status == "MANUAL_REVIEW_REQUIRED":
        validation_status = "MANUAL_REVIEW_REQUIRED"
        conflict_status = "NOT_RUN"
    elif status == "WAITING_RECONCILE":
        validation_status = "PASSED_PRIMARY" if row[1] else "NOT_RUN"
        conflict_status = "SEVERE_CONFLICT"
    else:
        validation_status = "FAILED"
        conflict_status = "NOT_RUN"
    return validation_status, conflict_status


def _probe_fred_downstream_read(cm: ConnectionManager) -> tuple[str, str | None, str | None]:
    from backend.app.layer1_axes.clean_observation_reader import (
        CleanObservationFallbackForbiddenError,
        CleanObservationReadError,
        read_macro_clean_observations,
    )

    with cm.writer() as con:
        row = con.execute(
            """
            SELECT schema_hash, content_hash
            FROM axis_observation
            WHERE indicator_id = ?
            ORDER BY publish_timestamp DESC
            LIMIT 1
            """,
            [FRED_ACCEPTANCE_SERIES_ID],
        ).fetchone()
        try:
            read_macro_clean_observations(con, FRED_ACCEPTANCE_SPEC_INDICATOR_ID, limit=3)
        except CleanObservationReadError:
            status = "NO_CLEAN_ROWS"
        except CleanObservationFallbackForbiddenError:
            status = "DEGRADED_REJECTED"
        else:
            status = "PRIMARY_GRADE_READ"
    schema_hash = _optional_str(row[0]) if row else None
    content_hash = _optional_str(row[1]) if row else None
    return status, schema_hash, content_hash


def preview_from_route_payload(
    request: AcceptanceRequest,
    route_payload: dict[str, Any],
    *,
    missing_prerequisites: tuple[str, ...] = (),
) -> AcceptancePreview:
    route_grade = _route_grade_from_payload(route_payload)
    route_status = _optional_str(route_payload.get("route_status")) or "UNKNOWN"
    live_ready = not missing_prerequisites and route_grade != "blocked"
    if missing_prerequisites:
        reason = (
            f"route_status={route_status}; "
            f"missing_prerequisites={'; '.join(missing_prerequisites)}"
        )
        status = "FAIL"
    elif route_grade == "blocked":
        reason = f"route_status={route_status}"
        status = "FAIL"
    else:
        reason = f"route_status={route_status}"
        status = "PASS"
    return AcceptancePreview(
        request=request,
        route_grade=route_grade,
        implementation_mode="live",
        status=status,
        reason=reason,
        missing_prerequisites=missing_prerequisites,
        live_ready=live_ready,
    )


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
