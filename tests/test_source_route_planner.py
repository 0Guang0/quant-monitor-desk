"""Round2.6 Phase B — SourceRoutePlan contract tests (test-only planner)."""

from __future__ import annotations

from tests.contract_gate_support import ContractSourceRoutePlanner


def test_qmtDisabled_routePlanShowsSkipReason() -> None:
    planner = ContractSourceRoutePlanner()
    plan = planner.plan(
        data_domain="cn_equity_minute_bar",
        operation="fetch_minute_bar",
    )
    assert plan.route_status == "DISABLED_SOURCE"
    assert plan.selected_source_id is None
    qmt = next(c for c in plan.candidates if c.source_id == "qmt_xtdata")
    assert qmt.skip_reason is not None
    assert qmt.capability_declared is True
    lowered = (qmt.skip_reason or "").lower()
    assert (
        "disabled" in lowered
        or "authorization" in lowered
        or "platform" in lowered
    )


def test_noAvailableSource_hasNoSelectedSource() -> None:
    planner = ContractSourceRoutePlanner()
    plan = planner.plan(
        data_domain="us_equity_daily_bar",
        operation="fetch_us_daily_bar_validation",
    )
    assert plan.route_status in {"DISABLED_SOURCE", "NO_AVAILABLE_SOURCE"}
    assert plan.selected_source_id is None
    assert all(c.skip_reason or not c.enabled for c in plan.candidates if not c.enabled)


def test_fallbackAddsQualityFlag() -> None:
    planner = ContractSourceRoutePlanner()
    plan = planner.plan(
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        use_fallback=True,
    )
    if plan.selected_source_id == "qmt_xtdata":
        assert "SOURCE_FALLBACK_USED" in plan.quality_flags
    else:
        assert plan.route_status == "READY"
        assert plan.selected_source_id == "baostock"


def test_readyRoute_selectedSourceIdNotNull() -> None:
    planner = ContractSourceRoutePlanner()
    plan = planner.plan(
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
    )
    assert plan.route_status == "READY"
    assert plan.selected_source_id == "baostock"
    assert plan.quality_flags == []


def test_capabilityMissing_routeStatusCapabilityMissing() -> None:
    planner = ContractSourceRoutePlanner()
    plan = planner.plan(
        data_domain="cn_equity_realtime",
        operation="fetch_realtime_quote",
        extra_candidates=[("baostock", "Primary")],
    )
    baostock = next(c for c in plan.candidates if c.source_id == "baostock")
    assert baostock.capability_declared is False
    assert baostock.enabled is False
    assert plan.route_status == "CAPABILITY_MISSING"
    assert plan.selected_source_id is None
