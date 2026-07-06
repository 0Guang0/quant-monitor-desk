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
from tests.contract_gate_support import (
    ALLOWED_ADAPTER_FACTORY_PATHS,
    PROJECT_ROOT,
    SERVICE_CONTRACT,
    collect_imports,
    load_yaml,
    scan_package_for_create_adapter,
)
from tests.service_path_support import make_fixture_port, write_bar_fixture

BACKEND_APP = PROJECT_ROOT / "backend" / "app"
RUNNERS = BACKEND_APP / "sync" / "runners.py"
CONCRETE_ADAPTER_PREFIX = "backend.app.datasources.adapters."


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


def test_apiAndAgentCannotImportAdapterFactory() -> None:
    """覆盖范围：生产代码不得绕过服务门面直接创建适配器
    测试对象：contract forbidden_direct_callers 包扫描
    目的/目标：API 和 agent 层只能通过统一服务拉数，不能自己 import 适配器工厂
    验证点：violations 列表为空
    失败含义：调用方可绕过服务门面直接建 adapter，边界审计失效
    """
    contract = load_yaml(SERVICE_CONTRACT)
    forbidden_pkgs = contract.get("call_boundaries", {}).get("forbidden_direct_callers") or []
    violations: list[str] = []
    for pkg in forbidden_pkgs:
        pkg_path = pkg.replace("backend.app.", "")
        violations.extend(scan_package_for_create_adapter(pkg_path))
    assert violations == [], (
        "production modules must not import create_adapter directly: " + "; ".join(violations)
    )


def test_serviceBuildsRouteBeforeFetch() -> None:
    """覆盖范围：服务契约声明的抓取步骤顺序
    测试对象：SERVICE_CONTRACT public_methods.fetch.required_steps
    目的/目标：必须先定路由、过资源守卫，最后才创建适配器并真正拉数
    验证点：steps 列表与契约冻结顺序完全一致（load_source_registry → … → ensure_fetch_log_or_failure_event）
    失败含义：文档与实现步骤错位，gate 无法证明先路由后抓取
    """
    contract = load_yaml(SERVICE_CONTRACT)
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


def test_datasourceServiceContract_statusIsActive() -> None:
    """覆盖范围：DataSourceService 契约 status 升格（R3H-10 S10-02）
    测试对象：specs/contracts/datasource_service_contract.yaml status 字段
    目的/目标：C2 SSOT 契约须为 active，禁止长期 draft 漂移
    验证点：status == active
    失败含义：契约仍为 draft，审计无法认定 DataSourceService 为产品 fetch SSOT
    """
    contract = load_yaml(SERVICE_CONTRACT)
    assert contract.get("status") == "active"


def test_datasourceServiceContract_requiredTestsIncludeR3h10Gate() -> None:
    """覆盖范围：契约 required_tests 含 R3H-10 行为门禁用例
    测试对象：datasource_service_contract.yaml required_tests
    目的/目标：机器可读绑定 active 契约与 S10-01/03/04/05 gate 测试
    验证点：含 status gate 与 r3h10 关键行为测名
    失败含义：升格 gate 或行为测未登记，后续回归可删而不触发契约扫描
    """
    contract = load_yaml(SERVICE_CONTRACT)
    required = set(contract.get("required_tests") or [])
    for name in (
        "tests/test_datasource_service.py::test_datasourceServiceContract_statusIsActive",
        "tests/test_sync_orchestrator.py::test_r3h10S10_01_incremental_requiresDatasourceServiceInProductionProfile",
        "tests/test_sync_orchestrator.py::test_r3h10S10_01_backfill_requiresDatasourceServiceInProductionProfile",
        "tests/test_sync_orchestrator.py::test_r3h10S10_01_reconcile_adapterBypassFailClosedPerAdr025",
    ):
        assert name in required


def test_serviceFetch_runtimeGateOrder(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：运行时 fetch 闸门实际执行顺序
    测试对象：DataSourceService.fetch（monkeypatch guard/adapter）
    目的/目标：guard → enter_fetching → create_adapter → adapter_fetch，且写 ROUTE_PLAN 与 fetch_log
    验证点：order 索引顺序；result=SUCCESS；route_count=1；log_count=1
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


def test_serviceContract_declaresFetchGateOrder() -> None:
    """覆盖范围：契约步骤与专用测试一致
    测试对象：test_serviceBuildsRouteBeforeFetch 委托
    目的/目标：契约测试与步骤列表测试保持同一断言源
    验证点：调用 test_serviceBuildsRouteBeforeFetch 不失败
    失败含义：重复门禁分叉，契约变更只改一处仍可能漏检
    """
    test_serviceBuildsRouteBeforeFetch()


def test_forbiddenDirectCallers_includesSyncRunners_andScanIsContractDriven() -> None:
    """覆盖范围：同步编排 runner 不得直连适配器工厂
    测试对象：forbidden_direct_callers + scan_package_for_create_adapter('sync/runners')
    目的/目标：定时同步任务也应走服务门面，不能自己 import 工厂
    验证点：backend.app.sync.runners 在 forbidden；runners 扫描 violations 为空
    失败含义：同步 runner 可绕过服务直接建 adapter
    """
    contract = load_yaml(SERVICE_CONTRACT)
    forbidden = contract.get("call_boundaries", {}).get("forbidden_direct_callers") or []
    assert "backend.app.sync.runners" in forbidden
    assert scan_package_for_create_adapter("sync/runners") == []


def test_createAdapterImports_onlyUnderTests() -> None:
    """覆盖范围：create_adapter 仅允许出现在工厂模块路径
    测试对象：backend/app/**/*.py import 扫描（排除 ALLOWED_ADAPTER_FACTORY_PATHS）
    目的/目标：除 datasources 工厂外任何生产代码不得 import create_adapter
    验证点：violations 列表为空
    失败含义：隐藏入口可实例化任意 adapter，服务边界名存实亡
    """
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
    """覆盖范围：sync/runners.py 导入洁净性
    测试对象：collect_imports(RUNNERS)
    目的/目标：runner 不得 import create_adapter 或具体 Adapter 类
    验证点：imports 无 create_adapter、无 adapters 包具体 Adapter
    失败含义：runner 与 vendor 适配器耦合，无法统一经 service fetch
    """
    imports = collect_imports(RUNNERS)
    assert "create_adapter" not in imports
    assert not any(imp.startswith(CONCRETE_ADAPTER_PREFIX) for imp in imports)
    assert not any(imp.endswith("Adapter") and "adapters" in imp for imp in imports)


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
    """覆盖范围：机器资源不足时的路由与日志行为
    测试对象：DataSourceService.fetch（ResourceGuard HARD_STOP）
    目的/目标：内存等硬指标不达标时应立刻停住，留下暂停事件，且不能假装已经拉过数
    验证点：pytest.raises(ResourceGuardBlockedError, decision=HARD_STOP, 含 RESOURCE_GUARD_PAUSED)；两条 ROUTE_PLAN（READY 后 RESOURCE_GUARD_PAUSED）；fetch_log count=0
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
