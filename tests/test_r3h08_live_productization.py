"""R3H-08 Wave 2 live productization tracer bullets (S08-BOOT+).

参考采纳 cite: specs/contracts/reference_adoption_guardrails.yaml L13-28 adoption_ladder
(L1/L2/L3 等级 SSOT · BOOT 矩阵列)；ADR-027 ProductLiveGate env fail-closed。
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from tests.contract_gate_support import PROJECT_ROOT, trellis_task_dir

TASK_ROOT = trellis_task_dir("06-29-round3h-r3h08-live-productization")
BASELINE_MATRIX = TASK_ROOT / "research/live-tier-baseline-matrix.md"

LIVE_PROD_24_SOURCES = frozenset(
    {
        "fred",
        "us_treasury",
        "sec_edgar",
        "cftc_cot",
        "bis",
        "world_bank",
        "alpha_vantage",
        "deribit",
        "baostock",
        "cninfo",
        "mootdx",
        "yahoo_finance",
        "akshare",
        "stooq",
        "coingecko",
        "eastmoney",
        "sina_finance",
        "tdx_pytdx",
        "ths_ifind",
        "qmt_xtdata",
        "qmt_xqshare",
        "kalshi",
        "polymarket",
        "web_search",
    }
)


def test_productLiveGate_rejectsWhenEnvNotSet(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：产品 live env gate 默认 fail-closed
    测试对象：backend.app.datasources.product_live_gate.assert_product_live_allowed
    目的/目标：未设置 QMD_ALLOW_LIVE_FETCH 时产品 live 必须被拒绝（ADR-027）
    验证点：monkeypatch 清空 env 后 assert_product_live_allowed 抛出 code=LIVE_FETCH_REJECTED
    失败含义：默认即可产品 live，违反 rehearsal 边界与 env-gated PASS 要求
    """
    from backend.app.datasources.product_live_gate import (
        ProductLiveGateError,
        assert_product_live_allowed,
    )

    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    with pytest.raises(ProductLiveGateError) as exc_info:
        assert_product_live_allowed(source_id="fred", operation="fetch")
    assert exc_info.value.code == "LIVE_FETCH_REJECTED"


