"""R3FR-03 TDX/pytdx provider port tests (AC-TDX-01..06)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml
from backend.app.datasources.adapters.fetch_port import PortError
from backend.app.datasources.fetch_ports import tdx_pytdx_port as tdx_port_module
from backend.app.datasources.fetch_ports.tdx_pytdx_port import (
    EQUITY_INDEX_MAX_ROWS,
    FULL_MARKET_SCAN_ENABLED,
    MAX_NETWORK_CALLS,
    MINUTE_BARS_ENABLED,
    SECURITY_LIST_MAX_ROWS,
    TdxPytdxFetchPort,
)
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.normalizers.tdx import (
    build_equity_bar_manifest,
    manifest_content_hash,
    manifest_schema_hash,
)
from backend.app.config import PROJECT_ROOT
from backend.app.ops.tdx_live_manual_probe_gate import (
    FORBIDDEN_LIVE_ENTRYPOINTS,
    TdxLiveManualProbeAuthorizationError,
    TdxLiveManualProbeRequest,
    TdxPytdxAuthorization,
    assert_live_entrypoint_not_forbidden,
    issue_tdx_live_authorization_after_gate,
)


def _equity_req(**overrides: object) -> FetchRequest:
    base = {
        "run_id": "t",
        "source_id": "tdx_pytdx",
        "data_domain": "cn_equity_daily_bar",
        "instrument_id": "sh.600519",
        "market_id": "cn",
        "end_time": "2026-06-22",
    }
    base.update(overrides)
    return FetchRequest(**base)


def _gate_auth(tmp_path: Path, **overrides: object) -> TdxPytdxAuthorization:
    auth = tmp_path / "tdx_pytdx_live_manual_probe_authorization_2026-06-22.md"
    auth.write_text(
        """# TDX Live Manual Probe Authorization

authorized_session_id: sess-planning-test-001

I authorize the Round 3 018C tdx_pytdx live manual probe scoped to
docs/quality/tdx_pytdx_live_manual_probe_authorization_2026-06-22.md only.
See `.trellis/tasks/06-22-round3-018c-live-manual-probe-plan/live_manual_probe_plan.md`.
This probe does not close Eastmoney stock_zh_a_hist / R3-B2.75-REQ2-EM.

## TDX host

