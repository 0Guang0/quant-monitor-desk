"""R3H-04 预测市场适配器测试（Batch 3H）。

覆盖范围：kalshi、polymarket 的 fetch port、probability_signal 证据契约、路由与 Layer smoke。
测试对象：backend/app/datasources/normalizers/probability_signal.py 及 kalshi/polymarket fetch port 模块。
目的/目标：证明预测市场源可在 replay-first 路径下产出 probability_signal_evidence_v1 并满足 route/registry 终态。
验证点：各 step 子集（evidence_contract、kalshi、polymarket、layer）通过当前 pytest 验收。
失败含义：Batch 3H R3H-04 无法在 Round4 前闭合预测市场源生产入口决策。
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from backend.app.config import PROJECT_ROOT
from tests.service_path_support import enable_source_route, patch_fetch_port_evidence_adapter

_KALSHI_REPLAY = (
    PROJECT_ROOT / "tests/fixtures/replay/prediction_market/kalshi/probability_replay.json"
)
_POLYMARKET_REPLAY = (
    PROJECT_ROOT
    / "tests/fixtures/replay/prediction_market/polymarket/probability_replay.json"
)
_POLY_ADVERSARIAL = (
    PROJECT_ROOT
    / "tests/fixtures/replay/prediction_market/polymarket/adversarial_resolved_outcome.json"
)


def test_bootSkeleton_testModuleLoads() -> None:
    """覆盖范围：Execute 9.0 预测市场测试模块骨架是否可加载
    测试对象：tests/test_prediction_market_adapters.py 模块本身
    目的/目标：确认 R3H-04 专用测试文件已登记且 pytest 可收集
    验证点：模块 docstring 声明 kalshi/polymarket 覆盖范围
    失败含义：Execute 无法在本模块追加预测市场适配器回归用例
    """
    import tests.test_prediction_market_adapters as mod

    assert "kalshi" in (mod.__doc__ or "")
    assert "polymarket" in (mod.__doc__ or "")


def test_bootSkeleton_probabilitySignalNormalizerModuleExists() -> None:
    """覆盖范围：Execute 9.0 probability_signal normalizer 模块可导入
    测试对象：backend.app.datasources.normalizers.probability_signal
    目的/目标：确认 R3H-04 证据 normalizer SSOT 已落地
    验证点：PROBABILITY_SIGNAL_EVIDENCE_SCHEMA_VERSION 非空
    失败含义：probability_signal_evidence_v1 normalizer 缺失，后续 port 无 SSOT
    """
    from backend.app.datasources.normalizers import probability_signal as mod

    assert mod.PROBABILITY_SIGNAL_EVIDENCE_SCHEMA_VERSION == "probability_signal_evidence_v1"


def test_evidence_contract_writeReadRoundTrip_fixturePreservesFields(tmp_path: Path) -> None:
    """覆盖范围：probability_signal 证据包 read/write 往返
    测试对象：write_probability_signal_evidence_bundle + read_probability_signal_evidence_bundle
    目的/目标：replay fixture 经 normalizer 无损读写 canonical 概率字段
    验证点：source_fetch_id、content_hash、schema_hash、probability 保留；无禁止字段
    失败含义：probability_signal_evidence_v1 无法贯通 replay 链，9.1 契约未闭合
    """
    from backend.app.datasources.normalizers.probability_signal import (
        FORBIDDEN_RESOLUTION_FIELDS,
        PROBABILITY_SIGNAL_EVIDENCE_SCHEMA_VERSION,
        read_probability_signal_evidence_bundle,
        write_probability_signal_evidence_bundle,
    )

    legacy = json.loads(_KALSHI_REPLAY.read_text(encoding="utf-8"))
    out = tmp_path / "roundtrip"
    write_probability_signal_evidence_bundle(out, legacy)
    bundle = read_probability_signal_evidence_bundle(out)
    assert bundle["schema_version"] == PROBABILITY_SIGNAL_EVIDENCE_SCHEMA_VERSION
    assert bundle["source_fetch_id"] == "kalshi-replay-kxhighny"
    assert bundle["content_hash"]
    assert bundle.get("schema_hash")
    assert bundle.get("fetch_log")
    for field in FORBIDDEN_RESOLUTION_FIELDS:
        assert field not in bundle
        for sig in bundle.get("signals") or []:
            assert field not in sig


def test_evidence_contract_replayFixture_probabilityCanonical() -> None:
    """覆盖范围：Kalshi replay fixture 与 normalizer 读路径
    测试对象：tests/fixtures/replay/prediction_market/kalshi/probability_replay.json
    目的/目标：replay 使用 probability_signal_evidence_v1 canonical 字段
    验证点：read 往返；source_id 与 market_ticker、probability 稳定
    失败含义：replay 仍依赖 legacy 字段，registry 无法登记路径
    """
    from backend.app.datasources.normalizers.probability_signal import (
        PROBABILITY_SIGNAL_EVIDENCE_SCHEMA_VERSION,
        read_probability_signal_evidence_bundle,
    )

    bundle = read_probability_signal_evidence_bundle(_KALSHI_REPLAY)
    assert bundle["schema_version"] == PROBABILITY_SIGNAL_EVIDENCE_SCHEMA_VERSION
    assert bundle["source_id"] == "kalshi"
    assert bundle["signals"][0]["market_ticker"] == "KXHIGHNY-24"
    assert bundle["signals"][0]["probability"] == 0.435


def test_evidence_contract_polymarketReplay_hasLiquiditySpreadResolutionSource() -> None:
    """覆盖范围：Polymarket replay liquidity/spread/resolution_source 契约
    测试对象：polymarket probability_replay.json + read_probability_signal_evidence_bundle
    目的/目标：polymarket 须记录 liquidity、volume、spread、resolution_source（URL 元数据）
    验证点：spread/liquidity/volume 存在；resolution_source 为 URL 字符串
    失败含义：polymarket 概率证据缺流动性/价差元数据，无法区分于 kalshi
    """
    from backend.app.datasources.normalizers.probability_signal import (
        read_probability_signal_evidence_bundle,
    )

    bundle = read_probability_signal_evidence_bundle(_POLYMARKET_REPLAY)
    sig = bundle["signals"][0]
    assert sig.get("liquidity") == 120000
    assert sig.get("volume") == 45000
    assert sig.get("spread") == 0.02
    assert str(sig.get("resolution_source", "")).startswith("https://")
    assert sig.get("resolved") is None
    assert sig.get("resolved_outcome") is None


def _prediction_req(source_id: str, data_domain: str, instrument_id: str, **overrides: object):
    from backend.app.datasources.fetch_result import FetchRequest

    base = {
        "run_id": f"r3h04-{source_id}",
        "source_id": source_id,
        "data_domain": data_domain,
        "instrument_id": instrument_id,
    }
    base.update(overrides)
    return FetchRequest(**base)


def test_kalshi_port_mockFetch_emitsProbabilitySignalEvidenceV1() -> None:
    """覆盖范围：mock Kalshi port 默认安全抓取
    测试对象：create_kalshi_fetch_port + KalshiMockFetchPort.fetch_payload
    目的/目标：port 直接产出 probability_signal_evidence_v1，无 factual resolution
    验证点：schema_version、signals[].probability、source_fetch_id、content_hash
    失败含义：L2 port 仍输出 legacy rows 形状，无法登记 READY_WITH_EVIDENCE
    """
    from backend.app.datasources.fetch_ports.kalshi_port import create_kalshi_fetch_port
    from backend.app.datasources.normalizers.probability_signal import (
        PROBABILITY_SIGNAL_EVIDENCE_SCHEMA_VERSION,
    )

    port = create_kalshi_fetch_port(market_tickers=("KXHIGHNY-24",), max_markets=1)
    payload = port.fetch_payload(
        _prediction_req("kalshi", "prediction_market_probability", "KXHIGHNY-24")
    )
    body = json.loads(payload.content.decode("utf-8"))
    assert body["schema_version"] == PROBABILITY_SIGNAL_EVIDENCE_SCHEMA_VERSION
    assert body["source_fetch_id"]
    assert body["content_hash"]
    assert body.get("schema_hash")
    assert body["signals"][0].get("probability") is not None
    assert "factual_resolution" not in body
    assert "resolved_outcome" not in body["signals"][0]


def test_kalshi_port_capOverflow_blocksOverMaxMarkets() -> None:
    """覆盖范围：Kalshi port 市场数 cap 溢出
    测试对象：KalshiMockFetchPort 构造 max_markets 超上限
    目的/目标：任务卡 cap 在 port 层硬拒绝
    验证点：max_markets 超 MAX_MARKETS 时 fetch 前 PortError
    失败含义：cap 可被 port 参数绕过导致无界市场扫描
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.kalshi_port import (
        MAX_MARKETS,
        create_kalshi_fetch_port,
    )

    port = create_kalshi_fetch_port(
        market_tickers=("KXHIGHNY-24",), max_markets=MAX_MARKETS + 1
    )
    with pytest.raises(PortError, match="cap"):
        port.fetch_payload(
            _prediction_req("kalshi", "prediction_market_probability", "KXHIGHNY-24")
        )


