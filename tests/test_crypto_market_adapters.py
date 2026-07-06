"""R3H-02 加密市场数据适配器测试（Batch 3H）。

覆盖范围：deribit、coingecko 的 fetch port、crypto_market 证据契约、路由与 Layer smoke。
测试对象：backend/app/datasources/normalizers/crypto_market.py 及 deribit/coingecko fetch port 模块。
目的/目标：证明加密源可在 replay-first 路径下产出 crypto_market_evidence_v1 并满足 cap/route 终态。
验证点：test_crypto_market_adapters 全量及 -k layer 子集通过当前 pytest 验收。
失败含义：Batch 3H R3H-02 无法在 Round4 前闭合加密市场源生产入口决策。
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
import yaml

from backend.app.config import PROJECT_ROOT

_DERIBIT_REPLAY = (
    PROJECT_ROOT
    / "tests/fixtures/replay/crypto_market/deribit/btc_options_surface_replay.json"
)
_COINGECKO_REPLAY = (
    PROJECT_ROOT / "tests/fixtures/replay/crypto_market/coingecko/btc_spot_replay.json"
)


def test_bootSkeleton_testModuleLoads() -> None:
    """覆盖范围：Execute 9.0 加密市场测试模块骨架是否可加载
    测试对象：tests/test_crypto_market_adapters.py 模块本身
    目的/目标：确认 R3H-02 crypto 测试文件已登记且 pytest 可收集
    验证点：模块 docstring 声明 deribit/coingecko 覆盖
    失败含义：Execute 无法在本模块追加加密市场适配器回归用例
    """
    import tests.test_crypto_market_adapters as mod

    assert "deribit" in (mod.__doc__ or "")
    assert "coingecko" in (mod.__doc__ or "")


def test_bootSkeleton_cryptoMarketNormalizerModuleExists() -> None:
    """覆盖范围：Execute 9.0 crypto_market normalizer 模块可导入
    测试对象：backend.app.datasources.normalizers.crypto_market
    目的/目标：确认 R3H-02 crypto 证据 normalizer SSOT 已落地
    验证点：CRYPTO_MARKET_EVIDENCE_SCHEMA_VERSION 非空
    失败含义：crypto_market_evidence_v1 normalizer 缺失
    """
    from backend.app.datasources.normalizers import crypto_market as mod

    assert mod.CRYPTO_MARKET_EVIDENCE_SCHEMA_VERSION == "crypto_market_evidence_v1"


def test_evidence_contract_writeReadRoundTrip_fixturePreservesFields(tmp_path: Path) -> None:
    """覆盖范围：crypto_market 证据包 read/write 往返
    测试对象：write_crypto_market_evidence_bundle + read_crypto_market_evidence_bundle
    目的/目标：replay fixture 经 normalizer 无损读写 canonical 字段
    验证点：source_fetch_id、content_hash、schema_hash、asset_id 保留
    失败含义：crypto_market_evidence_v1 无法贯通 replay 链
    """
    from backend.app.datasources.normalizers.crypto_market import (
        CRYPTO_MARKET_EVIDENCE_SCHEMA_VERSION,
        read_crypto_market_evidence_bundle,
        write_crypto_market_evidence_bundle,
    )

    legacy = json.loads(_COINGECKO_REPLAY.read_text(encoding="utf-8"))
    out = tmp_path / "roundtrip"
    write_crypto_market_evidence_bundle(out, legacy)
    bundle = read_crypto_market_evidence_bundle(out)
    assert bundle["schema_version"] == CRYPTO_MARKET_EVIDENCE_SCHEMA_VERSION
    assert bundle["source_fetch_id"] == "coingecko-replay-btc"
    assert bundle["content_hash"]
    assert bundle.get("schema_hash")
    assert bundle["instruments"][0]["asset_id"] == "bitcoin"


def _crypto_req(source_id: str, data_domain: str, instrument_id: str, **overrides: object):
    from backend.app.datasources.fetch_result import FetchRequest

    base = {
        "run_id": f"r3h02-{source_id}",
        "source_id": source_id,
        "data_domain": data_domain,
        "instrument_id": instrument_id,
    }
    base.update(overrides)
    return FetchRequest(**base)


def test_deribit_port_mockFetch_emitsCryptoMarketEvidenceV1() -> None:
    """覆盖范围：mock Deribit port 衍生品/期权面抓取
    测试对象：create_deribit_fetch_port + DeribitMockFetchPort.fetch_payload
    目的/目标：port 产出 crypto_market_evidence_v1，无交易/账户语义
    验证点：schema_version、instruments[].instrument_name、mark_iv、source_fetch_id
    失败含义：Deribit 无 port 路径或引入交易 API 面
    """
    from backend.app.datasources.fetch_ports.deribit_port import create_deribit_fetch_port
    from backend.app.datasources.fetch_result import FetchRequest
    from backend.app.datasources.normalizers.crypto_market import (
        CRYPTO_MARKET_EVIDENCE_SCHEMA_VERSION,
    )

    port = create_deribit_fetch_port(
        instruments=("BTC-28JUN24-65000-C",), max_surface_rows=5
    )
    req = FetchRequest(
        run_id="r3h02-deribit",
        source_id="deribit",
        data_domain="crypto_options_surface",
        instrument_id="BTC-28JUN24-65000-C",
    )
    payload = port.fetch_payload(req)
    body = json.loads(payload.content.decode("utf-8"))
    assert body["schema_version"] == CRYPTO_MARKET_EVIDENCE_SCHEMA_VERSION
    assert body["source_id"] == "deribit"
    assert body.get("source_fetch_id")
    inst = (body.get("instruments") or [])[0]
    assert inst.get("instrument_name")
    assert inst.get("mark_iv") is not None
    assert "account" not in json.dumps(body).lower()


def test_deribit_port_capOverflow_blocksOverMaxSurfaceRows() -> None:
    """覆盖范围：Deribit surface 行数 cap 溢出
    测试对象：DeribitMockFetchPort 构造 max_surface_rows 超上限
    目的/目标：ResourceGuard cap 在 port 层硬拒绝
    验证点：max_surface_rows 超 MAX_SURFACE_ROWS 时 PortError
    失败含义：cap 可被绕过导致无界期权面扫描
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.deribit_port import (
        MAX_SURFACE_ROWS,
        create_deribit_fetch_port,
    )
    from backend.app.datasources.fetch_result import FetchRequest

    port = create_deribit_fetch_port(
        instruments=("BTC-28JUN24-65000-C",),
        max_surface_rows=MAX_SURFACE_ROWS + 1,
    )
    req = FetchRequest(
        run_id="r3h02-deribit-cap",
        source_id="deribit",
        data_domain="crypto_options_surface",
        instrument_id="BTC-28JUN24-65000-C",
    )
    with pytest.raises(PortError, match="cap"):
        port.fetch_payload(req)


