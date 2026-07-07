"""Matrix live incremental/evidence handlers (extracted from acceptance spine)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from backend.app.db.connection import ConnectionManager
from backend.app.ops.source_route_db_acceptance import (
    AcceptanceReport,
    AcceptanceRequest,
    _count_clean_rows,
    _matrix_evidence_fetch_live_report,
    _matrix_incremental_live_report,
    _optional_str,
    _run_fred_macro_live_sync,
    replace,
)


def _raw_orchestrator(data_root: Path, cm: ConnectionManager):
    from backend.app.sync.orchestrator import DataSyncOrchestrator

    raw_root = data_root / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    return raw_root, DataSyncOrchestrator(cm)


def _finish_incremental_matrix_live(
    request: AcceptanceRequest,
    matrix_target,
    cm: ConnectionManager,
    route_payload: dict[str, Any],
    *,
    sync_status: str,
    job_id: str | None,
) -> AcceptanceReport:
    rows = _count_clean_rows(cm, request.data_domain)
    return _matrix_incremental_live_report(
        request,
        route_payload,
        cm,
        matrix_target=matrix_target,
        sync_status=sync_status,
        rows_written=rows,
        job_id=job_id,
    )


def execute_primary_matrix_live(
    request: AcceptanceRequest,
    matrix_target,
    cm: ConnectionManager,
    data_root: Path,
    route_payload: dict[str, Any],
) -> AcceptanceReport:
    from backend.app.ops.source_route_db_acceptance_matrix import (
        EVIDENCE_FETCH_MATRIX_SOURCE_IDS,
    )

    dispatch: dict[str, Callable[..., AcceptanceReport]] = {
        "baostock": execute_baostock_matrix_live,
        "cninfo": execute_cninfo_matrix_live,
        "sec_edgar": execute_sec_edgar_matrix_live,
        "us_treasury": execute_us_treasury_matrix_live,
        "cftc_cot": execute_cftc_matrix_live,
        "bis": execute_bis_matrix_live,
        "world_bank": execute_world_bank_matrix_live,
        "deribit": execute_deribit_matrix_live,
        "alpha_vantage": execute_alpha_vantage_matrix_live,
        "fred": execute_fred_matrix_live,
    }
    for source_id in EVIDENCE_FETCH_MATRIX_SOURCE_IDS:
        dispatch[source_id] = execute_matrix_evidence_fetch_live
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


def execute_validation_matrix_probe(
    request: AcceptanceRequest,
    matrix_target,
    cm: ConnectionManager,
    data_root: Path,
    route_payload: dict[str, Any],
) -> AcceptanceReport:
    """Validation sources: route preview plus live fetch probe (TD-07)."""
    from backend.app.ops.matrix_live_runners import (
        evidence_fetch_failure_class,
        run_matrix_evidence_fetch_live,
    )

    sync_status, ok, error_message = run_matrix_evidence_fetch_live(
        request=request,
        data_root=data_root,
        instrument_id=None,
    )
    if not ok:
        route_report = AcceptanceReport.from_route_payload(request, route_payload)
        return replace(
            route_report,
            implementation_mode="live",
            write_grade="blocked",
            failure_class=evidence_fetch_failure_class(sync_status),  # type: ignore[arg-type]
            downstream_layer_read_status="VALIDATION_ONLY",
            status="FAIL",
            errors=(error_message or "validation fetch probe failed",),
        )
    return AcceptanceReport.qualified_non_primary_from_route_payload(
        request,
        route_payload,
        positioning=matrix_target.positioning,
        expected_write_grade=matrix_target.expected_write_grade,
        downstream_expectation=matrix_target.downstream_expectation,
    )


def execute_baostock_matrix_live(
    request: AcceptanceRequest,
    matrix_target,
    cm: ConnectionManager,
    data_root: Path,
    route_payload: dict[str, Any],
) -> AcceptanceReport:
    from datetime import date, timedelta

    from backend.app.ops.baostock_incremental_run import (
        build_baostock_incremental_service,
        run_baostock_bar_incremental,
    )
    from backend.app.sync.watermark import IncrementalWindow

    raw_root, orch = _raw_orchestrator(data_root, cm)
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
    return _finish_incremental_matrix_live(
        request,
        matrix_target,
        cm,
        route_payload,
        sync_status=result.status,
        job_id=result.job_id,
    )


def execute_cninfo_matrix_live(
    request: AcceptanceRequest,
    matrix_target,
    cm: ConnectionManager,
    data_root: Path,
    route_payload: dict[str, Any],
) -> AcceptanceReport:
    from backend.app.datasources.fetch_ports.cninfo_port import create_cninfo_fetch_port
    from backend.app.ops.cninfo_incremental_run import (
        build_cninfo_incremental_service,
        run_cninfo_incremental,
    )
    from backend.app.ops.source_route_db_acceptance_matrix import matrix_cninfo_symbols

    raw_root, orch = _raw_orchestrator(data_root, cm)
    symbols = matrix_cninfo_symbols()
    port = create_cninfo_fetch_port(symbols=symbols, max_rows=3, use_mock=False)
    service = build_cninfo_incremental_service(
        data_root=raw_root,
        fetch_port=port,
        since_by_instrument={},
        job_events=orch._jobs,
    )
    report = run_cninfo_incremental(orch, service=service, symbols=symbols)
    job_id = (
        _optional_str(report.instrument_results[0].get("job_id"))
        if report.instrument_results
        else None
    )
    return _finish_incremental_matrix_live(
        request,
        matrix_target,
        cm,
        route_payload,
        sync_status=report.overall_status,
        job_id=job_id,
    )


def execute_sec_edgar_matrix_live(
    request: AcceptanceRequest,
    matrix_target,
    cm: ConnectionManager,
    data_root: Path,
    route_payload: dict[str, Any],
) -> AcceptanceReport:
    from backend.app.datasources.fetch_ports.sec_edgar_port import create_sec_edgar_fetch_port
    from backend.app.ops.sec_edgar_incremental_run import (
        build_sec_edgar_incremental_service,
        run_sec_edgar_incremental,
    )

    raw_root, orch = _raw_orchestrator(data_root, cm)
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
    return _matrix_incremental_live_report(
        request,
        route_payload,
        cm,
        matrix_target=matrix_target,
        sync_status=str(cik_result.get("status", report.overall_status)),
        rows_written=int(cik_result.get("clean_row_count", 0)),
        job_id=_optional_str(cik_result.get("job_id")),
    )


def _run_macro_list_incremental(
    request: AcceptanceRequest,
    matrix_target,
    cm: ConnectionManager,
    data_root: Path,
    route_payload: dict[str, Any],
    *,
    instrument_ids: tuple[str, ...],
    create_port: Callable[..., Any],
    build_service,
    run_incremental: Callable[..., Any],
) -> AcceptanceReport:
    raw_root, orch = _raw_orchestrator(data_root, cm)
    port = create_port(instrument_ids, use_mock=False)
    service = build_service(
        data_root=raw_root,
        fetch_port=port,
        since_by_instrument={item: "2000-01-01" for item in instrument_ids},
        job_events=orch._jobs,
    )
    report = run_incremental(orch, service=service, instrument_ids=instrument_ids, use_mock=False)
    return _finish_incremental_matrix_live(
        request,
        matrix_target,
        cm,
        route_payload,
        sync_status=report.overall_status,
        job_id=None,
    )


def execute_us_treasury_matrix_live(
    request: AcceptanceRequest,
    matrix_target,
    cm: ConnectionManager,
    data_root: Path,
    route_payload: dict[str, Any],
) -> AcceptanceReport:
    from backend.app.ops.us_treasury_incremental_run import (
        build_us_treasury_incremental_service,
        create_us_treasury_incremental_port,
        run_us_treasury_incremental,
    )

    tenors = ("10Y",)
    return _run_macro_list_incremental(
        request,
        matrix_target,
        cm,
        data_root,
        route_payload,
        instrument_ids=tenors,
        create_port=lambda ids, **kw: create_us_treasury_incremental_port(tenors=ids, **kw),
        build_service=build_us_treasury_incremental_service,
        run_incremental=lambda orch, service, instrument_ids, **kw: run_us_treasury_incremental(
            orch, service=service, tenors=instrument_ids, **kw
        ),
    )


def execute_cftc_matrix_live(
    request: AcceptanceRequest,
    matrix_target,
    cm: ConnectionManager,
    data_root: Path,
    route_payload: dict[str, Any],
) -> AcceptanceReport:
    from backend.app.ops.cftc_incremental_run import (
        build_cftc_incremental_service,
        create_cftc_incremental_port,
        run_cftc_incremental,
    )

    markets = ("088691",)
    return _run_macro_list_incremental(
        request,
        matrix_target,
        cm,
        data_root,
        route_payload,
        instrument_ids=markets,
        create_port=lambda ids, **kw: create_cftc_incremental_port(markets=ids, **kw),
        build_service=build_cftc_incremental_service,
        run_incremental=lambda orch, service, instrument_ids, **kw: run_cftc_incremental(
            orch, service=service, markets=instrument_ids, **kw
        ),
    )


def execute_bis_matrix_live(
    request: AcceptanceRequest,
    matrix_target,
    cm: ConnectionManager,
    data_root: Path,
    route_payload: dict[str, Any],
) -> AcceptanceReport:
    from backend.app.ops.bis_incremental_run import (
        build_bis_incremental_service,
        create_bis_incremental_port,
        run_bis_incremental,
    )

    countries = ("US",)
    return _run_macro_list_incremental(
        request,
        matrix_target,
        cm,
        data_root,
        route_payload,
        instrument_ids=countries,
        create_port=lambda ids, **kw: create_bis_incremental_port(countries=ids, **kw),
        build_service=build_bis_incremental_service,
        run_incremental=lambda orch, service, instrument_ids, **kw: run_bis_incremental(
            orch, service=service, countries=instrument_ids, **kw
        ),
    )


def execute_world_bank_matrix_live(
    request: AcceptanceRequest,
    matrix_target,
    cm: ConnectionManager,
    data_root: Path,
    route_payload: dict[str, Any],
) -> AcceptanceReport:
    from backend.app.ops.world_bank_incremental_run import (
        build_world_bank_incremental_service,
        create_world_bank_incremental_port,
        run_world_bank_incremental,
    )

    countries = ("US",)
    return _run_macro_list_incremental(
        request,
        matrix_target,
        cm,
        data_root,
        route_payload,
        instrument_ids=countries,
        create_port=lambda ids, **kw: create_world_bank_incremental_port(countries=ids, **kw),
        build_service=build_world_bank_incremental_service,
        run_incremental=lambda orch, service, instrument_ids, **kw: run_world_bank_incremental(
            orch, service=service, countries=instrument_ids, **kw
        ),
    )


def execute_deribit_matrix_live(
    request: AcceptanceRequest,
    matrix_target,
    cm: ConnectionManager,
    data_root: Path,
    route_payload: dict[str, Any],
) -> AcceptanceReport:
    from backend.app.datasources.fetch_ports.deribit_port import create_deribit_fetch_port
    from backend.app.ops.deribit_incremental_run import (
        build_deribit_incremental_service,
        run_deribit_incremental,
    )
    from backend.app.ops.source_route_db_acceptance_matrix import resolve_matrix_deribit_live_instrument

    raw_root, orch = _raw_orchestrator(data_root, cm)
    instrument = resolve_matrix_deribit_live_instrument()
    port = create_deribit_fetch_port(instruments=(instrument,), max_surface_rows=3, use_mock=False)
    service = build_deribit_incremental_service(
        data_root=raw_root,
        fetch_port=port,
        since_by_instrument={instrument: "2000-01-01"},
        job_events=orch._jobs,
    )
    report = run_deribit_incremental(orch, service=service, instruments=(instrument,))
    job_id = (
        _optional_str(report.instrument_results[0].get("job_id"))
        if report.instrument_results
        else None
    )
    return _finish_incremental_matrix_live(
        request,
        matrix_target,
        cm,
        route_payload,
        sync_status=report.overall_status,
        job_id=job_id,
    )


def execute_alpha_vantage_matrix_live(
    request: AcceptanceRequest,
    matrix_target,
    cm: ConnectionManager,
    data_root: Path,
    route_payload: dict[str, Any],
) -> AcceptanceReport:
    from backend.app.datasources.fetch_ports.alpha_vantage_port import create_alpha_vantage_fetch_port
    from backend.app.ops.alpha_vantage_incremental_run import (
        build_alpha_vantage_incremental_service,
        enabled_alpha_vantage_source_registry,
        run_alpha_vantage_incremental,
    )
    from backend.app.ops.source_route_db_acceptance_matrix import matrix_alpha_vantage_symbol

    raw_root, orch = _raw_orchestrator(data_root, cm)
    symbol = matrix_alpha_vantage_symbol()
    port = create_alpha_vantage_fetch_port(symbols=(symbol,), max_rows=3, use_mock=False)
    service = build_alpha_vantage_incremental_service(
        data_root=raw_root,
        fetch_port=port,
        job_events=orch._jobs,
        source_registry=enabled_alpha_vantage_source_registry(),
    )
    report = run_alpha_vantage_incremental(orch, service=service, symbols=(symbol,))
    job_id = (
        _optional_str(report.symbol_results[0].get("job_id"))
        if report.symbol_results
        else None
    )
    return _finish_incremental_matrix_live(
        request,
        matrix_target,
        cm,
        route_payload,
        sync_status=report.overall_status,
        job_id=job_id,
    )


def execute_fred_matrix_live(
    request: AcceptanceRequest,
    matrix_target,
    cm: ConnectionManager,
    data_root: Path,
    route_payload: dict[str, Any],
) -> AcceptanceReport:
    from backend.app.datasources.product_live_gate import ProductLiveGateError
    from backend.app.ops.source_route_db_acceptance import (
        FRED_ACCEPTANCE_SERIES_ID,
        FRED_ACCEPTANCE_SPEC_INDICATOR_ID,
        _acceptance_job_statuses,
        _probe_fred_downstream_read,
    )

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


def execute_matrix_evidence_fetch_live(
    request: AcceptanceRequest,
    matrix_target,
    cm: ConnectionManager,
    data_root: Path,
    route_payload: dict[str, Any],
) -> AcceptanceReport:
    from backend.app.ops.matrix_live_runners import (
        evidence_fetch_failure_class,
        run_matrix_evidence_fetch_live,
    )
    from backend.app.ops.source_route_db_acceptance_matrix import (
        matrix_coingecko_asset_id,
        matrix_kalshi_market_ticker,
    )
    from backend.app.datasources.product_live_ports import SOURCE_LIVE_DEFAULTS

    instrument_id = None
    if request.source_id == "kalshi":
        instrument_id = matrix_kalshi_market_ticker()
    elif request.source_id == "coingecko":
        instrument_id = matrix_coingecko_asset_id()
    elif request.source_id == "ths_ifind":
        instrument_id = str(SOURCE_LIVE_DEFAULTS["ths_ifind"]["concepts"][0])

    sync_status, ok, error_message = run_matrix_evidence_fetch_live(
        request=request,
        data_root=data_root,
        instrument_id=instrument_id,
    )
    if not ok:
        route_report = AcceptanceReport.from_route_payload(request, route_payload)
        return replace(
            route_report,
            implementation_mode="live",
            write_grade="not_written",
            failure_class=evidence_fetch_failure_class(sync_status),  # type: ignore[arg-type]
            downstream_layer_read_status="NO_EVIDENCE",
            status="FAIL",
            errors=(error_message or "evidence fetch failed",),
        )
    return _matrix_evidence_fetch_live_report(
        request,
        route_payload,
        cm,
        matrix_target=matrix_target,
        sync_status=sync_status,
        data_root=data_root,
    )