def test_polymarket_port_capOverflow_blocksOverMaxMarkets() -> None:
    """覆盖范围：Polymarket port 市场数 cap 溢出
    测试对象：PolymarketMockFetchPort 构造 max_markets 超上限
    目的/目标：任务卡 cap 在 port 层硬拒绝（对称 kalshi）
    验证点：max_markets 超 MAX_MARKETS 时 fetch 前 PortError
    失败含义：polymarket cap 可被 port 参数绕过
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.polymarket_port import (
        MAX_MARKETS,
        create_polymarket_fetch_port,
    )

    port = create_polymarket_fetch_port(
        market_slugs=("will-fed-cut-rates-2024",), max_markets=MAX_MARKETS + 1
    )
    with pytest.raises(PortError, match="cap"):
        port.fetch_payload(
            _prediction_req("polymarket", "prediction_market_probability", "will-fed-cut-rates-2024")
        )


def test_kalshi_port_windowSpan_blocksOverMaxWindowDays() -> None:
    """覆盖范围：Kalshi fetch 窗口天数 cap
    测试对象：KalshiMockFetchPort.fetch_payload start/end 跨度
    目的/目标：§7 max_window_days=30 在 fetch 入口 reject
    验证点：31 日历日窗口触发 PortError 且消息含 cap
    失败含义：window cap 未接线
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.kalshi_port import (
        MAX_WINDOW_DAYS,
        create_kalshi_fetch_port,
    )

    port = create_kalshi_fetch_port(market_tickers=("KXHIGHNY-24",), max_markets=1)
    end = datetime.now(UTC).date()
    start = end - timedelta(days=MAX_WINDOW_DAYS + 1)
    req = _prediction_req(
        "kalshi",
        "prediction_market_probability",
        "KXHIGHNY-24",
        start_time=start.isoformat(),
        end_time=end.isoformat(),
    )
    with pytest.raises(PortError, match="cap"):
        port.fetch_payload(req)


