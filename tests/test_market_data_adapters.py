"""R3H-02 跨资产/US 市场数据适配器测试（Batch 3H）。

覆盖范围：五源市场数据适配器（alpha_vantage、stooq、yahoo_finance）的 fetch port、
证据契约、路由与 Layer smoke（yahoo 永久 validation-only）。
测试对象：backend/app/datasources/normalizers/market_data.py 及兄弟 fetch port 模块。
目的/目标：证明三源可在 replay-first 路径下产出 market_data_evidence_v1 并满足 route/registry 终态。
验证点：各 step 子集（evidence_contract、alpha_vantage、stooq、yahoo、layer）通过当前 pytest 验收。
失败含义：Batch 3H R3H-02 无法在 Round4 前闭合市场源生产入口决策。
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
import yaml

from backend.app.config import PROJECT_ROOT

_AV_REPLAY = (
    PROJECT_ROOT / "tests/fixtures/replay/market_data/alpha_vantage/aapl_daily_replay.json"
)
_STOOQ_REPLAY = PROJECT_ROOT / "tests/fixtures/replay/market_data/stooq/global_daily_replay.json"
_YAHOO_REPLAY = (
    PROJECT_ROOT / "tests/fixtures/replay/market_data/yahoo_finance/aapl_validation_replay.json"
)


def test_evidence_contract_writeReadRoundTrip_fixturePreservesFields(tmp_path: Path) -> None:
    """覆盖范围：market_data 证据包 read/write 往返
    测试对象：write_daily_bar_evidence_bundle + read_daily_bar_evidence_bundle
    目的/目标：replay fixture 经 normalizer 无损读写 canonical OHLCV + trade_date
    验证点：source_fetch_id、content_hash、schema_hash、trade_date 保留；无 date 别名
    失败含义：market_data_evidence_v1 无法贯通 replay 链，9.1 契约未闭合
    """
    from backend.app.datasources.normalizers.market_data import (
        MARKET_DATA_EVIDENCE_SCHEMA_VERSION,
        read_daily_bar_evidence_bundle,
        write_daily_bar_evidence_bundle,
    )

    legacy = json.loads(_AV_REPLAY.read_text(encoding="utf-8"))
    out = tmp_path / "roundtrip"
    write_daily_bar_evidence_bundle(out, legacy)
    bundle = read_daily_bar_evidence_bundle(out)
    assert bundle["schema_version"] == MARKET_DATA_EVIDENCE_SCHEMA_VERSION
    assert bundle["source_fetch_id"] == "av-replay-aapl"
    assert bundle["content_hash"]
    assert bundle.get("schema_hash")
    for bar in bundle["bars"]:
        assert bar.get("trade_date")
        assert "date" not in bar


def test_evidence_contract_replayFixture_tradeDateCanonical() -> None:
    """覆盖范围：Alpha Vantage replay fixture 与 normalizer 读路径
    测试对象：tests/fixtures/replay/market_data/alpha_vantage/aapl_daily_replay.json
    目的/目标：replay 使用 trade_date + market_data_evidence_v1 canonical 字段
    验证点：read_daily_bar_evidence_bundle 往返；source_id 与首条 trade_date 稳定
    失败含义：replay 仍依赖 legacy 字段，registry 无法登记路径
    """
    from backend.app.datasources.normalizers.market_data import (
        MARKET_DATA_EVIDENCE_SCHEMA_VERSION,
        read_daily_bar_evidence_bundle,
    )

    bundle = read_daily_bar_evidence_bundle(_AV_REPLAY)
    assert bundle["schema_version"] == MARKET_DATA_EVIDENCE_SCHEMA_VERSION
    assert bundle["source_id"] == "alpha_vantage"
    assert bundle["source_fetch_id"] == "av-replay-aapl"
    assert bundle.get("window_kind") == "trading_sessions"
    assert bundle["bars"][0]["trade_date"] == "2024-01-02"
    for bar in bundle["bars"]:
        assert bar.get("trade_date")
        assert "date" not in bar


@pytest.mark.parametrize(
    ("replay_path", "source_id"),
    [
        (_STOOQ_REPLAY, "stooq"),
        (_YAHOO_REPLAY, "yahoo_finance"),
    ],
)
def test_evidence_contract_replayFixture_windowKindTradingSessions(
    replay_path: Path, source_id: str
) -> None:
    """覆盖范围：stooq/yahoo replay bundle window_kind 契约
    测试对象：market_data replay fixtures + read_daily_bar_evidence_bundle
    目的/目标：R3H07 CAL-US — US equity replay window_kind 必须为 trading_sessions
    验证点：bundle.window_kind == trading_sessions；source_id 与 fixture 一致
    失败含义：window_kind 仍为 calendar_days，C3/G4 窗口语义不可信
    """
    from backend.app.datasources.normalizers.market_data import read_daily_bar_evidence_bundle

    bundle = read_daily_bar_evidence_bundle(replay_path)
    assert bundle.get("window_kind") == "trading_sessions"
    assert bundle["source_id"] == source_id


def _market_req(source_id: str, data_domain: str, instrument_id: str, **overrides: object):
    from backend.app.datasources.fetch_result import FetchRequest

    base = {
        "run_id": f"r3h02-{source_id}",
        "source_id": source_id,
        "data_domain": data_domain,
        "instrument_id": instrument_id,
    }
    base.update(overrides)
    return FetchRequest(**base)


def test_alpha_vantage_port_mockFetch_emitsMarketDataEvidenceV1() -> None:
    """覆盖范围：mock Alpha Vantage port 默认安全抓取
    测试对象：create_alpha_vantage_fetch_port + AlphaVantageMockFetchPort.fetch_payload
    目的/目标：port 直接产出 market_data_evidence_v1，无需 bridge 侧车
    验证点：schema_version、bars[].trade_date、source_fetch_id、content_hash
    失败含义：L2 port 仍输出 legacy rows 形状，无法登记 READY_WITH_EVIDENCE
    """
    from backend.app.datasources.fetch_ports.alpha_vantage_port import create_alpha_vantage_fetch_port
    from backend.app.datasources.normalizers.market_data import MARKET_DATA_EVIDENCE_SCHEMA_VERSION

    port = create_alpha_vantage_fetch_port(symbols=("AAPL",), max_rows=3, use_mock=True)
    payload = port.fetch_payload(_market_req("alpha_vantage", "us_equity_daily_bar", "AAPL"))
    body = json.loads(payload.content.decode("utf-8"))
    assert body["schema_version"] == MARKET_DATA_EVIDENCE_SCHEMA_VERSION
    assert body["source_fetch_id"]
    assert body["content_hash"]
    assert body.get("schema_hash")
    for bar in body.get("bars") or []:
        assert bar.get("trade_date")
        assert "date" not in bar


def test_alpha_vantage_port_liveWithoutApiKey_blocksUnauthorized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：未授权 live Alpha Vantage fetch
    测试对象：AlphaVantageLiveFetchPort.fetch_payload
    目的/目标：缺 ALPHA_VANTAGE_API_KEY 时不得联网成功
    验证点：PortError.status 为 USER_AUTH_REQUIRED
    失败含义：无 key 仍可 live fetch，违反 R3H hardening
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.alpha_vantage_port import create_alpha_vantage_fetch_port

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
    port = create_alpha_vantage_fetch_port(symbols=("AAPL",), max_rows=3, use_mock=False)
    with pytest.raises(PortError) as exc_info:
        port.fetch_payload(_market_req("alpha_vantage", "us_equity_daily_bar", "AAPL"))
    assert exc_info.value.status == "USER_AUTH_REQUIRED"
    assert "ALPHA_VANTAGE_API_KEY" in exc_info.value.message


def test_alpha_vantage_port_capOverflow_blocksOverMaxRows() -> None:
    """覆盖范围：port 行数 cap 溢出
    测试对象：AlphaVantageMockFetchPort 构造 max_rows 超上限
    目的/目标：ResourceGuard/任务卡 cap 在 port 层硬拒绝
    验证点：max_rows 超 MAX_ROWS 时 fetch 前 PortError
    失败含义：cap 可被 port 参数绕过导致无界 market pull
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.alpha_vantage_port import (
        MAX_ROWS,
        create_alpha_vantage_fetch_port,
    )

    port = create_alpha_vantage_fetch_port(
        symbols=("AAPL",), max_rows=MAX_ROWS + 1, use_mock=True
    )
    with pytest.raises(PortError, match="cap"):
        port.fetch_payload(_market_req("alpha_vantage", "us_equity_daily_bar", "AAPL"))


