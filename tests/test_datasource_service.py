"""Round2.6 Phase B/C — DataSourceService boundary and fetch facade tests."""

from __future__ import annotations

import json
from pathlib import Path

from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.datasources.adapters.fetch_port import LocalFixtureFetchPort
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.service import DataSourceService
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.sync.event_payload import parse_event_payload
from backend.app.sync.jobs import SyncJobSpec, SyncJobStateMachine
from tests.contract_gate_support import (
    ALLOWED_ADAPTER_FACTORY_PATHS,
    PROJECT_ROOT,
    SERVICE_CONTRACT,
    collect_imports,
    load_yaml,
    scan_package_for_create_adapter,
)

BACKEND_APP = PROJECT_ROOT / "backend" / "app"
RUNNERS = BACKEND_APP / "sync" / "runners.py"
CONCRETE_ADAPTER_PREFIX = "backend.app.datasources.adapters."


def _load_service_contract() -> dict:
    return load_yaml(SERVICE_CONTRACT)


def test_apiAndAgentCannotImportAdapterFactory() -> None:
    contract = _load_service_contract()
    forbidden_pkgs = contract.get("call_boundaries", {}).get("forbidden_direct_callers") or []
    violations: list[str] = []
    for pkg in forbidden_pkgs:
        pkg_path = pkg.replace("backend.app.", "")
        violations.extend(scan_package_for_create_adapter(pkg_path))
    assert violations == [], (
        "production modules must not import create_adapter directly: " + "; ".join(violations)
    )


def test_serviceBuildsRouteBeforeFetch() -> None:
    """Contract + runtime: route plan and guard precede adapter fetch."""
    contract = _load_service_contract()
    steps = contract["public_methods"]["fetch"]["required_steps"]
    assert steps == [
        "load_source_registry",
        "load_capability_registry",
        "build_source_route_plan",
        "check_resource_guard",
        "create_adapter_internal_only",
        "call_adapter_fetch",
        "ensure_fetch_log_or_failure_event",
    ]


def test_serviceFetch_runtimeGateOrder(tmp_path: Path, monkeypatch) -> None:
    """Runtime gate order: route event → guard → adapter fetch → fetch_log."""
    order: list[str] = []

    def guard_check(self):
        order.append("guard")
        return Decision.OK, ""

    monkeypatch.setattr(ResourceGuard, "check", guard_check)

    def fake_create_test_adapter(sid, registry, data_root, **kwargs):
        order.append("create_adapter")

        class ProbeAdapter:
            source_id = sid

            def fetch(self, req, *, con, job_id=None):
                order.append("adapter_fetch")
                from datetime import UTC, datetime

                from backend.app.datasources.fetch_result import FetchResult

                return FetchResult(
                    run_id=req.run_id,
                    source_id=sid,
                    data_domain=req.data_domain,
                    status="SUCCESS",
                    row_count=1,
                    fetch_time=datetime.now(UTC).isoformat(),
                    raw_file_paths=["/tmp/probe.json"],
                )

        return ProbeAdapter()

    monkeypatch.setattr(
        "backend.app.datasources.adapters.create_test_adapter",
        fake_create_test_adapter,
    )

    db = tmp_path / "order.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    jobs = SyncJobStateMachine(cm)
    reg = SourceRegistry()
    reg.load()
    service = DataSourceService(
        source_registry=reg,
        data_root=tmp_path / "raw",
        job_events=jobs,
    )
    spec = SyncJobSpec(
        run_id="run-order",
        job_id="job-order",
        job_type="incremental",
        data_domain="cn_equity_daily_bar",
        market_id="CN_A",
        source_id="baostock",
        adapter_id="baostock",
        date_start=None,
        date_end=None,
        instrument_id="000001",
        partition_key=None,
        trigger_reason=None,
    )
    job_id = jobs.create_job(spec)
    req = FetchRequest(
        run_id="run-order",
        source_id="baostock",
        data_domain="cn_equity_daily_bar",
    )
    entered_fetching = False

    def on_enter_fetching():
        nonlocal entered_fetching
        entered_fetching = True
        order.append("enter_fetching")

    with cm.writer() as con:
        result = service.fetch(
            req,
            con=con,
            job_id=job_id,
            on_enter_fetching=on_enter_fetching,
        )
    assert result.status == "SUCCESS"
    assert order.index("guard") < order.index("enter_fetching")
    assert order.index("enter_fetching") < order.index("create_adapter")
    assert order.index("create_adapter") < order.index("adapter_fetch")
    with cm.writer() as con:
        route_count = con.execute(
            "SELECT COUNT(*) FROM job_event_log WHERE job_id=? AND event_type='ROUTE_PLAN'",
            [job_id],
        ).fetchone()[0]
        log_count = con.execute(
            "SELECT COUNT(*) FROM fetch_log WHERE job_id=?", [job_id]
        ).fetchone()[0]
    assert route_count == 1
    assert log_count == 1
    assert entered_fetching