def test_polymarket_port_windowSpan_blocksOverMaxWindowDays() -> None:
    """覆盖范围：Polymarket fetch 窗口天数 cap
    测试对象：PolymarketMockFetchPort.fetch_payload start/end 跨度
    目的/目标：§7 max_window_days=30 在 fetch 入口 reject
    验证点：31 日历日窗口触发 PortError
    失败含义：polymarket window cap 未接线
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.polymarket_port import (
        MAX_WINDOW_DAYS,
        create_polymarket_fetch_port,
    )

    port = create_polymarket_fetch_port(
        market_slugs=("will-fed-cut-rates-2024",), max_markets=1
    )
    end = datetime.now(UTC).date()
    start = end - timedelta(days=MAX_WINDOW_DAYS + 1)
    req = _prediction_req(
        "polymarket",
        "prediction_market_probability",
        "will-fed-cut-rates-2024",
        start_time=start.isoformat(),
        end_time=end.isoformat(),
    )
    with pytest.raises(PortError, match="cap"):
        port.fetch_payload(req)


def test_resolve_probabilityNormalizer_rejectsForbiddenResolutionField() -> None:
    """覆盖范围：normalizer 拒绝禁止 resolve 字段
    测试对象：build_probability_signal_evidence_bundle + adversarial fixture
    目的/目标：tampered replay 不得通过 read 路径
    验证点：含 resolved_outcome 的 fixture → ProbabilitySignalEvidenceError
    失败含义：对抗 fixture 可绕过禁止字段守卫
    """
    from backend.app.datasources.normalizers.probability_signal import (
        ProbabilitySignalEvidenceError,
        read_probability_signal_evidence_bundle,
    )

    with pytest.raises(ProbabilitySignalEvidenceError, match="forbidden"):
        read_probability_signal_evidence_bundle(_POLY_ADVERSARIAL)


def test_resolve_probabilityNormalizer_rejectsNonUrlResolutionSource() -> None:
    """覆盖范围：resolution_source 须为 URL 元数据
    测试对象：build_probability_signal_evidence_bundle
    目的/目标：禁止含 resolution 语义的纯文本充当 resolution_source
    验证点：非 http(s) URL → ProbabilitySignalEvidenceError
    失败含义：resolution_source 可承载事实判定语义
    """
    from backend.app.datasources.normalizers.probability_signal import (
        ProbabilitySignalEvidenceError,
        build_probability_signal_evidence_bundle,
    )

    with pytest.raises(ProbabilitySignalEvidenceError, match="http"):
        build_probability_signal_evidence_bundle(
            signals=[
                {
                    "market_slug": "x",
                    "probability": 0.5,
                    "resolution_source": "Market resolved YES on Jan 1",
                    "source_used": "polymarket",
                }
            ],
            data_domain="prediction_market_probability",
            source_id="polymarket",
            source_fetch_id="test",
            content_hash="hash",
            as_of_timestamp="2024-01-01T00:00:00Z",
        )


def test_kalshi_port_route_readyWhenSourceEnabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：显式启用 kalshi 后 route READY
    测试对象：SourceRoutePlanner + kalshi prediction_market_probability 域
    目的/目标：registry/capability READY 后 route 可选中 kalshi
    验证点：route_status=READY；selected_source_id=kalshi
    失败含义：即使源已启用也无法 route 到 Kalshi port
    """
    planner = enable_source_route(
        monkeypatch,
        source_id="kalshi",
        data_domain="prediction_market_probability",
    )
    plan = planner.plan(
        data_domain="prediction_market_probability",
        operation="fetch_prediction_market_probability",
        run_id="r3h04-kalshi-route-ready",
        job_id="kalshi-route-positive",
    )
    assert plan.route_status == "READY"
    assert plan.selected_source_id == "kalshi"


