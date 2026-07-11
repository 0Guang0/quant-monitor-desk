"""数据源服务门面与抓取边界测试（Round2.6 Phase B/C）。

覆盖范围：服务契约步骤顺序、禁止直连适配器工厂、路由事件与 fetch_log 联动。
"""

from __future__ import annotations

from pathlib import Path

from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.service import DataSourceService
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.sync.event_payload import parse_event_payload
from backend.app.sync.jobs import SyncJobSpec, SyncJobStateMachine
from tests.service_path_support import make_fixture_port, seed_activation_base, write_bar_fixture


def _patch_probe_adapter_factory(monkeypatch, *, track_order: list[str] | None = None) -> None:
    def fake_create_test_adapter(sid, registry, data_root, **kwargs):
        if track_order is not None:
            track_order.append("create_adapter")

        class ProbeAdapter:
            source_id = sid

            def fetch(self, req, *, con, job_id=None):
                if track_order is not None:
                    track_order.append("adapter_fetch")
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


def test_serviceFetch_runtimeGateOrder(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：运行时 fetch 闸门实际执行顺序（顺序即契约）
    测试对象：DataSourceService.fetch（monkeypatch guard/adapter）
    目的/目标：datasource_service_contract 步骤顺序为产品契约：guard → enter_fetching → create_adapter → adapter_fetch；成功路径写 ROUTE_PLAN 与 fetch_log
    验证点：order 索引顺序；result=SUCCESS；route_count=1；log_count=1；guard 阻断 outcome 见 test_serviceGuardBlocked_emitsResourceGuardPausedRoutePlan
    失败含义：运行时跳过路由或守卫，与契约步骤不一致
    """
    order: list[str] = []

    def guard_check(self):
        order.append("guard")
        return Decision.OK, ""

    monkeypatch.setattr(ResourceGuard, "check", guard_check)
    _patch_probe_adapter_factory(monkeypatch, track_order=order)

    db = tmp_path / "order.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    jobs = SyncJobStateMachine(cm)
    reg = SourceRegistry()
    reg.load()
    with cm.writer() as con:
        seed_activation_base(con, reg)
    service = DataSourceService(
        source_registry=reg,
        data_root=tmp_path / "raw",
        job_events=jobs,
        staged_fixture_mode=True,
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


def test_servicePreviewRoute_returnsReadyPlan() -> None:
    """覆盖范围：preview_route 只读路由预览
    测试对象：DataSourceService.preview_route
    目的/目标：不触发 fetch 即可得到 READY 计划与 baostock 选中
    验证点：route_status=READY；selected_source_id=baostock
    失败含义：运维预览接口无法判断日线主路径是否可用
    """
    service = DataSourceService()
    plan = service.preview_route(
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
    )
    assert plan.route_status == "READY"
    assert plan.selected_source_id == "baostock"


def test_serviceWritesRoutePlanPayloadBeforeFetch(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：真正拉数前是否先写下路由决策
    测试对象：DataSourceService.fetch + job_event_log
    目的/目标：事后要能还原「当时选了哪条路」，路由计划必须在调适配器之前就落库
    验证点：ROUTE_PLAN 行存在；payload 含 route_status/selected_source_id/candidates/run_id/job_id/route_plan_id/created_at
    失败含义：事后无法重建当时路由决策，故障复盘缺证据
    """
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    db = tmp_path / "svc.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    jobs = SyncJobStateMachine(cm)
    fixture = tmp_path / "bar.json"
    write_bar_fixture(fixture)
    reg = SourceRegistry()
    reg.load()
    with cm.writer() as con:
        seed_activation_base(con, reg)
    service = DataSourceService(
        source_registry=reg,
        data_root=tmp_path / "raw",
        fetch_port=make_fixture_port(fixture),
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
    """覆盖范围：路由被策略禁用时的日志行为
    测试对象：DataSourceService.fetch（cn_equity_realtime 禁用域）
    目的/目标：即使没去拉数，也要留下「被策略拒绝」的记录，不能静默消失
    验证点：result.status=DISABLED_SOURCE；fetch_log 行 status 同、row_count=0
    失败含义：禁用路由无日志，运维无法区分「未跑」与「被策略拒绝」
    """
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
    """覆盖范围：ResourceGuard 阻断时的事件与 fetch_log 行为（route_grade 专测见 test_datasource_route_grade_payload）
    测试对象：DataSourceService.fetch（ResourceGuard HARD_STOP）
    目的/目标：内存等硬指标不达标时应立刻停住，留下暂停事件，且不能假装已经拉过数
    验证点：pytest.raises(ResourceGuardBlockedError, decision=HARD_STOP)；两条 ROUTE_PLAN payload 含 route_status/decision/route_plan_id；第二条 RESOURCE_GUARD_PAUSED 且 selected_source_id=None；fetch_log count=0
    失败含义：守卫阻断仍写 fetch 或缺暂停事件，容量事故无法追溯
    """
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
    with cm.writer() as con:
        seed_activation_base(con, reg)
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
    assert first.get("decision") == "route_plan"
    assert first.get("route_plan_id")
    assert second.get("route_status") == "RESOURCE_GUARD_PAUSED"
    assert second.get("decision") == "route_plan"
    assert second.get("route_plan_id")
    assert second.get("selected_source_id") is None
    with cm.writer() as con:
        log_count = con.execute(
            "SELECT COUNT(*) FROM fetch_log WHERE job_id = ?", [job_id]
        ).fetchone()[0]
    assert log_count == 0


def test_serviceUserAuthRequiredRoute_writesDisabledFetchLog(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：USER_AUTH_REQUIRED 路由写禁用 fetch_log
    测试对象：DataSourceService.fetch（注入 AuthBlockedPlanner）
    目的/目标：缺用户授权时 route 事件标明 USER_AUTH_REQUIRED 且 fetch_log=DISABLED_SOURCE
    验证点：result=DISABLED_SOURCE；ROUTE_PLAN payload；fetch_log status
    失败含义：授权缺失仍尝试 vendor 或无日志，合规审计缺口
    """
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
    """覆盖范围：请求指定源与路由实际选中源不一致时的审计标记
    测试对象：DataSourceService.fetch（请求 akshare，路由选 baostock）
    目的/目标：调用方要的源和系统最终选的源不同时，必须在路由事件里标明，不能悄悄改
    验证点：payload requested_source_id=akshare；selected_source_id=baostock；quality_flags 含 REQUESTED_SOURCE_OVERRIDDEN_BY_ROUTE
    失败含义：静默改源无审计标记，数据血缘与运维预期不一致
    """
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    _patch_probe_adapter_factory(monkeypatch)

    db = tmp_path / "override.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    jobs = SyncJobStateMachine(cm)
    reg = SourceRegistry()
    reg.load()
    with cm.writer() as con:
        seed_activation_base(con, reg)
    service = DataSourceService(
        source_registry=reg,
        data_root=tmp_path / "raw",
        job_events=jobs,
        staged_fixture_mode=True,
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