def test_serviceContract_declaresFetchGateOrder() -> None:
    test_serviceBuildsRouteBeforeFetch()


def test_forbiddenDirectCallers_includesSyncRunners_andScanIsContractDriven() -> None:
    contract = _load_service_contract()
    forbidden = contract.get("call_boundaries", {}).get("forbidden_direct_callers") or []
    assert "backend.app.sync.runners" in forbidden
    assert scan_package_for_create_adapter("sync/runners") == []


def test_createAdapterImports_onlyUnderTests() -> None:
    """create_adapter imports allowed only in datasources factory modules until Task 2 service."""
    violations: list[str] = []
    for py_file in BACKEND_APP.rglob("*.py"):
        if py_file in ALLOWED_ADAPTER_FACTORY_PATHS:
            continue
        imports = collect_imports(py_file)
        if "create_adapter" in imports or any(imp.endswith(".create_adapter") for imp in imports):
            rel = py_file.relative_to(PROJECT_ROOT)
            violations.append(str(rel))
    assert violations == [], f"create_adapter found outside allowed factory paths: {violations}"


def test_syncRunners_doesNotImportConcreteAdaptersOrFactory() -> None:
    imports = collect_imports(RUNNERS)
    assert "create_adapter" not in imports
    assert not any(imp.startswith(CONCRETE_ADAPTER_PREFIX) for imp in imports)
    assert not any(imp.endswith("Adapter") and "adapters" in imp for imp in imports)


def test_servicePreviewRoute_returnsReadyPlan() -> None:
    service = DataSourceService()
    plan = service.preview_route(
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
    )
    assert plan.route_status == "READY"
    assert plan.selected_source_id == "baostock"


