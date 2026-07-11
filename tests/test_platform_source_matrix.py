"""Round2.6 Phase C — 平台数据源矩阵路由规划器行为测试。

纯 YAML 条目核对已迁至 scripts/check_platform_source_matrix.py。
"""

from __future__ import annotations

import sys

import pytest

from tests.contract_gate_support import PROJECT_ROOT, load_yaml, platform_key
from tests.service_path_support import plan_route

PLATFORM_MATRIX = PROJECT_ROOT / "specs/contracts/platform_source_matrix.yaml"


@pytest.mark.skipif(sys.platform == "win32", reason="plan_route non-Windows scheduling covered on linux CI")
def test_qmtXtdataNonWindowsNotSchedulable() -> None:
    """覆盖范围：qmt_xtdata 在非 Windows 平台不可调度
    测试对象：plan_route 分钟线路由（非 win32 CI）
    目的/目标：非 Windows 上路由不得选中 qmt_xtdata
    验证点：selected_source_id 为 None；qmt_xtdata 候选 disabled 且含 disabled_reason
    失败含义：跨平台误调度 QMT 会导致运行时硬失败或静默跳过
    """
    plan = plan_route(
        data_domain="cn_equity_minute_bar",
        operation="fetch_minute_bar",
    )
    assert plan.selected_source_id is None
    qmt = next(c for c in plan.candidates if c.source_id == "qmt_xtdata")
    assert qmt.enabled is False
    assert qmt.disabled_reason is not None


def test_qmtXqshareMissingEnvNotSchedulable(tmp_path, monkeypatch) -> None:
    """覆盖范围：qmt_xqshare 缺必需环境变量时不可调度（ADR-018 先开关再安检）
    测试对象：platform_source_matrix.yaml requires_env 与 plan(con=) 日线路由
    目的/目标：默认关闭时先被开关本拒绝；正规 overlay 打开后缺 env 须给出 missing_env
    验证点：①无 overlay → skip_reason 含 source_disabled；②overlay+缺 env → missing_env
    失败含义：无凭证仍入选会导致生产拉数静默失败，或安检顺序回退到旧口径
    """
    import duckdb

    from backend.app.datasources.activation_overlay import write_activation_overlay
    from backend.app.datasources.capability_registry import SourceCapabilityRegistry
    from backend.app.datasources.route_planner import SourceRoutePlanner
    from backend.app.datasources.source_registry import SourceRegistry
    from backend.app.db.migrate import apply_migrations

    matrix = load_yaml(PLATFORM_MATRIX)
    entry = matrix["platforms"][platform_key()]["qmt_xqshare"]
    for env_name in entry.get("requires_env") or []:
        monkeypatch.delenv(env_name, raising=False)
    assert entry["default_enabled"] is False

    # ① 默认：先开关本拒绝（YAML enabled_by_default=false）
    plan_default = plan_route(
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        extra_candidates=[("qmt_xqshare", "Primary")],
    )
    xq0 = next(c for c in plan_default.candidates if c.source_id == "qmt_xqshare")
    assert xq0.enabled is False
    assert "source_disabled" in (xq0.skip_reason or "")

    # ② overlay 打开后：平台安检须暴露 missing_env
    db = tmp_path / "xqshare-env.duckdb"
    con = duckdb.connect(str(db))
    apply_migrations(con)
    reg = SourceRegistry()
    reg.load()
    reg.sync_to_db(con, tombstone_missing=False)
    write_activation_overlay(
        con,
        source_id="qmt_xqshare",
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        enabled=True,
        reason="[sandbox] enable qmt_xqshare to assert missing_env",
        changed_by="test_platform_source_matrix",
        sandbox=True,
    )
    caps = SourceCapabilityRegistry()
    caps.load()
    plan = SourceRoutePlanner(source_registry=reg, capability_registry=caps).plan(
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        run_id="xq-env",
        job_id="xq-env",
        extra_candidates=[("qmt_xqshare", "Primary")],
        con=con,
    )
    xq = next(c for c in plan.candidates if c.source_id == "qmt_xqshare")
    assert xq.enabled is False
    assert xq.skip_reason is not None
    assert "missing_env" in (xq.skip_reason or "")


def test_qmtXqshare_neverAutoProbed() -> None:
    """覆盖范围：qmt_xqshare 禁止自动探测
    测试对象：platform_source_matrix.yaml rules 与 plan_route
    目的/目标：契约须声明 never auto-probed；路由中 xqshare 保持禁用
    验证点：rules 含 never auto-probed；候选 qmt_xqshare.enabled 为 False
    失败含义：自动探测会触发未授权 QMT 连接或合规风险
    """
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
    """覆盖范围：平台矩阵向路由候选注入 disabled_reason
    测试对象：platform_source_matrix.yaml rules 与 plan_route 分钟线路由
    目的/目标：所有禁用候选须有可审计的 disabled_reason
    验证点：rules 要求 disabled_reason；plan 中每个 disabled 候选均有非空 disabled_reason
    失败含义：无原因禁用会导致运维无法解释路由决策
    """
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