def test_alpha_vantage_port_route_readyWhenSourceEnabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：显式启用 alpha_vantage 后 route READY
    测试对象：SourceRoutePlanner（内存 registry 覆盖 enabled）
    目的/目标：授权配置后 us_equity_daily_bar 可选 alpha_vantage primary
    验证点：route_status=READY；selected_source_id=alpha_vantage
    失败含义：即使源已启用也无法 route 到 Alpha Vantage port
    """
    from backend.app.datasources.capability_registry import SourceCapabilityRegistry
    from backend.app.datasources.route_planner import SourceRoutePlanner
    from backend.app.datasources.source_registry import DomainRoleBinding, SourceRegistry

    registry = SourceRegistry()
    registry.load()
    rec = registry.get("alpha_vantage")
    object.__setattr__(rec, "is_enabled", True)
    orig_domain_roles = registry.get_domain_roles

    def _equity_domain_enabled(data_domain: str):
        binding = orig_domain_roles(data_domain)
        if data_domain != "us_equity_daily_bar":
            return binding
        return DomainRoleBinding(
            primary_source_id=binding.primary_source_id,
            validation_source_id=binding.validation_source_id,
            fallback_policy=binding.fallback_policy,
            domain_enabled_by_default=True,
            fallback_source_ids=binding.fallback_source_ids,
        )

    monkeypatch.setattr(registry, "get_domain_roles", _equity_domain_enabled)
    capabilities = SourceCapabilityRegistry()
    capabilities.load()
    planner = SourceRoutePlanner(source_registry=registry, capability_registry=capabilities)
    monkeypatch.setattr(planner, "_platform_allows", lambda _sid: (True, None))
    plan = planner.plan(
        data_domain="us_equity_daily_bar",
        operation="fetch_us_daily_bar",
        run_id="r3h02-av-route-ready",
        job_id="av-route-positive",
        extra_candidates=[("alpha_vantage", "Primary")],
    )
    av = next((c for c in plan.candidates if c.source_id == "alpha_vantage"), None)
    assert av is not None
    assert av.enabled is True
    assert plan.route_status == "READY"
    assert plan.selected_source_id == "alpha_vantage"


def test_alpha_vantage_port_route_disabledWhenSourceUnauthorized() -> None:
    """覆盖范围：未授权 alpha_vantage 默认路由 DISABLED
    测试对象：SourceRoutePlanner.plan（us_equity_daily_bar）
    目的/目标：R3H02-R-23 无 API key / 未启用时 route DISABLED_SOURCE
    验证点：route_status=DISABLED_SOURCE；selected_source_id=None；alpha_vantage enabled=False
    失败含义：未授权 AV 可被误选为 production primary
    """
    from tests.service_path_support import production_route_planner

    planner = production_route_planner()
    plan = planner.plan(
        data_domain="us_equity_daily_bar",
        operation="fetch_us_daily_bar",
        run_id="r3h02-av-route-disabled",
        job_id="av-route-negative",
    )
    assert plan.route_status == "DISABLED_SOURCE"
    assert plan.selected_source_id is None
    av = next((c for c in plan.candidates if c.source_id == "alpha_vantage"), None)
    assert av is not None
    assert av.enabled is False


def test_yahoo_port_route_readyWhenSourceAndDomainEnabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：显式启用 yahoo validation 域后 route READY
    测试对象：SourceRoutePlanner + yahoo_finance validation op
    目的/目标：R3H02-R-25 validation 域启用后可选 yahoo 作 Validation 路径（非 primary）
    验证点：route_status=READY；selected_source_id=yahoo_finance；extra Primary 仍阻断
    失败含义：yahoo validation 域无法 route 到 replay port
    """
    from backend.app.datasources.capability_registry import SourceCapabilityRegistry
    from backend.app.datasources.route_planner import SourceRoutePlanner
    from backend.app.datasources.source_registry import DomainRoleBinding, SourceRegistry

    registry = SourceRegistry()
    registry.load()
    rec = registry.get("yahoo_finance")
    object.__setattr__(rec, "is_enabled", True)
    orig_domain_roles = registry.get_domain_roles

    def _etf_domain_enabled(data_domain: str):
        binding = orig_domain_roles(data_domain)
        if data_domain != "etf_daily_bar":
            return binding
        return DomainRoleBinding(
            primary_source_id=binding.primary_source_id,
            validation_source_id=binding.validation_source_id,
            fallback_policy=binding.fallback_policy,
            domain_enabled_by_default=True,
            fallback_source_ids=binding.fallback_source_ids,
        )

    monkeypatch.setattr(registry, "get_domain_roles", _etf_domain_enabled)
    capabilities = SourceCapabilityRegistry()
    capabilities.load()
    planner = SourceRoutePlanner(source_registry=registry, capability_registry=capabilities)
    monkeypatch.setattr(planner, "_platform_allows", lambda _sid: (True, None))
    plan = planner.plan(
        data_domain="etf_daily_bar",
        operation="fetch_etf_daily_bar_validation",
        run_id="r3h02-yahoo-route-ready",
        job_id="yahoo-route-positive",
        extra_candidates=[("yahoo_finance", "Validation")],
    )
    yahoo = next((c for c in plan.candidates if c.source_id == "yahoo_finance"), None)
    assert yahoo is not None
    assert yahoo.enabled is True
    assert plan.route_status == "READY"
    assert plan.selected_source_id == "yahoo_finance"