def test_kalshi_port_route_disabledWhenSourceUnauthorized() -> None:
    """覆盖范围：默认禁用 kalshi 路由
    测试对象：SourceRoutePlanner.plan（prediction_market_probability）
    目的/目标：enabled_by_default=false 时 route DISABLED_SOURCE
    验证点：route_status=DISABLED_SOURCE；selected_source_id=None
    失败含义：未显式启用的预测市场源被误选为 production primary
    """
    from tests.service_path_support import production_route_planner

    planner = production_route_planner()
    plan = planner.plan(
        data_domain="prediction_market_probability",
        operation="fetch_prediction_market_probability",
        run_id="r3h04-kalshi-route-disabled",
        job_id="kalshi-route-negative",
    )
    assert plan.route_status == "DISABLED_SOURCE"
    assert plan.selected_source_id is None
    candidate = next((c for c in plan.candidates if c.source_id == "kalshi"), None)
    assert candidate is not None
    assert candidate.enabled is False


def test_polymarket_port_mockFetch_emitsProbabilitySignalWithSpread() -> None:
    """覆盖范围：mock Polymarket port 概率/流动性抓取
    测试对象：create_polymarket_fetch_port + PolymarketMockFetchPort.fetch_payload
    目的/目标：port 产出 probability_signal_evidence_v1 含 spread/resolution_source
    验证点：schema_version、spread、liquidity、resolution_source URL
    失败含义：Polymarket 无 port 路径或缺流动性元数据
    """
    from backend.app.datasources.fetch_ports.polymarket_port import create_polymarket_fetch_port
    from backend.app.datasources.normalizers.probability_signal import (
        PROBABILITY_SIGNAL_EVIDENCE_SCHEMA_VERSION,
    )

    port = create_polymarket_fetch_port(
        market_slugs=("will-fed-cut-rates-2024",), max_markets=1
    )
    payload = port.fetch_payload(
        _prediction_req("polymarket", "prediction_market_probability", "will-fed-cut-rates-2024")
    )
    body = json.loads(payload.content.decode("utf-8"))
    assert body["schema_version"] == PROBABILITY_SIGNAL_EVIDENCE_SCHEMA_VERSION
    sig = body["signals"][0]
    assert sig.get("spread") is not None
    assert sig.get("liquidity") is not None
    assert str(sig.get("resolution_source", "")).startswith("https://")


