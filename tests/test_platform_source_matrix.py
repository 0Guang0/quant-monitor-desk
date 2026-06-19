"""Round2.6 Phase C — platform source matrix tests (production planner)."""

from __future__ import annotations

from tests.contract_gate_support import PROJECT_ROOT, load_yaml, platform_key
from tests.service_path_support import plan_route

PLATFORM_MATRIX = PROJECT_ROOT / "specs/contracts/platform_source_matrix.yaml"


def test_qmtXtdataNonWindowsNotSchedulable() -> None:
    matrix = load_yaml(PLATFORM_MATRIX)
    key = platform_key()
    entry = matrix["platforms"]["linux" if key == "windows" else key]["qmt_xtdata"]
    assert entry["available_if_user_configured"] is False
    assert entry["default_enabled"] is False

    if key != "windows":
        plan = plan_route(
            data_domain="cn_equity_minute_bar",
            operation="fetch_minute_bar",
        )
        assert plan.selected_source_id is None
        qmt = next(c for c in plan.candidates if c.source_id == "qmt_xtdata")
        assert qmt.enabled is False
        assert qmt.disabled_reason is not None


def test_qmtXqshareMissingEnvNotSchedulable(monkeypatch) -> None:
    matrix = load_yaml(PLATFORM_MATRIX)
    entry = matrix["platforms"][platform_key()]["qmt_xqshare"]
    for env_name in entry.get("requires_env") or []:
        monkeypatch.delenv(env_name, raising=False)
    assert entry["default_enabled"] is False

    plan = plan_route(
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        extra_candidates=[("qmt_xqshare", "Primary")],
    )
    xq = next(c for c in plan.candidates if c.source_id == "qmt_xqshare")
    assert xq.enabled is False
    assert xq.skip_reason is not None
    assert "missing_env" in (xq.skip_reason or "")


def test_qmtXqshare_neverAutoProbed() -> None:
    matrix = load_yaml(PLATFORM_MATRIX)
    rules = matrix.get("rules") or []
    assert any("never auto-probed" in r.lower() for r in rules)

    plan = plan_route(
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        extra_candidates=[("qmt_xqshare", "Primary")],
    )
    xq = next(c for c in plan.candidates if c.source_id == "qmt_xqshare")
    assert xq.enabled is False


def test_platformMatrix_feedsDisabledReason() -> None:
    matrix = load_yaml(PLATFORM_MATRIX)
    rules = matrix.get("rules") or []
    assert any("disabled_reason" in r for r in rules)

    plan = plan_route(
        data_domain="cn_equity_minute_bar",
        operation="fetch_minute_bar",
    )
    disabled = [c for c in plan.candidates if not c.enabled]
    assert disabled
    assert all(c.disabled_reason for c in disabled)