def test_coingecko_port_capOverflow_blocksOverMaxAssets() -> None:
    """覆盖范围：CoinGecko factory assets 数量 cap
    测试对象：create_coingecko_fetch_port asset_ids 超上限
    目的/目标：§7 max_assets=10 在 factory 层硬拒绝
    验证点：len(asset_ids) > MAX_ASSETS 构造即 PortError
    失败含义：assets cap 可被绕过
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.coingecko_port import MAX_ASSETS, create_coingecko_fetch_port

    with pytest.raises(PortError, match=str(MAX_ASSETS)):
        create_coingecko_fetch_port(
            asset_ids=tuple(f"asset{i}" for i in range(MAX_ASSETS + 1)),
            max_assets=5,
        )


def test_coingecko_port_capOverflow_blocksOverMaxAssetsOnFetch() -> None:
    """覆盖范围：CoinGecko port max_assets 运行时 cap
    测试对象：CoingeckoMockFetchPort max_assets 超上限
    目的/目标：ResourceGuard max_assets=10 在 fetch 层硬拒绝
    验证点：max_assets 超 MAX_ASSETS 时 PortError
    失败含义：CoinGecko cap 无对抗性保护
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.coingecko_port import MAX_ASSETS, create_coingecko_fetch_port

    port = create_coingecko_fetch_port(asset_ids=("bitcoin",), max_assets=MAX_ASSETS + 1)
    with pytest.raises(PortError, match="cap"):
        port.fetch_payload(_crypto_req("coingecko", "crypto_spot_market", "bitcoin"))


