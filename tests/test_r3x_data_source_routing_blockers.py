"""R3X 数据源路由阻断项回归（ADV-A2 集群）。

覆盖范围：source_registry 声明域与 domain_roles 完备性、适配器合约状态枚举、
平台源矩阵与全量域路由预览是否 fail-closed 或显式 READY。
"""

from __future__ import annotations

from backend.app.datasources.service import _default_operation

from tests.contract_gate_support import PROJECT_ROOT, load_yaml
from tests.service_path_support import production_route_planner

SOURCE_REGISTRY = PROJECT_ROOT / "specs/datasource_registry/source_registry.yaml"
ADAPTER_CONTRACT = PROJECT_ROOT / "specs/contracts/data_adapter_contract.md"
PLATFORM_MATRIX = PROJECT_ROOT / "specs/contracts/platform_source_matrix.yaml"


def _registry_domains() -> set[str]:
    registry = load_yaml(SOURCE_REGISTRY)
    domains: set[str] = set()
    for source in registry.get("sources") or []:
        domains.update(source.get("allowed_domains") or [])
    return domains


def _domain_roles_keys() -> set[str]:
    registry = load_yaml(SOURCE_REGISTRY)
    return set((registry.get("domain_roles") or {}).keys())


def test_everyDeclaredDomain_hasDomainRoleBinding() -> None:
    """覆盖范围：source_registry 声明域与 domain_roles 键的完备性（ADV-A2-003）
    测试对象：sources[].allowed_domains vs domain_roles 键集合
    目的/目标：每个已声明的数据域都必须有路由角色绑定
    验证点：declared - roles 差集为空
    失败含义：某域无法被 SourceRoutePlanner 路由，生产 fetch 会断链
    """
    declared = _registry_domains()
    roles = _domain_roles_keys()
    missing = sorted(declared - roles)
    assert missing == [], f"domain_roles missing for declared domains: {missing}"


def test_fetchResultContract_listsDisabledAndNotPublishedStatuses() -> None:
    """覆盖范围：data_adapter_contract 对运行时 FetchResult 状态枚举（ADV-A2-001）
    测试对象：data_adapter_contract.md 正文
    目的/目标：合约须文档化 DISABLED_SOURCE 与 NOT_PUBLISHED_YET 等阻断状态
    验证点：文本含 DISABLED_SOURCE 与 NOT_PUBLISHED_YET
    失败含义：适配器合约与运行时状态不同步，调用方无法按合约处理阻断
    """
    text = ADAPTER_CONTRACT.read_text(encoding="utf-8")
    assert "DISABLED_SOURCE" in text
    assert "NOT_PUBLISHED_YET" in text


def test_platformMatrix_declaresCninfoYahooAndTdxPytdx() -> None:
    """覆盖范围：platform_source_matrix 对各平台源覆盖（ADV-A2-006）
    测试对象：platforms.* 下的 source 条目
    目的/目标：cninfo、yahoo_finance、tdx_pytdx 须在每平台矩阵中声明
    验证点：各 platform 对 required 三源的 missing 列表为空
    失败含义：跨平台部署时部分源无矩阵条目，路由/能力检查缺依据
    """
    matrix = load_yaml(PLATFORM_MATRIX)
    required = {"cninfo", "yahoo_finance", "tdx_pytdx"}
    for platform, entries in (matrix.get("platforms") or {}).items():
        missing = sorted(required - set(entries.keys()))
        assert missing == [], f"platform {platform!r} missing matrix entries: {missing}"