def test_serviceWritesRoutePlanPayloadBeforeFetch(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    db = tmp_path / "svc.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    jobs = SyncJobStateMachine(cm)
    fixture = tmp_path / "bar.json"
    fixture.write_text(
        json.dumps([{"symbol": "000001", "close": 1.0, "trade_date": "2026-06-15"}]),
        encoding="utf-8",
    )
    reg = SourceRegistry()
    reg.load()
    service = DataSourceService(
        source_registry=reg,
        data_root=tmp_path / "raw",
        fetch_port=LocalFixtureFetchPort(fixture, row_count=1),
        job_events=jobs,
    )
    spec = SyncJobSpec(
        run_id="run-svc",
        job_id="job-svc",
        job_type="incremental",
        data_domain="cn_equity_daily_bar",
        market_id="CN_A",
        source_id="baostock",
        adapter_id="baostock",
        date_start=None,
        date_end=None,
        instrument_id="000001",
        partition_key=None,
        trigger_reason=None,
    )
    spec_job = jobs.create_job(spec)
    req = FetchRequest(
        run_id="run-svc",
        source_id="baostock",
        data_domain="cn_equity_daily_bar",
        market_id="CN_A",
        instrument_id="000001",
    )
    with cm.writer() as con:
        service.fetch(req, con=con, job_id=spec_job)
    with cm.writer() as con:
        row = con.execute(
            """
            SELECT event_type, payload_json FROM job_event_log
            WHERE job_id = ? AND event_type = 'ROUTE_PLAN'
            ORDER BY created_at ASC LIMIT 1
            """,
            [spec_job],
        ).fetchone()
    assert row is not None
    payload = parse_event_payload(row[1])
    assert payload.get("route_status") == "READY"
    assert payload.get("selected_source_id") == "baostock"
    assert payload.get("decision") == "route_plan"
    assert "candidates" in payload
    assert payload.get("run_id") == "run-svc"
    assert payload.get("job_id") == spec_job
    assert payload.get("route_plan_id")
    assert payload.get("created_at")


def test_serviceDisabledRoute_writesFetchLog(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    db = tmp_path / "disabled.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    jobs = SyncJobStateMachine(cm)
    reg = SourceRegistry()
    reg.load()
    service = DataSourceService(
        source_registry=reg,
        data_root=tmp_path / "raw",
        job_events=jobs,
    )
    spec = SyncJobSpec(
        run_id="run-dis",
        job_id="job-dis",
        job_type="incremental",
        data_domain="cn_equity_realtime",
        market_id="CN_A",
        source_id="baostock",
        adapter_id="baostock",
        date_start=None,
        date_end=None,
        instrument_id="000001",
        partition_key=None,
        trigger_reason=None,
    )
    job_id = jobs.create_job(spec)
    req = FetchRequest(
        run_id="run-dis",
        source_id="baostock",
        data_domain="cn_equity_realtime",
    )
    with cm.writer() as con:
        result = service.fetch(req, con=con, job_id=job_id)
    assert result.status == "DISABLED_SOURCE"
    with cm.writer() as con:
        log_row = con.execute(
            "SELECT status, row_count FROM fetch_log WHERE job_id = ?", [job_id]
        ).fetchone()
    assert log_row is not None
    assert log_row[0] == "DISABLED_SOURCE"
    assert log_row[1] == 0


def test_serviceGuardBlocked_emitsResourceGuardPausedRoutePlan(tmp_path: Path, monkeypatch) -> None:
    from backend.app.core.resource_guard import ResourceSnapshot

    snap = ResourceSnapshot(
        available_memory_gb=0.1,
        disk_free_gb=0.1,
        process_rss_mb=100.0,
        project_size_gb=0.1,
    )

    def _hard_stop(self):
        return Decision.HARD_STOP, "available memory below threshold"

    monkeypatch.setattr(ResourceGuard, "snapshot", lambda self: snap)
    monkeypatch.setattr(ResourceGuard, "check", _hard_stop)

    db = tmp_path / "guard.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    jobs = SyncJobStateMachine(cm)
    reg = SourceRegistry()
    reg.load()
    service = DataSourceService(
        source_registry=reg,
        data_root=tmp_path / "raw",
        job_events=jobs,
    )
    spec = SyncJobSpec(
        run_id="run-guard",
        job_id="job-guard",
        job_type="incremental",
        data_domain="cn_equity_daily_bar",
        market_id="CN_A",
        source_id="baostock",
        adapter_id="baostock",
        date_start=None,
        date_end=None,
        instrument_id="000001",
        partition_key=None,
        trigger_reason=None,
    )
    job_id = jobs.create_job(spec)
    req = FetchRequest(
        run_id="run-guard",
        source_id="baostock",
        data_domain="cn_equity_daily_bar",
    )
    from backend.app.datasources.service import ResourceGuardBlockedError

    with cm.writer() as con:
        try:
            service.fetch(req, con=con, job_id=job_id)
        except ResourceGuardBlockedError as exc:
            assert exc.decision == Decision.HARD_STOP
            assert "RESOURCE_GUARD_PAUSED" in str(exc)
        else:
            raise AssertionError("expected ResourceGuardBlockedError")

    with cm.writer() as con:
        statuses = [
            row[0]
            for row in con.execute(
                """
                SELECT payload_json FROM job_event_log
                WHERE job_id = ? AND event_type = 'ROUTE_PLAN'
                ORDER BY created_at ASC
                """,
                [job_id],
            ).fetchall()
        ]
    assert len(statuses) == 2
    first = parse_event_payload(statuses[0])
    second = parse_event_payload(statuses[1])
    assert first.get("route_status") == "READY"
    assert second.get("route_status") == "RESOURCE_GUARD_PAUSED"
    assert second.get("selected_source_id") is None
    with cm.writer() as con:
        log_count = con.execute(
            "SELECT COUNT(*) FROM fetch_log WHERE job_id = ?", [job_id]
        ).fetchone()[0]
    assert log_count == 0


def test_serviceUserAuthRequiredRoute_writesDisabledFetchLog(tmp_path: Path, monkeypatch) -> None:
    from backend.app.datasources.route_models import SourceRouteCandidate, SourceRoutePlan

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))

    class AuthBlockedPlanner:
        def plan(self, **kwargs):
            return SourceRoutePlan(
                route_plan_id=SourceRoutePlan.new_id(),
                run_id=kwargs["run_id"],
                job_id=kwargs["job_id"],
                data_domain=kwargs["data_domain"],
                operation=kwargs["operation"],
                route_status="USER_AUTH_REQUIRED",
                selected_source_id=None,
                candidates=[
                    SourceRouteCandidate(
                        source_id="qmt_xqshare",
                        role="Primary",
                        enabled=False,
                        allowed_domain=kwargs["data_domain"],
                        capability_declared=True,
                        disabled_reason="user_authorization_required",
                        skip_reason="user_authorization_required",
                    )
                ],
            )

    db = tmp_path / "auth.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    jobs = SyncJobStateMachine(cm)
    reg = SourceRegistry()
    reg.load()
    service = DataSourceService(
        source_registry=reg,
        data_root=tmp_path / "raw",
        route_planner=AuthBlockedPlanner(),
        job_events=jobs,
    )
    spec = SyncJobSpec(
        run_id="run-auth",
        job_id="job-auth",
        job_type="incremental",
        data_domain="cn_equity_realtime",
        market_id="CN_A",
        source_id="qmt_xqshare",
        adapter_id="qmt_xqshare",
        date_start=None,
        date_end=None,
        instrument_id="000001",
        partition_key=None,
        trigger_reason=None,
    )
    job_id = jobs.create_job(spec)
    req = FetchRequest(
        run_id="run-auth",
        source_id="qmt_xqshare",
        data_domain="cn_equity_realtime",
    )
    with cm.writer() as con:
        result = service.fetch(req, con=con, job_id=job_id)
    assert result.status == "DISABLED_SOURCE"
    with cm.writer() as con:
        route_row = con.execute(
            """
            SELECT payload_json FROM job_event_log
            WHERE job_id = ? AND event_type = 'ROUTE_PLAN' LIMIT 1
            """,
            [job_id],
        ).fetchone()
        log_row = con.execute("SELECT status FROM fetch_log WHERE job_id = ?", [job_id]).fetchone()
    assert route_row is not None
    payload = parse_event_payload(route_row[0])
    assert payload.get("route_status") == "USER_AUTH_REQUIRED"
    assert log_row is not None
    assert log_row[0] == "DISABLED_SOURCE"


