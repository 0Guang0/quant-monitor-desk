"""018C 低成本数据接口探针：路由矩阵、能力注册与证据落盘。"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from backend.app.datasources.adapters.fetch_port import FetchPayload, StubFetchPort
from backend.app.datasources.capability_registry import (
    OperationDisabledError,
    SourceCapabilityRegistry,
)
from backend.app.ops.interface_probe import (
    SIDECAR_SINA_OPERATION,
    build_route_matrix,
    decide_closeout,
    run_interface_probe,
)

ROOT = Path(__file__).resolve().parents[1]


def _yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def test_tdxPytdx_disabledByDefault() -> None:
    """覆盖范围：source_registry 中 tdx_pytdx 默认启用策略
    测试对象：tdx_pytdx 注册表条目
    目的/目标：TDX 探针源必须默认关闭且标记为仅校验用途
    验证点：enabled_by_default=False；validation_only=True
    失败含义：TDX 默认可用，违反 018C fail-closed 与 live pilot 策略
    """
    entry = next(
        s
        for s in _yaml(ROOT / "specs/datasource_registry/source_registry.yaml")["sources"]
        if s["source_id"] == "tdx_pytdx"
    )
    assert entry["enabled_by_default"] is False
    assert entry["validation_only"] is True


def test_capabilityRegistry_rejectsTdxPytdx() -> None:
    """覆盖范围：SourceCapabilityRegistry 对禁用源的操作断言
    测试对象：assert_source_domain_operation('tdx_pytdx', ...)
    目的/目标：能力层须拒绝对已禁用 TDX 源发起 fetch
    验证点：抛出 OperationDisabledError
    失败含义：禁用源仍可通过能力注册表调用，路由门禁失效
    """
    reg = SourceCapabilityRegistry()
    reg.load()
    with pytest.raises(OperationDisabledError):
        reg.assert_source_domain_operation("tdx_pytdx", "cn_equity_daily_bar", "fetch_daily_bar")


def test_sinaSidecar_distinctFromEastmoneyHist() -> None:
    """覆盖范围：akshare 日 K 校验的两条并行 vendor API
    测试对象：source_capabilities.yaml 中 cn_equity_daily_bar operations
    目的/目标：新浪 sidecar 须与东财 stock_zh_a_hist 使用不同 vendor_api
    验证点：fetch_daily_bar_validation→stock_zh_a_hist；sina→stock_zh_a_daily
    失败含义：两条校验路径实为同一 API，018C sidecar 去重目标未达成
    """
    ops = _yaml(ROOT / "specs/datasource_registry/source_capabilities.yaml")["sources"]["akshare"][
        "domains"
    ]["cn_equity_daily_bar"]["operations"]
    assert ops["fetch_daily_bar_validation"]["vendor_api"] == "stock_zh_a_hist"
    assert ops["fetch_daily_bar_sina_validation"]["vendor_api"] == "stock_zh_a_daily"


def test_routeMatrix_tdxFailClosed() -> None:
    """覆盖范围：build_route_matrix 对 tdx_pytdx 的路由预览
    测试对象：route matrix 中 source_id=tdx_pytdx 的行
    目的/目标：TDX 在所有 domain 预览中均不得被选为可用主源
    验证点：source_enabled_by_default=False；selected_source_id≠tdx_pytdx
    失败含义：路由矩阵仍将 TDX 选为主源，探针 fail-closed 破裂
    """
    for row in build_route_matrix()["routes"]:
        if row["source_id"] == "tdx_pytdx":
            assert not row["source_enabled_by_default"]
            assert row["selected_source_id"] != "tdx_pytdx"


def test_decision_doesNotCloseRequest2() -> None:
    """覆盖范围：interface probe 结案判定对 R3-B2.75-REQ2-EM 的边界
    测试对象：decide_closeout
    目的/目标：新浪 sidecar 探针成功不得宣告关闭东财 hist 缺口
    验证点：does_not_close_R3-B2.75-REQ2-EM 为真；不解除 production_live_readiness 阻塞
    失败含义：低成本探针被误当作 REQ2 结案，审计追踪被提前关闭
    """
    d = decide_closeout(
        [{"operation": SIDECAR_SINA_OPERATION, "status": "SUCCESS"}],
        build_route_matrix(),
    )
    assert d["does_not_close_R3-B2.75-REQ2-EM"]
    assert d["does_not_unblock_production_live_readiness"]


def test_r3h10_interfaceProbeFetchDelegatesThroughDataSourceService(
    tmp_path: Path, monkeypatch
) -> None:
    """覆盖范围：interface_probe 网络 fetch 经 DataSourceService（S10-04）
    测试对象：run_single_probe → _fetch_payload_via_service
    目的/目标：probe 不得 silent bypass C2 facade 直调 port.fetch_payload
    验证点：port.fetch_payload 未调用；record rehearsal_only 且 status=SUCCESS 且 row_count≥1
    失败含义：probe 仍直连 fetch_ports，旁路 route/guard/fetch_log 链
    """
    from backend.app.datasources.adapters.fetch_port import FetchPayload
    from backend.app.datasources.fetch_result import FetchResult
    from backend.app.ops.interface_probe import PROBE_TARGETS, run_single_probe

    port_calls: list[str] = []

    class _SpyService:
        def __init__(self, **kwargs):
            pass

        def fetch(self, req, *, con, job_id=None, operation=None):
            raw = tmp_path / "raw.json"
            raw.write_text('{"rows":[{"x":1}]}', encoding="utf-8")
            return FetchResult(
                run_id=req.run_id,
                source_id=req.source_id,
                data_domain=req.data_domain,
                status="SUCCESS",
                row_count=1,
                fetch_time="2026-06-29T00:00:00Z",
                raw_file_paths=[str(raw)],
            )

    class _SpyPort:
        def fetch_payload(self, req):
            port_calls.append("fetch_payload")
            return FetchPayload(content=b"{}", file_type="json", row_count=0)

    monkeypatch.setattr("backend.app.ops.interface_probe.DataSourceService", _SpyService)
    monkeypatch.setattr(
        "backend.app.ops.interface_probe._resolve_fetch_port",
        lambda target: _SpyPort(),
    )

    target = next(t for t in PROBE_TARGETS if t.operation == "fetch_daily_bar_sina_validation")
    record = run_single_probe(target, sandbox_root=tmp_path / "sandbox")
    assert port_calls == []
    assert record.get("rehearsal_only") is True
    assert record["status"] == "SUCCESS"
    assert record.get("row_count", 0) >= 1


def test_r3h10_interfaceProbeRunSingleProbeUsesFetchViaServiceHelper() -> None:
    """覆盖范围：run_single_probe 成功路径源码守卫（S10-04 负向回归）
    测试对象：backend.app.ops.interface_probe.run_single_probe 源码
    目的/目标：移除 _fetch_payload_via_service 时本测应 RED（源码级守门）
    验证点：run_single_probe 源码含 _fetch_payload_via_service 调用
    失败含义：probe 可改回 port.fetch_payload 直连而不被测试发现
    """
    import inspect

    from backend.app.ops import interface_probe

    src = inspect.getsource(interface_probe.run_single_probe)
    assert "_fetch_payload_via_service" in src


def test_runInterfaceProbe_writesEvidence(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：run_interface_probe 端到端证据落盘
    测试对象：run_interface_probe
    目的/目标：探针运行后须在 evidence 目录写出决策 Markdown
    验证点：interface_probe_decision.md 文件存在
    失败含义：探针无审计证据，018C 手工复核无法追溯
    """
    from backend.app.datasources.fetch_result import FetchResult

    monkeypatch.setattr("backend.app.ops.interface_probe._safe_key_table_row_counts", lambda _p: {})
    monkeypatch.setattr(
        "backend.app.ops.interface_probe.build_route_matrix",
        lambda: {"generated_at": "2026-06-29T00:00:00Z", "routes": []},
    )

    class _OkService:
        def __init__(self, **kwargs):
            pass

        def fetch(self, req, *, con, job_id=None, operation=None):
            raw = tmp_path / "probe-raw.json"
            raw.write_text("{}", encoding="utf-8")
            return FetchResult(
                run_id=req.run_id,
                source_id=req.source_id,
                data_domain=req.data_domain,
                status="SUCCESS",
                row_count=1,
                fetch_time="2026-06-29T00:00:00Z",
                raw_file_paths=[str(raw)],
            )

    monkeypatch.setattr("backend.app.ops.interface_probe.DataSourceService", _OkService)
    monkeypatch.setattr(
        "backend.app.ops.interface_probe._resolve_fetch_port",
        lambda t: StubFetchPort(payload=b"{}"),
    )

    db = tmp_path / "db.duckdb"
    db.write_bytes(b"x")
    ev = tmp_path / "evidence"
    run_interface_probe(evidence_dir=ev, sandbox_root=tmp_path / "sb", db_path=db)
    assert (ev / "interface_probe_decision.md").is_file()


def test_tdxAdapter_registeredInFactory() -> None:
    """覆盖范围：适配器工厂注册表（ADV-A2-009）
    测试对象：_ADAPTER_TYPES
    目的/目标：tdx_pytdx 须已注册到工厂，但默认启用仍由 registry 控制
    验证点：'tdx_pytdx' in _ADAPTER_TYPES
    失败含义：TDX 适配器未接入工厂，探针/路由无法实例化
    """
    from backend.app.datasources.adapters import _ADAPTER_TYPES

    assert "tdx_pytdx" in _ADAPTER_TYPES