def test_alpha_vantage_port_capOverflow_blocksOverMaxSymbols() -> None:
    """覆盖范围：Alpha Vantage factory symbols 数量 cap
    测试对象：create_alpha_vantage_fetch_port symbols 超上限
    目的/目标：§7 max_symbols=5 在 factory 层硬拒绝
    验证点：len(symbols) > MAX_SYMBOLS 构造即 PortError
    失败含义：symbols cap 可被绕过导致无界并发标的拉取
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.alpha_vantage_port import (
        MAX_SYMBOLS,
        create_alpha_vantage_fetch_port,
    )

    with pytest.raises(PortError, match=str(MAX_SYMBOLS)):
        create_alpha_vantage_fetch_port(
            symbols=tuple(f"SYM{i}" for i in range(MAX_SYMBOLS + 1)),
            max_rows=3,
            use_mock=True,
        )


def test_alpha_vantage_port_windowSpan_blocksOverMaxWindowDays() -> None:
    """覆盖范围：Alpha Vantage US equity fetch trading-session 窗口 cap
    测试对象：AlphaVantageMockFetchPort.fetch_payload start/end 跨度
    目的/目标：ADR-007 max_window_days=120 按 trading sessions 在 US equity 入口 reject
    验证点：跨度含 >120 交易日时 PortError 且消息含 cap
    失败含义：US equity window cap 仍按自然日计界，可拉取超窗历史
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.alpha_vantage_port import (
        MAX_WINDOW_DAYS,
        create_alpha_vantage_fetch_port,
    )
    from backend.app.ops.data_health_profiles.us_trading_calendar import get_trading_days

    port = create_alpha_vantage_fetch_port(symbols=("AAPL",), max_rows=3, use_mock=True)
    end = date(2024, 6, 14)
    start = date(2023, 10, 1)
    assert len(get_trading_days(start, end)) > MAX_WINDOW_DAYS
    req = _market_req(
        "alpha_vantage",
        "us_equity_daily_bar",
        "AAPL",
        start_time=start.isoformat(),
        end_time=end.isoformat(),
    )
    with pytest.raises(PortError, match="cap"):
        port.fetch_payload(req)