def test_polymarket_port_route_readyWhenSourceEnabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：显式启用 polymarket 后 route READY（Validation 候选）
    测试对象：SourceRoutePlanner + prediction_market_probability 域
    目的/目标：polymarket validation_only 作 Validation 候选时可 route
    验证点：route_status=READY；selected_source_id=polymarket
    失败含义：polymarket 无法 route 到 replay port
    """
    planner = enable_source_route(
        monkeypatch,
        source_id="polymarket",
        data_domain="prediction_market_probability",
    )
    plan = planner.plan(
        data_domain="prediction_market_probability",
        operation="fetch_prediction_market_probability",
        run_id="r3h04-poly-route-ready",
        job_id="poly-route-positive",
        extra_candidates=[("polymarket", "Validation")],
    )
    assert plan.route_status == "READY"
    assert plan.selected_source_id == "polymarket"


def test_layer_smoke_kalshiReplay_probabilitySignalProvenance() -> None:
    """覆盖范围：Kalshi replay → Layer5 provenance（概率信号，非事实判定）
    测试对象：probability_signal_bundle_layer5_provenance + EvidenceFoundationValidator
    目的/目标：概率证据可溯源但不 resolve 事件结果
    验证点：provenance 有 fetch_id/hash；FACTUAL_SOURCE 校验通过；summary 无 resolve 语义
    失败含义：预测市场证据无法绑定 Layer5 或误升格为事实判定
    """
    from backend.app.datasources.normalizers.probability_signal import (
        probability_signal_bundle_layer5_provenance,
        read_probability_signal_evidence_bundle,
    )
    from backend.app.layer5_evidence.foundation import EvidenceFoundationValidator
    from backend.app.layer5_evidence.models import (
        EvidenceFoundationRecord,
        EvidenceKind,
        ManualReviewState,
        SourceProvenance,
    )

    bundle = read_probability_signal_evidence_bundle(_KALSHI_REPLAY)
    prov_fields = probability_signal_bundle_layer5_provenance(bundle)
    assert prov_fields["source_fetch_ids"] == ("kalshi-replay-kxhighny",)
    assert prov_fields["source_content_hashes"] == ("kalshi-replay-hash-kxhighny",)
    record = EvidenceFoundationRecord(
        evidence_id="r3h04-kalshi-layer",
        target_id="KXHIGHNY-24",
        target_type="prediction_market_contract",
        trade_date=date(2024, 6, 25),
        evidence_kind=EvidenceKind.DERIVED_VALIDATION,
        evidence_summary="Kalshi probability signal 0.435; not a resolved outcome",
        need_human_review=False,
        manual_review_state=ManualReviewState.NOT_REQUIRED,
        created_by="r3h04_layer_smoke",
        provenance=SourceProvenance(
            source_fetch_ids=prov_fields["source_fetch_ids"],
            source_content_hashes=prov_fields["source_content_hashes"],
        ),
    )
    EvidenceFoundationValidator().validate_record(record)


def test_layer_smoke_polymarketReplay_resolutionSourceIsMetadataOnly() -> None:
    """覆盖范围：Polymarket resolution_source 仅为 URL 元数据
    测试对象：polymarket replay bundle signals[]
    目的/目标：resolution_source 不得表示 resolved=true 或事实判定
    验证点：resolution_source 为 URL；无 resolved/resolved_outcome 字段
    失败含义：polymarket 价格/metadata 被误读为事实结果
    """
    from backend.app.datasources.normalizers.probability_signal import (
        read_probability_signal_evidence_bundle,
    )

    bundle = read_probability_signal_evidence_bundle(_POLYMARKET_REPLAY)
    sig = bundle["signals"][0]
    assert "resolved" not in sig
    assert "resolved_outcome" not in sig
    assert str(sig["resolution_source"]).startswith("https://")


def test_kalshi_port_liveWithoutOptIn_blocksUnauthorized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：未 opt-in 的 Kalshi live fetch
    测试对象：create_kalshi_fetch_port(use_mock=False) + ProductLiveGate
    目的/目标：缺 QMD_ALLOW_LIVE_FETCH 时产品 live 路径 fail-closed
    验证点：ProductLiveGateError code=LIVE_FETCH_REJECTED；不得 silent 联网
    失败含义：无用户 gate 仍可 capped live fetch，违反 R3H-04 §2.8
    """
    from backend.app.datasources.fetch_ports.kalshi_port import create_kalshi_fetch_port
    from backend.app.datasources.product_live_gate import ProductLiveGateError

    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    with pytest.raises(ProductLiveGateError) as exc_info:
        create_kalshi_fetch_port(
            market_tickers=("KXHIGHNY-24",), max_markets=1, use_mock=False
        )
    assert exc_info.value.code == "LIVE_FETCH_REJECTED"


