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

        if _is_fred_macro_series_request(request):
            route_payload = _fred_macro_route_payload(request)
            gate_errors: list[str] = []
            if not str(os.environ.get("FRED_API_KEY", "")).strip():
                gate_errors.append("FRED_API_KEY missing for macro_series:fred:fetch_macro_series")
            return _preview_from_route_payload(
                request,
                route_payload,
                missing_prerequisites=tuple(gate_errors),
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
    ) -> AcceptanceReport:
        _ = live_authorized
        resolved_root = Path(data_root).expanduser().resolve()
        if _is_canonical_main_data_root(resolved_root):
            return AcceptanceReport.contract_violation(
                request,
                f"canonical main data root rejected for acceptance: {resolved_root}",
            )
        cm = _bootstrap_acceptance_db(resolved_root)
        if _is_fred_macro_series_request(request):
            route_payload = _fred_macro_route_payload(request)
            _persist_route_evidence(cm, route_payload)
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
            return _execute_fred_macro_acceptance(request, cm, resolved_root, route_payload)
        from backend.app.ops.source_route_db_acceptance_matrix import find_matrix_target

        matrix_target = find_matrix_target(request)
        if matrix_target is not None:
            return _execute_matrix_target(
                request,
                matrix_target,
                cm,
                resolved_root,
                live_authorized=live_authorized,
            )
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


def _execute_fred_macro_acceptance(
    request: AcceptanceRequest,
    cm: ConnectionManager,
    data_root: Path,
    route_payload: dict[str, Any],
) -> AcceptanceReport:
    from backend.app.datasources.product_live_gate import ProductLiveGateError

    try:
        sync_report = _run_fred_macro_live_sync(cm, data_root)
    except ProductLiveGateError as exc:
        return AcceptanceReport.blocked_from_route_payload(request, route_payload, str(exc))

    route_report = AcceptanceReport.from_route_payload(request, route_payload)
    series = sync_report.series_results[0] if sync_report.series_results else {}
    validation_status, conflict_status = _acceptance_job_statuses(
        cm,
        _optional_str(series.get("job_id")),
    )
    read_status, schema_hash, content_hash = _probe_fred_downstream_read(cm)
    pass_status = (
        route_report.route_plan_id is not None
        and sync_report.overall_status == "COMPLETED"
        and sync_report.total_rows_written > 0
        and read_status == "PRIMARY_GRADE_READ"
    )
    errors: tuple[str, ...] = ()
    if not pass_status:
        errors = (
            "FRED live acceptance did not complete fetch/write/read: "
            f"overall_status={sync_report.overall_status}; "
            f"series={list(sync_report.series_results)}; downstream={read_status}",
        )
    return replace(
        route_report,
        implementation_mode="live",
        write_grade="primary_grade_clean" if sync_report.total_rows_written > 0 else "not_written",
        schema_hash=schema_hash,
        content_hash=content_hash,
        validation_status=validation_status,
        conflict_status=conflict_status,
        failure_class="NONE" if pass_status else "FAIL_EXTERNAL",
        downstream_layer_read_status=read_status,
        status="PASS" if pass_status else "FAIL",
        errors=errors,
    )


def _execute_matrix_target(
    request: AcceptanceRequest,
    matrix_target,
    cm: ConnectionManager,
    data_root: Path,
    *,
    live_authorized: bool,
) -> AcceptanceReport:
    from backend.app.datasources.product_live_gate import (
        ProductLiveGateError,
        is_product_live_fetch_allowed,
    )
    from backend.app.ops.source_route_db_acceptance_matrix import (
        is_non_primary_positioning,
        matrix_target_key,
        missing_gate_errors,
        preview_route_payload,
    )

    route_payload = preview_route_payload(request)
    _persist_route_evidence(cm, route_payload)
    target_key = matrix_target_key(matrix_target)
    if not live_authorized:
        return AcceptanceReport.blocked_from_route_payload(
            request,
            route_payload,
            f"live authorization missing for {target_key}",
        )
    gate_errors = missing_gate_errors(matrix_target)
    if gate_errors:
        return AcceptanceReport.blocked_from_route_payload(
            request,
            route_payload,
            "; ".join(gate_errors),
        )
    if is_non_primary_positioning(matrix_target):
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
    dispatch = {
        "baostock": _execute_baostock_matrix_live,
        "cninfo": _execute_cninfo_matrix_live,
        "sec_edgar": _execute_sec_edgar_matrix_live,
        "us_treasury": _execute_us_treasury_matrix_live,
        "cftc_cot": _execute_cftc_matrix_live,
        "bis": _execute_bis_matrix_live,
        "world_bank": _execute_world_bank_matrix_live,
        "deribit": _execute_deribit_matrix_live,
        "alpha_vantage": _execute_alpha_vantage_matrix_live,
        "coingecko": _execute_matrix_evidence_fetch_live,
        "kalshi": _execute_matrix_evidence_fetch_live,
        "qmt_xtdata": _execute_matrix_evidence_fetch_live,
    }
    handler = dispatch.get(request.source_id)
    if handler is None:
        route_report = AcceptanceReport.from_route_payload(request, route_payload)
        return replace(
            route_report,
            implementation_mode="live",
            failure_class="NOT_IMPLEMENTED",
            status="FAIL",
            errors=(f"live execute handler not wired for {request.source_id}",),
        )
    return handler(request, matrix_target, cm, data_root, route_payload)