def test_alpha_vantage_port_optionChain_capOverflow_blocksOverMaxStrikes() -> None:
    """覆盖范围：Alpha Vantage option chain strike cap
    测试对象：AlphaVantageMockFetchPort max_option_strikes 超上限
    目的/目标：§7 max_option_strikes=20 在 port 层硬拒绝
    验证点：max_option_strikes 超 MAX_OPTION_STRIKES 时 PortError
    失败含义：期权链 cap 无保护，可触发全链扫描
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.alpha_vantage_port import (
        MAX_OPTION_STRIKES,
        create_alpha_vantage_fetch_port,
    )

    port = create_alpha_vantage_fetch_port(
        symbols=("AAPL",),
        max_rows=3,
        max_option_strikes=MAX_OPTION_STRIKES + 1,
        use_mock=True,
    )
    with pytest.raises(PortError, match="cap"):
        port.fetch_payload(_market_req("alpha_vantage", "us_option_chain", "AAPL"))


def test_stooq_port_capOverflow_blocksOverMaxRows() -> None:
    """覆盖范围：Stooq port 行数 cap 溢出
    测试对象：StooqMockFetchPort 构造 max_rows 超上限
    目的/目标：ResourceGuard max_rows=500 在 port 层硬拒绝
    验证点：max_rows 超 MAX_ROWS 时 fetch 前 PortError
    失败含义：Stooq cap 无 pytest 保护，回归可绕过
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.stooq_port import MAX_ROWS, create_stooq_fetch_port

    port = create_stooq_fetch_port(symbols=("AAPL.US",), max_rows=MAX_ROWS + 1)
    with pytest.raises(PortError, match="cap"):
        port.fetch_payload(_market_req("stooq", "global_market_daily_bar", "AAPL.US"))


def test_stooq_port_capOverflow_blocksOverMaxSymbols() -> None:
    """覆盖范围：Stooq factory symbols 数量 cap
    测试对象：create_stooq_fetch_port symbols 超上限
    目的/目标：§7 max_symbols=5 在 factory 层硬拒绝
    验证点：len(symbols) > MAX_SYMBOLS 构造即 PortError
    失败含义：symbols cap 可被绕过
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.stooq_port import MAX_SYMBOLS, create_stooq_fetch_port

    with pytest.raises(PortError, match=str(MAX_SYMBOLS)):
        create_stooq_fetch_port(
            symbols=tuple(f"SYM{i}.US" for i in range(MAX_SYMBOLS + 1)),
            max_rows=3,
        )


def test_stooqLiveFetchPort_doesNotFallBackToReplayOnHtmlBlock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：Stooq product live bot/geo 阻断须诚实 FAIL
    测试对象：create_stooq_fetch_port(use_mock=False)
    目的/目标：live 路径不得 replay fixture 假绿（ADR-016 honesty_rules）
    验证点：HTTP 阻断时 PortError 抛出，不返回 replay source_fetch_id
    失败含义：矩阵 stooq validation 行可用 replay 冒充 live PASS
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports import tier_b_validation_live as tbl
    from backend.app.datasources.fetch_ports.stooq_port import create_stooq_fetch_port

    def _blocked(_self, _req):
        raise PortError("NETWORK_ERROR", "Stooq returned HTML instead of CSV (bot/geo block)")

    monkeypatch.setattr(tbl.StooqLiveFetchPort, "fetch_payload", _blocked)
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    port = create_stooq_fetch_port(symbols=("AAPL.US",), max_rows=3, use_mock=False)
    req = _market_req("stooq", "global_market_daily_bar", "AAPL.US")
    with pytest.raises(PortError, match="HTML"):
        port.fetch_payload(req)


def test_stooq_port_windowSpan_blocksOverMaxWindowDays() -> None:
    """覆盖范围：Stooq fetch 窗口天数 cap
    测试对象：StooqMockFetchPort.fetch_payload start/end 跨度
    目的/目标：§7 max_window_days=120 在 fetch 入口 reject_over_cap
    验证点：121 日历日窗口触发 PortError
    失败含义：Stooq window cap 未 enforce
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.stooq_port import MAX_WINDOW_DAYS, create_stooq_fetch_port

    port = create_stooq_fetch_port(symbols=("AAPL.US",), max_rows=3)
    end = datetime.now(UTC).date()
    start = end - timedelta(days=MAX_WINDOW_DAYS + 1)
    req = _market_req(
        "stooq",
        "global_market_daily_bar",
        "AAPL.US",
        start_time=start.isoformat(),
        end_time=end.isoformat(),
    )
    with pytest.raises(PortError, match="cap"):
        port.fetch_payload(req)


