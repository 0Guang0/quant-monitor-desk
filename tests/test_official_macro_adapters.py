"""R3H-01 官方宏观/披露适配器测试（Batch 3H）。

覆盖范围：六源官方宏观与披露适配器（fred、us_treasury、sec_edgar、cftc_cot、bis、world_bank）
的 fetch port、证据契约、路由与 Layer smoke。
测试对象：backend/app/datasources/normalizers/official_macro.py 及兄弟 fetch port 模块。
目的/目标：证明六源可在 replay-first 路径下产出合规证据并满足 route/registry 终态。
验证点：各 step 子集（evidence_contract、fred_port、layer 等）按 EXECUTION_INDEX §1 通过。
失败含义：Batch 3H R3H-01 无法在 Round4 前闭合官方源生产入口决策。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from backend.app.config import PROJECT_ROOT

_LIVE_FRED = (
    PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g01/live_wire/fred_live_fetch_evidence.json"
)
_PROMOTE_FRED = PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g01/fred/fred_evidence.json"


def test_bootSkeleton_testModuleLoads() -> None:
    """覆盖范围：Execute 9.0 测试模块骨架是否可加载
    测试对象：tests/test_official_macro_adapters.py 模块本身
    目的/目标：确认 R3H-01 专用测试文件已登记且 pytest 可收集
    验证点：本测试通过即表示骨架就绪，后续 9.1+ 可挂证据契约用例
    失败含义：Execute 无法在本模块追加六源适配器回归用例
    """
    assert True


def test_evidence_contract_livePayload_declaresOfficialMacroSchema(tmp_path: Path) -> None:
    """覆盖范围：FRED live 抓取证据经 normalizer 写出 promote 包
    测试对象：materialize_fred_evidence_from_live（official_macro normalizer）
    目的/目标：live 与 promote 共用 official_macro_evidence_v1，观测行用 observation_date
    验证点：schema_version==official_macro_evidence_v1；观测无 date 别名；无 DH sidecar
    失败含义：G10 未闭合，live 与 promote 字段仍靠 bridge 侧车与 date 别名硬凑
    """
    from backend.app.datasources.normalizers.official_macro import (
        OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION,
        materialize_fred_evidence_from_live,
        read_fred_evidence_bundle,
    )

    out = tmp_path / "fred_promote"
    materialize_fred_evidence_from_live(_LIVE_FRED, out)
    bundle = read_fred_evidence_bundle(out)
    assert bundle["schema_version"] == OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION
    assert len(bundle["observations"]) == 3
    for obs in bundle["observations"]:
        assert obs.get("observation_date")
        assert "date" not in obs
    assert not (out / "pilot_v2_closeout.json").is_file()
    assert not (out / "validation_report_summary.json").is_file()


def test_evidence_contract_writeReadRoundTrip_fixturePreservesFields(tmp_path: Path) -> None:
    """覆盖范围：既有 promote fixture 经 read/write 往返
    测试对象：write_fred_evidence_bundle + read_fred_evidence_bundle
    目的/目标：rehearsal_loader 与 bridge 读同一 canonical 形状，legacy date 升级 observation_date
    验证点：source_fetch_id、content_hash、as_of_timestamp、retrieved_at 保留；观测日期不丢
    失败含义：promote 链无法无损读写官方宏观证据，staging 行会缺日期或指纹
    """
    from backend.app.datasources.normalizers.official_macro import (
        read_fred_evidence_bundle,
        write_fred_evidence_bundle,
    )

    legacy = json.loads(_PROMOTE_FRED.read_text(encoding="utf-8"))
    out = tmp_path / "roundtrip"
    write_fred_evidence_bundle(out, legacy)
    bundle = read_fred_evidence_bundle(out)
    assert bundle["source_fetch_id"] == "fred-fetch-1"
    assert bundle["content_hash"] == "fred-hash-complete"
    assert bundle["as_of_timestamp"] == "2026-06-23T18:00:00Z"
    assert bundle["retrieved_at"] == "2026-06-23T18:00:00Z"
    assert bundle["observations"][0]["observation_date"] == "2024-01-02"


def test_evidence_contract_stagingRows_observationDateEndToEnd(tmp_path: Path) -> None:
    """覆盖范围：live → promote → rehearsal staging 行
    测试对象：materialize_fred_promote_evidence + staging_rows_from_bundle
    目的/目标：observation_date 从 live 经 normalizer 到 staging trade_date，无需字段重命名
    验证点：3 行 staging；DGS10×2 + VIXCLS×1；trade_date 来自 observation_date
    失败含义：FRED 官方宏观证据无法贯通 promote 预演链，G10/G14 仍开放
    """
    from backend.app.ops.sandbox_clean_write.live_evidence_bridge import (
        materialize_fred_promote_evidence,
    )
    from backend.app.ops.sandbox_clean_write.rehearsal_loader import (
        load_rehearsal_bundle,
        staging_rows_from_bundle,
    )
    from backend.app.ops.sandbox_clean_write.rehearsal_plan import RehearsalCandidate

    out = tmp_path / "fred"
    materialize_fred_promote_evidence(_LIVE_FRED, out)
    candidate = RehearsalCandidate(
        source_id="fred",
        domain="macro_series",
        operation="fetch_macro_series",
        symbols_or_series=("DGS10", "VIXCLS"),
        window_days=120,
    )
    bundle = load_rehearsal_bundle(candidate, evidence_dir=out, dry_run=False, cap_profile="r3g03")
    rows = staging_rows_from_bundle(
        bundle,
        batch_id="evidence-contract",
        max_rows=400,
        start_date="2026-01-01",
        end_date="2026-12-31",
    )
    assert len(rows) == 3
    dgs10 = [r for r in rows if r.instrument_id == "DGS10"]
    vix = [r for r in rows if r.instrument_id == "VIXCLS"]
    assert len(dgs10) == 2
    assert len(vix) == 1
    assert {r.trade_date for r in dgs10} == {"2026-06-25", "2026-06-24"}
    assert vix[0].trade_date == "2026-06-25"


_FRED_REPLAY = (
    PROJECT_ROOT / "tests/fixtures/replay/official_macro/fred/dgs10_replay_bundle.json"
)


def _fred_macro_req(**overrides: object):
    from backend.app.datasources.fetch_result import FetchRequest

    base = {
        "run_id": "r3h01-fred-port",
        "source_id": "fred",
        "data_domain": "macro_series",
        "instrument_id": "DGS10",
    }
    base.update(overrides)
    return FetchRequest(**base)


def test_fred_port_mockFetch_emitsOfficialMacroEvidenceV1() -> None:
    """覆盖范围：mock FRED port 默认安全抓取
    测试对象：create_fred_fetch_port + FredMockFetchPort.fetch_payload
    目的/目标：port 直接产出 official_macro_evidence_v1，无需 bridge 侧车
    验证点：schema_version、observations[].observation_date、source_fetch_id、content_hash
    失败含义：L2 port 仍输出 legacy rows 形状，G10 与 fetch 路径分裂
    """
    from backend.app.datasources.fetch_ports.fred_port import create_fred_fetch_port
    from backend.app.datasources.normalizers.official_macro import (
        OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION,
    )

    port = create_fred_fetch_port(series_ids=("DGS10",), max_rows=3, use_mock=True)
    payload = port.fetch_payload(_fred_macro_req())
    body = json.loads(payload.content.decode("utf-8"))
    assert body["schema_version"] == OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION
    assert body["series_id"] == "DGS10"
    assert body.get("source_fetch_id")
    assert body.get("content_hash")
    assert body.get("as_of_timestamp")
    obs = body.get("observations") or []
    assert obs
    for row in obs:
        assert row.get("observation_date")
        assert "date" not in row
        assert row.get("value") is not None


def test_fred_port_p0Whitelist_rejectsUnknownSeries() -> None:
    """覆盖范围：P0 series 白名单门禁
    测试对象：FredMockFetchPort.fetch_payload
    目的/目标：非白名单 series 在 port 层 fail-closed
    验证点：UNKNOWN_SERIES 抛出 PortError
    失败含义：任意 macro series 可被 sandbox port 拉取
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.fred_port import create_fred_fetch_port

    port = create_fred_fetch_port(series_ids=("UNKNOWN_SERIES",), max_rows=3, use_mock=True)
    with pytest.raises(PortError, match="whitelist"):
        port.fetch_payload(_fred_macro_req(instrument_id="UNKNOWN_SERIES"))


