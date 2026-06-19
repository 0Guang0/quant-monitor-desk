"""Round2.6 Phase C — SourceRoutePlan production planner tests."""

from __future__ import annotations

from tests.service_path_support import production_route_planner


def _planner():
    return production_route_planner()

def test_qmtDisabled_routePlanShowsSkipReason() -> None:
    planner = _planner()
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
    assert (
        "disabled" in lowered
        or "authorization" in lowered
        or "platform" in lowered
    )


def test_noAvailableSource_hasNoSelectedSource() -> None:
    planner = _planner()
    plan = planner.plan(
        data_domain="us_equity_daily_bar",
        operation="fetch_us_daily_bar_validation",
        run_id="run-2",
        job_id="job-2",
    )
    assert plan.route_status in {"DISABLED_SOURCE", "NO_AVAILABLE_SOURCE"}
    assert plan.selected_source_id is None
    assert all(c.skip_reason or not c.enabled for c in plan.candidates if not c.enabled)


def test_fallbackAddsQualityFlag() -> None:
    planner = _planner()
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
    planner = _planner()
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
    planner = _planner()
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
    assert plan.route_status == "CAPABILITY_MISSING"
    assert plan.selected_source_id is None


def test_userAuthRequired_routeStatusWhenAuthorizationMissing() -> None:
    planner = _planner()
    plan = planner.plan(
        data_domain="cn_equity_realtime",
        operation="fetch_realtime_quote_remote",
        run_id="run-auth",
        job_id="job-auth",
        extra_candidates=[("qmt_xqshare", "Primary")],
    )
    assert plan.route_status == "USER_AUTH_REQUIRED"
    assert plan.selected_source_id is None
    xq = next(c for c in plan.candidates if c.source_id == "qmt_xqshare")
    assert xq.skip_reason is not None
    assert "user_authorization" in xq.skip_reason or xq.skip_reason.startswith(
        "missing_env:"
    )