| host | port | provided_by | provided_on | reachability_note | reference_only_default | user_attestation |
| ---- | ---- | ----------- | ----------- | ----------------- | ---------------------- | ---------------- |
| 127.0.0.1 | 7709 | owner | 2026-06-22 | user confirms | false | bounded read-only probe |
""",
        encoding="utf-8",
    )
    base = {
        "source_id": "tdx_pytdx",
        "data_domain": "cn_equity_daily_bar",
        "operation": "fetch_daily_bar",
        "symbols_or_markets": ("sh.600519",),
        "date_window": "recent 5 trading days",
        "max_rows": 3,
        "authorization_evidence": str(auth),
        "tdx_host": "127.0.0.1",
        "tdx_port": 7709,
        "authorized_session_id": "sess-planning-test-001",
    }
    base.update(overrides)
    return issue_tdx_live_authorization_after_gate(TdxLiveManualProbeRequest(**base))


def test_tdxPytdxPort_issueAuthorizationNotPublicOnPortModule() -> None:
    """覆盖范围：port 层不可公有签发 gate token
    测试对象：backend.app.datasources.fetch_ports.tdx_pytdx_port
    目的/目标：AA-R3FR03-A4-01 — issue_tdx_live_authorization 不得暴露在 port 包
    验证点：模块无 issue_tdx_live_authorization 属性
    失败含义：任意代码可绕过 gate MD 自签 token
    """
    assert not hasattr(tdx_port_module, "issue_tdx_live_authorization")


def test_tdxPytdxPort_missingPytdx_returnsDisabledSource(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """覆盖范围：缺 pytdx 依赖时的 port 行为
    测试对象：TdxPytdxFetchPort.fetch_payload
    目的/目标：AC-TDX-01 — 缺包返回 DISABLED_SOURCE 而非崩溃
    验证点：PortError.status == DISABLED_SOURCE
    失败含义：未安装 pytdx 时进程崩溃或误报可联网
    """
    monkeypatch.setitem(sys.modules, "pytdx", None)
    monkeypatch.setitem(sys.modules, "pytdx.hq", None)
    monkeypatch.setattr(
        "backend.app.datasources.fetch_ports.tdx_pytdx_port.enforce_live_entrypoint_stack",
        lambda: None,
    )
    port = TdxPytdxFetchPort(("sh.600519",), 3, authorization=_gate_auth(tmp_path))
    with pytest.raises(PortError) as exc_info:
        port.fetch_payload(_equity_req())
    assert exc_info.value.status == "DISABLED_SOURCE"


def test_tdxNormalizer_equityManifest_hasRequiredFieldsAndHash() -> None:
    """覆盖范围：equity raw manifest 与 hash
    测试对象：build_equity_bar_manifest + manifest_*_hash
    目的/目标：AC-TDX-04 — manifest 含必需字段与稳定 hash
    验证点：行级 trade_date；content_hash 与 schema_hash 非空且稳定
    失败含义：raw evidence 无法做 lineage 或 schema 漂移检测
    """
    rows = [{"datetime": "2026-06-18", "close": 1405.0}]
    manifest = build_equity_bar_manifest("sh.600519", rows)
    assert manifest["rows"][0]["trade_date"] == "2026-06-18"
    assert len(manifest_content_hash(manifest)) == 64
    assert len(manifest_schema_hash(manifest)) == 64


def test_tdxPytdxPort_rejectsMinuteBars() -> None:
    """覆盖范围：分钟线请求拒绝
    测试对象：TdxPytdxFetchPort.fetch_payload
    目的/目标：AC-TDX-03 — minute_bars_enabled=false 时显式拒绝
    验证点：minute domain 抛出 PortError 且消息含 minute
    失败含义：默认开启分钟线或静默截断
    """
    port = TdxPytdxFetchPort(("sh.600519",), 3)
    with pytest.raises(PortError, match="minute"):
        port.fetch_payload(
            FetchRequest(
                run_id="t",
                source_id="tdx_pytdx",
                data_domain="cn_equity_minute_bar",
                instrument_id="sh.600519",
                market_id="cn",
                end_time="2026-06-22",
            )
        )
    assert MINUTE_BARS_ENABLED is False


def test_tdxPytdxPort_rejectsFullMarketScan() -> None:
    """覆盖范围：全市场扫描拒绝
    测试对象：TdxPytdxFetchPort.fetch_payload
    目的/目标：AC-TDX-03 — full_market_scan_enabled=false 时拒绝
    验证点：instrument_id=* 抛出 PortError
    失败含义：无界全市场扫描泄漏
    """
    port = TdxPytdxFetchPort(("*",), 3)
    with pytest.raises(PortError, match="full market scan"):
        port.fetch_payload(_equity_req(instrument_id="*"))
    assert FULL_MARKET_SCAN_ENABLED is False


def test_tdxPytdxPort_rejectsOverCap() -> None:
    """覆盖范围：超 cap 行数拒绝
    测试对象：TdxPytdxFetchPort.fetch_payload
    目的/目标：AC-TDX-03 — equity/index max_rows=3 硬上限
    验证点：max_rows=10 时 PortError 含 exceeds cap
    失败含义：cap 可被 port 参数绕过
    """
    port = TdxPytdxFetchPort(("sh.600519",), EQUITY_INDEX_MAX_ROWS + 7)
    with pytest.raises(PortError, match="exceeds cap"):
        port.fetch_payload(_equity_req())
    assert EQUITY_INDEX_MAX_ROWS == 3


def test_tdxPytdxPort_withoutAuth_raisesUserAuthRequired() -> None:
    """覆盖范围：无 gate 授权 token
    测试对象：TdxPytdxFetchPort.fetch_payload
    目的/目标：AC-TDX-02 — 无授权不联网
    验证点：PortError.status == USER_AUTH_REQUIRED
    失败含义：直调 port 可绕过 live gate
    """
    port = TdxPytdxFetchPort(("sh.600519",), 3)
    with pytest.raises(PortError) as exc_info:
        port.fetch_payload(_equity_req())
    assert exc_info.value.status == "USER_AUTH_REQUIRED"


def test_tdxPytdxPort_fakeAuthWithoutGateToken_raisesUserAuthRequired() -> None:
    """覆盖范围：伪造 authorization 无 gate_token
    测试对象：TdxPytdxAuthorization + TdxPytdxFetchPort
    目的/目标：verified=True 但无 gate 签发仍拒绝
    验证点：USER_AUTH_REQUIRED
    失败含义：手工构造 Authorization 可绕过 gate
    """
    port = TdxPytdxFetchPort(
        ("sh.600519",),
        3,
        authorization=TdxPytdxAuthorization(verified=True, host="127.0.0.1", port=7709),
    )
    with pytest.raises(PortError) as exc_info:
        port.fetch_payload(_equity_req())
    assert exc_info.value.status == "USER_AUTH_REQUIRED"


def test_tdxPytdxPort_directCallWithGateToken_blockedByStack(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """覆盖范围：直调 TdxPytdxFetchPort 绕过 orchestration
    测试对象：TdxPytdxFetchPort.fetch_payload + gate 签发 token
    目的/目标：AC-TDX-02 I02 — 有 gate token 但无 approved 调用栈仍拒绝
    验证点：PortError.status == USER_AUTH_REQUIRED 且消息含 forbidden
    失败含义：token 可配合直调 port 绕过 live gate
    """
    monkeypatch.setitem(sys.modules, "pytdx", object())
    monkeypatch.setitem(sys.modules, "pytdx.hq", object())
    port = TdxPytdxFetchPort(("sh.600519",), 3, authorization=_gate_auth(tmp_path))
    with pytest.raises(PortError) as exc_info:
        port.fetch_payload(_equity_req())
    assert exc_info.value.status == "USER_AUTH_REQUIRED"
    assert "forbidden" in exc_info.value.message.lower()


def test_tdxPytdxPort_remainingNetworkCalls_exhausted(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """覆盖范围：port 层 remaining_network_calls 预算
    测试对象：TdxPytdxFetchPort.fetch_payload(remaining_network_calls=0)
    目的/目标：AA-R3FR03-A4-03 — 耗尽预算 fail-fast 不 connect
    验证点：PortError 消息含 network call budget
    失败含义：直调 port 可无限 connect 突破 cap
    """
    monkeypatch.setitem(sys.modules, "pytdx", object())
    monkeypatch.setitem(sys.modules, "pytdx.hq", object())
    monkeypatch.setattr(
        "backend.app.datasources.fetch_ports.tdx_pytdx_port.enforce_live_entrypoint_stack",
        lambda: None,
    )
    port = TdxPytdxFetchPort(
        ("sh.600519",),
        3,
        authorization=_gate_auth(tmp_path),
        remaining_network_calls=0,
    )
    with pytest.raises(PortError, match="network call budget"):
        port.fetch_payload(_equity_req())


def test_tdxLiveGate_forbiddenDirectPortFqnRegistered() -> None:
    """覆盖范围：FORBIDDEN_LIVE_ENTRYPOINTS 登记 port FQN
    测试对象：FORBIDDEN_LIVE_ENTRYPOINTS + assert_live_entrypoint_not_forbidden
    目的/目标：AC-TDX-02 — forbidden FQN 可被 assert 拒绝
    验证点：port FQN 在集合中；assert 抛 TdxLiveManualProbeAuthorizationError
    失败含义：FORBIDDEN 列表未含直调 port 入口
    """
    port_fqn = "backend.app.datasources.fetch_ports.tdx_pytdx_port.TdxPytdxFetchPort"
    assert port_fqn in FORBIDDEN_LIVE_ENTRYPOINTS
    with pytest.raises(TdxLiveManualProbeAuthorizationError, match="forbidden live entrypoint"):
        assert_live_entrypoint_not_forbidden(port_fqn)


def _load_capabilities() -> dict:
    path = PROJECT_ROOT / "specs/datasource_registry/source_capabilities.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def test_tdxPytdx_capsMatchTaskCard() -> None:
    """覆盖范围：registry resource_caps 与任务卡 SSOT
    测试对象：source_capabilities.yaml tdx_pytdx.resource_caps
    目的/目标：AC-TDX-06 — caps 与 frozen §5 一致
    验证点：各 cap 字段值匹配 R3FR-03
    失败含义：registry 与 gate/port caps 权威冲突
    """
    caps = (_load_capabilities().get("sources") or {}).get("tdx_pytdx", {}).get(
        "resource_caps"
    ) or {}
    assert caps["security_list_max_rows"] == SECURITY_LIST_MAX_ROWS == 20
    assert caps["equity_daily_bar_max_symbols"] == EQUITY_INDEX_MAX_ROWS == 3
    assert caps["index_daily_bar_max_symbols"] == 3
    assert caps["max_network_calls"] == MAX_NETWORK_CALLS == 5
    assert caps["minute_bars_enabled"] is False
    assert caps["full_market_scan_enabled"] is False


def test_tdxRoute_tdxPytdx_disabledByDefault() -> None:
    """覆盖范围：tdx_pytdx 路由默认禁用
    测试对象：source_registry.yaml + build_route_matrix
    目的/目标：AC-TDX-06 — enabled_by_default=false，非 primary
    验证点：registry enabled_by_default=False；route matrix 不选 tdx 为 primary
    失败含义：TDX 默认可被 production route 选中
    """
    from backend.app.ops.interface_probe import build_route_matrix

    registry_path = PROJECT_ROOT / "specs/datasource_registry/source_registry.yaml"
    entry = next(
        s
        for s in (yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {})["sources"]
        if s["source_id"] == "tdx_pytdx"
    )
    assert entry["enabled_by_default"] is False
    assert entry["validation_only"] is True
    for row in build_route_matrix()["routes"]:
        if row["source_id"] == "tdx_pytdx":
            assert not row["source_enabled_by_default"]
            assert row["selected_source_id"] != "tdx_pytdx"
