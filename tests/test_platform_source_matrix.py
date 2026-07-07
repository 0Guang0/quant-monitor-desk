"""Round2.6 Phase C — 平台数据源矩阵与生产路由规划器测试。

覆盖范围：specs/contracts/platform_source_matrix.yaml 对 QMT 类源的平台可用性与 disabled_reason 规则。
"""

from __future__ import annotations

import sys

import pytest

from tests.contract_gate_support import PROJECT_ROOT, load_yaml, platform_key
from tests.service_path_support import plan_route

PLATFORM_MATRIX = PROJECT_ROOT / "specs/contracts/platform_source_matrix.yaml"


def test_qmtXtdata_matrixEntry_nonWindowsDisabled() -> None:
    """覆盖范围：qmt_xtdata 在 linux/macos 矩阵条目
    测试对象：platform_source_matrix.yaml platforms.linux/macos.qmt_xtdata
    目的/目标：非 Windows 平台 YAML 须标记不可用
    验证点：available_if_user_configured/default_enabled 均为 False
    失败含义：矩阵登记允许非 Windows 调度 xtdata，与契约 rules 冲突
    """
    matrix = load_yaml(PLATFORM_MATRIX)
    for platform in ("linux", "macos"):
        entry = matrix["platforms"][platform]["qmt_xtdata"]
        assert entry["available_if_user_configured"] is False
        assert entry["default_enabled"] is False


def test_qmtXtdata_matrixEntry_windowsRequiresAuth() -> None:
    """覆盖范围：qmt_xtdata 在 Windows 矩阵条目
    测试对象：platform_source_matrix.yaml platforms.windows.qmt_xtdata
    目的/目标：Windows 上 xtdata 仅可在用户授权+env 后配置，默认不启用
    验证点：available_if_user_configured 为 True；default_enabled 为 False
    失败含义：Windows 矩阵误标默认可用，路由与合规预期漂移
    """
    matrix = load_yaml(PLATFORM_MATRIX)
    entry = matrix["platforms"]["windows"]["qmt_xtdata"]
    assert entry["available_if_user_configured"] is True
    assert entry["default_enabled"] is False


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


def test_qmtXqshareMissingEnvNotSchedulable(monkeypatch) -> None:
    """覆盖范围：qmt_xqshare 缺必需环境变量时不可调度
    测试对象：platform_source_matrix.yaml requires_env 与 plan_route 日线路由
    目的/目标：清除 requires_env 后候选须禁用并给出 missing_env 类 skip_reason
    验证点：default_enabled 为 False；xqshare 候选 enabled=False 且 skip_reason 含 missing_env
    失败含义：无凭证仍入选会导致生产拉数静默失败
    """
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