def test_productLiveGate_allowsWhenEnvOptedIn(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：显式 env opt-in 后产品 live gate 放行 env 层
    测试对象：backend.app.datasources.product_live_gate.assert_product_live_allowed
    目的/目标：QMD_ALLOW_LIVE_FETCH=1 时 env 检查通过（后续切片再接 ResourceGuard/tier）
    验证点：设置 env 后不抛 ProductLiveGateError
    失败含义：env opt-in 无法解除 gate，后续 S08-01..05 无法接线
    """
    from backend.app.datasources.product_live_gate import (
        assert_product_live_allowed,
        is_product_live_fetch_allowed,
    )

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    assert is_product_live_fetch_allowed() is True
    assert_product_live_allowed(source_id="fred", operation="fetch")


def test_liveTierBaselineMatrix_covers24SourcesWithAdoptionColumns() -> None:
    """覆盖范围：S08-BOOT 基线矩阵 24 源盘点
    测试对象：research/live-tier-baseline-matrix.md
    目的/目标：LIVE-PROD-24 每源有 tier/port/状态/切片/reference_anchor/adoption_level
    验证点：矩阵含 24 个 source_id 行；表头含 reference_anchor 与 adoption_level；web_search 延后注记
    失败含义：Execute 无法按矩阵逐源推进 08C→08A→08B→08D
    """
    assert BASELINE_MATRIX.is_file(), f"missing baseline matrix: {BASELINE_MATRIX}"
    text = BASELINE_MATRIX.read_text(encoding="utf-8")
    assert "reference_anchor" in text
    assert "adoption_level" in text
    assert "web_search" in text and ("延后" in text or "defer" in text.lower() or "post-Round4" in text)

    found_sources: set[str] = set()
    for line in text.splitlines():
        if not line.startswith("|") or line.count("|") < 6:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not cells:
            continue
        source_cell = cells[0].strip("`")
        if source_cell in LIVE_PROD_24_SOURCES:
            found_sources.add(source_cell)
            assert cells[5], f"{source_cell} missing reference_anchor"
            assert cells[6], f"{source_cell} missing adoption_level"

    missing = sorted(LIVE_PROD_24_SOURCES - found_sources)
    assert not missing, f"baseline matrix missing sources: {missing}"


def test_liveTierBaselineMatrix_tierMatchesPassPlan() -> None:
    """覆盖范围：矩阵 tier 列与 PASS §2.1 一致
    测试对象：live-tier-baseline-matrix.md tier 列
    目的/目标：防止 BOOT 矩阵 tier 与 R3H_PASS_EXECUTION_PLAN 漂移
    验证点：抽样 Tier A/B/C 代表源 tier 字母匹配 PASS 表
    失败含义：后续切片 Tier 路由与写库守卫会接错轨
    """
    text = BASELINE_MATRIX.read_text(encoding="utf-8")
    expectations = {
        "fred": "A",
        "yahoo_finance": "B",
        "kalshi": "C",
        "web_search": "C",
    }
    for source_id, expected_tier in expectations.items():
        pattern = re.compile(
            rf"\|\s*`{re.escape(source_id)}`\s*\|\s*\*\*{expected_tier}\*\*",
            re.MULTILINE,
        )
        assert pattern.search(text), f"{source_id} tier {expected_tier} not found in matrix"


_08C_CASES: tuple[tuple[str, str, str], ...] = (
    ("fred", "macro_series", "DGS10"),
    ("us_treasury", "us_treasury_yield_curve", "10Y"),
    ("sec_edgar", "us_filings", "0000320193"),
    ("cftc_cot", "cot_positioning", "088691"),
    ("bis", "central_bank_policy", "US"),
    ("world_bank", "development_indicator", "US"),
    ("alpha_vantage", "us_equity_daily_bar", "AAPL"),
    ("deribit", "crypto_options_surface", "BTC-PERPETUAL"),
)


@pytest.mark.parametrize(("source_id", "data_domain", "instrument_id"), _08C_CASES)
def test_r3h08_08c_productLivePort_rejectsWithoutEnv(
    monkeypatch: pytest.MonkeyPatch,
    source_id: str,
    data_domain: str,
    instrument_id: str,
) -> None:
    """覆盖范围：S08-01 08C 八源产品 live port env gate
    测试对象：create_product_live_fetch_port
    目的/目标：未 opt-in QMD_ALLOW_LIVE_FETCH 时 08C port 工厂 fail-closed
    验证点：ProductLiveGateError code=LIVE_FETCH_REJECTED
    失败含义：08C 源可绕过 ProductLiveGate 直接 live fetch
    cite: OpenBB fetcher.py L74-85 arch; digital-oracle bis.py L46-66 L2
    """
    from backend.app.datasources.product_live_gate import ProductLiveGateError
    from backend.app.datasources.product_live_ports import create_product_live_fetch_port

    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    with pytest.raises(ProductLiveGateError) as exc_info:
        create_product_live_fetch_port(source_id=source_id, data_domain=data_domain)
    assert exc_info.value.code == "LIVE_FETCH_REJECTED"


@pytest.mark.parametrize(("source_id", "data_domain", "instrument_id"), _08C_CASES)
def test_r3h08_08c_productLivePort_liveBranchWithEnv(
    monkeypatch: pytest.MonkeyPatch,
    source_id: str,
    data_domain: str,
    instrument_id: str,
) -> None:
    """覆盖范围：S08-01 08C 八源 live 分支契约
    测试对象：create_product_live_fetch_port + fetch_payload
    目的/目标：env opt-in 后每源 live port 可产出 evidence payload（mock HTTP 或 delegate）
    验证点：row_count>=1；非 ProductLiveGateError
    失败含义：08C 源 live 分支未接线或仍 mock-only
    cite: reference-adoption-r3h08.md §7.2 S08-01
    """
    from backend.app.datasources.fetch_result import FetchRequest
    from backend.app.datasources.product_live_ports import create_product_live_fetch_port

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    if source_id == "fred":
        monkeypatch.setenv("FRED_API_KEY", "a" * 32)

        def _mock_obs(self, series_id: str):
            from datetime import UTC, datetime, timedelta

            today = datetime.now(UTC).date()
            return [
                {
                    "series_id": series_id,
                    "observation_date": today.isoformat(),
                    "value": "4.25",
                }
            ]

        monkeypatch.setattr(
            "backend.app.datasources.fetch_ports.fred_port.FredLiveFetchPort._live_observations",
            _mock_obs,
        )
    if source_id == "sec_edgar":
        monkeypatch.setenv("SEC_EDGAR_USER_AGENT", "QMD Test contact@test.example.com")
    if source_id == "alpha_vantage":
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "test-key")

    port = create_product_live_fetch_port(source_id=source_id, data_domain=data_domain)
    req = FetchRequest(
        run_id=f"r3h08-08c-{source_id}",
        source_id=source_id,
        data_domain=data_domain,
        instrument_id=instrument_id,
    )
    payload = port.fetch_payload(req)
    assert payload.row_count >= 1


def test_r3h08_08c_serviceGoldPath_stagedFixtureModeFalse(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：S08-01 DataSourceService 金路径
    测试对象：build_product_live_service + DataSourceService.fetch
    目的/目标：staged_fixture_mode=False 时产品 live 经 service 金路径 fetch
    验证点：service.staged_fixture_mode is False；fetch SUCCESS
    失败含义：产品 live 仍依赖 fixture service 或 bypass service
    """
    from backend.app.datasources.fetch_result import FetchRequest
    from backend.app.datasources.product_live_ports import build_product_live_service
    from backend.app.db.migrate import apply_migrations

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setenv("FRED_API_KEY", "a" * 32)

    def _mock_obs(self, series_id: str):
        from datetime import UTC, datetime

        today = datetime.now(UTC).date()
        return [
            {
                "series_id": series_id,
                "observation_date": today.isoformat(),
                "value": "4.25",
            }
        ]

    monkeypatch.setattr(
        "backend.app.datasources.fetch_ports.fred_port.FredLiveFetchPort._live_observations",
        _mock_obs,
    )

    from backend.app.datasources.capability_registry import SourceCapabilityRegistry
    from backend.app.datasources.source_registry import DomainRoleBinding, SourceRegistry

    registry = SourceRegistry()
    registry.load()
    rec = registry.get("fred")
    object.__setattr__(rec, "is_enabled", True)
    orig_domain_roles = registry.get_domain_roles

    def _macro_enabled(domain: str):
        binding = orig_domain_roles(domain)
        if domain != "macro_series":
            return binding
        return DomainRoleBinding(
            primary_source_id=binding.primary_source_id,
            validation_source_id=binding.validation_source_id,
            fallback_policy=binding.fallback_policy,
            domain_enabled_by_default=True,
            fallback_source_ids=binding.fallback_source_ids,
        )

    monkeypatch.setattr(registry, "get_domain_roles", _macro_enabled)
    caps = SourceCapabilityRegistry()
    caps.load()

    service = build_product_live_service(
        source_id="fred",
        data_domain="macro_series",
        data_root=tmp_path / "raw",
    )
    object.__setattr__(service, "_source_registry", registry)
    object.__setattr__(service, "_capability_registry", caps)
    from backend.app.datasources.route_planner import SourceRoutePlanner

    object.__setattr__(
        service,
        "_route_planner",
        SourceRoutePlanner(source_registry=registry, capability_registry=caps),
    )
    assert service.staged_fixture_mode is False
    monkeypatch.setattr(service._route_planner, "_platform_allows", lambda _sid: (True, None))
    port = service._fetch_port

    def fake_create_adapter(sid, reg, data_root, **kwargs):
        inner_port = kwargs.get("fetch_port") or port

        class FetchPortProbeAdapter:
            source_id = sid

            def fetch(self, req, *, con, job_id=None, record_fetch_log=True):
                from datetime import UTC, datetime

                from backend.app.datasources.fetch_result import FetchResult

                payload = inner_port.fetch_payload(req)
                return FetchResult(
                    run_id=req.run_id,
                    source_id=sid,
                    data_domain=req.data_domain,
                    status="SUCCESS",
                    row_count=payload.row_count,
                    fetch_time=datetime.now(UTC).isoformat(),
                    raw_file_paths=["evidence://product-live-probe"],
                )

        return FetchPortProbeAdapter()

    monkeypatch.setattr("backend.app.datasources.service.create_adapter", fake_create_adapter)
    from backend.app.db.connection import ConnectionManager

    db = tmp_path / "svc.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
        req = FetchRequest(
            run_id="r3h08-08c-svc",
            source_id="fred",
            data_domain="macro_series",
            instrument_id="DGS10",
        )
        result = service.fetch(req, con=con, job_id="job-08c")
    assert result.status == "SUCCESS"
    assert result.row_count >= 1


_08A_CASES: tuple[tuple[str, str], ...] = (
    ("baostock", "cn_equity_daily_bar"),
    ("cninfo", "cn_announcements"),
    ("mootdx", "cn_equity_daily_bar"),
)


@pytest.mark.parametrize(("source_id", "data_domain"), _08A_CASES)
def test_r3h08_08a_cnPrimary_productLiveOptIn(
    monkeypatch: pytest.MonkeyPatch,
    source_id: str,
    data_domain: str,
) -> None:
    """覆盖范围：S08-02 08A CN primary 三源产品 live
    测试对象：create_product_live_fetch_port
    目的/目标：baostock/cninfo/mootdx 经 ProductLiveGate 可 opt-in live（非 rehearsal 冒充）
    验证点：env opt-in 后 payload row_count>=1
    失败含义：CN primary 仍只能走 cn_rehearsal_live_ports 冒充产品
    cite: EasyXT unified_data_interface.py L172-237 forbidden 反例
    """
    from backend.app.datasources.fetch_result import FetchRequest
    from backend.app.datasources.product_live_ports import create_product_live_fetch_port

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    port = create_product_live_fetch_port(source_id=source_id, data_domain=data_domain)
    req = FetchRequest(
        run_id=f"r3h08-08a-{source_id}",
        source_id=source_id,
        data_domain=data_domain,
        instrument_id="sh.600519",
    )
    assert port.fetch_payload(req).row_count >= 1


def test_r3h08_08a_rehearsalPorts_remainRehearsalOnly() -> None:
    """覆盖范围：S08-02 rehearsal 负向
    测试对象：rehearsal_boundary + interface_probe REHEARSAL_ONLY
    目的/目标：rehearsal 入口不得冒充 R3H-08 产品 live SSOT
    验证点：REHEARSAL_ONLY=True；interface_probe 带 REHEARSAL_DISCLAIMER
    失败含义：rehearsal 与产品 live 边界混淆
    cite: EasyXT unified_data_interface.py L172-237 forbidden 反例
    """
    from backend.app.ops import interface_probe
    from backend.app.ops.rehearsal_boundary import PRODUCT_LIVE_READY, REHEARSAL_DISCLAIMER, REHEARSAL_ONLY

    assert interface_probe.REHEARSAL_ONLY is REHEARSAL_ONLY
    assert REHEARSAL_DISCLAIMER
    assert PRODUCT_LIVE_READY is False


def test_r3h08_08b_validationOnly_rejectsCanonicalMainDb(tmp_path: Path) -> None:
    """覆盖范围：S08-03 Tier B validation_only 负向
    测试对象：limited_production_entry._assert_validation_source_isolated_db
    目的/目标：yahoo 等 validation_only 源不得写 canonical main DB
    验证点：canonical main 路径抛 PRODUCTION_DB_PATH_REJECTED
    失败含义：Tier B 可升 primary 写 canonical
    cite: limited_production_entry.py L166-180; EasyXT validation forbidden
    """
    from backend.app.config import DATA_ROOT
    from backend.app.ops.sandbox_clean_write.limited_production_entry import (
        LimitedProductionEntryError,
        _assert_validation_source_isolated_db,
    )

    canonical = DATA_ROOT / "duckdb" / "quant_monitor.duckdb"
    with pytest.raises(LimitedProductionEntryError, match="r3g03_pilot|audit-sandbox"):
        _assert_validation_source_isolated_db("yahoo_finance", canonical)


def test_r3h08_08b_yahoo_productLiveFetch_optIn(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：S08-03 Tier B yahoo 产品 live fetch（非 primary 提升）
    测试对象：create_product_live_fetch_port(yahoo_finance)
    目的/目标：validation_only 源可 env-gated fetch，但不改变 registry primary
    验证点：env opt-in 后 mock replay payload 成功
    失败含义：Tier B fetch 路径未接通
    cite: digital-oracle yfinance_provider.py HTTP 形态 L2/L3
    """
    from backend.app.datasources.fetch_result import FetchRequest
    from backend.app.datasources.product_live_ports import create_product_live_fetch_port
    from backend.app.datasources.source_registry import SourceRegistry

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    reg = SourceRegistry()
    reg.load()
    roles = reg.get_domain_roles("us_equity_daily_bar")
    assert roles.primary_source_id != "yahoo_finance"
    port = create_product_live_fetch_port(
        source_id="yahoo_finance",
        data_domain="us_equity_daily_bar",
    )
    req = FetchRequest(
        run_id="r3h08-08b-yahoo",
        source_id="yahoo_finance",
        data_domain="us_equity_daily_bar",
        instrument_id="AAPL",
    )
    assert port.fetch_payload(req).row_count >= 1


_08B_TIER_B_CASES: tuple[tuple[str, str, str], ...] = (
    ("akshare", "cn_equity_daily_bar", "sh.600519"),
    ("stooq", "us_equity_daily_bar", "AAPL.US"),
    ("coingecko", "crypto_asset_reference", "bitcoin"),
    ("eastmoney", "cn_equity_daily_bar", "sh.600519"),
    ("sina_finance", "cn_equity_daily_bar", "sh.600519"),
    ("tdx_pytdx", "cn_equity_daily_bar", "sh.600519"),
    ("ths_ifind", "concept_theme", "新能源"),
    ("qmt_xtdata", "cn_equity_daily_bar", "000001.SZ"),
    ("qmt_xqshare", "cn_equity_daily_bar", "000001.SZ"),
)


def _tier_b_auth_env(monkeypatch: pytest.MonkeyPatch, source_id: str) -> None:
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    if source_id == "ths_ifind":
        monkeypatch.setenv("THS_IFIND_LICENSE_ARTIFACT", "/tmp/ifind-license.json")
    if source_id == "qmt_xtdata":
        monkeypatch.setenv("QMT_XTDATA_AUTHORIZED", "1")
    if source_id == "qmt_xqshare":
        monkeypatch.setenv("XQSHARE_REMOTE_HOST", "127.0.0.1")
        monkeypatch.setenv("XQSHARE_REMOTE_PORT", "8888")
        monkeypatch.setenv("QMT_XQSHARE_AUTHORIZED", "1")


@pytest.mark.parametrize(("source_id", "data_domain", "instrument_id"), _08B_TIER_B_CASES)
def test_r3h08_08b_tierB_productLiveGate_rejectsWithoutEnv(
    monkeypatch: pytest.MonkeyPatch,
    source_id: str,
    data_domain: str,
    instrument_id: str,
) -> None:
    """覆盖范围：S08-03 Tier B 九源 env gate 负向
    测试对象：create_product_live_fetch_port
    目的/目标：未 opt-in QMD_ALLOW_LIVE_FETCH 时 Tier B 源 fail-closed
    验证点：ProductLiveGateError code=LIVE_FETCH_REJECTED
    失败含义：Tier B validation 源可绕过 ProductLiveGate
    """
    from backend.app.datasources.product_live_gate import ProductLiveGateError
    from backend.app.datasources.product_live_ports import create_product_live_fetch_port

    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    with pytest.raises(ProductLiveGateError) as exc_info:
        create_product_live_fetch_port(source_id=source_id, data_domain=data_domain)
    assert exc_info.value.code == "LIVE_FETCH_REJECTED"


@pytest.mark.parametrize(("source_id", "data_domain", "instrument_id"), _08B_TIER_B_CASES)
def test_r3h08_08b_tierB_productLiveFetch_optIn(
    monkeypatch: pytest.MonkeyPatch,
    source_id: str,
    data_domain: str,
    instrument_id: str,
) -> None:
    """覆盖范围：S08-03 Tier B 九源 env-gated product live fetch
    测试对象：create_product_live_fetch_port + fetch_payload
    目的/目标：validation_only 源可 env-gated fetch，不改变 registry primary
    验证点：env opt-in 后 mock replay payload row_count>=1
    失败含义：LIVE-PROD-24 Tier B 契约未接通
    cite: digital-oracle yfinance_provider.py HTTP 形态 L2/L3
    """
    from backend.app.datasources.fetch_result import FetchRequest
    from backend.app.datasources.product_live_ports import create_product_live_fetch_port

    _tier_b_auth_env(monkeypatch, source_id)
    from backend.app.datasources.live_tier_router import resolve_live_tier

    assert resolve_live_tier(source_id) == "B"
    port = create_product_live_fetch_port(source_id=source_id, data_domain=data_domain)
    req = FetchRequest(
        run_id=f"r3h08-08b-{source_id}",
        source_id=source_id,
        data_domain=data_domain,
        instrument_id=instrument_id,
    )
    assert port.fetch_payload(req).row_count >= 1


def test_r3h08_08c_livePortFactory_noSilentFallbackToMock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：S08-01 08C silent-fallback 负向
    测试对象：create_fred_fetch_port(use_mock=False)
    目的/目标：live 分支被拒绝时不得静默退回 mock port
    验证点：无 env 时抛 ProductLiveGateError（非返回 mock port）
    失败含义：EasyXT 式 silent fallback 渗入产品 live 路径
    cite: reference-adoption-r3h08.md §3 silent_fallback 铁证
    """
    from backend.app.datasources.fetch_ports.fred_port import create_fred_fetch_port
    from backend.app.datasources.product_live_gate import ProductLiveGateError

    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    with pytest.raises(ProductLiveGateError) as exc_info:
        create_fred_fetch_port(series_ids=("DGS10",), max_rows=3, use_mock=False)
    assert exc_info.value.code == "LIVE_FETCH_REJECTED"


@pytest.mark.parametrize("source_id", ("kalshi", "polymarket"))
def test_r3h08_08d_tierC_productLiveGate(
    monkeypatch: pytest.MonkeyPatch,
    source_id: str,
) -> None:
    """覆盖范围：S08-04 Tier C 概率源 env-gated
    测试对象：create_product_live_fetch_port
    目的/目标：kalshi/polymarket 经 ProductLiveGate 而非仅 smoke env
    验证点：无 env 拒绝；有 env 可创建 gated port
    失败含义：Tier C 仍仅 rehearsal smoke 路径
    cite: digital-oracle kalshi.py L88-96; polymarket.py L48-60 L2
    """
    from backend.app.datasources.product_live_gate import ProductLiveGateError
    from backend.app.datasources.product_live_ports import create_product_live_fetch_port

    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    domain = "prediction_market_probability"
    with pytest.raises(ProductLiveGateError) as exc_info:
        create_product_live_fetch_port(source_id=source_id, data_domain=domain)
    assert exc_info.value.code == "LIVE_FETCH_REJECTED"
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    port = create_product_live_fetch_port(source_id=source_id, data_domain=domain)
    assert port is not None


@pytest.mark.parametrize("source_id", ("kalshi", "polymarket"))
def test_r3h08_08d_tierC_productLiveFetch_payload(
    monkeypatch: pytest.MonkeyPatch,
    source_id: str,
) -> None:
    """覆盖范围：S08-04 Tier C 概率源 fetch_payload 契约
    测试对象：create_product_live_fetch_port + fetch_payload
    目的/目标：kalshi/polymarket 经 ProductLiveGate 后可产出 mock evidence payload
    验证点：env opt-in 后 row_count>=1；非 ProductLiveGateError
    失败含义：Tier C 仅 gate 创建、无 fetch 契约测
    cite: digital-oracle kalshi.py L88-96; polymarket.py L48-60 L2
    """
    from backend.app.datasources.fetch_result import FetchRequest
    from backend.app.datasources.product_live_ports import create_product_live_fetch_port

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    if source_id == "kalshi":
        monkeypatch.setattr(
            "backend.app.datasources.fetch_ports.kalshi_port._fetch_live_kalshi_market",
            lambda ticker: {
                "market_ticker": ticker,
                "event_ticker": ticker.split("-")[0],
                "yes_bid": 0.42,
                "yes_ask": 0.45,
                "probability": 0.435,
                "volume": 1200,
                "liquidity": 5000,
                "source_used": "kalshi",
            },
        )
    if source_id == "polymarket":
        monkeypatch.setattr(
            "backend.app.datasources.fetch_ports.polymarket_port._fetch_live_polymarket_market",
            lambda slug: {
                "market_slug": slug,
                "yes_bid": 0.61,
                "yes_ask": 0.63,
                "probability": 0.62,
                "volume": 45000,
                "liquidity": 120000,
                "spread": 0.02,
                "resolution_source": "https://example.com/polymarket/resolution-rules",
                "source_used": "polymarket",
            },
        )
    domain = "prediction_market_probability"
    port = create_product_live_fetch_port(source_id=source_id, data_domain=domain)
    instrument = "KXHIGHNY-24" if source_id == "kalshi" else "will-fed-cut-rates-2024"
    req = FetchRequest(
        run_id=f"r3h08-08d-{source_id}",
        source_id=source_id,
        data_domain=domain,
        instrument_id=instrument,
    )
    assert port.fetch_payload(req).row_count >= 1


def test_r3h08_08d_tierC_productLiveGate_resourceGuard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：S08-04 Tier C ResourceGuard AC
    测试对象：gate_live_fetch_port
    目的/目标：env opt-in 后 ResourceGuard PAUSE/HARD_STOP 仍 fail-closed
    验证点：ProductLiveGateError code=RESOURCE_GUARD_PAUSED
    失败含义：产品 live 绕过 sync_plan 对齐的预算守卫
    cite: ADR-027 ProductLiveGate chain
    """
    from backend.app.core.resource_guard import Decision
    from backend.app.datasources.product_live_gate import ProductLiveGateError, gate_live_fetch_port

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setattr(
        "backend.app.datasources.product_live_gate.ResourceGuard.check",
        lambda self: (Decision.HARD_STOP, "test hard stop"),
    )
    with pytest.raises(ProductLiveGateError) as exc_info:
        gate_live_fetch_port(source_id="kalshi")
    assert exc_info.value.code == "RESOURCE_GUARD_PAUSED"


def test_r3h08_08d_tierC_doesNotWriteCleanBar() -> None:
    """覆盖范围：S08-04 Tier C 不写 clean bar
    测试对象：live_tier_router.resolve_live_tier
    目的/目标：kalshi/polymarket 为 Tier C，非 Tier A clean bar 域
    验证点：tier=C；不在 Tier A 集合
    失败含义：概率源误接 clean bar promote
    """
    from backend.app.datasources.live_tier_router import TIER_A_SOURCES, resolve_live_tier

    for source_id in ("kalshi", "polymarket"):
        assert resolve_live_tier(source_id) == "C"
        assert source_id not in TIER_A_SOURCES


def test_r3h08_05_reconcile_acceptsDatasourceService(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：S08-05 reconcile datasource_service= 金路径
    测试对象：DataSyncOrchestrator.run_reconcile
    目的/目标：生产 profile 下 reconcile 可经 datasource_service= 进入（ADR-025 defer 闭合）
    验证点：不抛 ValueError match DataSourceService；返回 SyncJobResult
    失败含义：reconcile 仍只能 adapter bypass 或硬拒绝 service 路径
    cite: QMD orchestrator.py L272+; OpenBB fetcher.py arch
    """
    from datetime import UTC, datetime

    from backend.app.datasources.fetch_result import FetchResult
    from backend.app.datasources.service import DataSourceService
    from backend.app.sync.orchestrator import DataSyncOrchestrator
    from tests.test_sync_orchestrator import _orchestrator, _simulate_production_profile

    _simulate_production_profile(monkeypatch)
    orch = _orchestrator(tmp_path)
    conflict_id = "conflict-r3h08-svc"
    with orch._cm.writer() as con:
        con.execute(
            """
            INSERT INTO source_conflict (
                conflict_id, run_id, job_id, data_domain, market_id,
                field_name, primary_source, primary_value,
                competing_source, competing_value, normalized_diff,
                severity, reconcile_status, manual_review_required, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                conflict_id,
                "run-r3h08-svc",
                "job-r3h08-svc",
                "market_bar_1d",
                "CN_A",
                "close",
                "baostock",
                "100",
                "qmt_xtdata",
                "150",
                "0.5",
                "severe",
                "UNRESOLVED",
                True,
                datetime.now(UTC),
            ],
        )

    class _SvcStub(DataSourceService):
        def fetch(self, req, *, con, job_id=None, operation=None, on_enter_fetching=None):
            return FetchResult(
                run_id=req.run_id,
                source_id=req.source_id,
                data_domain=req.data_domain,
                status="FAILED",
                row_count=0,
                fetch_time=datetime.now(UTC).isoformat(),
                error_message="stub-no-staging",
            )

    result = orch.run_reconcile(conflict_id, datasource_service=_SvcStub())
    assert result.status == "MANUAL_REVIEW_REQUIRED"


def test_r3h08_05_qmdDataLiveFetch_dryRunDefault(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：S08-05 qmd data live-fetch dry_run 默认
    测试对象：data_commands.live_fetch
    目的/目标：CLI live 子命令默认 dry_run；product_live=True；经 ProductLiveGate
    验证点：dry_run=True；product_live=True；无网络 fetch
    失败含义：CLI 无 live 入口或默认非 dry_run
    """
    from backend.app.cli.data_commands import live_fetch

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    payload = live_fetch(
        source_id="fred",
        data_domain="macro_series",
        dry_run=True,
    )
    assert payload["dry_run"] is True
    assert payload["product_live"] is True
    assert payload["command"] == "live-fetch"


def test_r3h08_liveTierRouter_resolvesPassTiers() -> None:
    """覆盖范围：LiveTierRouter PASS §2.1 映射
    测试对象：resolve_live_tier
    目的/目标：代表源 tier A/B/C 与矩阵一致
    验证点：fred=A；yahoo=B；kalshi=C
    失败含义：tier 路由与 PASS 漂移
    """
    from backend.app.datasources.live_tier_router import resolve_live_tier

    assert resolve_live_tier("fred") == "A"
    assert resolve_live_tier("yahoo_finance") == "B"
    assert resolve_live_tier("kalshi") == "C"


def test_r3h08_05_liveFetch_rejectsWithoutEnv(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：S08-05 live_fetch 无 env 负向
    测试对象：data_commands.live_fetch
    目的/目标：未 opt-in 时 CLI live-fetch fail-closed
    验证点：CliFailure error_code=LIVE_FETCH_REJECTED
    失败含义：CLI 可绕过 ProductLiveGate 预览 live 路由
    """
    from backend.app.cli.data_commands import live_fetch
    from backend.app.cli.errors import CliFailure

    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    with pytest.raises(CliFailure) as exc_info:
        live_fetch(source_id="fred", data_domain="macro_series")
    assert exc_info.value.error_code == "LIVE_FETCH_REJECTED"


def test_r3h08_05_liveFetch_rejectsWhenResourceGuardHardStop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：S08-05 live_fetch ResourceGuard HARD_STOP 负向
    测试对象：data_commands.live_fetch(dry_run=False)
    目的/目标：guard 非 OK 时禁止非 dry-run 产品 live fetch
    验证点：CliFailure error_code=RESOURCE_GUARD_PAUSED
    失败含义：CLI live-fetch 绕过预算守卫写库
    """
    from backend.app.cli.data_commands import live_fetch
    from backend.app.cli.errors import CliFailure
    from backend.app.core.resource_guard import Decision

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setattr(
        "backend.app.datasources.service.DataSourceService.check_resource_guard",
        lambda self: (Decision.HARD_STOP, "test hard stop"),
    )
    with pytest.raises(CliFailure) as exc_info:
        live_fetch(source_id="fred", data_domain="macro_series", dry_run=False)
    assert exc_info.value.error_code == "RESOURCE_GUARD_PAUSED"


def test_r3h08_05_liveFetch_rejectsWhenRouteNotReady(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：S08-05 live_fetch route_status!=READY 负向
    测试对象：data_commands.live_fetch(dry_run=False)
    目的/目标：路由未 READY 时禁止非 dry-run 产品 live fetch
    验证点：CliFailure error_code=DISABLED_SOURCE
    失败含义：CLI 可在禁用源上执行 live fetch
    """
    from backend.app.cli.data_commands import live_fetch
    from backend.app.cli.errors import CliFailure
    from backend.app.core.resource_guard import Decision

    class _BlockedPlan:
        route_status = "DISABLED_SOURCE"
        selected_source_id = "fred"

        def to_payload_dict(self) -> dict[str, str]:
            return {"route_status": self.route_status}

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setattr(
        "backend.app.datasources.service.DataSourceService.check_resource_guard",
        lambda self: (Decision.OK, None),
    )
    monkeypatch.setattr(
        "backend.app.datasources.service.DataSourceService.preview_route",
        lambda self, **kwargs: _BlockedPlan(),
    )
    with pytest.raises(CliFailure) as exc_info:
        live_fetch(source_id="fred", data_domain="macro_series", dry_run=False)
    assert exc_info.value.error_code == "DISABLED_SOURCE"


def test_r3h08_05_probeTracer_linksInterfaceProbeServicePath() -> None:
    """覆盖范围：S08-05 probe→service R3H-08 追溯链
    测试对象：interface_probe.run_single_probe + EXECUTION_INDEX §2.1
    目的/目标：探针网络 fetch 与 R3H-08 产品 live 均经 DataSourceService 金路径
    验证点：run_single_probe 源码含 DataSourceService；INDEX 链接 test_interface_probe_018c
    失败含义：probe 与产品 live 金路径割裂，审计无法追溯
    """
    import inspect

    from backend.app.ops import interface_probe

    svc_src = inspect.getsource(interface_probe._fetch_payload_via_service)
    assert "DataSourceService" in svc_src
    index_text = (TASK_ROOT / "EXECUTION_INDEX.md").read_text(encoding="utf-8")
    assert "test_interface_probe_018c.py" in index_text


def test_r3h08_05_qmdDataLiveFetch_cliSubprocessDryRun(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """覆盖范围：S08-05 qmd data live-fetch CLI 子进程
    测试对象：backend.app.cli.main data live-fetch
    目的/目标：CLI 注册 live-fetch 且默认 dry_run JSON 可解析
    验证点：exit 0；stdout JSON dry_run=true、command=live-fetch
    失败含义：main.py 未接线 live-fetch 子命令
    """
    import os

    data_root = tmp_path / "data"
    data_root.mkdir()
    env = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT), "QMD_DATA_ROOT": str(data_root)}
    env["QMD_ALLOW_LIVE_FETCH"] = "1"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "backend.app.cli.main",
            "data",
            "live-fetch",
            "--source-id",
            "fred",
            "--domain",
            "macro_series",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["command"] == "live-fetch"
    assert payload["dry_run"] is True
    assert payload["product_live"] is True