def test_coingecko_port_unknownAsset_rejectsWhitelist() -> None:
    """覆盖范围：CoinGecko 未知 asset 白名单负例
    测试对象：CoingeckoMockFetchPort whitelist guard
    目的/目标：P2-02 unknown asset fail-closed
    验证点：非白名单 asset_id 触发 PortError
    失败含义：未知 asset 可穿透 port
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.coingecko_port import create_coingecko_fetch_port

    port = create_coingecko_fetch_port(asset_ids=("bitcoin",), max_assets=5)
    with pytest.raises(PortError, match="whitelist"):
        port.fetch_payload(_crypto_req("coingecko", "crypto_spot_market", "dogecoin"))


def test_deribit_port_unknownInstrument_rejectsWhitelist() -> None:
    """覆盖范围：Deribit 未知 instrument 白名单负例
    测试对象：DeribitMockFetchPort whitelist guard
    目的/目标：P2-02 unknown instrument fail-closed
    验证点：非白名单 instrument_id 触发 PortError
    失败含义：未知 instrument 可穿透 port
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.deribit_port import create_deribit_fetch_port

    port = create_deribit_fetch_port(instruments=("BTC-28JUN24-65000-C",), max_surface_rows=5)
    with pytest.raises(PortError, match="whitelist"):
        port.fetch_payload(_crypto_req("deribit", "crypto_options_surface", "FAKE-OPT"))


def _load_capabilities() -> dict:
    path = PROJECT_ROOT / "specs/datasource_registry/source_capabilities.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _enable_crypto_source_route(
    monkeypatch: pytest.MonkeyPatch,
    *,
    source_id: str,
    data_domain: str,
):
    from backend.app.datasources.capability_registry import SourceCapabilityRegistry
    from backend.app.datasources.route_planner import SourceRoutePlanner
    from backend.app.datasources.source_registry import DomainRoleBinding, SourceRegistry

    registry = SourceRegistry()
    registry.load()
    rec = registry.get(source_id)
    object.__setattr__(rec, "is_enabled", True)
    orig_domain_roles = registry.get_domain_roles

    def _domain_enabled(domain: str):
        binding = orig_domain_roles(domain)
        if domain != data_domain:
            return binding
        return DomainRoleBinding(
            primary_source_id=binding.primary_source_id,
            validation_source_id=binding.validation_source_id,
            fallback_policy=binding.fallback_policy,
            domain_enabled_by_default=True,
            fallback_source_ids=binding.fallback_source_ids,
        )

    monkeypatch.setattr(registry, "get_domain_roles", _domain_enabled)
    capabilities = SourceCapabilityRegistry()
    capabilities.load()
    planner = SourceRoutePlanner(source_registry=registry, capability_registry=capabilities)
    monkeypatch.setattr(planner, "_platform_allows", lambda _sid: (True, None))
    return planner


