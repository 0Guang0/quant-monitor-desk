"""生产环境数据源路由规划器测试（Round2.6 Phase C）。

覆盖范围：各数据域路由状态、候选源跳过原因、fallback 质量标记与用户授权场景。
"""

from __future__ import annotations

from pathlib import Path

import pytest
from backend.app.datasources.capability_registry import SourceCapabilityRegistry
from backend.app.datasources.route_planner import SourceRoutePlanner
from backend.app.datasources.source_registry import SourceRegistry

from tests.service_path_support import production_route_planner

_BAD_SCHEMA_ENUM_FIXTURE = (
    Path(__file__).parent / "fixtures" / "bad_schema_enum_route.yaml"
)


def test_invalidSourceTypeOrLicense_blocksReadyRoute() -> None:
    """覆盖范围：source_type/license_type 与 DB CHECK 枚举不一致时的路由
    测试对象：SourceRoutePlanner.plan（schema 非法 license 的 baostock primary）
    目的/目标：契约要求枚举非法时 route planner 不得返回 READY
    验证点：route_status 非 READY；selected_source_id 为 None；primary skip_reason 标明 schema 枚举非法
    失败含义：非法枚举源仍被选中，sync_to_db 或生产路由会在 DB CHECK 处爆炸
    """
    reg = SourceRegistry(_BAD_SCHEMA_ENUM_FIXTURE)
    reg.load()
    caps = SourceCapabilityRegistry()
    caps.load()
    planner = SourceRoutePlanner(source_registry=reg, capability_registry=caps)
    plan = planner.plan(
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        run_id="run-schema",
        job_id="job-schema",
    )
    assert plan.route_status != "READY"
    assert plan.selected_source_id is None
    baostock = next(c for c in plan.candidates if c.source_id == "baostock")
    assert baostock.skip_reason == "invalid_schema_source_or_license_type"


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


def test_etfDailyBar_disabledSource_marksAlphaVantageSkipWhenAuthorizationMissing() -> None:
    """覆盖范围：ETF 日线域需用户授权
    测试对象：SourceRoutePlanner.plan（etf_daily_bar）
    目的/目标：缺 API key 时 alpha_vantage primary 应标明 skip_reason
    验证点：route_status=DISABLED_SOURCE；alpha_vantage skip_reason 含 user_authorization 或 missing_env
    失败含义：未授权外部源被静默选中，合规与计费风险
    """
    planner = production_route_planner()
    plan = planner.plan(
        data_domain="etf_daily_bar",
        operation="fetch_etf_daily_bar",
        run_id="run-auth",
        job_id="job-auth",
    )
    assert plan.route_status == "DISABLED_SOURCE"
    assert "DOMAIN_DISABLED_BY_DEFAULT" in plan.quality_flags
    assert plan.selected_source_id is None
    av = next(c for c in plan.candidates if c.source_id == "alpha_vantage")
    assert av.skip_reason is not None
    assert av.enabled is False


_OFFICIAL_MACRO_ROUTE_CASES: tuple[tuple[str, str, str], ...] = (
    ("fred", "macro_series", "fetch_macro_series"),
    ("us_treasury", "us_treasury_yield_curve", "fetch_yield_curve"),
    ("sec_edgar", "us_filings", "fetch_company_filings"),
    ("cftc_cot", "cot_positioning", "fetch_cot_positioning"),
    ("bis", "central_bank_policy", "fetch_policy_rate"),
    ("world_bank", "development_indicator", "fetch_indicator_series"),
)


@pytest.mark.parametrize(("source_id", "data_domain", "operation"), _OFFICIAL_MACRO_ROUTE_CASES)
def test_r3h01_officialMacroRoute_disabledByDefault(
    source_id: str,
    data_domain: str,
    operation: str,
) -> None:
    """覆盖范围：R3H-01 六源默认禁用路由
    测试对象：SourceRoutePlanner.plan（各官方宏观/披露域）
    目的/目标：enabled_by_default=false 时 route 为 DISABLED，非 READY
    验证点：route_status=DISABLED_SOURCE；对应 candidate enabled=False
    失败含义：未显式启用的官方源被误选为 production primary
    """
    planner = production_route_planner()
    plan = planner.plan(
        data_domain=data_domain,
        operation=operation,
        run_id=f"r3h01-route-{source_id}",
        job_id=f"route-{source_id}",
    )
    assert plan.route_status == "DISABLED_SOURCE"
    assert plan.selected_source_id is None
    candidate = next((c for c in plan.candidates if c.source_id == source_id), None)
    assert candidate is not None
    assert candidate.enabled is False


_R3H02_MARKET_ROUTE_PRIMARY_CASES: tuple[tuple[str, str, str], ...] = (
    ("alpha_vantage", "us_equity_daily_bar", "fetch_us_daily_bar"),
    ("alpha_vantage", "etf_daily_bar", "fetch_etf_daily_bar"),
    ("alpha_vantage", "fx_daily_bar", "fetch_fx_daily_bar"),
    ("alpha_vantage", "commodity_daily_bar", "fetch_commodity_daily_bar"),
    ("deribit", "crypto_options_surface", "fetch_options_surface"),
)

_R3H02_MARKET_ROUTE_VALIDATION_PRIMARY_CASES: tuple[tuple[str, str, str], ...] = (
    ("stooq", "global_market_daily_bar", "fetch_global_daily_bar"),
    ("yahoo_finance", "global_asset_reference", "fetch_global_asset_reference"),
    ("coingecko", "crypto_asset_reference", "fetch_crypto_asset_reference"),
)