def test_polymarket_port_liveWithoutOptIn_blocksUnauthorized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：未 opt-in 的 Polymarket live fetch
    测试对象：create_polymarket_fetch_port(use_mock=False) + ProductLiveGate
    目的/目标：缺 QMD_ALLOW_LIVE_FETCH 时产品 live 路径 fail-closed
    验证点：ProductLiveGateError code=LIVE_FETCH_REJECTED
    失败含义：无用户 gate 仍可 capped live fetch
    """
    from backend.app.datasources.fetch_ports.polymarket_port import create_polymarket_fetch_port
    from backend.app.datasources.product_live_gate import ProductLiveGateError

    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    with pytest.raises(ProductLiveGateError) as exc_info:
        create_polymarket_fetch_port(
            market_slugs=("will-fed-cut-rates-2024",), max_markets=1, use_mock=False
        )
    assert exc_info.value.code == "LIVE_FETCH_REJECTED"


def test_kalshi_liveSmoke_authorizationYamlPresent() -> None:
    """覆盖范围：Kalshi live smoke 授权 YAML SSOT 落盘
    测试对象：PREDICTION_LIVE_AUTHORIZATION_DEFAULT
    目的/目标：Tier B live smoke 须有 audit-sandbox 授权证据
    验证点：authorization_present=true；kalshi.enabled=true
    失败含义：live smoke 无授权样板，handoff 无法证明用户 gate
    """
    from backend.app.ops.prediction_market_live_smoke import (
        PREDICTION_LIVE_AUTHORIZATION_DEFAULT,
        load_prediction_live_authorization,
    )

    assert PREDICTION_LIVE_AUTHORIZATION_DEFAULT.is_file()
    auth = load_prediction_live_authorization(PREDICTION_LIVE_AUTHORIZATION_DEFAULT)
    assert auth["authorization_present"] is True
    assert auth["kalshi"]["enabled"] is True


@pytest.mark.skipif(
    __import__("os").environ.get("KALSHI_LIVE_SMOKE", "").strip().lower() not in {"1", "true", "yes"},
    reason="KALSHI_LIVE_SMOKE not set — Tier B optional live smoke",
)
def test_kalshi_liveSmoke_envGated_writesEvidenceToAuditSandbox(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：env-gated Kalshi capped live smoke 证据落盘
    测试对象：run_kalshi_live_smoke
    目的/目标：用户 Gate 下 live fetch 产出 probability_signal 并写入 audit-sandbox
    验证点：evidence JSON 含 live_smoke=true；bundle.schema_version=probability_signal_evidence_v1
    失败含义：capped live smoke 路径不可执行或证据未落盘
    """
    from backend.app.ops.prediction_market_live_smoke import run_kalshi_live_smoke

    monkeypatch.setenv("KALSHI_LIVE_SMOKE", "1")
    out = tmp_path / "kalshi_live_smoke_evidence.json"
    evidence_path = run_kalshi_live_smoke(
        market_ticker="KXFED-27APR-T4.25",
        evidence_path=out,
    )
    record = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert record["live_smoke"] is True
    assert record["sandbox_only"] is True
    assert record["bundle"]["schema_version"] == "probability_signal_evidence_v1"
    assert "factual_resolution" not in record["bundle"]