def test_yahoo_port_capOverflow_blocksOverMaxRows() -> None:
    """覆盖范围：Yahoo Finance port 行数 cap 溢出
    测试对象：YahooFinanceMockFetchPort 构造 max_rows 超上限
    目的/目标：ResourceGuard max_rows=500 在 port 层硬拒绝
    验证点：max_rows 超 MAX_ROWS 时 PortError
    失败含义：Yahoo validation port cap 无对抗性保护
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.yahoo_finance_port import (
        MAX_ROWS,
        create_yahoo_finance_fetch_port,
    )

    port = create_yahoo_finance_fetch_port(symbols=("AAPL",), max_rows=MAX_ROWS + 1)
    with pytest.raises(PortError, match="cap"):
        port.fetch_payload(_market_req("yahoo_finance", "us_equity_daily_bar", "AAPL"))


def test_yahoo_port_capOverflow_blocksOverMaxSymbols() -> None:
    """覆盖范围：Yahoo factory symbols 数量 cap
    测试对象：create_yahoo_finance_fetch_port symbols 超上限
    目的/目标：§7 max_symbols=3 在 factory 层硬拒绝
    验证点：len(symbols) > MAX_SYMBOLS 构造即 PortError
    失败含义：Yahoo symbols cap 可被绕过
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.yahoo_finance_port import (
        MAX_SYMBOLS,
        create_yahoo_finance_fetch_port,
    )

    with pytest.raises(PortError, match=str(MAX_SYMBOLS)):
        create_yahoo_finance_fetch_port(
            symbols=("AAPL", "MSFT", "SPY", "QQQ"),
            max_rows=3,
        )


def test_yahooAdapter_createFetchPort_boundaryUsesReplayPort() -> None:
    """覆盖范围：adapters 注册指向 yahoo_finance_port 边界
    测试对象：create_fetch_port_for_source('yahoo_finance')
    目的/目标：§9.4 消除 skeleton-only 双轨；默认 port 可产出 evidence v1
    验证点：port fetch 返回 market_data_evidence_v1 且 source_id=yahoo_finance
    失败含义：adapter 层仍与 L2 port 分裂，G16/§9.4 未闭合
    """
    from backend.app.datasources.adapters import create_fetch_port_for_source
    from backend.app.datasources.normalizers.market_data import MARKET_DATA_EVIDENCE_SCHEMA_VERSION

    port = create_fetch_port_for_source("yahoo_finance")
    body = json.loads(
        port.fetch_payload(_market_req("yahoo_finance", "us_equity_daily_bar", "AAPL")).content.decode(
            "utf-8"
        )
    )
    assert body["schema_version"] == MARKET_DATA_EVIDENCE_SCHEMA_VERSION
    assert body["source_id"] == "yahoo_finance"


def _load_capabilities() -> dict:
    path = PROJECT_ROOT / "specs/datasource_registry/source_capabilities.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _enable_market_source_route(
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


@pytest.mark.parametrize(
    ("source_id", "data_domain", "operation"),
    [
        ("yahoo_finance", "global_asset_reference", "fetch_global_asset_reference"),
        ("stooq", "global_market_daily_bar", "fetch_global_daily_bar"),
    ],
)
def test_r3h02_validationOnlySource_blockedAsPrimaryWhenForced(
    monkeypatch: pytest.MonkeyPatch,
    source_id: str,
    data_domain: str,
    operation: str,
) -> None:
    """覆盖范围：validation-only 源不得作为 Primary 路由候选
    测试对象：SourceRoutePlanner + 启用 validation-only 源与域
    目的/目标：对齐 akshare test_layer1_ingestion_gates 对抗模式
    验证点：yaml primary 或 extra_candidates Primary 时 skip_reason=validation_only_cannot_be_primary
    失败含义：validation-only 源可 silent 升格 primary，G13 未闭合
    """
    planner = _enable_market_source_route(
        monkeypatch, source_id=source_id, data_domain=data_domain
    )
    plan = planner.plan(
        data_domain=data_domain,
        operation=operation,
        run_id=f"r3h02-valonly-{source_id}",
        job_id=f"valonly-{source_id}",
    )
    candidate = next(c for c in plan.candidates if c.source_id == source_id)
    assert candidate.capability_declared is True
    assert candidate.skip_reason == "validation_only_cannot_be_primary"
    assert plan.route_status == "VALIDATION_ONLY_BLOCKED"
    assert plan.selected_source_id is None


