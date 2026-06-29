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
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import yaml
from backend.app.config import PROJECT_ROOT

_LIVE_FRED = (
    PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g01/live_wire/fred_live_fetch_evidence.json"
)
_PROMOTE_FRED = PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g01/fred/fred_evidence.json"


def test_bootSkeleton_testModuleLoads() -> None:
    """覆盖范围：Execute 9.0 测试模块骨架是否可加载
    测试对象：tests/test_official_macro_adapters.py 模块本身
    目的/目标：确认 R3H-01 专用测试文件已登记且 pytest 可收集
    验证点：模块 docstring 声明六源覆盖范围
    失败含义：Execute 无法在本模块追加六源适配器回归用例
    """
    import tests.test_official_macro_adapters as mod

    assert "六源" in (mod.__doc__ or "")
    assert "fred" in (mod.__doc__ or "")


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
    assert len(bundle["observations"]) >= 1
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
    """覆盖范围：live → promote → macro staging 行
    测试对象：materialize_fred_promote_evidence + populate_macro_from_bundle
    目的/目标：observation_date 从 live 经 normalizer 到 axis_observation staging
    验证点：3 行 staging；DGS10×2 + VIXCLS×1；as_of 来自 observation_date
    失败含义：FRED 官方宏观证据无法贯通 R3H-06 macro clean 链，G10/G14 仍开放
    """
    import duckdb

    from backend.app.db.migrate import apply_migrations
    from backend.app.ops.sandbox_clean_write.live_evidence_bridge import (
        materialize_fred_promote_evidence,
    )
    from backend.app.ops.sandbox_clean_write.rehearsal_loader import (
        load_rehearsal_bundle,
        populate_macro_from_bundle,
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
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    count = populate_macro_from_bundle(
        con,
        bundle,
        batch_id="evidence-contract",
        max_rows=400,
        start_date="2026-01-01",
        end_date="2026-12-31",
    )
    assert count == 3
    payload = json.loads((out / "fred_evidence.json").read_text(encoding="utf-8"))
    observations = payload.get("observations") or []
    rows = con.execute(
        "SELECT indicator_id, CAST(publish_timestamp AS DATE), raw_value "
        "FROM stg_axis_observation_smoke"
    ).fetchall()
    dgs10 = [r for r in rows if r[0] == "DGS10"]
    vix = [r for r in rows if r[0] == "VIXCLS"]
    assert len(dgs10) == 2
    assert len(vix) == 1
    for indicator_id, pub_date, raw_value in rows:
        pub_str = str(pub_date)
        matched = any(
            str(obs.get("series_id")) == indicator_id
            and str(obs.get("observation_date") or obs.get("date")) == pub_str
            and float(obs.get("value") or 0) == float(raw_value)
            for obs in observations
        )
        assert matched, f"no evidence row for {indicator_id} {pub_str} {raw_value}"


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
    assert body["source_fetch_id"]
    assert body["content_hash"]
    assert body.get("schema_hash")
    assert body.get("fetch_log", {}).get("source_fetch_id")
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

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    port = create_fred_fetch_port(series_ids=("DGS10",), max_rows=3, use_mock=False)
    with pytest.raises(PortError) as exc_info:
        port.fetch_payload(_fred_macro_req())
    assert exc_info.value.status == "USER_AUTH_REQUIRED"
    assert "FRED_API_KEY" in exc_info.value.message


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
    assert bundle["source_fetch_id"] == "fred-replay-dgs10"
    assert bundle["content_hash"] == "fred-replay-hash-dgs10"
    for obs in bundle["observations"]:
        assert obs.get("observation_date")
        assert "date" not in obs


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


_TREASURY_YIELD_REPLAY = (
    PROJECT_ROOT
    / "tests/fixtures/replay/official_macro/us_treasury/yield_curve_replay_bundle.json"
)
_TREASURY_INFLATION_REPLAY = (
    PROJECT_ROOT
    / "tests/fixtures/replay/official_macro/us_treasury/inflation_expectation_replay_bundle.json"
)


def _us_treasury_yield_req(**overrides: object):
    from backend.app.datasources.fetch_result import FetchRequest

    base = {
        "run_id": "r3h01-us-treasury-port",
        "source_id": "us_treasury",
        "data_domain": "us_treasury_yield_curve",
        "instrument_id": "10Y",
    }
    base.update(overrides)
    return FetchRequest(**base)


def _us_treasury_inflation_req(**overrides: object):
    from backend.app.datasources.fetch_result import FetchRequest

    base = {
        "run_id": "r3h01-us-treasury-inflation",
        "source_id": "us_treasury",
        "data_domain": "inflation_expectation",
        "instrument_id": "breakeven_10y",
    }
    base.update(overrides)
    return FetchRequest(**base)


def test_us_treasury_port_mockFetch_emitsYieldCurveEvidence() -> None:
    """覆盖范围：mock US Treasury port 收益率曲线抓取
    测试对象：create_us_treasury_fetch_port + UsTreasuryMockFetchPort.fetch_payload
    目的/目标：port 直接产出 yield curve 证据包，字段含 observation_date/tenor/yield_percent
    验证点：schema_version、source_fetch_id、content_hash、canonical observation_date
    失败含义：L2 port 未交付或仍输出 legacy 形状，无法登记 READY_WITH_EVIDENCE
    """
    from backend.app.datasources.fetch_ports.us_treasury_port import create_us_treasury_fetch_port
    from backend.app.datasources.normalizers.official_macro import (
        OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION,
    )

    port = create_us_treasury_fetch_port(
        tenors=("10Y", "2Y"),
        max_rows=3,
        data_domain="us_treasury_yield_curve",
        use_mock=True,
    )
    payload = port.fetch_payload(_us_treasury_yield_req())
    body = json.loads(payload.content.decode("utf-8"))
    assert body["schema_version"] == OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION
    assert body["source_id"] == "us_treasury"
    assert body["data_domain"] == "us_treasury_yield_curve"
    assert body.get("source_fetch_id")
    assert body.get("content_hash")
    assert body.get("as_of_timestamp")
    obs = body.get("observations") or []
    assert obs
    for row in obs:
        assert row.get("observation_date")
        assert "date" not in row
        assert row.get("tenor")
        assert row.get("yield_percent") is not None


def test_us_treasury_port_mockFetch_emitsInflationExpectationEvidence() -> None:
    """覆盖范围：mock US Treasury port 通胀预期参考抓取
    测试对象：create_us_treasury_fetch_port（inflation_expectation 域）
    目的/目标：port 产出通胀预期证据包，字段含 metric_name/metric_value
    验证点：data_domain==inflation_expectation；观测行 canonical observation_date
    失败含义：通胀预期域无 port 路径，us_treasury 双域承诺未闭合
    """
    from backend.app.datasources.fetch_ports.us_treasury_port import create_us_treasury_fetch_port
    from backend.app.datasources.normalizers.official_macro import (
        OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION,
    )

    port = create_us_treasury_fetch_port(
        tenors=("breakeven_10y",),
        max_rows=3,
        data_domain="inflation_expectation",
        use_mock=True,
    )
    payload = port.fetch_payload(_us_treasury_inflation_req())
    body = json.loads(payload.content.decode("utf-8"))
    assert body["schema_version"] == OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION
    assert body["data_domain"] == "inflation_expectation"
    obs = body.get("observations") or []
    assert obs
    for row in obs:
        assert row.get("observation_date")
        assert row.get("metric_name")
        assert row.get("metric_value") is not None


def test_us_treasury_port_tenorWhitelist_rejectsUnknownTenor() -> None:
    """覆盖范围：收益率曲线 tenor 白名单门禁
    测试对象：UsTreasuryMockFetchPort.fetch_payload
    目的/目标：非白名单 tenor 在 port 层 fail-closed
    验证点：UNKNOWN_TENOR 抛出 PortError
    失败含义：任意 tenor 可被 sandbox port 拉取，突破 §7 cap 语义
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.us_treasury_port import create_us_treasury_fetch_port

    port = create_us_treasury_fetch_port(
        tenors=("UNKNOWN_TENOR",),
        max_rows=3,
        data_domain="us_treasury_yield_curve",
        use_mock=True,
    )
    with pytest.raises(PortError, match="whitelist"):
        port.fetch_payload(_us_treasury_yield_req(instrument_id="UNKNOWN_TENOR"))


def test_us_treasury_port_capOverflow_blocksOverMaxRows() -> None:
    """覆盖范围：port 行数 cap 溢出
    测试对象：UsTreasuryMockFetchPort 构造 max_rows 超上限
    目的/目标：ResourceGuard/任务卡 cap（500 rows）在 port 层硬拒绝
    验证点：max_rows 超 MAX_ROWS 时 fetch 前 PortError
    失败含义：cap 可被 port 参数绕过导致无界 Treasury pull
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.us_treasury_port import (
        MAX_ROWS,
        create_us_treasury_fetch_port,
    )

    port = create_us_treasury_fetch_port(
        tenors=("10Y",),
        max_rows=MAX_ROWS + 1,
        data_domain="us_treasury_yield_curve",
        use_mock=True,
    )
    with pytest.raises(PortError, match="cap"):
        port.fetch_payload(_us_treasury_yield_req())


def test_us_treasury_port_capOverflow_blocksOverMaxTenors() -> None:
    """覆盖范围：port tenor 数量 cap 溢出
    测试对象：create_us_treasury_fetch_port 构造 tenors 超上限
    目的/目标：§7 默认 20 tenors cap 在 factory 层硬拒绝
    验证点：len(tenors) > MAX_TENORS 时构造即 PortError
    失败含义：tenor cap 可被绕过
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.us_treasury_port import (
        MAX_TENORS,
        create_us_treasury_fetch_port,
    )

    too_many = tuple(f"T{i}Y" for i in range(MAX_TENORS + 1))
    with pytest.raises(PortError, match="tenor"):
        create_us_treasury_fetch_port(
            tenors=too_many,
            max_rows=3,
            data_domain="us_treasury_yield_curve",
            use_mock=True,
        )


def test_us_treasury_port_replayFixture_yieldCurveObservationDateCanonical() -> None:
    """覆盖范围：yield curve replay fixture 与 normalizer 读路径
    测试对象：tests/fixtures/replay/official_macro/us_treasury/yield_curve_replay_bundle.json
    目的/目标：replay 使用 observation_date + schema_version，非 legacy date
    验证点：read_yield_curve_evidence_bundle 往返；观测行无 date 别名
    失败含义：replay 仍依赖 legacy 字段，9.6 registry 无法登记路径
    """
    from backend.app.datasources.normalizers.official_macro import (
        OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION,
        read_yield_curve_evidence_bundle,
    )

    bundle = read_yield_curve_evidence_bundle(_TREASURY_YIELD_REPLAY)
    assert bundle["schema_version"] == OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION
    assert bundle["data_domain"] == "us_treasury_yield_curve"
    for obs in bundle["observations"]:
        assert obs.get("observation_date")
        assert obs.get("tenor")
        assert "date" not in obs


def test_us_treasury_port_replayFixture_inflationExpectationCanonical() -> None:
    """覆盖范围：inflation expectation replay fixture 与 normalizer 读路径
    测试对象：tests/fixtures/replay/official_macro/us_treasury/inflation_expectation_replay_bundle.json
    目的/目标：replay 使用 observation_date + metric_name/metric_value
    验证点：read_inflation_expectation_evidence_bundle 往返
    失败含义：通胀预期 replay 路径缺失，双域证据无法登记
    """
    from backend.app.datasources.normalizers.official_macro import (
        OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION,
        read_inflation_expectation_evidence_bundle,
    )

    bundle = read_inflation_expectation_evidence_bundle(_TREASURY_INFLATION_REPLAY)
    assert bundle["schema_version"] == OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION
    assert bundle["data_domain"] == "inflation_expectation"
    for obs in bundle["observations"]:
        assert obs.get("observation_date")
        assert obs.get("metric_name")
        assert "date" not in obs


def test_us_treasury_port_route_readyWhenSourceEnabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：显式启用 us_treasury 后 route READY
    测试对象：SourceRoutePlanner（内存 registry 覆盖 enabled）
    目的/目标：授权配置后 us_treasury_yield_curve 可选 us_treasury primary
    验证点：route_status=READY；selected_source_id=us_treasury
    失败含义：即使源已启用也无法 route 到官方 Treasury port
    """
    from backend.app.datasources.capability_registry import SourceCapabilityRegistry
    from backend.app.datasources.route_planner import SourceRoutePlanner
    from backend.app.datasources.source_registry import SourceRegistry

    registry = SourceRegistry()
    registry.load()
    rec = registry.get("us_treasury")
    object.__setattr__(rec, "is_enabled", True)
    orig_domain_roles = registry.get_domain_roles

    def _yield_curve_domain_enabled(data_domain: str):
        binding = orig_domain_roles(data_domain)
        if data_domain != "us_treasury_yield_curve":
            return binding
        from backend.app.datasources.source_registry import DomainRoleBinding

        return DomainRoleBinding(
            primary_source_id=binding.primary_source_id,
            validation_source_id=binding.validation_source_id,
            fallback_policy=binding.fallback_policy,
            domain_enabled_by_default=True,
            fallback_source_ids=binding.fallback_source_ids,
        )

    monkeypatch.setattr(registry, "get_domain_roles", _yield_curve_domain_enabled)
    capabilities = SourceCapabilityRegistry()
    capabilities.load()
    planner = SourceRoutePlanner(source_registry=registry, capability_registry=capabilities)
    monkeypatch.setattr(planner, "_platform_allows", lambda _sid: (True, None))
    plan = planner.plan(
        data_domain="us_treasury_yield_curve",
        operation="fetch_yield_curve",
        run_id="r3h01-treasury-route-ready",
        job_id="treasury-route-positive",
        extra_candidates=[("us_treasury", "Primary")],
    )
    treasury = next((c for c in plan.candidates if c.source_id == "us_treasury"), None)
    assert treasury is not None
    assert treasury.enabled is True
    assert plan.route_status == "READY"
    assert plan.selected_source_id == "us_treasury"


_CFTC_REPLAY = (
    PROJECT_ROOT / "tests/fixtures/replay/official_macro/cftc_cot/cot_replay_bundle.json"
)
_BIS_POLICY_REPLAY = (
    PROJECT_ROOT / "tests/fixtures/replay/official_macro/bis/policy_rate_replay_bundle.json"
)
_WORLD_BANK_REPLAY = (
    PROJECT_ROOT
    / "tests/fixtures/replay/official_macro/world_bank/indicator_replay_bundle.json"
)


def _cftc_req(**overrides: object):
    from backend.app.datasources.fetch_result import FetchRequest

    base = {
        "run_id": "r3h01-cftc-port",
        "source_id": "cftc_cot",
        "data_domain": "cot_positioning",
        "instrument_id": "088691",
    }
    base.update(overrides)
    return FetchRequest(**base)


def _bis_policy_req(**overrides: object):
    from backend.app.datasources.fetch_result import FetchRequest

    base = {
        "run_id": "r3h01-bis-port",
        "source_id": "bis",
        "data_domain": "central_bank_policy",
        "instrument_id": "US",
    }
    base.update(overrides)
    return FetchRequest(**base)


def _world_bank_req(**overrides: object):
    from backend.app.datasources.fetch_result import FetchRequest

    base = {
        "run_id": "r3h01-world-bank-port",
        "source_id": "world_bank",
        "data_domain": "development_indicator",
        "instrument_id": "US",
    }
    base.update(overrides)
    return FetchRequest(**base)


def test_cftc_port_mockFetch_emitsCotEvidence() -> None:
    """覆盖范围：mock CFTC COT port 周频持仓抓取
    测试对象：create_cftc_cot_fetch_port + CftcCotMockFetchPort.fetch_payload
    目的/目标：port 产出 COT 证据包，字段含 market_code/report_date/trader_category
    验证点：schema_version、source_fetch_id、content_hash、canonical report_date
    失败含义：CFTC 官方持仓源无 port 路径，无法登记 READY_WITH_EVIDENCE
    """
    from backend.app.datasources.fetch_ports.cftc_cot_port import create_cftc_cot_fetch_port
    from backend.app.datasources.normalizers.official_macro import (
        OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION,
    )

    port = create_cftc_cot_fetch_port(markets=("088691",), max_rows=3, use_mock=True)
    payload = port.fetch_payload(_cftc_req())
    body = json.loads(payload.content.decode("utf-8"))
    assert body["schema_version"] == OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION
    assert body["data_domain"] == "cot_positioning"
    assert body.get("source_fetch_id")
    assert body.get("content_hash")
    obs = body.get("observations") or []
    assert obs
    for row in obs:
        assert row.get("market_code")
        assert row.get("report_date")
        assert row.get("trader_category")


def test_cftc_port_marketWhitelist_rejectsUnknown() -> None:
    """覆盖范围：COT market 白名单门禁
    测试对象：CftcCotMockFetchPort.fetch_payload
    目的/目标：非白名单 market 在 port 层 fail-closed
    验证点：UNKNOWN 抛出 PortError
    失败含义：任意 market 可被 sandbox port 拉取
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.cftc_cot_port import create_cftc_cot_fetch_port

    port = create_cftc_cot_fetch_port(markets=("UNKNOWN",), max_rows=3, use_mock=True)
    with pytest.raises(PortError, match="whitelist"):
        port.fetch_payload(_cftc_req(instrument_id="UNKNOWN"))


def test_cftc_port_replayFixture_canonical() -> None:
    """覆盖范围：COT replay fixture 与 normalizer 读路径
    测试对象：tests/fixtures/replay/official_macro/cftc_cot/cot_replay_bundle.json
    目的/目标：replay 使用 report_date + schema_version
    验证点：read_cot_positioning_evidence_bundle 往返
    失败含义：COT replay 路径缺失，9.6 registry 无法登记
    """
    from backend.app.datasources.normalizers.official_macro import read_cot_positioning_evidence_bundle

    bundle = read_cot_positioning_evidence_bundle(_CFTC_REPLAY)
    assert bundle["data_domain"] == "cot_positioning"
    for obs in bundle["observations"]:
        assert obs.get("report_date")
        assert obs.get("market_code")


def test_bis_port_mockFetch_emitsPolicyRateEvidence() -> None:
    """覆盖范围：mock BIS port 政策利率抓取
    测试对象：create_bis_fetch_port（central_bank_policy 域）
    目的/目标：port 产出 BIS 政策利率证据包
    验证点：data_domain==central_bank_policy；含 policy_rate 与 observation_date
    失败含义：BIS 政策利率域无 port 路径
    """
    from backend.app.datasources.fetch_ports.bis_port import create_bis_fetch_port
    from backend.app.datasources.normalizers.official_macro import (
        OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION,
    )

    port = create_bis_fetch_port(
        countries=("US",),
        max_rows=3,
        data_domain="central_bank_policy",
        use_mock=True,
    )
    payload = port.fetch_payload(_bis_policy_req())
    body = json.loads(payload.content.decode("utf-8"))
    assert body["schema_version"] == OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION
    assert body["data_domain"] == "central_bank_policy"
    obs = body.get("observations") or []
    assert obs[0].get("policy_rate") is not None
    assert obs[0].get("observation_date")


def test_bis_port_mockFetch_emitsCreditGapEvidence() -> None:
    """覆盖范围：mock BIS port 信贷/GDP 缺口抓取
    测试对象：create_bis_fetch_port（credit_gap 域）
    目的/目标：port 产出 credit gap 证据包
    验证点：data_domain==credit_gap；含 credit_to_gdp_gap
    失败含义：BIS credit gap 域无 port 路径
    """
    from backend.app.datasources.fetch_ports.bis_port import create_bis_fetch_port
    from backend.app.datasources.fetch_result import FetchRequest

    port = create_bis_fetch_port(
        countries=("US",),
        max_rows=3,
        data_domain="credit_gap",
        use_mock=True,
    )
    req = FetchRequest(
        run_id="r3h01-bis-credit",
        source_id="bis",
        data_domain="credit_gap",
        instrument_id="US",
    )
    payload = port.fetch_payload(req)
    body = json.loads(payload.content.decode("utf-8"))
    assert body["data_domain"] == "credit_gap"
    assert body["observations"][0].get("credit_to_gdp_gap") is not None


def test_bis_port_replayFixture_policyRateCanonical() -> None:
    """覆盖范围：BIS policy replay fixture 读路径
    测试对象：tests/fixtures/replay/official_macro/bis/policy_rate_replay_bundle.json
    目的/目标：replay 使用 observation_date + policy_rate
    验证点：read_bis_policy_rate_evidence_bundle 往返
    失败含义：BIS replay 路径缺失
    """
    from backend.app.datasources.normalizers.official_macro import read_bis_policy_rate_evidence_bundle

    bundle = read_bis_policy_rate_evidence_bundle(_BIS_POLICY_REPLAY)
    assert bundle["data_domain"] == "central_bank_policy"
    for obs in bundle["observations"]:
        assert obs.get("observation_date")
        assert obs.get("country_code")


def test_world_bank_port_mockFetch_emitsIndicatorEvidence() -> None:
    """覆盖范围：mock World Bank port 发展指标抓取
    测试对象：create_world_bank_fetch_port
    目的/目标：port 产出 World Bank 指标证据包
    验证点：含 indicator_id、value、observation_date
    失败含义：World Bank 源无 port 路径
    """
    from backend.app.datasources.fetch_ports.world_bank_port import create_world_bank_fetch_port
    from backend.app.datasources.normalizers.official_macro import (
        OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION,
    )

    port = create_world_bank_fetch_port(
        countries=("US",),
        indicators=("NY.GDP.MKTP.CD",),
        max_rows=3,
        data_domain="development_indicator",
        use_mock=True,
    )
    payload = port.fetch_payload(_world_bank_req())
    body = json.loads(payload.content.decode("utf-8"))
    assert body["schema_version"] == OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION
    assert body["data_domain"] == "development_indicator"
    obs = body.get("observations") or []
    assert obs[0].get("indicator_id")
    assert obs[0].get("value") is not None


def test_world_bank_port_indicatorWhitelist_rejectsUnknown() -> None:
    """覆盖范围：World Bank indicator 白名单门禁
    测试对象：WorldBankMockFetchPort
    目的/目标：非白名单 indicator 在 port 层 fail-closed
    验证点：UNKNOWN 抛出 PortError
    失败含义：任意 indicator 可被 sandbox port 拉取
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.world_bank_port import create_world_bank_fetch_port

    port = create_world_bank_fetch_port(
        countries=("US",),
        indicators=("UNKNOWN.IND",),
        max_rows=3,
        data_domain="development_indicator",
        use_mock=True,
    )
    with pytest.raises(PortError, match="whitelist"):
        port.fetch_payload(_world_bank_req())


def test_world_bank_port_replayFixture_canonical() -> None:
    """覆盖范围：World Bank replay fixture 读路径
    测试对象：tests/fixtures/replay/official_macro/world_bank/indicator_replay_bundle.json
    目的/目标：replay 使用 observation_date + indicator_id
    验证点：read_world_bank_indicator_evidence_bundle 往返
    失败含义：World Bank replay 路径缺失
    """
    from backend.app.datasources.normalizers.official_macro import (
        read_world_bank_indicator_evidence_bundle,
    )

    bundle = read_world_bank_indicator_evidence_bundle(_WORLD_BANK_REPLAY)
    assert bundle["data_domain"] == "development_indicator"
    for obs in bundle["observations"]:
        assert obs.get("observation_date")
        assert obs.get("indicator_id")


def test_layer_smoke_fredReplay_layer1IngestionPreview() -> None:
    """覆盖范围：FRED replay → Layer1 ingestion evidence 预览
    测试对象：official_macro_bundle_layer1_preview + fred replay bundle
    目的/目标：官方宏观证据可被 Layer1 摄取链消费（smoke，非 R3H-05 全审计）
    验证点：preview 含 source_fetch_id、content_hash、sample_observation_date
    失败含义：Layer1 无法绑定官方宏观 replay 证据指纹
    """
    from backend.app.datasources.normalizers.official_macro import read_fred_evidence_bundle
    from backend.app.layer1_axes.ingestion_evidence import official_macro_bundle_layer1_preview

    bundle = read_fred_evidence_bundle(_FRED_REPLAY)
    preview = official_macro_bundle_layer1_preview(bundle)
    assert preview["source_fetch_id"] == "fred-replay-dgs10"
    assert preview["content_hash"] == "fred-replay-hash-dgs10"
    assert preview["observation_count"] >= 1
    assert preview["sample_observation_date"]


def test_layer_smoke_fredReplay_layer5FactualSourceProvenance() -> None:
    """覆盖范围：FRED replay → Layer5 factual_source 溯源字段
    测试对象：official_macro_bundle_layer5_provenance + EvidenceFoundationValidator
    目的/目标：replay 行具备 Layer5 契约要求的 source_fetch_id/content_hash 溯源
    验证点：provenance 非空；factual_source 记录通过 foundation 校验
    失败含义：官方宏观证据无法挂接 Layer5 factual_source 链
    """
    from datetime import date

    from backend.app.datasources.normalizers.official_macro import read_fred_evidence_bundle
    from backend.app.layer1_axes.ingestion_evidence import official_macro_bundle_layer5_provenance
    from backend.app.layer5_evidence.foundation import EvidenceFoundationValidator
    from backend.app.layer5_evidence.models import (
        EvidenceFoundationRecord,
        EvidenceKind,
        InstrumentEvidenceRef,
        ManualReviewState,
        SourceProvenance,
    )

    bundle = read_fred_evidence_bundle(_FRED_REPLAY)
    prov_fields = official_macro_bundle_layer5_provenance(bundle)
    assert prov_fields["source_fetch_ids"]
    assert prov_fields["source_content_hashes"]

    record = EvidenceFoundationRecord(
        evidence_id="EV-R3H01-FRED-SMOKE",
        target_id="MACRO-DGS10",
        target_type="macro_indicator",
        trade_date=date(2026, 6, 25),
        evidence_kind=EvidenceKind.FACTUAL_SOURCE,
        evidence_summary="DGS10 official macro replay smoke",
        need_human_review=False,
        manual_review_state=ManualReviewState.NOT_REQUIRED,
        created_by="r3h01_layer_smoke",
        instrument_ref=InstrumentEvidenceRef(
            instrument_id="MACRO-DGS10",
            symbol="DGS10",
            asset_type="macro_series",
            market_id="US",
            exchange="FRED",
            currency="USD",
            is_active=True,
        ),
        provenance=SourceProvenance(
            source_fetch_ids=prov_fields["source_fetch_ids"],
            source_content_hashes=prov_fields["source_content_hashes"],
        ),
    )
    EvidenceFoundationValidator().validate_record(record)


def test_layer_smoke_secEdgarReplay_layer1AndLayer5Binding() -> None:
    """覆盖范围：SEC EDGAR filings replay → Layer1/Layer5 smoke
    测试对象：sec_edgar filings replay + layer preview/provenance helpers
    目的/目标：披露证据同样可产出 Layer1 预览与 Layer5 溯源（双域 smoke 之一）
    验证点：filings 包映射后 content_hash 与 source_fetch_id 非空
    失败含义：披露源无法进入 Layer 证据链
    """
    from backend.app.datasources.normalizers.sec_edgar import read_filings_evidence_bundle
    from backend.app.layer1_axes.ingestion_evidence import (
        official_macro_bundle_layer1_preview,
        official_macro_bundle_layer5_provenance,
    )

    bundle = read_filings_evidence_bundle(
        PROJECT_ROOT / "tests/fixtures/replay/sec_edgar/filings_replay_bundle.json"
    )
    macro_shaped = {**bundle, "observations": bundle.get("filings") or []}
    preview = official_macro_bundle_layer1_preview(macro_shaped)
    prov = official_macro_bundle_layer5_provenance(bundle)
    assert preview["content_hash"]
    assert preview["source_fetch_id"]
    assert prov["source_fetch_ids"]
    assert prov["source_content_hashes"]


_BIS_CREDIT_GAP_REPLAY = (
    PROJECT_ROOT / "tests/fixtures/replay/official_macro/bis/credit_gap_replay_bundle.json"
)


def _load_capabilities() -> dict:
    path = PROJECT_ROOT / "specs/datasource_registry/source_capabilities.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _enable_source_route(
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


_CAPABILITY_CASES: tuple[tuple[str, str, str, callable], ...] = (
    (
        "fred",
        "macro_series",
        "fetch_macro_series",
        lambda: __import__(
            "backend.app.datasources.fetch_ports.fred_port", fromlist=["create_fred_fetch_port"]
        ).create_fred_fetch_port(series_ids=("DGS10",), max_rows=3, use_mock=True),
    ),
    (
        "us_treasury",
        "us_treasury_yield_curve",
        "fetch_yield_curve",
        lambda: __import__(
            "backend.app.datasources.fetch_ports.us_treasury_port",
            fromlist=["create_us_treasury_fetch_port"],
        ).create_us_treasury_fetch_port(
            tenors=("10Y",), max_rows=3, data_domain="us_treasury_yield_curve", use_mock=True
        ),
    ),
    (
        "cftc_cot",
        "cot_positioning",
        "fetch_cot_positioning",
        lambda: __import__(
            "backend.app.datasources.fetch_ports.cftc_cot_port",
            fromlist=["create_cftc_cot_fetch_port"],
        ).create_cftc_cot_fetch_port(markets=("088691",), max_rows=3, use_mock=True),
    ),
    (
        "bis",
        "central_bank_policy",
        "fetch_policy_rate",
        lambda: __import__(
            "backend.app.datasources.fetch_ports.bis_port", fromlist=["create_bis_fetch_port"]
        ).create_bis_fetch_port(
            countries=("US",), max_rows=3, data_domain="central_bank_policy", use_mock=True
        ),
    ),
    (
        "world_bank",
        "development_indicator",
        "fetch_indicator_series",
        lambda: __import__(
            "backend.app.datasources.fetch_ports.world_bank_port",
            fromlist=["create_world_bank_fetch_port"],
        ).create_world_bank_fetch_port(
            countries=("US",),
            indicators=("NY.GDP.MKTP.CD",),
            max_rows=3,
            data_domain="development_indicator",
            use_mock=True,
        ),
    ),
)


@pytest.mark.parametrize(
    ("source_id", "data_domain", "operation", "port_factory"),
    _CAPABILITY_CASES,
)
def test_r3h01_capabilityFields_matchPortOutput(
    source_id: str,
    data_domain: str,
    operation: str,
    port_factory,
) -> None:
    """覆盖范围：source_capabilities observation/bundle 字段与 port 输出对齐
    测试对象：各官方源 fetch port payload + YAML capability 声明
    目的/目标：P1-01 契约字段层级混写漂移闭合
    验证点：观测行键 ⊆ observation_fields；包顶键 ⊇ bundle_fields
    失败含义：registry 字段声明与 port 输出不一致，下游校验误报
    """
    from backend.app.datasources.fetch_result import FetchRequest

    caps = (_load_capabilities().get("sources") or {}).get(source_id, {})
    op_spec = (
        ((caps.get("domains") or {}).get(data_domain) or {}).get("operations") or {}
    ).get(operation, {})
    observation_fields = set(op_spec.get("observation_fields") or op_spec.get("fields") or [])
    bundle_fields = set(op_spec.get("bundle_fields") or [])

    port = port_factory()
    if source_id == "fred":
        req = _fred_macro_req()
    elif source_id == "cftc_cot":
        req = _cftc_req()
    elif source_id == "us_treasury":
        req = _us_treasury_yield_req()
    elif source_id == "world_bank":
        req = _world_bank_req()
    else:
        req = _bis_policy_req()

    body = json.loads(port.fetch_payload(req).content.decode("utf-8"))
    if observation_fields:
        rows = body.get("observations") or []
        assert rows, f"{source_id} payload missing observation rows"
        assert set(rows[0].keys()) >= observation_fields
    if bundle_fields:
        assert set(body.keys()) >= bundle_fields


@pytest.mark.parametrize(
    ("source_id", "yaml_key", "port_attr"),
    [
        ("fred", "max_series", "MAX_SERIES"),
        ("fred", "max_rows_per_series", "MAX_ROWS_PER_SERIES"),
        ("fred", "max_window_days", "MAX_WINDOW_DAYS"),
        ("us_treasury", "max_tenors", "MAX_TENORS"),
        ("us_treasury", "max_rows", "MAX_ROWS"),
        ("sec_edgar", "max_ciks", "MAX_CIKS"),
        ("sec_edgar", "max_filings", "MAX_FILINGS"),
        ("cftc_cot", "max_markets", "MAX_MARKETS"),
        ("cftc_cot", "max_rows", "MAX_ROWS"),
        ("bis", "max_countries", "MAX_COUNTRIES"),
        ("world_bank", "max_indicators", "MAX_INDICATORS"),
        ("world_bank", "max_countries", "MAX_COUNTRIES"),
    ],
)
def test_r3h01_officialMacroCaps_matchRegistry(
    source_id: str,
    yaml_key: str,
    port_attr: str,
) -> None:
    """覆盖范围：registry resource_caps 与 port 模块常量 parity
    测试对象：source_capabilities.yaml + 各 *_port.py MAX_* 常量
    目的/目标：P2-01 YAML↔port cap 漂移可被 CI 钉死
    验证点：YAML cap 值 == port 模块同名常量
    失败含义：registry 与 port 层 cap 权威分裂
    """
    caps = (_load_capabilities().get("sources") or {}).get(source_id, {}).get("resource_caps") or {}
    module_name = {
        "fred": "fred_port",
        "us_treasury": "us_treasury_port",
        "sec_edgar": "sec_edgar_port",
        "cftc_cot": "cftc_cot_port",
        "bis": "bis_port",
        "world_bank": "world_bank_port",
    }[source_id]
    mod = __import__(f"backend.app.datasources.fetch_ports.{module_name}", fromlist=[port_attr])
    assert caps[yaml_key] == getattr(mod, port_attr)


def test_cftc_port_capOverflow_blocksOverMaxRows() -> None:
    """覆盖范围：CFTC COT port 行数 cap 溢出
    测试对象：CftcCotMockFetchPort max_rows 超上限
    目的/目标：P1-02/G-02 §7 52 weeks cap 在 port 层硬拒绝
    验证点：max_rows 超 MAX_ROWS 时 PortError
    失败含义：CFTC cap 无 pytest 保护，回归可绕过
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.cftc_cot_port import MAX_ROWS, create_cftc_cot_fetch_port

    port = create_cftc_cot_fetch_port(markets=("088691",), max_rows=MAX_ROWS + 1, use_mock=True)
    with pytest.raises(PortError, match="cap"):
        port.fetch_payload(_cftc_req())


def test_cftc_port_capOverflow_blocksOverMaxMarkets() -> None:
    """覆盖范围：CFTC COT factory markets 数量 cap
    测试对象：create_cftc_cot_fetch_port markets 超上限
    目的/目标：§7 5 markets cap 在 factory 层拒绝
    验证点：len(markets) > MAX_MARKETS 构造即 PortError
    失败含义：markets cap 可被绕过
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.cftc_cot_port import MAX_MARKETS, create_cftc_cot_fetch_port

    too_many = tuple(str(i) for i in range(MAX_MARKETS + 1))
    with pytest.raises(PortError, match="market"):
        create_cftc_cot_fetch_port(markets=too_many, max_rows=3, use_mock=True)


def test_bis_port_capOverflow_blocksOverMaxRows() -> None:
    """覆盖范围：BIS port 行数 cap 溢出
    测试对象：BisMockFetchPort max_rows 超上限
    目的/目标：P1-02/G-03 cap 负例闭合
    验证点：max_rows 超 MAX_ROWS 时 PortError
    失败含义：BIS cap 无 pytest 保护
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.bis_port import MAX_ROWS, create_bis_fetch_port

    port = create_bis_fetch_port(
        countries=("US",), max_rows=MAX_ROWS + 1, data_domain="central_bank_policy", use_mock=True
    )
    with pytest.raises(PortError, match="cap"):
        port.fetch_payload(_bis_policy_req())


def test_bis_port_capOverflow_blocksOverMaxCountries() -> None:
    """覆盖范围：BIS factory countries 数量 cap
    测试对象：create_bis_fetch_port countries 超上限
    目的/目标：§7 5 countries cap 在 factory 层拒绝
    验证点：len(countries) > MAX_COUNTRIES 构造即 PortError
    失败含义：countries cap 可被绕过
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.bis_port import MAX_COUNTRIES, create_bis_fetch_port

    too_many = tuple(f"C{i}" for i in range(MAX_COUNTRIES + 1))
    with pytest.raises(PortError, match="countr"):
        create_bis_fetch_port(
            countries=too_many, max_rows=3, data_domain="central_bank_policy", use_mock=True
        )


def test_world_bank_port_capOverflow_blocksOverMaxRows() -> None:
    """覆盖范围：World Bank port 行数 cap 溢出
    测试对象：WorldBankMockFetchPort max_rows 超上限
    目的/目标：P1-02/G-04 cap 负例闭合
    验证点：max_rows 超 MAX_ROWS 时 PortError
    失败含义：World Bank cap 无 pytest 保护
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.world_bank_port import (
        MAX_ROWS,
        create_world_bank_fetch_port,
    )

    port = create_world_bank_fetch_port(
        countries=("US",),
        indicators=("NY.GDP.MKTP.CD",),
        max_rows=MAX_ROWS + 1,
        data_domain="development_indicator",
        use_mock=True,
    )
    with pytest.raises(PortError, match="cap"):
        port.fetch_payload(_world_bank_req())


def test_world_bank_port_capOverflow_blocksOverMaxIndicators() -> None:
    """覆盖范围：World Bank factory indicators 数量 cap
    测试对象：create_world_bank_fetch_port indicators 超上限
    目的/目标：§7 5 indicators cap 在 factory 层拒绝
    验证点：len(indicators) > MAX_INDICATORS 构造即 PortError
    失败含义：indicators cap 可被绕过
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.world_bank_port import (
        MAX_INDICATORS,
        create_world_bank_fetch_port,
    )

    too_many = tuple(f"IND.{i}" for i in range(MAX_INDICATORS + 1))
    with pytest.raises(PortError, match="indicator"):
        create_world_bank_fetch_port(
            countries=("US",),
            indicators=too_many,
            max_rows=3,
            data_domain="development_indicator",
            use_mock=True,
        )


def test_fred_port_capOverflow_blocksOverMaxSeries() -> None:
    """覆盖范围：FRED factory series 数量 cap
    测试对象：create_fred_fetch_port series_ids 超上限
    目的/目标：P1-03/G-05 MAX_SERIES=10 可被 CI 钉死
    验证点：len(series_ids) > MAX_SERIES 构造即 PortError
    失败含义：series 维 cap 无负例保护
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.fred_port import MAX_SERIES, create_fred_fetch_port

    too_many = tuple(f"S{i}" for i in range(MAX_SERIES + 1))
    with pytest.raises(PortError, match="series"):
        create_fred_fetch_port(series_ids=too_many, max_rows=3, use_mock=True)


def test_fred_port_capOverflow_rejectsNonPositiveMaxRows() -> None:
    """覆盖范围：FRED port max_rows<=0 拒绝
    测试对象：reject_over_cap 对非法行数
    目的/目标：P2-02 cap 消息语义改进（非正数单独拒绝）
    验证点：max_rows=0 时 PortError 消息含 must be positive
    失败含义：零/负行数与超 cap 混淆，难诊断
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.fred_port import create_fred_fetch_port

    port = create_fred_fetch_port(series_ids=("DGS10",), max_rows=0, use_mock=True)
    with pytest.raises(PortError, match="must be positive"):
        port.fetch_payload(_fred_macro_req())


def test_fred_port_windowStart_respectsMaxWindowDays() -> None:
    """覆盖范围：FRED live port 窗口天数 cap
    测试对象：FredLiveFetchPort._window_start
    目的/目标：P3-01/G-05 MAX_WINDOW_DAYS=120 边界可测
    验证点：window start 不早于 now-120d
    失败含义：window cap 无行为锚点
    """
    from backend.app.datasources.fetch_ports.fred_port import MAX_WINDOW_DAYS, FredLiveFetchPort

    port = FredLiveFetchPort(series_ids=("DGS10",), max_rows=3, date_window="3y")
    earliest = datetime.now(UTC).date() - timedelta(days=MAX_WINDOW_DAYS + 1)
    assert port._window_start() > earliest


def test_fred_evidence_read_corruptBundle_missingHash_raises(tmp_path: Path) -> None:
    """覆盖范围：损坏证据包缺指纹时 fail-closed
    测试对象：read_fred_evidence_bundle
    目的/目标：P1-05 禁止静默 unknown-hash 回填
    验证点：缺 content_hash 抛出 OfficialMacroEvidenceError
    失败含义：损坏证据可伪装完整 bundle
    """
    from backend.app.datasources.normalizers.official_macro import (
        OfficialMacroEvidenceError,
        read_fred_evidence_bundle,
    )

    corrupt = tmp_path / "corrupt_fred.json"
    corrupt.write_text(
        json.dumps(
            {
                "observations": [
                    {"series_id": "DGS10", "observation_date": "2026-01-01", "value": "1"}
                ],
                "source_fetch_id": "bad",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(OfficialMacroEvidenceError, match="content_hash"):
        read_fred_evidence_bundle(corrupt)


def test_fred_port_emitsSchemaHashAndFetchLog() -> None:
    """覆盖范围：port 输出 schema_hash 与 fetch_log 证据字段
    测试对象：FredMockFetchPort.fetch_payload
    目的/目标：G-08 活卡 §5 第 6 条证据字段闭合
    验证点：payload 含 schema_hash、fetch_log.source_fetch_id
    失败含义：证据矩阵缺 schema_hash/fetch_log 登记
    """
    from backend.app.datasources.fetch_ports.fred_port import create_fred_fetch_port
    from backend.app.datasources.normalizers.evidence_bundle import schema_hash_for_version
    from backend.app.datasources.normalizers.official_macro import (
        OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION,
    )

    port = create_fred_fetch_port(series_ids=("DGS10",), max_rows=3, use_mock=True)
    body = json.loads(port.fetch_payload(_fred_macro_req()).content.decode("utf-8"))
    assert body["schema_hash"] == schema_hash_for_version(OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION)
    assert body["fetch_log"]["source_fetch_id"] == body["source_fetch_id"]


@pytest.mark.parametrize(
    ("source_id", "data_domain", "operation", "extra_candidates"),
    [
        ("cftc_cot", "cot_positioning", "fetch_cot_positioning", [("cftc_cot", "Primary")]),
        ("bis", "central_bank_policy", "fetch_policy_rate", [("bis", "Primary")]),
        ("world_bank", "development_indicator", "fetch_indicator_series", [("world_bank", "Primary")]),
    ],
)
def test_r3h01_officialMacroRoute_readyWhenSourceEnabled(
    monkeypatch: pytest.MonkeyPatch,
    source_id: str,
    data_domain: str,
    operation: str,
    extra_candidates: list[tuple[str, str]],
) -> None:
    """覆盖范围：cftc/bis/world_bank route READY 正例
    测试对象：SourceRoutePlanner（显式启用源）
    目的/目标：G-06 三源 route READY 对称 fred/treasury/sec
    验证点：route_status=READY；selected_source_id 匹配
    失败含义：三源启用后仍无法 route 到官方 port
    """
    planner = _enable_source_route(monkeypatch, source_id=source_id, data_domain=data_domain)
    plan = planner.plan(
        data_domain=data_domain,
        operation=operation,
        run_id=f"r3h01-ready-{source_id}",
        job_id=f"ready-{source_id}",
        extra_candidates=extra_candidates,
    )
    candidate = next((c for c in plan.candidates if c.source_id == source_id), None)
    assert candidate is not None
    assert candidate.enabled is True
    assert plan.route_status == "READY"
    assert plan.selected_source_id == source_id


def test_bis_port_route_creditGap_readyWhenSourceEnabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：BIS credit_gap 域 route READY
    测试对象：SourceRoutePlanner credit_gap 域
    目的/目标：G-07 BIS credit_gap 路由测闭合
    验证点：route_status=READY；selected_source_id=bis
    失败含义：credit_gap 域无 route 正例
    """
    planner = _enable_source_route(monkeypatch, source_id="bis", data_domain="credit_gap")
    plan = planner.plan(
        data_domain="credit_gap",
        operation="fetch_credit_to_gdp_gap",
        run_id="r3h01-bis-credit-route",
        job_id="bis-credit-ready",
        extra_candidates=[("bis", "Primary")],
    )
    assert plan.route_status == "READY"
    assert plan.selected_source_id == "bis"


def test_bis_creditGap_replayFixture_canonical() -> None:
    """覆盖范围：BIS credit_gap replay fixture 读路径
    测试对象：tests/fixtures/replay/official_macro/bis/credit_gap_replay_bundle.json
    目的/目标：A2 删 read_bis_credit_gap 后以通用 reader + fixture 替代
    验证点：_read_observations_bundle 路径；含 credit_to_gdp_gap
    失败含义：credit_gap replay 死代码路径未闭合
    """
    from backend.app.datasources.normalizers.official_macro import (
        _normalize_bis_credit_gap_row,
        _read_observations_bundle,
        build_bis_credit_gap_evidence_bundle,
    )

    bundle = _read_observations_bundle(
        _BIS_CREDIT_GAP_REPLAY,
        label="BIS credit gap evidence",
        normalize_obs=_normalize_bis_credit_gap_row,
        build_bundle=build_bis_credit_gap_evidence_bundle,
        source_id="bis",
    )
    assert bundle["data_domain"] == "credit_gap"
    assert bundle["source_fetch_id"] == "bis-replay-credit-gap"
    assert bundle["observations"][0]["credit_to_gdp_gap"] == "2.4"


def test_layer_smoke_missingContentHash_raises() -> None:
    """覆盖范围：Layer1 smoke 缺指纹负例
    测试对象：official_macro_bundle_layer1_preview
    目的/目标：G-01 §9.7 缺 content_hash/source_fetch_id 应失败
    验证点：ValueError 含 missing
    失败含义：损坏 bundle 仍可通过 Layer smoke
    """
    from backend.app.layer1_axes.ingestion_evidence import official_macro_bundle_layer1_preview

    corrupt = {
        "source_id": "fred",
        "observations": [{"observation_date": "2026-01-01", "value": "1", "series_id": "DGS10"}],
    }
    with pytest.raises(ValueError, match="missing"):
        official_macro_bundle_layer1_preview(corrupt)


def test_liveEvidenceBridge_resolveRawPath_rejectsOutsideProjectRoot() -> None:
    """覆盖范围：live evidence bridge 路径 jail
    测试对象：live_evidence_bridge._resolve_raw_path
    目的/目标：A3 _resolve_raw_path PROJECT_ROOT 约束
    验证点：项目外绝对路径抛出 LiveEvidenceBridgeError
    失败含义：任意文件路径可被 bridge 读取
    """
    from backend.app.ops.sandbox_clean_write.live_evidence_bridge import (
        LiveEvidenceBridgeError,
        _resolve_raw_path,
    )
    from tests.path_jail_support import path_outside_project_root

    outside = path_outside_project_root(suffix="outside.json")
    outside.write_text("{}", encoding="utf-8")
    with pytest.raises(LiveEvidenceBridgeError, match="escapes project root"):
        _resolve_raw_path(outside)


def test_fred_liveCap_pilotAuthLayerDocumented() -> None:
    """覆盖范围：FRED L2 port cap 与 R3E pilot 授权分层边界
    测试对象：fred_port MAX_* 常量
    目的/目标：A6 NB pilot vs L2 FRED cap 分层登记
    验证点：L2 port 暴露 MAX_WINDOW_DAYS/MAX_SERIES 常量
    失败含义：授权分层无行为锚点
    """
    from backend.app.datasources.fetch_ports import fred_port

    assert fred_port.MAX_WINDOW_DAYS == 120
    assert fred_port.MAX_SERIES == 10
    assert fred_port.MAX_ROWS_PER_SERIES == 500