def test_serviceFetch_recordsSourceOverrideQualityFlag(tmp_path: Path, monkeypatch) -> None:
    """ADV-A2-007: routed source override must be auditable via quality_flags."""
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))

    def fake_create_test_adapter(sid, registry, data_root, **kwargs):
        class ProbeAdapter:
            source_id = sid

            def fetch(self, req, *, con, job_id=None):
                from datetime import UTC, datetime

                from backend.app.datasources.fetch_result import FetchResult

                return FetchResult(
                    run_id=req.run_id,
                    source_id=sid,
                    data_domain=req.data_domain,
                    status="SUCCESS",
                    row_count=1,
                    fetch_time=datetime.now(UTC).isoformat(),
                    raw_file_paths=["/tmp/probe.json"],
                )

        return ProbeAdapter()

    monkeypatch.setattr(
        "backend.app.datasources.adapters.create_test_adapter",
        fake_create_test_adapter,
    )

    db = tmp_path / "override.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    jobs = SyncJobStateMachine(cm)
    reg = SourceRegistry()
    reg.load()
    service = DataSourceService(
        source_registry=reg,
        data_root=tmp_path / "raw",
        job_events=jobs,
    )
    spec = SyncJobSpec(
        run_id="run-ovr",
        job_id="job-ovr",
        job_type="incremental",
        data_domain="cn_equity_daily_bar",
        market_id="CN_A",
        source_id="akshare",
        adapter_id="akshare",
        date_start=None,
        date_end=None,
        instrument_id="000001",
        partition_key=None,
        trigger_reason=None,
    )
    job_id = jobs.create_job(spec)
    req = FetchRequest(
        run_id="run-ovr",
        source_id="akshare",
        data_domain="cn_equity_daily_bar",
    )
    with cm.writer() as con:
        service.fetch(req, con=con, job_id=job_id)
    with cm.writer() as con:
        row = con.execute(
            """
            SELECT payload_json FROM job_event_log
            WHERE job_id = ? AND event_type = 'ROUTE_PLAN' LIMIT 1
            """,
            [job_id],
        ).fetchone()
    assert row is not None
    payload = parse_event_payload(row[0])
    assert payload.get("requested_source_id") == "akshare"
    assert payload.get("selected_source_id") == "baostock"
    assert "REQUESTED_SOURCE_OVERRIDDEN_BY_ROUTE" in (payload.get("quality_flags") or [])