def test_defaultOperation_mapsEveryDomainRoleDomain() -> None:
    """覆盖范围：_default_operation 与 domain_roles 全量映射（ADV-A2-005）
    测试对象：DataSourceService._default_operation
    目的/目标：每个 domain_roles 键须有确定默认 operation，且与测试表一致
    验证点：无缺失域；各域返回值等于 expected 表
    失败含义：服务层默认 operation 漂移，路由 planner 收到错误 operation
    """
    expected = {
        "cn_equity_daily_bar": "fetch_daily_bar",
        "cn_equity_minute_bar": "fetch_minute_bar",
        "cn_equity_realtime": "fetch_realtime_quote",
        "cn_equity_basic_financial": "fetch_basic_financial",
        "cn_filings": "fetch_filing_index",
        "cn_announcements": "fetch_announcement_index",
        "cn_pdf_reports": "fetch_pdf_report",
        "cn_index": "fetch_index_daily_bar",
        "cn_index_daily_bar": "fetch_index_daily_bar",
        "sector_board": "fetch_sector_board",
        "us_equity_daily_bar": "fetch_us_daily_bar_validation",
        "etf_daily_bar": "fetch_etf_daily_bar_validation",
        "global_asset_reference": "fetch_global_asset_reference",
        "security_list": "fetch_security_list",
        "macro_supplementary": "fetch_macro_series",
        "macro_series": "fetch_macro_series",
        "capital_flow": "fetch_capital_flow",
        "central_bank_policy": "fetch_policy_rate",
        "commodity_daily_bar": "fetch_commodity_daily_bar",
        "concept_theme": "fetch_concept_theme",
        "cot_positioning": "fetch_cot_positioning",
        "credit_gap": "fetch_credit_to_gdp_gap",
        "crypto_asset_reference": "fetch_crypto_asset_reference",
        "crypto_derivatives": "fetch_derivatives_instruments",
        "crypto_futures_term_structure": "fetch_futures_term_structure",
        "crypto_options_surface": "fetch_options_surface",
        "crypto_spot_market": "fetch_spot_market_reference",
        "development_indicator": "fetch_indicator_series",
        "event_market_contract": "fetch_event_market_contracts",
        "event_resolution_evidence": "fetch_event_resolution_evidence",
        "fx_daily_bar": "fetch_fx_daily_bar",
        "global_macro_reference": "fetch_macro_reference",
        "global_market_daily_bar": "fetch_global_daily_bar",
        "inflation_expectation": "fetch_inflation_expectation_reference",
        "prediction_market_probability": "fetch_prediction_market_probability",
        "regulated_event_contract": "fetch_regulated_event_contracts",
        "research_report": "fetch_research_report_index",
        "supplemental_web_evidence": "fetch_supplemental_web_evidence",
        "us_filings": "fetch_company_filings",
        "us_insider_form4": "fetch_form4_transactions",
        "us_option_chain": "fetch_us_option_chain_validation",
        "us_treasury_yield_curve": "fetch_yield_curve",
        "vix_cds_supplement": "fetch_vix_cds_supplement",
    }
    missing = sorted(set(_domain_roles_keys()) - set(expected.keys()))
    assert missing == [], f"test table missing domain_roles keys: {missing}"
    drift = [
        f"{domain}: expected {expected[domain]!r}, got {_default_operation(domain)!r}"
        for domain in sorted(expected)
        if _default_operation(domain) != expected[domain]
    ]
    assert drift == [], f"_default_operation drift: {drift}"


def test_declaredDomains_routePreviewOrExplicitDisabled() -> None:
    """覆盖范围：全量 domain_roles 域的路由预览语义
    测试对象：SourceRoutePlanner.plan 对每个 domain
    目的/目标：READY 须有选中源；非 READY 须显式阻断且无选中源
    验证点：READY→selected_source_id 非空；否则 route_status 在已知阻断集合内
    失败含义：某域路由状态含糊，运维无法判断是可用还是应阻断
    """
    planner = production_route_planner()
    for domain in sorted(_domain_roles_keys()):
        op = _default_operation(domain)
        plan = planner.plan(
            data_domain=domain,
            operation=op,
            run_id=f"run-{domain}",
            job_id=f"job-{domain}",
        )
        if plan.route_status == "READY":
            assert plan.selected_source_id is not None
        else:
            assert plan.selected_source_id is None
            assert plan.route_status in {
                "DISABLED_SOURCE",
                "NO_AVAILABLE_SOURCE",
                "CAPABILITY_MISSING",
                "USER_AUTH_REQUIRED",
                "VALIDATION_ONLY_BLOCKED",
            }


def test_cnEquityBasicFinancial_routesToBaostock() -> None:
    """覆盖范围：cn_equity_basic_financial 域的主源选择
    测试对象：SourceRoutePlanner 对 fetch_basic_financial 的预览
    目的/目标：A 股基本面域应路由到 baostock 且状态 READY
    验证点：route_status=READY；selected_source_id=baostock
    失败含义：基本面数据主源错误或未就绪，下游 Layer 无法拉取
    """
    planner = production_route_planner()
    plan = planner.plan(
        data_domain="cn_equity_basic_financial",
        operation="fetch_basic_financial",
        run_id="run-fin",
        job_id="job-fin",
    )
    assert plan.route_status == "READY"
    assert plan.selected_source_id == "baostock"


def test_tdxPytdxDomains_remainDisabledByDefault() -> None:
    """覆盖范围：tdx_pytdx 关联域的默认阻断
    测试对象：security_list、cn_index_daily_bar 路由预览
    目的/目标：TDX 域默认 DISABLED_SOURCE，候选须带 skip_reason
    验证点：route_status=DISABLED_SOURCE；selected_source_id=None；tdx 候选有 skip_reason
    失败含义：TDX 默认可路由，违反 validation_only + disabled-by-default 策略
    """
    planner = production_route_planner()
    for domain in ("security_list", "cn_index_daily_bar"):
        plan = planner.plan(
            data_domain=domain,
            operation=_default_operation(domain),
            run_id=f"run-{domain}",
            job_id=f"job-{domain}",
        )
        assert plan.route_status == "DISABLED_SOURCE"
        assert plan.selected_source_id is None
        tdx = next(c for c in plan.candidates if c.source_id == "tdx_pytdx")
        assert tdx.skip_reason is not None