def test_coingecko_validationOnlySource_blockedAsPrimaryWhenForced(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：coingecko validation-only 不得作为 Primary 路由候选
    测试对象：SourceRoutePlanner + 启用 coingecko 与 crypto_spot_market 域
    目的/目标：R3H02-R-10 加密域 validation-only 路由对抗
    验证点：yaml primary 时 skip_reason=validation_only_cannot_be_primary
    失败含义：aggregator 可 silent 升格 primary
    """
    planner = _enable_crypto_source_route(
        monkeypatch, source_id="coingecko", data_domain="crypto_asset_reference"
    )
    plan = planner.plan(
        data_domain="crypto_asset_reference",
        operation="fetch_crypto_asset_reference",
        run_id="r3h02-valonly-coingecko",
        job_id="valonly-coingecko",
        extra_candidates=[("coingecko", "Primary")],
    )
    candidate = next(c for c in plan.candidates if c.source_id == "coingecko")
    assert candidate.capability_declared is True
    assert candidate.skip_reason == "validation_only_cannot_be_primary"
    assert plan.route_status == "VALIDATION_ONLY_BLOCKED"
    assert plan.selected_source_id is None


@pytest.mark.parametrize(
    ("source_id", "data_domain", "operation", "instrument_id", "port_factory"),
    [
        (
            "deribit",
            "crypto_options_surface",
            "fetch_options_surface",
            "BTC-28JUN24-65000-C",
            lambda: __import__(
                "backend.app.datasources.fetch_ports.deribit_port",
                fromlist=["create_deribit_fetch_port"],
            ).create_deribit_fetch_port(
                instruments=("BTC-28JUN24-65000-C",), max_surface_rows=5
            ),
        ),
        (
            "coingecko",
            "crypto_spot_market",
            "fetch_spot_market_reference",
            "bitcoin",
            lambda: __import__(
                "backend.app.datasources.fetch_ports.coingecko_port",
                fromlist=["create_coingecko_fetch_port"],
            ).create_coingecko_fetch_port(asset_ids=("bitcoin",), max_assets=5),
        ),
    ],
)
def test_r3h02_cryptoCapabilityFields_matchPortOutput(
    source_id: str,
    data_domain: str,
    operation: str,
    instrument_id: str,
    port_factory,
) -> None:
    """覆盖范围：crypto source_capabilities 字段与 port 输出对齐
    测试对象：deribit/coingecko fetch port payload + YAML capability 声明
    目的/目标：R3H02-R-15 契约字段分层闭合
    验证点：观测行键 ⊇ observation_fields；包顶键 ⊇ bundle_fields
    失败含义：registry 字段声明与 crypto port 输出不一致
    """
    caps = (_load_capabilities().get("sources") or {}).get(source_id, {})
    op_spec = (
        ((caps.get("domains") or {}).get(data_domain) or {}).get("operations") or {}
    ).get(operation, {})
    observation_fields = set(op_spec.get("observation_fields") or op_spec.get("fields") or [])
    bundle_fields = set(op_spec.get("bundle_fields") or [])

    body = json.loads(
        port_factory()
        .fetch_payload(_crypto_req(source_id, data_domain, instrument_id))
        .content.decode("utf-8")
    )
    if observation_fields:
        rows = body.get("instruments") or []
        assert rows
        assert observation_fields <= set(rows[0].keys())
    if bundle_fields:
        assert bundle_fields <= set(body.keys())


@pytest.mark.parametrize(
    ("source_id", "yaml_key", "port_attr", "module_name"),
    [
        ("deribit", "max_instruments", "MAX_INSTRUMENTS", "deribit_port"),
        ("deribit", "max_surface_rows", "MAX_SURFACE_ROWS", "deribit_port"),
        ("coingecko", "max_assets", "MAX_ASSETS", "coingecko_port"),
    ],
)
def test_r3h02_cryptoCaps_matchRegistry(
    source_id: str,
    yaml_key: str,
    port_attr: str,
    module_name: str,
) -> None:
    """覆盖范围：crypto registry resource_caps 与 port 常量 parity
    测试对象：source_capabilities.yaml + deribit/coingecko *_port.py
    目的/目标：R3H02-R-16 五源 caps parity（加密子集）
    验证点：YAML cap 值 == port 模块同名常量
    失败含义：registry 与 port cap 漂移
    """
    caps = (_load_capabilities().get("sources") or {}).get(source_id, {}).get("resource_caps") or {}
    mod = __import__(f"backend.app.datasources.fetch_ports.{module_name}", fromlist=[port_attr])
    assert caps[yaml_key] == getattr(mod, port_attr)


def test_deribit_port_replayFixture_instrumentFieldsCanonical() -> None:
    """覆盖范围：Deribit replay fixture 读路径
    测试对象：tests/fixtures/replay/crypto_market/deribit/btc_options_surface_replay.json
    目的/目标：replay 含 instrument_name、mark_iv 等 canonical 字段
    验证点：read_crypto_market_evidence_bundle 往返
    失败含义：Deribit replay 路径缺失
    """
    from backend.app.datasources.normalizers.crypto_market import read_crypto_market_evidence_bundle

    bundle = read_crypto_market_evidence_bundle(_DERIBIT_REPLAY)
    assert bundle["source_id"] == "deribit"
    inst = bundle["instruments"][0]
    assert inst["instrument_name"] == "BTC-28JUN24-65000-C"
    assert inst.get("mark_iv") is not None


def test_coingecko_port_mockFetch_emitsCryptoMarketEvidenceV1() -> None:
    """覆盖范围：mock CoinGecko port 现货参考抓取
    测试对象：create_coingecko_fetch_port + CoingeckoMockFetchPort.fetch_payload
    目的/目标：aggregator validation port 产出 crypto_market_evidence_v1
    验证点：schema_version、asset_id、price_usd、volume_24h_usd
    失败含义：CoinGecko 无 port 路径，无法登记 validation READY
    """
    from backend.app.datasources.fetch_ports.coingecko_port import create_coingecko_fetch_port
    from backend.app.datasources.fetch_result import FetchRequest
    from backend.app.datasources.normalizers.crypto_market import (
        CRYPTO_MARKET_EVIDENCE_SCHEMA_VERSION,
    )

    port = create_coingecko_fetch_port(asset_ids=("bitcoin",), max_assets=5)
    req = FetchRequest(
        run_id="r3h02-coingecko",
        source_id="coingecko",
        data_domain="crypto_spot_market",
        instrument_id="bitcoin",
    )
    payload = port.fetch_payload(req)
    body = json.loads(payload.content.decode("utf-8"))
    assert body["schema_version"] == CRYPTO_MARKET_EVIDENCE_SCHEMA_VERSION
    assert body["source_id"] == "coingecko"
    inst = (body.get("instruments") or [])[0]
    assert inst.get("asset_id") == "bitcoin"
    assert inst.get("price_usd") is not None
    assert inst.get("market_cap_usd") is not None


def test_coingecko_port_validationOnly_notExchangeGradePrimary() -> None:
    """覆盖范围：coingecko 不得作为交易所级 primary
    测试对象：SourceRegistry
    目的/目标：coingecko validation_only；crypto_derivatives primary 为 deribit
    验证点：coingecko.validation_only=True；crypto_derivatives primary=deribit
    失败含义：aggregator 被误选为交易所级 primary
    """
    from backend.app.datasources.source_registry import SourceRegistry

    registry = SourceRegistry()
    registry.load()
    cg = registry.get("coingecko")
    assert cg.validation_only is True
    binding = registry.get_domain_roles("crypto_derivatives")
    assert binding.primary_source_id == "deribit"
    assert binding.primary_source_id != "coingecko"


def test_coingecko_port_replayFixture_spotFieldsCanonical() -> None:
    """覆盖范围：CoinGecko replay fixture 读路径
    测试对象：tests/fixtures/replay/crypto_market/coingecko/btc_spot_replay.json
    目的/目标：replay 含 asset_id、price_usd、volume_24h_usd
    验证点：read_crypto_market_evidence_bundle 往返
    失败含义：CoinGecko replay 路径缺失
    """
    from backend.app.datasources.normalizers.crypto_market import read_crypto_market_evidence_bundle

    bundle = read_crypto_market_evidence_bundle(_COINGECKO_REPLAY)
    inst = bundle["instruments"][0]
    assert inst["asset_id"] == "bitcoin"
    assert inst.get("price_usd") is not None


def test_layer_smoke_deribitReplay_layer5FactualSourceProvenance() -> None:
    """覆盖范围：Deribit replay → Layer5 factual_source 溯源字段
    测试对象：crypto_market_bundle_layer5_provenance + EvidenceFoundationValidator
    目的/目标：crypto replay 具备 Layer5 契约要求的溯源（smoke）
    验证点：provenance 非空；factual_source 记录通过 foundation 校验
    失败含义：加密市场证据无法挂接 Layer5 factual_source 链
    """
    from backend.app.datasources.normalizers.crypto_market import (
        crypto_market_bundle_layer5_provenance,
        read_crypto_market_evidence_bundle,
    )
    from backend.app.layer5_evidence.models import InstrumentEvidenceRef
    from tests.conftest_layer_smoke import assert_layer5_factual_source_record

    bundle = read_crypto_market_evidence_bundle(_DERIBIT_REPLAY)
    prov_fields = crypto_market_bundle_layer5_provenance(bundle)
    assert_layer5_factual_source_record(
        prov_fields,
        evidence_id="EV-R3H02-DERIBIT-SMOKE",
        target_id="CRYPTO-BTC-OPT",
        target_type="crypto_derivative",
        trade_date=date(2024, 6, 25),
        evidence_summary="Deribit options surface replay smoke",
        created_by="r3h02_crypto_layer_smoke",
        instrument_ref=InstrumentEvidenceRef(
            instrument_id="CRYPTO-BTC-OPT",
            symbol="BTC",
            asset_type="crypto_option",
            market_id="CRYPTO",
            exchange="DERIBIT",
            currency="USD",
            is_active=True,
        ),
    )


def test_layer_smoke_coingeckoReplay_layer2IngestionPreview() -> None:
    """覆盖范围：CoinGecko replay → Layer2 ingestion 预览
    测试对象：crypto_market_bundle_layer2_preview
    目的/目标：crypto 证据可被 Layer2 摄取链消费（smoke）
    验证点：preview 含 source_fetch_id、content_hash
    失败含义：Layer2 无法绑定 crypto replay 证据指纹
    """
    from backend.app.datasources.normalizers.crypto_market import (
        crypto_market_bundle_layer2_preview,
        read_crypto_market_evidence_bundle,
    )

    bundle = read_crypto_market_evidence_bundle(_COINGECKO_REPLAY)
    preview = crypto_market_bundle_layer2_preview(bundle)
    assert preview["source_fetch_id"] == "coingecko-replay-btc"
    assert preview["content_hash"]


def test_layer_smoke_cryptoReplay_layer4MarketStructurePreview() -> None:
    """覆盖范围：crypto replay → Layer4 market structure 预览
    测试对象：crypto_market_bundle_layer4_preview + deribit/coingecko replay
    目的/目标：R3H02-R-24 crypto Layer4 smoke（deribit + coingecko replay）
    验证点：preview 含 sample_instrument、source_fetch_id；无 OHLCV 历史字段
    失败含义：加密证据无法被 Layer4 结构链消费
    """
    from backend.app.datasources.normalizers.crypto_market import (
        crypto_market_bundle_layer4_preview,
        read_crypto_market_evidence_bundle,
    )

    for replay in (_DERIBIT_REPLAY, _COINGECKO_REPLAY):
        bundle = read_crypto_market_evidence_bundle(replay)
        preview = crypto_market_bundle_layer4_preview(bundle)
        assert preview["source_fetch_id"]
        assert preview["content_hash"]
        assert preview["sample_instrument"]
        assert "open" not in preview
        assert "close" not in preview