@pytest.mark.parametrize(
    ("source_id", "data_domain", "operation", "instrument_id", "port_factory"),
    [
        (
            "alpha_vantage",
            "us_equity_daily_bar",
            "fetch_us_daily_bar",
            "AAPL",
            lambda: __import__(
                "backend.app.datasources.fetch_ports.alpha_vantage_port",
                fromlist=["create_alpha_vantage_fetch_port"],
            ).create_alpha_vantage_fetch_port(symbols=("AAPL",), max_rows=3, use_mock=True),
        ),
        (
            "stooq",
            "global_market_daily_bar",
            "fetch_global_daily_bar",
            "AAPL.US",
            lambda: __import__(
                "backend.app.datasources.fetch_ports.stooq_port",
                fromlist=["create_stooq_fetch_port"],
            ).create_stooq_fetch_port(symbols=("AAPL.US",), max_rows=3),
        ),
        (
            "yahoo_finance",
            "us_equity_daily_bar",
            "fetch_us_daily_bar_validation",
            "AAPL",
            lambda: __import__(
                "backend.app.datasources.fetch_ports.yahoo_finance_port",
                fromlist=["create_yahoo_finance_fetch_port"],
            ).create_yahoo_finance_fetch_port(symbols=("AAPL",), max_rows=3),
        ),
    ],
)
def test_r3h02_capabilityFields_matchPortOutput(
    source_id: str,
    data_domain: str,
    operation: str,
    instrument_id: str,
    port_factory,
) -> None:
    """覆盖范围：source_capabilities observation/bundle 字段与 port 输出对齐
    测试对象：R3H-02 市场源 fetch port payload + YAML capability 声明
    目的/目标：P1-05 契约字段分层混写漂移闭合
    验证点：观测行键 ⊇ observation_fields；包顶键 ⊇ bundle_fields
    失败含义：registry 字段声明与 port 输出不一致
    """
    caps = (_load_capabilities().get("sources") or {}).get(source_id, {})
    op_spec = (
        ((caps.get("domains") or {}).get(data_domain) or {}).get("operations") or {}
    ).get(operation, {})
    observation_fields = set(op_spec.get("observation_fields") or op_spec.get("fields") or [])
    bundle_fields = set(op_spec.get("bundle_fields") or [])

    body = json.loads(
        port_factory().fetch_payload(_market_req(source_id, data_domain, instrument_id)).content.decode(
            "utf-8"
        )
    )
    if observation_fields:
        rows = body.get("bars") or body.get("option_chain") or []
        assert rows, f"{source_id} payload missing observation rows"
        assert observation_fields <= set(rows[0].keys())
    if bundle_fields:
        assert bundle_fields <= set(body.keys())


@pytest.mark.parametrize(
    ("source_id", "yaml_key", "port_attr", "module_name"),
    [
        ("alpha_vantage", "max_symbols", "MAX_SYMBOLS", "alpha_vantage_port"),
        ("alpha_vantage", "max_rows", "MAX_ROWS", "alpha_vantage_port"),
        ("alpha_vantage", "max_window_days", "MAX_WINDOW_DAYS", "alpha_vantage_port"),
        ("alpha_vantage", "max_option_strikes", "MAX_OPTION_STRIKES", "alpha_vantage_port"),
        ("stooq", "max_symbols", "MAX_SYMBOLS", "stooq_port"),
        ("stooq", "max_rows", "MAX_ROWS", "stooq_port"),
        ("stooq", "max_window_days", "MAX_WINDOW_DAYS", "stooq_port"),
        ("yahoo_finance", "max_symbols", "MAX_SYMBOLS", "yahoo_finance_port"),
        ("yahoo_finance", "max_window_days", "MAX_WINDOW_DAYS", "yahoo_finance_port"),
    ],
)
def test_r3h02_marketCaps_matchRegistry(
    source_id: str,
    yaml_key: str,
    port_attr: str,
    module_name: str,
) -> None:
    """覆盖范围：registry resource_caps 与 port 模块常量 parity
    测试对象：source_capabilities.yaml + 各 market *_port.py MAX_* 常量
    目的/目标：P2-01 YAML↔port cap 漂移可被 CI 钉死
    验证点：YAML cap 值 == port 模块同名常量
    失败含义：registry 与 port 层 cap 权威分裂
    """
    caps = (_load_capabilities().get("sources") or {}).get(source_id, {}).get("resource_caps") or {}
    mod = __import__(f"backend.app.datasources.fetch_ports.{module_name}", fromlist=[port_attr])
    assert caps[yaml_key] == getattr(mod, port_attr)


@pytest.mark.parametrize(
    ("source_id", "data_domain", "instrument_id", "port_factory", "bad_id"),
    [
        (
            "alpha_vantage",
            "us_equity_daily_bar",
            "ZZZZ",
            lambda: __import__(
                "backend.app.datasources.fetch_ports.alpha_vantage_port",
                fromlist=["create_alpha_vantage_fetch_port"],
            ).create_alpha_vantage_fetch_port(symbols=("AAPL",), max_rows=3, use_mock=True),
            "whitelist",
        ),
        (
            "stooq",
            "global_market_daily_bar",
            "UNKNOWN.US",
            lambda: __import__(
                "backend.app.datasources.fetch_ports.stooq_port",
                fromlist=["create_stooq_fetch_port"],
            ).create_stooq_fetch_port(symbols=("AAPL.US",), max_rows=3),
            "whitelist",
        ),
        (
            "yahoo_finance",
            "us_equity_daily_bar",
            "ZZZZ",
            lambda: __import__(
                "backend.app.datasources.fetch_ports.yahoo_finance_port",
                fromlist=["create_yahoo_finance_fetch_port"],
            ).create_yahoo_finance_fetch_port(symbols=("AAPL",), max_rows=3),
            "whitelist",
        ),
    ],
)
def test_r3h02_marketPort_unknownInstrument_rejectsWhitelist(
    source_id: str,
    data_domain: str,
    instrument_id: str,
    port_factory,
    bad_id: str,
) -> None:
    """覆盖范围：市场 port 未知标的白名单负例
    测试对象：各 market fetch port whitelist guard
    目的/目标：P2-02 unknown symbol fail-closed，非静默空包
    验证点：非白名单 instrument_id 触发 PortError
    失败含义：未知标的可穿透 port，ResourceGuard 失效
    """
    from backend.app.datasources.adapters.fetch_port import PortError

    with pytest.raises(PortError, match=bad_id):
        port_factory().fetch_payload(_market_req(source_id, data_domain, instrument_id))


