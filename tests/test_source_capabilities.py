"""数据源能力与适配器域契约测试（Round2.6 Phase B/C）。

覆盖范围：source_registry 与 source_capabilities 对齐、适配器域映射、运行时能力断言。
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Any

import pytest
from backend.app.datasources.capability_registry import (
    ADAPTER_DOMAIN_COMPATIBILITY_MAP,
    OperationDisabledError,
    SourceCapabilityRegistry,
    UnknownCapabilityError,
)

from tests.contract_gate_support import PROJECT_ROOT, load_yaml

SOURCE_REGISTRY = PROJECT_ROOT / "specs/datasource_registry/source_registry.yaml"
SOURCE_CAPABILITIES = PROJECT_ROOT / "specs/datasource_registry/source_capabilities.yaml"


def load_source_registry() -> dict[str, Any]:
    return load_yaml(SOURCE_REGISTRY)


def load_source_capabilities() -> dict[str, Any]:
    return load_yaml(SOURCE_CAPABILITIES)


def capability_domains_for_source(capabilities: dict[str, Any], source_id: str) -> set[str]:
    entry = (capabilities.get("sources") or {}).get(source_id) or {}
    return set((entry.get("domains") or {}).keys())


def iter_production_adapter_classes():
    """Yield (source_id, adapter_class) for concrete adapter modules."""
    import backend.app.datasources.adapters as adapters_pkg

    skip = {
        "fetch_port",
        "skeleton_base",
        "__init__",
    }
    for mod_info in pkgutil.iter_modules(adapters_pkg.__path__, adapters_pkg.__name__ + "."):
        stem = mod_info.name.rsplit(".", 1)[-1]
        if stem in skip:
            continue
        mod = importlib.import_module(mod_info.name)
        for attr in dir(mod):
            obj = getattr(mod, attr)
            if (
                isinstance(obj, type)
                and hasattr(obj, "source_id")
                and hasattr(obj, "supported_domains")
                and attr.endswith("Adapter")
            ):
                yield getattr(obj, "source_id"), obj


def test_everyAllowedDomain_hasCapabilityDeclaration() -> None:
    """覆盖范围：注册表允许的域必须在能力清单里有对应声明
    测试对象：仓库内 source_registry.yaml 各源的 allowed_domains
    目的/目标：路由能用的域，能力文件里也得写清楚，否则拉数前无法判断是否支持
    验证点：missing 列表为空
    失败含义：路由/planner 可引用未声明能力的域，fetch 前无法 fail-closed
    """
    registry = load_source_registry()
    capabilities = load_source_capabilities()
    missing: list[str] = []
    for source in registry.get("sources") or []:
        source_id = source["source_id"]
        declared = capability_domains_for_source(capabilities, source_id)
        for domain in source.get("allowed_domains") or []:
            if domain not in declared:
                missing.append(f"{source_id}:{domain}")
    assert missing == [], f"allowed_domains missing capability declarations: {missing}"


def test_unknownSourceInRegistry_mustHaveCapabilityOrProposedStatus() -> None:
    """覆盖范围：注册表中的源在能力清单中有条目
    测试对象：source_registry sources 与 source_capabilities sources 键集合
    目的/目标：不得存在「已注册但无能力记录」的孤儿源
    验证点：每个 registry source_id 均在 cap_sources 中
    失败含义：新源只写 registry 未写 capabilities，路由矩阵缺行
    """
    registry = load_source_registry()
    capabilities = load_source_capabilities()
    cap_sources = set((capabilities.get("sources") or {}).keys())
    for source in registry.get("sources") or []:
        source_id = source["source_id"]
        if source_id not in cap_sources:
            raise AssertionError(
                f"source_registry source {source_id!r} has no entry in source_capabilities.yaml"
            )


def test_proposedDisabledSource_qmtXqshare_notEnabledByDefault() -> None:
    """覆盖范围：qmt_xqshare 提议禁用源默认策略
    测试对象：source_capabilities.yaml 中 qmt_xqshare 条目
    目的/目标：status=proposed_disabled_source 且所有操作 enabled_by_default=False
    验证点：status 字段与各 operation.enabled_by_default 均为 False
    失败含义：未审批的 QMT 共享源默认可调度，合规风险
    """
    capabilities = load_source_capabilities()
    entry = (capabilities.get("sources") or {}).get("qmt_xqshare") or {}
    assert entry.get("status") == "proposed_disabled_source"
    for domain_cfg in (entry.get("domains") or {}).values():
        for op in (domain_cfg.get("operations") or {}).values():
            assert op.get("enabled_by_default") is False


def test_adapterSupportedDomains_reconciledToCapabilityRegistryOrCompatibilityMap() -> None:
    """覆盖范围：适配器声明的域与能力清单是否对得上
    测试对象：各生产 Adapter.supported_domains + ADAPTER_DOMAIN_COMPATIBILITY_MAP
    目的/目标：代码里写的支持域，要么能力文件直声明，要么经兼容映射落到已声明域
    验证点：mismatches 列表为空
    失败含义：适配器声明的域无能力背书，运行时 DomainNotAllowed 与契约不一致
    """
    capabilities = load_source_capabilities()
    mismatches: list[str] = []
    for source_id, adapter_cls in iter_production_adapter_classes():
        compat = ADAPTER_DOMAIN_COMPATIBILITY_MAP.get(source_id, {})
        declared = capability_domains_for_source(capabilities, source_id)
        for legacy_domain in adapter_cls.supported_domains:
            registry_domain = compat.get(legacy_domain, legacy_domain)
            if registry_domain not in declared:
                mismatches.append(
                    f"{source_id}: adapter domain {legacy_domain!r} "
                    f"maps to {registry_domain!r} but capability missing"
                )
    assert mismatches == [], (
        "adapter supported_domains not reconciled to capabilities; "
        f"update adapters or ADAPTER_DOMAIN_COMPATIBILITY_MAP: {mismatches}"
    )


def test_compatibilityMap_doesNotEnableNewSources() -> None:
    """覆盖范围：兼容映射不得引入注册表外源
    测试对象：ADAPTER_DOMAIN_COMPATIBILITY_MAP 键集合
    目的/目标：映射表只能覆盖已注册 source_id，不能凭空启用新源
    验证点：COMPATIBILITY_MAP 键是 registry_ids 子集
    失败含义：未注册源经映射表被隐式启用，审计边界破裂
    """
    registry_ids = {s["source_id"] for s in load_source_registry().get("sources") or []}
    assert set(ADAPTER_DOMAIN_COMPATIBILITY_MAP.keys()).issubset(registry_ids)


def test_unknownCapability_rejectedBeforeFetch() -> None:
    """覆盖范围：能力清单使用的域命名规范
    测试对象：source_capabilities 全库域键集合
    目的/目标：权威能力域应使用具体业务域名，不能把旧版抽象域名当正式标准
    验证点：market_bar_1d 不在 all_domains；cn_equity_daily_bar 在
    失败含义：抽象域与具体域混用，路由与 adapter 契约漂移
    """
    capabilities = load_source_capabilities()
    all_domains: set[str] = set()
    for _source_id, entry in (capabilities.get("sources") or {}).items():
        all_domains.update((entry.get("domains") or {}).keys())
    assert "market_bar_1d" not in all_domains, (
        "legacy abstract domain must not be declared as capability authority"
    )
    assert "cn_equity_daily_bar" in all_domains


def test_compatibilityMap_coversEveryProductionAdapter() -> None:
    """覆盖范围：每个生产适配器的遗留域名映射完整性
    测试对象：iter_production_adapter_classes + ADAPTER_DOMAIN_COMPATIBILITY_MAP
    目的/目标：适配器代码里仍用旧域名的，要么能力文件已直声明，要么兼容表里有映射项
    验证点：每个 legacy_domain 要么在 declared 要么在 compat
    失败含义：遗留域名无映射且无直声明，对账测试无法闭环
    """
    capabilities = load_source_capabilities()
    for source_id, adapter_cls in iter_production_adapter_classes():
        compat = ADAPTER_DOMAIN_COMPATIBILITY_MAP.get(source_id, {})
        declared = capability_domains_for_source(capabilities, source_id)
        for legacy_domain in adapter_cls.supported_domains:
            if legacy_domain in declared:
                continue
            if legacy_domain not in compat:
                raise AssertionError(
                    f"{source_id}: legacy domain {legacy_domain!r} requires "
                    "ADAPTER_DOMAIN_COMPATIBILITY_MAP entry"
                )


def test_capabilityRegistry_assertSourceDomainOperation_acceptsKnown() -> None:
    """覆盖范围：已知源-域-操作三元组校验通过
    测试对象：SourceCapabilityRegistry.assert_source_domain_operation
    目的/目标：baostock + cn_equity_daily_bar + fetch_daily_bar 为合法组合
    验证点：调用不抛异常
    失败含义：主路径日线能力被误拒，同步无法启动
    """
    reg = SourceCapabilityRegistry()
    reg.load()
    reg.assert_source_domain_operation("baostock", "cn_equity_daily_bar", "fetch_daily_bar")


def test_capabilityRegistry_assertSourceDomainOperation_rejectsUnknown() -> None:
    """覆盖范围：未声明的源-域-操作组合应被拒绝
    测试对象：SourceCapabilityRegistry.assert_source_domain_operation
    目的/目标：baostock 不支持实时行情域，这种组合不应放行到拉数阶段
    验证点：baostock + cn_equity_realtime + fetch_daily_bar 时 pytest.raises(UnknownCapabilityError)
    失败含义：无能力组合仍可进入 fetch，vendor 调用浪费与审计缺口
    """
    reg = SourceCapabilityRegistry()
    reg.load()
    with pytest.raises(UnknownCapabilityError):
        reg.assert_source_domain_operation("baostock", "cn_equity_realtime", "fetch_daily_bar")


def test_capabilityRegistry_resolveRegistryDomain_passthroughWhenNoAlias() -> None:
    """覆盖范围：无别名时域解析应原样透传
    测试对象：SourceCapabilityRegistry.resolve_registry_domain / is_capability_declared
    目的/目标：没有遗留别名映射时，输入什么域名就按什么域名查能力
    验证点：resolve 返回 cn_equity_daily_bar；is_capability_declared(baostock, cn_equity_daily_bar)=True
    失败含义：域解析错误导致 capability 查询误报未声明
    """
    reg = SourceCapabilityRegistry()
    reg.load()
    assert reg.resolve_registry_domain("baostock", "cn_equity_daily_bar") == "cn_equity_daily_bar"
    assert reg.is_capability_declared("baostock", "cn_equity_daily_bar") is True


def test_proposedDisabledSource_tdxPytdx_notEnabledByDefault() -> None:
    """覆盖范围：tdx_pytdx 提议禁用源默认策略
    测试对象：source_capabilities.yaml 中 tdx_pytdx 条目
    目的/目标：与 qmt_xqshare 同样 status=proposed_disabled_source 且操作默认关闭
    验证点：status 与各 operation.enabled_by_default 均为 False
    失败含义：未审批 TDX 源默认可用，生产误连本地行情
    """
    capabilities = load_source_capabilities()
    entry = (capabilities.get("sources") or {}).get("tdx_pytdx") or {}
    assert entry.get("status") == "proposed_disabled_source"
    for domain_cfg in (entry.get("domains") or {}).values():
        for op in (domain_cfg.get("operations") or {}).values():
            assert op.get("enabled_by_default") is False


def test_capabilityRegistry_rejectsTdxPytdxProposedDisabledSource() -> None:
    """覆盖范围：tdx_pytdx 提议禁用源运行时拒绝
    测试对象：SourceCapabilityRegistry.assert_source_domain_operation（tdx_pytdx）
    目的/目标：A8-G1 — 未审批 TDX 源 fetch_daily_bar 应 OperationDisabledError
    验证点：tdx_pytdx + cn_equity_daily_bar + fetch_daily_bar 时 pytest.raises(OperationDisabledError)
    失败含义：提议禁用 TDX 仍可通过 registry 断言被调度
    """
    reg = SourceCapabilityRegistry()
    reg.load()
    with pytest.raises(OperationDisabledError):
        reg.assert_source_domain_operation(
            "tdx_pytdx", "cn_equity_daily_bar", "fetch_daily_bar"
        )


def test_capabilityRegistry_rejectsProposedDisabledSource() -> None:
    """覆盖范围：提议禁用源在运行时的拒绝逻辑
    测试对象：SourceCapabilityRegistry.assert_source_domain_operation（qmt_xqshare）
    目的/目标：即使 YAML 里写了能力条目，未审批的源也不应被真正调度
    验证点：qmt_xqshare + cn_equity_realtime + fetch_realtime_quote_remote 时 pytest.raises(OperationDisabledError)
    失败含义：提议禁用源仍可通过 registry 断言，绕过策略闸门
    """
    reg = SourceCapabilityRegistry()
    reg.load()
    with pytest.raises(OperationDisabledError):
        reg.assert_source_domain_operation(
            "qmt_xqshare", "cn_equity_realtime", "fetch_realtime_quote_remote"
        )


R3H01_OFFICIAL_MACRO_SOURCES: tuple[str, ...] = (
    "fred",
    "us_treasury",
    "sec_edgar",
    "cftc_cot",
    "bis",
    "world_bank",
)


def test_r3h01_officialMacroSources_readyWithEvidenceStatus() -> None:
    """覆盖范围：R3H-01 六源 registry 终态
    测试对象：source_capabilities.yaml 中 fred/us_treasury/sec_edgar/cftc_cot/bis/world_bank
    目的/目标：六源不得停留在 proposed_disabled_source，须 READY_WITH_EVIDENCE
    验证点：status==READY_WITH_EVIDENCE；replay_fixture_path 非空
    失败含义：Batch 3H 官方源仍以 vague proposed-disabled 占位
    """
    capabilities = load_source_capabilities()
    sources = capabilities.get("sources") or {}
    for source_id in R3H01_OFFICIAL_MACRO_SOURCES:
        entry = sources.get(source_id) or {}
        assert entry.get("status") == "READY_WITH_EVIDENCE", source_id
        assert entry.get("replay_fixture_path"), source_id


def test_r3h01_officialMacroSources_notProposedDisabledAtRuntime() -> None:
    """覆盖范围：R3H-01 六源 capability registry 运行时门禁
    测试对象：SourceCapabilityRegistry.assert_source_domain_operation
    目的/目标：READY 源不应因 proposed_disabled_source 被整体拒绝
    验证点：抛 OperationDisabledError 时消息为 operation disabled，非 proposed_disabled_source
    失败含义：registry 已 READY 但 runtime 仍按 proposed-disabled 拒绝
    """
    reg = SourceCapabilityRegistry()
    reg.load()
    checks = [
        ("fred", "macro_series", "fetch_macro_series"),
        ("us_treasury", "us_treasury_yield_curve", "fetch_yield_curve"),
        ("sec_edgar", "us_filings", "fetch_company_filings"),
        ("cftc_cot", "cot_positioning", "fetch_cot_positioning"),
        ("bis", "central_bank_policy", "fetch_policy_rate"),
        ("world_bank", "development_indicator", "fetch_indicator_series"),
    ]
    for source_id, domain, operation in checks:
        with pytest.raises(OperationDisabledError, match="disabled for"):
            reg.assert_source_domain_operation(source_id, domain, operation)


R3H02_MARKET_SOURCES: tuple[str, ...] = (
    "alpha_vantage",
    "stooq",
    "yahoo_finance",
    "deribit",
    "coingecko",
)


def test_r3h02_marketSources_readyWithEvidenceStatus() -> None:
    """覆盖范围：R3H-02 五源 registry 终态
    测试对象：source_capabilities.yaml 中 alpha_vantage/stooq/yahoo_finance/deribit/coingecko
    目的/目标：五源不得停留在 proposed_disabled_source，须 READY_WITH_EVIDENCE
    验证点：status==READY_WITH_EVIDENCE；replay_fixture_path 非空
    失败含义：Batch 3H 市场源仍以 vague proposed-disabled 占位
    """
    capabilities = load_source_capabilities()
    sources = capabilities.get("sources") or {}
    for source_id in R3H02_MARKET_SOURCES:
        entry = sources.get(source_id) or {}
        assert entry.get("status") == "READY_WITH_EVIDENCE", source_id
        assert entry.get("replay_fixture_path"), source_id
        assert entry.get("fetch_port_path"), source_id


def test_r3h02_marketSources_notProposedDisabledAtRuntime() -> None:
    """覆盖范围：R3H-02 五源 capability registry 运行时门禁
    测试对象：SourceCapabilityRegistry.assert_source_domain_operation
    目的/目标：READY 源不应因 proposed_disabled_source 被整体拒绝
    验证点：抛 OperationDisabledError 时消息为 operation disabled，非 proposed_disabled_source
    失败含义：registry 已 READY 但 runtime 仍按 proposed-disabled 拒绝
    """
    reg = SourceCapabilityRegistry()
    reg.load()
    checks = [
        ("alpha_vantage", "us_equity_daily_bar", "fetch_us_daily_bar"),
        ("stooq", "global_market_daily_bar", "fetch_global_daily_bar"),
        ("yahoo_finance", "us_equity_daily_bar", "fetch_us_daily_bar_validation"),
        ("deribit", "crypto_options_surface", "fetch_options_surface"),
        ("coingecko", "crypto_spot_market", "fetch_spot_market_reference"),
    ]
    for source_id, domain, operation in checks:
        with pytest.raises(OperationDisabledError, match="disabled for"):
            reg.assert_source_domain_operation(source_id, domain, operation)


R3H04_PREDICTION_WEB_SOURCES: tuple[str, ...] = (
    "kalshi",
    "polymarket",
    "web_search",
)


def test_r3h04_predictionWebSources_readyWithEvidenceStatus() -> None:
    """覆盖范围：R3H-04 三源 registry 终态
    测试对象：source_capabilities.yaml 中 kalshi/polymarket/web_search
    目的/目标：三源不得停留在 proposed_disabled_source，须 READY_WITH_EVIDENCE
    验证点：status==READY_WITH_EVIDENCE；replay_fixture_path 与 fetch_port_path 非空
    失败含义：Batch 3H 预测/web 源仍以 vague proposed-disabled 占位
    """
    capabilities = load_source_capabilities()
    sources = capabilities.get("sources") or {}
    for source_id in R3H04_PREDICTION_WEB_SOURCES:
        entry = sources.get(source_id) or {}
        assert entry.get("status") == "READY_WITH_EVIDENCE", source_id
        assert entry.get("replay_fixture_path"), source_id
        assert entry.get("fetch_port_path"), source_id


def test_r3h04_predictionWebSources_notProposedDisabledAtRuntime() -> None:
    """覆盖范围：R3H-04 三源 capability registry 运行时门禁
    测试对象：SourceCapabilityRegistry.assert_source_domain_operation
    目的/目标：READY 源不应因 proposed_disabled_source 被整体拒绝
    验证点：抛 OperationDisabledError 时消息为 operation disabled，非 proposed_disabled_source
    失败含义：registry 已 READY 但 runtime 仍按 proposed-disabled 拒绝
    """
    reg = SourceCapabilityRegistry()
    reg.load()
    checks = [
        ("kalshi", "prediction_market_probability", "fetch_regulated_probability_signal"),
        ("polymarket", "prediction_market_probability", "fetch_prediction_market_probability"),
        ("web_search", "supplemental_web_evidence", "fetch_supplemental_web_evidence"),
    ]
    for source_id, domain, operation in checks:
        with pytest.raises(OperationDisabledError, match="disabled for"):
            reg.assert_source_domain_operation(source_id, domain, operation)