@pytest.mark.skipif(
    __import__("os").environ.get("POLYMARKET_LIVE_SMOKE", "").strip().lower()
    not in {"1", "true", "yes"},
    reason="POLYMARKET_LIVE_SMOKE not set — Tier B optional live smoke",
)
def test_polymarket_liveSmoke_envGated_writesEvidenceToAuditSandbox(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：env-gated Polymarket capped live smoke 证据落盘
    测试对象：run_polymarket_live_smoke
    目的/目标：用户 Gate 下 live fetch 产出 probability_signal 并写入 audit-sandbox
    验证点：evidence JSON 含 live_smoke=true；signals 含 spread/liquidity 字段位
    失败含义：polymarket capped live smoke 未闭合
    """
    from backend.app.ops.prediction_market_live_smoke import run_polymarket_live_smoke

    monkeypatch.setenv("POLYMARKET_LIVE_SMOKE", "1")
    out = tmp_path / "polymarket_live_smoke_evidence.json"
    evidence_path = run_polymarket_live_smoke(
        market_slug="kraken-ipo-in-2025",
        evidence_path=out,
    )
    record = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert record["live_smoke"] is True
    sig = record["bundle"]["signals"][0]
    assert sig.get("probability") is not None
    assert "resolved_outcome" not in sig


def test_predictionMarket_dataSourceService_fetch_portIntegration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：DataSourceService.fetch 经 injected fetch_port 拉取三源证据
    测试对象：DataSourceService.fetch + kalshi/polymarket/web_search mock port
    目的/目标：证明 orchestrator 门面可贯通 L3 evidence port（staged_fixture_mode）
    验证点：三源各 1 条 SUCCESS；bundle schema_version 符合契约
    失败含义：三源仅孤立 port 测试，服务链未接入
    """
    from backend.app.datasources.fetch_ports.kalshi_port import create_kalshi_fetch_port
    from backend.app.datasources.fetch_ports.polymarket_port import create_polymarket_fetch_port
    from backend.app.datasources.fetch_ports.web_search_evidence_port import (
        create_web_search_evidence_fetch_port,
    )
    from backend.app.datasources.fetch_result import FetchRequest
    from backend.app.datasources.service import DataSourceService
    from backend.app.db.connection import ConnectionManager
    from backend.app.db.migrate import apply_migrations
    from backend.app.evidence.manual_review_staging import WEB_EVIDENCE_STAGING_SCHEMA_VERSION

    monkeypatch.setattr(
        "backend.app.datasources.capability_registry.SourceCapabilityRegistry.assert_source_domain_operation",
        lambda self, *_args, **_kwargs: None,
    )

    cases = (
        (
            "kalshi",
            "prediction_market_probability",
            create_kalshi_fetch_port(market_tickers=("KXHIGHNY-24",), max_markets=1),
            "KXHIGHNY-24",
            "probability_signal_evidence_v1",
        ),
        (
            "polymarket",
            "prediction_market_probability",
            create_polymarket_fetch_port(market_slugs=("will-fed-cut-rates-2024",), max_markets=1),
            "will-fed-cut-rates-2024",
            "probability_signal_evidence_v1",
        ),
        (
            "web_search",
            "supplemental_web_evidence",
            create_web_search_evidence_fetch_port(
                queries=("fed rate cut outlook 2024",), max_results=1
            ),
            "fed rate cut outlook 2024",
            WEB_EVIDENCE_STAGING_SCHEMA_VERSION,
        ),
    )
    db = tmp_path / "dss.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    for source_id, domain, port, instrument_id, expected_schema in cases:
        patch_fetch_port_evidence_adapter(monkeypatch, port)
        service = DataSourceService(
            data_root=tmp_path / "raw" / source_id,
            fetch_port=port,
            staged_fixture_mode=True,
        )
        req = FetchRequest(
            run_id=f"r3h04-dss-{source_id}",
            source_id=source_id,
            data_domain=domain,
            instrument_id=instrument_id,
        )
        with cm.writer() as con:
            result = service.fetch(req, con=con, job_id=f"job-{source_id}")
        assert result.status == "SUCCESS"
        assert result.row_count >= 1
        body = port.fetch_payload(req)
        assert expected_schema in body.content.decode("utf-8")


def test_kalshi_liveSmoke_authorizationTemplate_committedForCloneBootstrap() -> None:
    """覆盖范围：live smoke 授权 YAML bootstrap 模板
    测试对象：tests/fixtures/prediction_market_live_authorization.template.yaml
    目的/目标：fresh clone 可复制模板到 audit-sandbox
    验证点：模板含 authorization_present 与三源 enabled 段
    失败含义：gitignore 授权文件无 bootstrap 路径
    """
    from backend.app.ops.prediction_market_live_smoke import load_prediction_live_authorization

    template = PROJECT_ROOT / "tests/fixtures/prediction_market_live_authorization.template.yaml"
    assert template.is_file()
    auth = load_prediction_live_authorization(template)
    assert auth["authorization_present"] is True
    assert auth["kalshi"]["enabled"] is True
    assert auth["polymarket"]["enabled"] is True