def test_fred_port_liveWithoutApiKey_blocksUnauthorized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：未授权 live FRED fetch
    测试对象：FredLiveFetchPort.fetch_payload
    目的/目标：缺 FRED_API_KEY 时不得联网成功
    验证点：PortError.status 为 USER_AUTH_REQUIRED 或 FAILED 且消息含 API key
    失败含义：无 key 仍可 live fetch，违反 R3E hardening
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.fred_port import create_fred_fetch_port

    monkeypatch.delenv("FRED_API_KEY", raising=False)
    port = create_fred_fetch_port(series_ids=("DGS10",), max_rows=3, use_mock=False)
    with pytest.raises(PortError) as exc_info:
        port.fetch_payload(_fred_macro_req())
    assert exc_info.value.status in {"USER_AUTH_REQUIRED", "FAILED"}
    assert "FRED_API_KEY" in exc_info.value.message or "api" in exc_info.value.message.lower()


def test_fred_port_capOverflow_blocksOverMaxRows() -> None:
    """覆盖范围：port 行数 cap 溢出
    测试对象：FredMockFetchPort 构造 max_rows 超上限
    目的/目标：ResourceGuard/任务卡 cap 在 port 层硬拒绝
    验证点：max_rows 超 MAX_ROWS_PER_SERIES 时 fetch 前 PortError
    失败含义：cap 可被 port 参数绕过导致无界 macro pull
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.fred_port import (
        MAX_ROWS_PER_SERIES,
        create_fred_fetch_port,
    )

    port = create_fred_fetch_port(
        series_ids=("DGS10",),
        max_rows=MAX_ROWS_PER_SERIES + 1,
        use_mock=True,
    )
    with pytest.raises(PortError, match="cap"):
        port.fetch_payload(_fred_macro_req())


def test_fred_port_replayFixture_observationDateCanonical() -> None:
    """覆盖范围：replay fixture 与 normalizer 读路径
    测试对象：tests/fixtures/replay/official_macro/fred/dgs10_replay_bundle.json
    目的/目标：replay 使用 observation_date + schema_version，非 legacy date
    验证点：read_fred_evidence_bundle 往返；观测行无 date 别名
    失败含义：replay 仍依赖 legacy 字段，9.6 registry 无法登记路径
    """
    from backend.app.datasources.normalizers.official_macro import (
        OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION,
        read_fred_evidence_bundle,
    )

    bundle = read_fred_evidence_bundle(_FRED_REPLAY)
    assert bundle["schema_version"] == OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION
    assert bundle["series_id"] == "DGS10"
    for obs in bundle["observations"]:
        assert obs.get("observation_date")
        assert "date" not in obs


def test_fred_port_route_disabledByDefault_unauthorized() -> None:
    """覆盖范围：macro_series 路由默认禁用
    测试对象：SourceRoutePlanner + source_registry fred
    目的/目标：enabled_by_default=false 时 route 为 DISABLED，非 READY
    验证点：route_status=DISABLED_SOURCE；fred candidate enabled=False
    失败含义：未配置 FRED 仍被 route 选为 production primary
    """
    from backend.app.datasources.capability_registry import SourceCapabilityRegistry
    from backend.app.datasources.route_planner import SourceRoutePlanner
    from backend.app.datasources.source_registry import SourceRegistry

    registry = SourceRegistry()
    registry.load()
    capabilities = SourceCapabilityRegistry()
    capabilities.load()
    planner = SourceRoutePlanner(source_registry=registry, capability_registry=capabilities)
    plan = planner.plan(
        data_domain="macro_series",
        operation="fetch_macro_series",
        run_id="r3h01-fred-route",
        job_id="fred-route-negative",
    )
    assert plan.route_status == "DISABLED_SOURCE"
    assert plan.selected_source_id is None
    fred = next((c for c in plan.candidates if c.source_id == "fred"), None)
    assert fred is not None
    assert fred.enabled is False


def test_fred_port_route_readyWhenSourceEnabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：显式启用 fred 后 route READY
    测试对象：SourceRoutePlanner（内存 registry 覆盖 enabled）
    目的/目标：授权配置后 macro_series 可选 fred primary
    验证点：route_status=READY；selected_source_id=fred
    失败含义：即使源已启用也无法 route 到官方 macro port
    """
    from backend.app.datasources.capability_registry import SourceCapabilityRegistry
    from backend.app.datasources.route_planner import SourceRoutePlanner
    from backend.app.datasources.source_registry import SourceRegistry

    registry = SourceRegistry()
    registry.load()
    rec = registry.get("fred")
    object.__setattr__(rec, "is_enabled", True)
    orig_domain_roles = registry.get_domain_roles

    def _macro_domain_enabled(data_domain: str):
        binding = orig_domain_roles(data_domain)
        if data_domain != "macro_series":
            return binding
        from backend.app.datasources.source_registry import DomainRoleBinding

        return DomainRoleBinding(
            primary_source_id=binding.primary_source_id,
            validation_source_id=binding.validation_source_id,
            fallback_policy=binding.fallback_policy,
            domain_enabled_by_default=True,
            fallback_source_ids=binding.fallback_source_ids,
        )

    monkeypatch.setattr(registry, "get_domain_roles", _macro_domain_enabled)
    capabilities = SourceCapabilityRegistry()
    capabilities.load()
    planner = SourceRoutePlanner(source_registry=registry, capability_registry=capabilities)
    monkeypatch.setattr(planner, "_platform_allows", lambda _sid: (True, None))
    plan = planner.plan(
        data_domain="macro_series",
        operation="fetch_macro_series",
        run_id="r3h01-fred-route-ready",
        job_id="fred-route-positive",
        extra_candidates=[("fred", "Primary")],
    )
    fred = next((c for c in plan.candidates if c.source_id == "fred"), None)
    assert fred is not None
    assert fred.enabled is True
    assert plan.route_status == "READY"
    assert plan.selected_source_id == "fred"