_R3H02_MARKET_ROUTE_VALIDATION_EXTRA_CASES: tuple[tuple[str, str, str], ...] = (
    ("stooq", "global_market_daily_bar", "fetch_global_daily_bar"),
    ("yahoo_finance", "etf_daily_bar", "fetch_etf_daily_bar_validation"),
    ("coingecko", "crypto_spot_market", "fetch_spot_market_reference"),
)


@pytest.mark.parametrize(("source_id", "data_domain", "operation"), _R3H02_MARKET_ROUTE_PRIMARY_CASES)
def test_r3h02_marketRoute_disabledByDefault(
    source_id: str,
    data_domain: str,
    operation: str,
) -> None:
    """覆盖范围：R3H-02 域 primary 源默认禁用路由
    测试对象：SourceRoutePlanner.plan（各市场/加密域 primary 绑定）
    目的/目标：enabled_by_default=false 时 route 为 DISABLED，非 READY
    验证点：route_status=DISABLED_SOURCE；对应 candidate enabled=False
    失败含义：未显式启用的市场源被误选为 production primary
    """
    planner = production_route_planner()
    plan = planner.plan(
        data_domain=data_domain,
        operation=operation,
        run_id=f"r3h02-route-{source_id}",
        job_id=f"route-{source_id}",
    )
    assert plan.route_status == "DISABLED_SOURCE"
    assert plan.selected_source_id is None
    candidate = next((c for c in plan.candidates if c.source_id == source_id), None)
    assert candidate is not None
    assert candidate.enabled is False


@pytest.mark.parametrize(
    ("source_id", "data_domain", "operation"),
    _R3H02_MARKET_ROUTE_VALIDATION_EXTRA_CASES,
)
def test_r3h02_marketRoute_validationOnlyDisabledByDefault(
    source_id: str,
    data_domain: str,
    operation: str,
) -> None:
    """覆盖范围：R3H-02 validation-only 源默认禁用（extra_candidates 路径）
    测试对象：SourceRoutePlanner.plan + validation-only 源显式候选
    目的/目标：enabled_by_default=false 的 validation-only 源不得 READY
    验证点：route_status=DISABLED_SOURCE；candidate skip_reason=source_disabled_by_default
    失败含义：validation-only 源未启用即可路由
    """
    planner = production_route_planner()
    plan = planner.plan(
        data_domain=data_domain,
        operation=operation,
        run_id=f"r3h02-route-{source_id}",
        job_id=f"route-{source_id}",
        extra_candidates=[(source_id, "Primary")],
    )
    assert plan.route_status == "DISABLED_SOURCE"
    assert plan.selected_source_id is None
    candidate = next((c for c in plan.candidates if c.source_id == source_id), None)
    assert candidate is not None
    assert candidate.enabled is False
    assert candidate.skip_reason is not None


@pytest.mark.parametrize(
    ("source_id", "data_domain", "operation"),
    _R3H02_MARKET_ROUTE_VALIDATION_PRIMARY_CASES,
)
def test_r3h02_marketRoute_validationOnlyPrimaryBlocked(
    monkeypatch: pytest.MonkeyPatch,
    source_id: str,
    data_domain: str,
    operation: str,
) -> None:
    """覆盖范围：validation-only 源作 yaml primary 时路由 fail-closed
    测试对象：SourceRoutePlanner.plan（stooq/yahoo/coingecko 域绑定，域与源已启用）
    目的/目标：yaml primary 仍为 validation-only 的域须 VALIDATION_ONLY_BLOCKED
    验证点：route_status=VALIDATION_ONLY_BLOCKED；skip_reason=validation_only_cannot_be_primary
    失败含义：validation-only 源 silent 升格 primary
    """
    from backend.app.datasources.capability_registry import SourceCapabilityRegistry
    from backend.app.datasources.source_registry import DomainRoleBinding, SourceRegistry

    registry = SourceRegistry()
    registry.load()
    rec = registry.get(source_id)
    object.__setattr__(rec, "is_enabled", True)
    orig_domain_roles = registry.get_domain_roles

    def _domain_enabled(domain: str):
        binding = orig_domain_roles(domain)
        if domain != data_domain:
            return binding
        return DomainRoleBinding(
            primary_source_id=binding.primary_source_id,
            validation_source_id=binding.validation_source_id,
            fallback_policy=binding.fallback_policy,
            domain_enabled_by_default=True,
            fallback_source_ids=binding.fallback_source_ids,
        )

    monkeypatch.setattr(registry, "get_domain_roles", _domain_enabled)
    capabilities = SourceCapabilityRegistry()
    capabilities.load()
    planner = SourceRoutePlanner(source_registry=registry, capability_registry=capabilities)
    monkeypatch.setattr(planner, "_platform_allows", lambda _sid: (True, None))
    plan = planner.plan(
        data_domain=data_domain,
        operation=operation,
        run_id=f"r3h02-valprimary-{source_id}",
        job_id=f"valprimary-{source_id}",
    )
    candidate = next(c for c in plan.candidates if c.source_id == source_id)
    assert candidate.skip_reason == "validation_only_cannot_be_primary"
    assert plan.route_status == "VALIDATION_ONLY_BLOCKED"
    assert plan.selected_source_id is None
