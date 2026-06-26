"""018C TDX 实盘手工探针授权门控（纯本地，无网络）。"""

from __future__ import annotations

from pathlib import Path

import pytest
from backend.app.datasources.adapters.fetch_port import PortError
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.normalizers.tdx import parse_index_instrument
from backend.app.ops.interface_probe_fetch_ports import TdxPytdxProbeFetchPort
from backend.app.ops.tdx_live_manual_probe_gate import (
    TdxLiveManualProbeAuthorizationError,
    TdxLiveManualProbeRequest,
    validate_tdx_live_manual_probe_authorization,
)


def _sample_auth_text(*, session_id: str = "sess-planning-test-001") -> str:
    return f"""# TDX Live Manual Probe Authorization

authorized_session_id: {session_id}

I authorize the Round 3 018C tdx_pytdx live manual probe scoped to
docs/quality/tdx_pytdx_live_manual_probe_authorization_2026-06-22.md only.
See `.trellis/tasks/06-22-round3-018c-live-manual-probe-plan/live_manual_probe_plan.md`.
This probe does not close Eastmoney stock_zh_a_hist / R3-B2.75-REQ2-EM.

## TDX host

| host | port | provided_by | provided_on | reachability_note | reference_only_default | user_attestation |
| ---- | ---- | ----------- | ----------- | ----------------- | ---------------------- | ---------------- |
| 127.0.0.1 | 7709 | owner | 2026-06-22 | user confirms | false | bounded read-only probe |
"""


def test_tdxProbeFetchPort_blocksWithoutAuthorization() -> None:
    """覆盖范围：TdxPytdxProbeFetchPort 拉取前的授权检查
    测试对象：TdxPytdxProbeFetchPort.fetch_payload
    目的/目标：未通过授权校验时禁止任何 TDX 实盘网络请求
    验证点：抛出 PortError 且消息含 fetch blocked
    失败含义：无授权文件也能触发探针拉取，实盘门禁形同虚设
    """
    port = TdxPytdxProbeFetchPort(("sh.600519",), 3)
    with pytest.raises(PortError, match="fetch blocked"):
        port.fetch_payload(
            FetchRequest(
                run_id="t",
                source_id="tdx_pytdx",
                data_domain="cn_equity_daily_bar",
                instrument_id="sh.600519",
                market_id="cn",
                end_time="2026-06-22",
            )
        )


def test_validateTdxLiveManualProbe_missingFile_blocks() -> None:
    """覆盖范围：validate_tdx_live_manual_probe_authorization 文件存在性
    测试对象：TdxLiveManualProbeRequest.authorization_evidence 路径
    目的/目标：授权证据文件不存在时必须拒绝探针
    验证点：抛出 TdxLiveManualProbeAuthorizationError 且消息含 missing
    失败含义：可引用不存在的授权路径绕过门控
    """
    req = TdxLiveManualProbeRequest(
        source_id="tdx_pytdx",
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        symbols_or_markets=("sh.600519",),
        date_window="recent 5 trading days",
        max_rows=3,
        authorization_evidence="docs/quality/tdx_pytdx_live_manual_probe_authorization_2099-01-01.md",
        tdx_host="127.0.0.1",
        tdx_port=7709,
        authorized_session_id="sess-x",
    )
    with pytest.raises(TdxLiveManualProbeAuthorizationError, match="missing"):
        validate_tdx_live_manual_probe_authorization(req)


def test_validateTdxLiveManualProbe_validFile_passes(tmp_path: Path) -> None:
    """覆盖范围：完整授权文件与会话 ID 匹配场景
    测试对象：validate_tdx_live_manual_probe_authorization
    目的/目标：合法授权证据 + 匹配的 session/host/port 应放行校验
    验证点：不抛异常即通过
    失败含义：合规授权仍被拒绝，手工探针无法按计划执行
    """
    auth = tmp_path / "tdx_pytdx_live_manual_probe_authorization_2026-06-22.md"
    auth.write_text(_sample_auth_text(), encoding="utf-8")
    req = TdxLiveManualProbeRequest(
        source_id="tdx_pytdx",
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        symbols_or_markets=("sh.600519",),
        date_window="recent 5 trading days",
        max_rows=3,
        authorization_evidence=str(auth),
        tdx_host="127.0.0.1",
        tdx_port=7709,
        authorized_session_id="sess-planning-test-001",
    )
    validate_tdx_live_manual_probe_authorization(req)


def test_validateTdxLiveManualProbe_hostPortMismatch_blocks(tmp_path: Path) -> None:
    """覆盖范围：请求 host/port 与授权文件登记不一致
    测试对象：validate_tdx_live_manual_probe_authorization 主机绑定校验
    目的/目标：防止用 A 主机授权文件去连 B 主机 TDX
    验证点：host 与授权表不符时抛出 TdxLiveManualProbeAuthorizationError（host/port）
    失败含义：授权可跨主机复用，探针范围失控
    """
    auth = tmp_path / "tdx_pytdx_live_manual_probe_authorization_2026-06-22.md"
    auth.write_text(_sample_auth_text(), encoding="utf-8")
    req = TdxLiveManualProbeRequest(
        source_id="tdx_pytdx",
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        symbols_or_markets=("sh.600519",),
        date_window="recent 5 trading days",
        max_rows=3,
        authorization_evidence=str(auth),
        tdx_host="10.0.0.1",
        tdx_port=7709,
        authorized_session_id="sess-planning-test-001",
    )
    with pytest.raises(TdxLiveManualProbeAuthorizationError, match="host/port"):
        validate_tdx_live_manual_probe_authorization(req)


def test_validateTdxLiveManualProbe_sessionIdMismatch_blocks(tmp_path: Path) -> None:
    """覆盖范围：authorized_session_id 与授权文件登记不一致
    测试对象：validate_tdx_live_manual_probe_authorization 会话绑定
    目的/目标：A8-G2 — session_id 错误时必须拒绝
    验证点：抛出 TdxLiveManualProbeAuthorizationError 且消息含 authorized_session_id
    失败含义：授权可跨会话复用，探针范围失控
    """
    auth = tmp_path / "tdx_pytdx_live_manual_probe_authorization_2026-06-22.md"
    auth.write_text(_sample_auth_text(session_id="sess-planning-test-001"), encoding="utf-8")
    req = TdxLiveManualProbeRequest(
        source_id="tdx_pytdx",
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        symbols_or_markets=("sh.600519",),
        date_window="recent 5 trading days",
        max_rows=3,
        authorization_evidence=str(auth),
        tdx_host="127.0.0.1",
        tdx_port=7709,
        authorized_session_id="wrong-session-id",
    )
    with pytest.raises(TdxLiveManualProbeAuthorizationError, match="authorized_session_id"):
        validate_tdx_live_manual_probe_authorization(req)


def test_parseIndexInstrument_000001SH() -> None:
    """覆盖范围：TDX 指数代码解析辅助函数
    测试对象：parse_index_instrument
    目的/目标：将 000001.SH 规范化为 TDX 市场码与纯代码
    验证点：parse_index_instrument('000001.SH') == (1, '000001')
    失败含义：上证指数等标的无法正确映射，探针请求参数错误
    """
    assert parse_index_instrument("000001.SH") == (1, "000001")