def test_stooq_port_mockFetch_emitsMarketDataEvidenceV1() -> None:
    """覆盖范围：mock Stooq port validation 抓取
    测试对象：create_stooq_fetch_port + StooqMockFetchPort.fetch_payload
    目的/目标：validation-only port 产出 market_data_evidence_v1
    验证点：schema_version、bars[].trade_date、source_fetch_id
    失败含义：Stooq validation 源无 port 路径，无法登记 READY_WITH_EVIDENCE
    """
    from backend.app.datasources.fetch_ports.stooq_port import create_stooq_fetch_port
    from backend.app.datasources.normalizers.market_data import MARKET_DATA_EVIDENCE_SCHEMA_VERSION

    port = create_stooq_fetch_port(symbols=("AAPL.US",), max_rows=3)
    payload = port.fetch_payload(
        _market_req("stooq", "global_market_daily_bar", "AAPL.US")
    )
    body = json.loads(payload.content.decode("utf-8"))
    assert body["schema_version"] == MARKET_DATA_EVIDENCE_SCHEMA_VERSION
    assert body["source_id"] == "stooq"
    assert body.get("source_fetch_id")
    for bar in body.get("bars") or []:
        assert bar.get("trade_date")


def test_stooq_port_validationOnly_cannotBeSilentPrimary() -> None:
    """覆盖范围：stooq validation-only 不得 silent primary
    测试对象：SourceRoutePlanner 对 us_equity_daily_bar 的路由
    目的/目标：stooq 非 us_equity primary；exchange-grade 域须阻断 validation 升格
    验证点：us_equity 域 primary 为 alpha_vantage 非 stooq；stooq 为 validation_only
    失败含义：aggregator 静默升格为 primary，G13 未闭合
    """
    from backend.app.datasources.source_registry import SourceRegistry

    registry = SourceRegistry()
    registry.load()
    stooq = registry.get("stooq")
    assert stooq.validation_only is True
    binding = registry.get_domain_roles("us_equity_daily_bar")
    assert binding.primary_source_id == "alpha_vantage"
    assert binding.primary_source_id != "stooq"


def test_stooq_port_replayFixture_tradeDateCanonical() -> None:
    """覆盖范围：Stooq replay fixture 读路径
    测试对象：tests/fixtures/replay/market_data/stooq/global_daily_replay.json
    目的/目标：replay 使用 trade_date + market_data_evidence_v1
    验证点：read_daily_bar_evidence_bundle 往返
    失败含义：Stooq replay 路径缺失
    """
    from backend.app.datasources.normalizers.market_data import read_daily_bar_evidence_bundle

    bundle = read_daily_bar_evidence_bundle(_STOOQ_REPLAY)
    assert bundle["source_id"] == "stooq"
    assert bundle["bars"][0]["instrument_id"] == "AAPL.US"


def test_yahoo_port_mockFetch_emitsMarketDataEvidenceV1() -> None:
    """覆盖范围：mock Yahoo Finance port validation 抓取
    测试对象：create_yahoo_finance_fetch_port + YahooFinanceMockFetchPort.fetch_payload
    目的/目标：validation-only port 产出 market_data_evidence_v1（replay-first）
    验证点：schema_version、bars[].trade_date、source_fetch_id
    失败含义：Yahoo 仍 skeleton adapter，G16 未闭合
    """
    from backend.app.datasources.fetch_ports.yahoo_finance_port import create_yahoo_finance_fetch_port
    from backend.app.datasources.normalizers.market_data import MARKET_DATA_EVIDENCE_SCHEMA_VERSION

    port = create_yahoo_finance_fetch_port(symbols=("AAPL",), max_rows=3)
    payload = port.fetch_payload(
        _market_req("yahoo_finance", "us_equity_daily_bar", "AAPL")
    )
    body = json.loads(payload.content.decode("utf-8"))
    assert body["schema_version"] == MARKET_DATA_EVIDENCE_SCHEMA_VERSION
    assert body["source_id"] == "yahoo_finance"
    assert body.get("source_fetch_id")


def test_yahoo_port_validationOnly_blockedAsPrimary() -> None:
    """覆盖范围：yahoo validation-only 不得作为 us_equity primary
    测试对象：SourceRegistry + SourceRoutePlanner
    目的/目标：yahoo 永久 validation_only；us_equity primary 为 alpha_vantage
    验证点：registry.validation_only=True；us_equity primary != yahoo_finance
    失败含义：yahoo 被误升格 primary，违反 §2.8 grill 锁定
    """
    from backend.app.datasources.source_registry import SourceRegistry

    registry = SourceRegistry()
    registry.load()
    yahoo = registry.get("yahoo_finance")
    assert yahoo.validation_only is True
    binding = registry.get_domain_roles("us_equity_daily_bar")
    assert binding.primary_source_id == "alpha_vantage"
    assert binding.primary_source_id != "yahoo_finance"


