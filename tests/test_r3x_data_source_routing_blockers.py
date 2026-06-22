"""R3X data-source routing blocker tests (ADV-A2 cluster)."""

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
    """ADV-A2-003: every registry allowed domain must be routable via domain_roles."""
    declared = _registry_domains()
    roles = _domain_roles_keys()
    missing = sorted(declared - roles)
    assert missing == [], f"domain_roles missing for declared domains: {missing}"


def test_fetchResultContract_listsDisabledAndNotPublishedStatuses() -> None:
    """ADV-A2-001: contract must list runtime FetchResult statuses."""
    text = ADAPTER_CONTRACT.read_text(encoding="utf-8")
    assert "DISABLED_SOURCE" in text
    assert "NOT_PUBLISHED_YET" in text


def test_platformMatrix_declaresCninfoYahooAndTdxPytdx() -> None:
    """ADV-A2-006: planner sources must exist in platform matrix for every platform."""
    matrix = load_yaml(PLATFORM_MATRIX)
    required = {"cninfo", "yahoo_finance", "tdx_pytdx"}
    for platform, entries in (matrix.get("platforms") or {}).items():
        missing = sorted(required - set(entries.keys()))
        assert missing == [], f"platform {platform!r} missing matrix entries: {missing}"


def test_defaultOperation_mapsEveryDomainRoleDomain() -> None:
    """ADV-A2-005: service default operation must cover every domain_roles key."""
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
    """Each domain_roles domain must preview READY or explicit disabled route status."""
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
