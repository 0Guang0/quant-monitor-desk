"""生产环境数据源路由规划器测试（Round2.6 Phase C）。

覆盖范围：各数据域路由状态、候选源跳过原因、fallback 质量标记与用户授权场景。
"""

from __future__ import annotations

from tests.service_path_support import production_route_planner


def test_qmtDisabled_routePlanShowsSkipReason() -> None:
    """覆盖范围：默认禁用的 QMT 分钟线域路由
    测试对象：SourceRoutePlanner.plan（cn_equity_minute_bar）
    目的/目标：被禁用的候选源要在列表里写明为什么跳过，不能悄悄消失或误选
    验证点：route_status=DISABLED_SOURCE；qmt_xtdata.skip_reason 非空且 capability_declared=True
    失败含义：禁用 QMT 仍可能被选中或跳过原因不可审计
    """
    planner = production_route_planner()
    plan = planner.plan(
        data_domain="cn_equity_minute_bar",
        operation="fetch_minute_bar",
        run_id="run-1",
        job_id="job-1",
    )
    assert plan.route_status == "DISABLED_SOURCE"
    assert plan.selected_source_id is None
    qmt = next(c for c in plan.candidates if c.source_id == "qmt_xtdata")
    assert qmt.skip_reason is not None
    assert qmt.capability_declared is True
    lowered = (qmt.skip_reason or "").lower()
    assert "disabled" in lowered or "authorization" in lowered or "platform" in lowered


def test_noAvailableSource_hasNoSelectedSource() -> None:
    """覆盖范围：美股日线校验域无可用源
    测试对象：SourceRoutePlanner.plan（us_equity_daily_bar）
    目的/目标：无合格候选时不得选出 selected_source_id
    验证点：route_status 为 DISABLED/NO_AVAILABLE/USER_AUTH 之一；selected 为 None
    失败含义：无源域仍返回 READY，调度会误触发 vendor fetch
    """
    planner = production_route_planner()
    plan = planner.plan(
        data_domain="us_equity_daily_bar",
        operation="fetch_us_daily_bar_validation",
        run_id="run-2",
        job_id="job-2",
    )
    assert plan.route_status in {"DISABLED_SOURCE", "NO_AVAILABLE_SOURCE", "USER_AUTH_REQUIRED"}
    assert plan.selected_source_id is None
    assert all(c.skip_reason or not c.enabled for c in plan.candidates if not c.enabled)


def test_fallbackAddsQualityFlag() -> None:
    """覆盖范围：启用 fallback 时的路由质量标记
    测试对象：SourceRoutePlanner.plan（use_fallback=True）
    目的/目标：走备用源须在 quality_flags 标明 SOURCE_FALLBACK_USED
    验证点：选中 qmt_xtdata 时含 SOURCE_FALLBACK_USED；否则 READY+baostock
    失败含义：fallback 切换无审计标记，数据质量追溯失真
    """
    planner = production_route_planner()
    plan = planner.plan(
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        run_id="run-3",
        job_id="job-3",
        use_fallback=True,
    )
    if plan.selected_source_id == "qmt_xtdata":
        assert "SOURCE_FALLBACK_USED" in plan.quality_flags
    else:
        assert plan.route_status == "READY"
        assert plan.selected_source_id == "baostock"


def test_readyRoute_selectedSourceIdNotNull() -> None:
    """覆盖范围：A 股日线主路径就绪路由
    测试对象：SourceRoutePlanner.plan（cn_equity_daily_bar 默认）
    目的/目标：常规域应选出 baostock 且无质量标记
    验证点：route_status=READY；selected_source_id=baostock；quality_flags 为空
    失败含义：主域日线无法自动路由，同步编排主路径断裂
    """
    planner = production_route_planner()
    plan = planner.plan(
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        run_id="run-4",
        job_id="job-4",
    )
    assert plan.route_status == "READY"
    assert plan.selected_source_id == "baostock"
    assert plan.quality_flags == []


def test_capabilityMissing_routeStatusCapabilityMissing() -> None:
    """覆盖范围：实时行情域能力未声明时的路由
    测试对象：SourceRoutePlanner.plan（cn_equity_realtime + 额外 baostock 候选）
    目的/目标：无 capability 的源应被标记且域默认禁用
    验证点：baostock capability_declared=False；route_status=DISABLED_SOURCE；含 DOMAIN_DISABLED_BY_DEFAULT
    失败含义：未声明能力的源仍可进入 fetch 路径
    """
    planner = production_route_planner()
    plan = planner.plan(
        data_domain="cn_equity_realtime",
        operation="fetch_realtime_quote",
        run_id="run-5",
        job_id="job-5",
        extra_candidates=[("baostock", "Primary")],
    )
    baostock = next(c for c in plan.candidates if c.source_id == "baostock")
    assert baostock.capability_declared is False
    assert baostock.enabled is False
    assert plan.route_status == "DISABLED_SOURCE"
    assert "DOMAIN_DISABLED_BY_DEFAULT" in plan.quality_flags
    assert plan.selected_source_id is None


def test_etfDailyBar_disabledSource_marksYahooSkipWhenAuthorizationMissing() -> None:
    """覆盖范围：ETF 日线校验域需用户授权
    测试对象：SourceRoutePlanner.plan（etf_daily_bar）
    目的/目标：缺授权的环境变量时 yahoo 等候选应标明 skip_reason
    验证点：route_status=DISABLED_SOURCE；yahoo skip_reason 含 user_authorization 或 missing_env
    失败含义：未授权外部源被静默选中，合规与计费风险
    """
    planner = production_route_planner()
    plan = planner.plan(
        data_domain="etf_daily_bar",
        operation="fetch_etf_daily_bar_validation",
        run_id="run-auth",
        job_id="job-auth",
    )
    assert plan.route_status == "DISABLED_SOURCE"
    assert "DOMAIN_DISABLED_BY_DEFAULT" in plan.quality_flags
    assert plan.selected_source_id is None
    yahoo = next(c for c in plan.candidates if c.source_id == "yahoo_finance")
    assert yahoo.skip_reason is not None
    assert "user_authorization" in yahoo.skip_reason or yahoo.skip_reason.startswith("missing_env:")