def _matrix_live_report(
    request: AcceptanceRequest,
    route_payload: dict[str, Any],
    cm: ConnectionManager,
    *,
    matrix_target,
    sync_status: str,
    rows_written: int,
    job_id: str | None,
    evidence_fetch_ok: bool = False,
) -> AcceptanceReport:
    route_report = AcceptanceReport.from_route_payload(request, route_payload)
    validation_status, conflict_status = _acceptance_job_statuses(cm, job_id)
    if evidence_fetch_ok:
        pass_status = route_report.route_plan_id is not None and sync_status in {
            "COMPLETED",
            "PASS",
            "SUCCESS",
            "OK",
        }
        downstream = (
            matrix_target.downstream_expectation
            if pass_status
            else "NO_EVIDENCE"
        )
        write_grade = "not_written"
        errors: tuple[str, ...] = ()
        if not pass_status:
            errors = (
                f"evidence fetch incomplete: sync_status={sync_status}",
            )
        return replace(
            route_report,
            implementation_mode="live",
            write_grade=write_grade,
            validation_status=validation_status,
            conflict_status=conflict_status,
            failure_class="NONE" if pass_status else "FAIL_EXTERNAL",
            downstream_layer_read_status=downstream,
            status="PASS" if pass_status else "FAIL",
            errors=errors,
        )
    downstream = (
        matrix_target.downstream_expectation
        if rows_written > 0
        else "NO_CLEAN_ROWS"
    )
    pass_status = (
        route_report.route_plan_id is not None
        and sync_status in {"COMPLETED", "PASS"}
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


def _count_clean_rows(cm: ConnectionManager, data_domain: str) -> int:
    from backend.app.ops.sandbox_clean_write.clean_write_targets import resolve_clean_write_target

    target = resolve_clean_write_target(data_domain)
    with cm.writer() as con:
        row = con.execute(f"SELECT COUNT(*) FROM {target.target_table}").fetchone()
    return int(row[0]) if row else 0


def _execute_baostock_matrix_live(request, matrix_target, cm, data_root, route_payload):
    from datetime import date, timedelta

    from backend.app.ops.baostock_incremental_run import (
        build_baostock_incremental_service,
        run_baostock_bar_incremental,
    )
    from backend.app.sync.orchestrator import DataSyncOrchestrator
    from backend.app.sync.watermark import IncrementalWindow

    raw_root = data_root / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    orch = DataSyncOrchestrator(cm)
    symbol = "sh.600519"
    service = build_baostock_incremental_service(
        data_root=raw_root,
        symbol=symbol,
        job_events=orch._jobs,
        use_mock=False,
    )
    end = date.today()
    window = IncrementalWindow(
        date_start=end - timedelta(days=30),
        date_end=end,
        watermark=None,
    )
    result = run_baostock_bar_incremental(
        orch,
        service=service,
        window=window,
        symbol=symbol,
        product_live=True,
    )
    rows = _count_clean_rows(cm, request.data_domain)
    return _matrix_live_report(
        request,
        route_payload,
        cm,
        matrix_target=matrix_target,
        sync_status=result.status,
        rows_written=rows,
        job_id=result.job_id,
    )


def _execute_cninfo_matrix_live(request, matrix_target, cm, data_root, route_payload):
    from backend.app.datasources.fetch_ports.cninfo_port import create_cninfo_fetch_port
    from backend.app.ops.cninfo_incremental_run import (
        build_cninfo_incremental_service,
        run_cninfo_incremental,
    )
    from backend.app.sync.orchestrator import DataSyncOrchestrator

    raw_root = data_root / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    orch = DataSyncOrchestrator(cm)
    from backend.app.ops.source_route_db_acceptance_matrix import matrix_cninfo_symbols

    symbols = matrix_cninfo_symbols()
    port = create_cninfo_fetch_port(symbols=symbols, max_rows=3, use_mock=False)
    service = build_cninfo_incremental_service(
        data_root=raw_root,
        fetch_port=port,
        since_by_instrument={},
        job_events=orch._jobs,
    )
    report = run_cninfo_incremental(orch, service=service, symbols=symbols)
    rows = _count_clean_rows(cm, request.data_domain)
    return _matrix_live_report(
        request,
        route_payload,
        cm,
        matrix_target=matrix_target,
        sync_status=report.overall_status,
        rows_written=rows,
        job_id=_optional_str(report.instrument_results[0].get("job_id"))
        if report.instrument_results
        else None,
    )


def _execute_sec_edgar_matrix_live(request, matrix_target, cm, data_root, route_payload):
    from backend.app.datasources.fetch_ports.sec_edgar_port import create_sec_edgar_fetch_port
    from backend.app.ops.sec_edgar_incremental_run import (
        build_sec_edgar_incremental_service,
        run_sec_edgar_incremental,
    )
    from backend.app.sync.orchestrator import DataSyncOrchestrator

    raw_root = data_root / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    orch = DataSyncOrchestrator(cm)
    port = create_sec_edgar_fetch_port(
        ciks=("0000320193",), max_filings=3, data_domain="us_filings", use_mock=False
    )
    service = build_sec_edgar_incremental_service(
        data_root=raw_root,
        fetch_port=port,
        since_by_cik={},
        job_events=orch._jobs,
    )
    report = run_sec_edgar_incremental(orch, service=service, ciks=("0000320193",))
    cik_result = report.cik_results[0] if report.cik_results else {}
    return _matrix_live_report(
        request,
        route_payload,
        cm,
        matrix_target=matrix_target,
        sync_status=str(cik_result.get("status", report.overall_status)),
        rows_written=int(cik_result.get("clean_row_count", 0)),
        job_id=_optional_str(cik_result.get("job_id")),
    )


def _execute_us_treasury_matrix_live(request, matrix_target, cm, data_root, route_payload):
    from backend.app.ops.us_treasury_incremental_run import (
        build_us_treasury_incremental_service,
        create_us_treasury_incremental_port,
        run_us_treasury_incremental,
    )
    from backend.app.sync.orchestrator import DataSyncOrchestrator

    tenors = ("10Y",)
    raw_root = data_root / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    orch = DataSyncOrchestrator(cm)
    port = create_us_treasury_incremental_port(tenors=tenors, use_mock=False)
    service = build_us_treasury_incremental_service(
        data_root=raw_root,
        fetch_port=port,
        since_by_instrument={tenor: "2000-01-01" for tenor in tenors},
        job_events=orch._jobs,
    )
    report = run_us_treasury_incremental(
        orch, service=service, tenors=tenors, use_mock=False
    )
    rows = _count_clean_rows(cm, request.data_domain)
    return _matrix_live_report(
        request,
        route_payload,
        cm,
        matrix_target=matrix_target,
        sync_status=report.overall_status,
        rows_written=rows,
        job_id=None,
    )


def _execute_cftc_matrix_live(request, matrix_target, cm, data_root, route_payload):
    from backend.app.ops.cftc_incremental_run import (
        build_cftc_incremental_service,
        create_cftc_incremental_port,
        run_cftc_incremental,
    )
    from backend.app.sync.orchestrator import DataSyncOrchestrator

    markets = ("088691",)
    raw_root = data_root / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    orch = DataSyncOrchestrator(cm)
    port = create_cftc_incremental_port(markets=markets, use_mock=False)
    service = build_cftc_incremental_service(
        data_root=raw_root,
        fetch_port=port,
        since_by_instrument={market: "2000-01-01" for market in markets},
        job_events=orch._jobs,
    )
    report = run_cftc_incremental(orch, service=service, markets=markets, use_mock=False)
    rows = _count_clean_rows(cm, request.data_domain)
    return _matrix_live_report(
        request,
        route_payload,
        cm,
        matrix_target=matrix_target,
        sync_status=report.overall_status,
        rows_written=rows,
        job_id=None,
    )


def _execute_bis_matrix_live(request, matrix_target, cm, data_root, route_payload):
    from backend.app.ops.bis_incremental_run import (
        build_bis_incremental_service,
        create_bis_incremental_port,
        run_bis_incremental,
    )
    from backend.app.sync.orchestrator import DataSyncOrchestrator

    countries = ("US",)
    raw_root = data_root / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    orch = DataSyncOrchestrator(cm)
    port = create_bis_incremental_port(countries=countries, use_mock=False)
    service = build_bis_incremental_service(
        data_root=raw_root,
        fetch_port=port,
        since_by_instrument={country: "2000-01-01" for country in countries},
        job_events=orch._jobs,
    )
    report = run_bis_incremental(orch, service=service, countries=countries, use_mock=False)
    rows = _count_clean_rows(cm, request.data_domain)
    return _matrix_live_report(
        request,
        route_payload,
        cm,
        matrix_target=matrix_target,
        sync_status=report.overall_status,
        rows_written=rows,
        job_id=None,
    )


def _execute_world_bank_matrix_live(request, matrix_target, cm, data_root, route_payload):
    from backend.app.ops.world_bank_incremental_run import (
        build_world_bank_incremental_service,
        create_world_bank_incremental_port,
        run_world_bank_incremental,
    )
    from backend.app.sync.orchestrator import DataSyncOrchestrator

    countries = ("US",)
    raw_root = data_root / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    orch = DataSyncOrchestrator(cm)
    port = create_world_bank_incremental_port(countries=countries, use_mock=False)
    service = build_world_bank_incremental_service(
        data_root=raw_root,
        fetch_port=port,
        since_by_instrument={country: "2000-01-01" for country in countries},
        job_events=orch._jobs,
    )
    report = run_world_bank_incremental(
        orch, service=service, countries=countries, use_mock=False
    )
    rows = _count_clean_rows(cm, request.data_domain)
    return _matrix_live_report(
        request,
        route_payload,
        cm,
        matrix_target=matrix_target,
        sync_status=report.overall_status,
        rows_written=rows,
        job_id=None,
    )


def _execute_deribit_matrix_live(request, matrix_target, cm, data_root, route_payload):
    from backend.app.datasources.fetch_ports.deribit_port import create_deribit_fetch_port
    from backend.app.ops.deribit_incremental_run import (
        build_deribit_incremental_service,
        run_deribit_incremental,
    )
    from backend.app.ops.source_route_db_acceptance_matrix import resolve_matrix_deribit_live_instrument
    from backend.app.sync.orchestrator import DataSyncOrchestrator

    raw_root = data_root / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    orch = DataSyncOrchestrator(cm)
    instrument = resolve_matrix_deribit_live_instrument()
    port = create_deribit_fetch_port(instruments=(instrument,), max_surface_rows=3, use_mock=False)
    service = build_deribit_incremental_service(
        data_root=raw_root,
        fetch_port=port,
        since_by_instrument={instrument: "2000-01-01"},
        job_events=orch._jobs,
    )
    report = run_deribit_incremental(orch, service=service, instruments=(instrument,))
    inst_result = report.instrument_results[0] if report.instrument_results else {}
    return _matrix_live_report(
        request,
        route_payload,
        cm,
        matrix_target=matrix_target,
        sync_status=str(inst_result.get("status", report.overall_status)),
        rows_written=int(inst_result.get("clean_row_count", 0)),
        job_id=_optional_str(inst_result.get("job_id")),
    )


def _execute_alpha_vantage_matrix_live(request, matrix_target, cm, data_root, route_payload):
    from backend.app.datasources.fetch_ports.alpha_vantage_port import (
        create_alpha_vantage_fetch_port,
    )
    from backend.app.ops.alpha_vantage_incremental_run import (
        build_alpha_vantage_incremental_service,
        enabled_alpha_vantage_source_registry,
        run_alpha_vantage_incremental,
    )
    from backend.app.ops.source_route_db_acceptance_matrix import matrix_alpha_vantage_symbol
    from backend.app.sync.orchestrator import DataSyncOrchestrator

    raw_root = data_root / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    orch = DataSyncOrchestrator(cm)
    symbol = matrix_alpha_vantage_symbol()
    port = create_alpha_vantage_fetch_port(symbols=(symbol,), max_rows=3, use_mock=False)
    service = build_alpha_vantage_incremental_service(
        data_root=raw_root,
        fetch_port=port,
        job_events=orch._jobs,
        source_registry=enabled_alpha_vantage_source_registry(),
    )
    report = run_alpha_vantage_incremental(orch, service=service, symbols=(symbol,))
    rows = _count_clean_rows(cm, request.data_domain)
    return _matrix_live_report(
        request,
        route_payload,
        cm,
        matrix_target=matrix_target,
        sync_status=report.overall_status,
        rows_written=rows,
        job_id=_optional_str(report.symbol_results[0].get("job_id"))
        if report.symbol_results
        else None,
    )


def _execute_matrix_evidence_fetch_live(request, matrix_target, cm, data_root, route_payload):
    from datetime import date

    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_result import FetchRequest
    from backend.app.datasources.product_live_ports import create_product_live_fetch_port
    from backend.app.ops.source_route_db_acceptance_matrix import (
        matrix_coingecko_asset_id,
        matrix_kalshi_market_ticker,
    )
    from backend.app.storage.raw_store import RawStore

    instrument_id = None
    if request.source_id == "kalshi":
        instrument_id = matrix_kalshi_market_ticker()
    elif request.source_id == "coingecko":
        instrument_id = matrix_coingecko_asset_id()

    port = create_product_live_fetch_port(
        source_id=request.source_id,
        data_domain=request.data_domain,
        operation=request.operation,
    )
    fetch_req = FetchRequest(
        run_id="acceptance-evidence-fetch",
        source_id=request.source_id,
        data_domain=request.data_domain,
        instrument_id=instrument_id,
    )
    try:
        payload = port.fetch_payload(fetch_req)
    except PortError as exc:
        route_report = AcceptanceReport.from_route_payload(request, route_payload)
        status = str(exc.status).upper()
        failure_class = "FAIL_EXTERNAL"
        if status in {"USER_AUTH_REQUIRED", "AUTH_FAILED"}:
            failure_class = "BLOCKED"
        return replace(
            route_report,
            implementation_mode="live",
            write_grade="not_written",
            failure_class=failure_class,
            downstream_layer_read_status="NO_EVIDENCE",
            status="FAIL",
            errors=(f"evidence fetch port error: {exc.message}",),
        )

    row_count = int(payload.row_count or 0)
    if row_count < 1:
        route_report = AcceptanceReport.from_route_payload(request, route_payload)
        return replace(
            route_report,
            implementation_mode="live",
            write_grade="not_written",
            failure_class="FAIL_EXTERNAL",
            downstream_layer_read_status="NO_EVIDENCE",
            status="FAIL",
            errors=("evidence fetch returned zero rows",),
        )

    raw_root = data_root / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    store = RawStore(raw_root)
    store.save(
        payload.content,
        source=request.source_id,
        data_domain=request.data_domain,
        file_type=payload.file_type,
        as_of=date.today().isoformat(),
    )
    return _matrix_live_report(
        request,
        route_payload,
        cm,
        matrix_target=matrix_target,
        sync_status="SUCCESS",
        rows_written=0,
        job_id=None,
        evidence_fetch_ok=True,
    )


def _run_fred_macro_live_sync(cm: ConnectionManager, data_root: Path):
    from backend.app.datasources.fetch_ports.fred_port import create_fred_fetch_port
    from backend.app.ops.fred_incremental_run import (
        build_fred_incremental_service,
        enabled_fred_source_registry,
        run_fred_macro_incremental,
    )
    from backend.app.ops.fred_incremental_watermark import read_since_dates_for_series
    from backend.app.sync.orchestrator import DataSyncOrchestrator

    series_ids = (FRED_ACCEPTANCE_SERIES_ID,)
    raw_root = data_root / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    registry = enabled_fred_source_registry()
    port = create_fred_fetch_port(series_ids=series_ids, max_rows=3, use_mock=False)
    orch = DataSyncOrchestrator(cm)
    with cm.writer() as con:
        since_map = read_since_dates_for_series(con, series_ids)
    service = build_fred_incremental_service(
        data_root=raw_root,
        fetch_port=port,
        since_by_series=since_map,
        job_events=orch._jobs,
        source_registry=registry,
    )
    return run_fred_macro_incremental(
        orch,
        service=service,
        series_ids=series_ids,
        use_mock=False,
        source_registry=registry,
    )


def _acceptance_job_statuses(
    cm: ConnectionManager,
    job_id: str | None,
) -> tuple[str, str]:
    if job_id is None:
        return "NOT_RUN", "NOT_RUN"
    with cm.writer() as con:
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


def _is_canonical_main_data_root(data_root: Path) -> bool:
    canonical_roots = {Path(PROJECT_ROOT / "data").resolve(), Path(DATA_ROOT).resolve()}
    if data_root in canonical_roots:
        return True
    canonical_db_paths = {root / "duckdb" / "quant_monitor.duckdb" for root in canonical_roots}
    return data_root / "duckdb" / "quant_monitor.duckdb" in canonical_db_paths


def _preview_from_route_payload(
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