def test_yahoo_port_replayFixture_migratedFrom3GSemantics() -> None:
    """覆盖范围：3G yahoo fixture 语义迁入 replay 路径
    测试对象：tests/fixtures/replay/market_data/yahoo_finance/aapl_validation_replay.json
    目的/目标：replay 含 AAPL/MSFT bars 与 trade_date（对齐 r3g01/yahoo_finance/bars.json）
    验证点：read_daily_bar_evidence_bundle 含多标的 bars
    失败含义：G16 yahoo fixture 未迁移，3G rehearsal 与 port 分裂
    """
    from backend.app.datasources.normalizers.market_data import read_daily_bar_evidence_bundle

    bundle = read_daily_bar_evidence_bundle(_YAHOO_REPLAY)
    symbols = {bar["instrument_id"] for bar in bundle["bars"]}
    assert "AAPL" in symbols
    assert "MSFT" in symbols


def test_layer_smoke_marketDataReplay_layer2IngestionPreview() -> None:
    """覆盖范围：market data replay → Layer2 ingestion evidence 预览
    测试对象：market_data_bundle_layer2_preview + alpha_vantage replay bundle
    目的/目标：市场证据可被 Layer2 摄取链消费（smoke，非 R3H-05 全审计）
    验证点：preview 含 source_fetch_id、content_hash、sample_trade_date
    失败含义：Layer2 无法绑定市场 replay 证据指纹
    """
    from backend.app.datasources.normalizers.market_data import (
        market_data_bundle_layer2_preview,
        read_daily_bar_evidence_bundle,
    )

    bundle = read_daily_bar_evidence_bundle(_AV_REPLAY)
    preview = market_data_bundle_layer2_preview(bundle)
    assert preview["source_fetch_id"] == "av-replay-aapl"
    assert preview["content_hash"]
    assert preview["sample_trade_date"]


def test_layer_smoke_marketDataReplay_layer4MarketStructurePreview() -> None:
    """覆盖范围：market data replay → Layer4 market structure 预览
    测试对象：market_data_bundle_layer4_preview
    目的/目标：Layer4 样本字段不含 Layer5 禁止 OHLCV 历史字段
    验证点：preview 含 instrument_id、as_of_trade_date；无 forbidden 字段
    失败含义：Layer4 预览泄露 Layer5 禁止字段
    """
    from backend.app.datasources.normalizers.market_data import (
        market_data_bundle_layer4_preview,
        read_daily_bar_evidence_bundle,
    )

    bundle = read_daily_bar_evidence_bundle(_AV_REPLAY)
    preview = market_data_bundle_layer4_preview(bundle)
    assert preview["sample_instrument_id"] == "AAPL"
    assert preview["as_of_trade_date"] == "2024-01-02"
    assert "open" not in preview
    assert "close" not in preview


def test_layer_smoke_marketDataReplay_layer5FactualSourceProvenance() -> None:
    """覆盖范围：market data replay → Layer5 factual_source 溯源字段
    测试对象：market_data_bundle_layer5_provenance + EvidenceFoundationValidator
    目的/目标：replay 行具备 Layer5 契约要求的 source_fetch_id/content_hash 溯源
    验证点：provenance 非空；factual_source 记录通过 foundation 校验
    失败含义：市场证据无法挂接 Layer5 factual_source 链
    """
    from backend.app.datasources.normalizers.market_data import (
        market_data_bundle_layer5_provenance,
        read_daily_bar_evidence_bundle,
    )
    from backend.app.layer5_evidence.models import InstrumentEvidenceRef
    from tests.conftest_layer_smoke import assert_layer5_factual_source_record

    bundle = read_daily_bar_evidence_bundle(_AV_REPLAY)
    prov_fields = market_data_bundle_layer5_provenance(bundle)
    assert_layer5_factual_source_record(
        prov_fields,
        evidence_id="EV-R3H02-MARKET-SMOKE",
        target_id="US-AAPL",
        target_type="equity",
        trade_date=date(2024, 1, 2),
        evidence_summary="AAPL market data replay smoke",
        created_by="r3h02_layer_smoke",
        instrument_ref=InstrumentEvidenceRef(
            instrument_id="US-AAPL",
            symbol="AAPL",
            asset_type="us_equity",
            market_id="US",
            exchange="NASDAQ",
            currency="USD",
            is_active=True,
        ),
    )


def test_layer_smoke_missingContentHash_raises() -> None:
    """覆盖范围：Layer2 smoke 缺指纹负例
    测试对象：market_data_bundle_layer2_preview
    目的/目标：缺 content_hash/source_fetch_id 应失败
    验证点：ValueError 抛出
    失败含义：缺字段仍绿，Layer smoke 无对抗性
    """
    from backend.app.datasources.normalizers.market_data import market_data_bundle_layer2_preview

    with pytest.raises(ValueError, match="content_hash"):
        market_data_bundle_layer2_preview({"bars": [{"trade_date": "2024-01-02"}]})
