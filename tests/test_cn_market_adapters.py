"""R3H-03 中国市场数据适配器测试（Batch 3H）。

覆盖范围：baostock、cninfo、akshare、tdx_pytdx、mootdx、eastmoney、sina_finance、
ths_ifind、qmt_xtdata、qmt_xqshare 的 fetch port、cn_market 证据契约、路由与 Layer smoke。
测试对象：backend/app/datasources/normalizers/cn_market.py 及十源 fetch port 模块。
目的/目标：证明中国市场源可在 replay-first 路径下产出 cn_market_evidence_v1 并满足 cap/route 终态。
验证点：test_cn_market_adapters 全量及 -k 子集通过当前 pytest 验收。
失败含义：Batch 3H R3H-03 无法在 Round4 前闭合中国市场源生产入口决策。
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
import yaml

from backend.app.config import PROJECT_ROOT

_LICENSE_GATE_ENV_VARS = (
    "QMT_XTDATA_AUTHORIZED",
    "THS_IFIND_LICENSE_ARTIFACT",
    "XQSHARE_REMOTE_HOST",
    "XQSHARE_REMOTE_PORT",
    "QMT_XQSHARE_AUTHORIZED",
)


def _clear_license_gate_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate default-unauthorized tests from project .env authorization flags."""
    for name in _LICENSE_GATE_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


_BAOSTOCK_REPLAY = (
    PROJECT_ROOT / "tests/fixtures/replay/cn_market/baostock/sh600519_daily_replay.json"
)
_CNINFO_REPLAY = (
    PROJECT_ROOT / "tests/fixtures/replay/cn_market/cninfo/sh600519_filings_replay.json"
)
_MOOTDX_REPLAY = PROJECT_ROOT / "tests/fixtures/replay/cn_market/tdx/mootdx_daily_replay.json"


def _cn_req(source_id: str, data_domain: str, instrument_id: str, **overrides: object):
    from backend.app.datasources.fetch_result import FetchRequest

    base = {
        "run_id": f"r3h03-{source_id}",
        "source_id": source_id,
        "data_domain": data_domain,
        "instrument_id": instrument_id,
    }
    base.update(overrides)
    return FetchRequest(**base)


def _load_capabilities() -> dict:
    path = PROJECT_ROOT / "specs/datasource_registry/source_capabilities.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _enable_cn_source_route(tmp_path: Path, *, source_id: str, data_domain: str):
    from tests.service_path_support import enable_source_route

    return enable_source_route(tmp_path, source_id=source_id, data_domain=data_domain)


# --- 9.1 evidence_contract ---


def test_evidence_contract_writeReadRoundTrip_fixturePreservesFields(tmp_path: Path) -> None:
    """覆盖范围：cn_market 证据包 read/write 往返
    测试对象：write_cn_market_evidence_bundle + read_cn_market_evidence_bundle
    目的/目标：replay fixture 经 normalizer 无损读写 canonical 字段
    验证点：source_fetch_id、content_hash、schema_hash、trade_date 保留
    失败含义：cn_market_evidence_v1 无法贯通 replay 链
    """
    from backend.app.datasources.normalizers.cn_market import (
        CN_MARKET_EVIDENCE_SCHEMA_VERSION,
        read_cn_market_evidence_bundle,
        write_cn_market_evidence_bundle,
    )

    legacy = json.loads(_BAOSTOCK_REPLAY.read_text(encoding="utf-8"))
    out = tmp_path / "roundtrip"
    write_cn_market_evidence_bundle(out, legacy)
    bundle = read_cn_market_evidence_bundle(out)
    assert bundle["schema_version"] == CN_MARKET_EVIDENCE_SCHEMA_VERSION
    assert bundle["source_fetch_id"] == "baostock-replay-600519"
    assert bundle.get("schema_hash")
    assert bundle["bars"][0]["trade_date"] == "2024-06-25"


def test_evidence_contract_stagedPilotBaostockShapeMigrates() -> None:
    """覆盖范围：staged pilot baostock 形状 L2 迁出
    测试对象：bars_from_baostock_staged_payload
    目的/目标：G11 staged pilot rows 转为 canonical bars
    验证点：trade_date、instrument_id、source_used=baostock
    失败含义：staged pilot 形状无法迁入 cn_market normalizer
    """
    from backend.app.datasources.normalizers.cn_market import bars_from_baostock_staged_payload

    payload = {
        "symbol": "sh.600519",
        "source": "baostock",
        "rows": [["2024-06-25", "sh.600519", "1400", "1410", "1395", "1405", "1000000"]],
    }
    bars = bars_from_baostock_staged_payload(payload)
    assert bars[0]["trade_date"] == "2024-06-25"
    assert bars[0]["instrument_id"] == "sh.600519"
    assert bars[0]["source_used"] == "baostock"


def test_evidence_contract_stagedPilotCninfoMetadataMigrates() -> None:
    """覆盖范围：staged pilot cninfo metadata 形状 L2 迁出
    测试对象：filings_from_cninfo_metadata_payload
    目的/目标：G16 cninfo metadata rows 转为 canonical filings
    验证点：title、observation_date、source_used=cninfo
    失败含义：cninfo staged metadata 无法迁入 cn_market normalizer
    """
    from backend.app.datasources.normalizers.cn_market import filings_from_cninfo_metadata_payload

    payload = {
        "symbol": "sh.600519",
        "source": "cninfo",
        "rows": [{"公告标题": "年报摘要", "公告时间": "2024-06-25"}],
    }
    filings = filings_from_cninfo_metadata_payload(payload)
    assert filings[0]["title"] == "年报摘要"
    assert filings[0]["source_used"] == "cninfo"


def test_evidence_contract_licenseGateDefaultDisabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：license_gate 默认 DISABLED
    测试对象：check_license_gate
    目的/目标：QMT/iFinD/xqshare 无 env 时非 AUTHORIZED
    验证点：qmt_xtdata/ths_ifind/qmt_xqshare 默认非 AUTHORIZED
    失败含义：授权门默认放行
    """
    _clear_license_gate_env(monkeypatch)
    from backend.app.datasources.auth.license_gate import LicenseGateDecision, check_license_gate

    for source_id in ("qmt_xtdata", "ths_ifind", "qmt_xqshare"):
        assert check_license_gate(source_id) != LicenseGateDecision.AUTHORIZED


# --- 9.2 baostock ---


def test_baostock_port_mockFetch_emitsCnMarketEvidenceV1() -> None:
    """覆盖范围：mock baostock port 日线抓取
    测试对象：create_baostock_fetch_port + BaostockMockFetchPort.fetch_payload
    目的/目标：port 产出 cn_market_evidence_v1
    验证点：schema_version、bars[].trade_date、source_fetch_id
    失败含义：baostock 无 port 路径
    """
    from backend.app.datasources.fetch_ports.baostock_port import create_baostock_fetch_port
    from backend.app.datasources.normalizers.cn_market import CN_MARKET_EVIDENCE_SCHEMA_VERSION

    port = create_baostock_fetch_port(symbols=("sh.600519",), max_rows=5)
    body = json.loads(
        port.fetch_payload(_cn_req("baostock", "cn_equity_daily_bar", "sh.600519")).content.decode()
    )
    assert body["schema_version"] == CN_MARKET_EVIDENCE_SCHEMA_VERSION
    assert body["source_id"] == "baostock"
    assert body.get("source_fetch_id")
    assert body["bars"][0]["trade_date"]


def test_baostock_port_capOverflow_blocksOverMaxRows() -> None:
    """覆盖范围：baostock 行数 cap 溢出
    测试对象：BaostockMockFetchPort max_rows 超上限
    目的/目标：ResourceGuard cap 在 port 层硬拒绝
    验证点：max_rows 超 MAX_ROWS 时 PortError
    失败含义：baostock cap 可被绕过
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.baostock_port import MAX_ROWS, create_baostock_fetch_port

    port = create_baostock_fetch_port(symbols=("sh.600519",), max_rows=MAX_ROWS + 1)
    with pytest.raises(PortError, match="cap"):
        port.fetch_payload(_cn_req("baostock", "cn_equity_daily_bar", "sh.600519"))


def test_baostock_port_windowSpan_blocksOverMaxWindowDays() -> None:
    """覆盖范围：baostock 日历窗口天数 cap
    测试对象：BaostockMockFetchPort start/end 跨度
    目的/目标：frozen §7 MAX_WINDOW_DAYS=120 在 fetch 入口 enforce
    验证点：121 日历日窗口触发 PortError 且消息含 cap
    失败含义：window cap 未接线，可拉取超窗历史
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.baostock_port import (
        MAX_WINDOW_DAYS,
        create_baostock_fetch_port,
    )

    port = create_baostock_fetch_port(symbols=("sh.600519",), max_rows=5)
    end = date(2024, 6, 30)
    start = end - timedelta(days=MAX_WINDOW_DAYS + 1)
    req = _cn_req(
        "baostock",
        "cn_equity_daily_bar",
        "sh.600519",
        start_time=start.isoformat(),
        end_time=end.isoformat(),
    )
    with pytest.raises(PortError, match="cap"):
        port.fetch_payload(req)


def test_baostock_route_primaryReadyOnCnEquityDailyBar() -> None:
    """覆盖范围：baostock cn_equity_daily_bar Primary READY
    测试对象：SourceRoutePlanner.plan
    目的/目标：常规 CN 日线域应选出 baostock
    验证点：route_status=READY；selected_source_id=baostock
    失败含义：baostock primary 路由未 READY
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
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        run_id="r3h03-baostock-route",
        job_id="baostock-route",
    )
    assert plan.route_status == "READY"
    assert plan.selected_source_id == "baostock"


# --- 9.3 cninfo ---


def test_cninfo_port_mockFetch_emitsFilingsMetadata() -> None:
    """覆盖范围：mock cninfo port 公告 metadata
    测试对象：create_cninfo_fetch_port
    目的/目标：cninfo replay-first metadata 路径
    验证点：filings[].title、observation_date、source_id=cninfo
    失败含义：cninfo 无 metadata port
    """
    from backend.app.datasources.fetch_ports.cninfo_port import create_cninfo_fetch_port
    from backend.app.datasources.normalizers.cn_market import CN_MARKET_EVIDENCE_SCHEMA_VERSION

    port = create_cninfo_fetch_port(symbols=("sh.600519",), max_rows=5)
    body = json.loads(
        port.fetch_payload(_cn_req("cninfo", "cn_announcements", "sh.600519")).content.decode()
    )
    assert body["schema_version"] == CN_MARKET_EVIDENCE_SCHEMA_VERSION
    assert body["filings"][0]["title"]
    assert body.get("observation_date") or body["filings"][0].get("observation_date")


def test_cninfo_port_pdfCapBlocksOversize() -> None:
    """覆盖范围：cninfo PDF cap 强制
    测试对象：CninfoMockFetchPort cn_pdf_reports domain
    目的/目标：§7 PDF 5MB cap 硬拒绝
    验证点：pdf_bytes 超 cap 时 PortError
    失败含义：PDF cap 无对抗性保护
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.cninfo_port import (
        MAX_PDF_BYTES,
        CninfoMockFetchPort,
    )

    port = CninfoMockFetchPort(
        symbols=("sh.600519",),
        max_rows=1,
        pdf_bytes=MAX_PDF_BYTES + 1,
        enable_pdf_live=True,
    )
    with pytest.raises(PortError, match="pdf"):
        port.fetch_payload(_cn_req("cninfo", "cn_pdf_reports", "sh.600519"))


def test_cninfo_port_filingsCapOverflow_blocksOverMaxFilings() -> None:
    """覆盖范围：cninfo filings 行数 cap 溢出
    测试对象：CninfoMockFetchPort max_rows 超 MAX_FILINGS
    目的/目标：A4-OPEN-02 filings cap 有 pytest 回归锚点
    验证点：max_rows 超 MAX_FILINGS 时 PortError
    失败含义：cninfo filings cap 可被绕过
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.cninfo_port import MAX_FILINGS, create_cninfo_fetch_port

    port = create_cninfo_fetch_port(symbols=("sh.600519",), max_rows=MAX_FILINGS + 1)
    with pytest.raises(PortError, match="cap"):
        port.fetch_payload(_cn_req("cninfo", "cn_announcements", "sh.600519"))


# --- 9.4 akshare ---


def test_akshare_port_validationOnly_hasQualityFlags() -> None:
    """覆盖范围：akshare validation port quality_flags
    测试对象：create_akshare_fetch_port
    目的/目标：aggregator 必须带 quality_flags
    验证点：quality_flags 含 AGGREGATOR_VALIDATION
    失败含义：akshare 无 quality_flags
    """
    from backend.app.datasources.fetch_ports.akshare_port import create_akshare_fetch_port

    port = create_akshare_fetch_port(symbols=("sh.600519",), max_rows=3)
    body = json.loads(
        port.fetch_payload(_cn_req("akshare", "cn_equity_daily_bar", "sh.600519")).content.decode()
    )
    flags = body.get("quality_flags") or []
    assert "AGGREGATOR_VALIDATION" in flags


def test_akshare_validationOnlySource_blockedAsPrimaryWhenForced(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：akshare validation-only 不得作为 Primary
    测试对象：SourceRoutePlanner + extra_candidates Primary
    目的/目标：akshare 永久 validation_only 路由对抗
    验证点：skip_reason=validation_only_cannot_be_primary
    失败含义：akshare 可 silent 升格 primary
    """
    planner = _enable_cn_source_route(
        tmp_path, source_id="akshare", data_domain="cn_equity_daily_bar"
    )
    plan = planner.plan(
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        run_id="r3h03-akshare-val",
        job_id="akshare-val",
        extra_candidates=[("akshare", "Primary")],
    )
    candidate = next(
        c for c in plan.candidates if c.source_id == "akshare" and c.role == "Primary"
    )
    assert candidate.skip_reason == "validation_only_cannot_be_primary"
    assert plan.selected_source_id != "akshare"


def test_akshare_port_capOverflow_blocksOverMaxRows() -> None:
    """覆盖范围：akshare 行数 cap 溢出
    测试对象：AkshareMockFetchPort max_rows 超上限
    目的/目标：G1/A4-OPEN-02 reject_over_cap 有登记对抗测
    验证点：max_rows 超 MAX_ROWS 时 PortError
    失败含义：akshare cap 可被绕过
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.akshare_port import MAX_ROWS, create_akshare_fetch_port

    port = create_akshare_fetch_port(symbols=("sh.600519",), max_rows=MAX_ROWS + 1)
    with pytest.raises(PortError, match="cap"):
        port.fetch_payload(_cn_req("akshare", "cn_equity_daily_bar", "sh.600519"))


@pytest.mark.parametrize("data_domain", ["cn_index", "sector_board"])
def test_akshare_validationOnly_blocksPrimaryOnYamlPrimaryDomains(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    data_domain: str,
) -> None:
    """覆盖范围：akshare yaml primary 域仍不得 runtime Primary
    测试对象：SourceRoutePlanner + cn_index/sector_board
    目的/目标：A3 yaml primary 脚注 + validation_only fail-closed
    验证点：extra_candidates Primary → validation_only_cannot_be_primary
    失败含义：移除 validation_only 后 akshare 可 silent 升格
    """
    planner = _enable_cn_source_route(tmp_path, source_id="akshare", data_domain=data_domain)
    plan = planner.plan(
        data_domain=data_domain,
        operation="fetch_index_daily_bar" if data_domain == "cn_index" else "fetch_sector_board",
        run_id=f"r3h03-akshare-{data_domain}",
        job_id=f"akshare-{data_domain}",
        extra_candidates=[("akshare", "Primary")],
    )
    candidate = next(
        c for c in plan.candidates if c.source_id == "akshare" and c.role == "Primary"
    )
    assert candidate.skip_reason == "validation_only_cannot_be_primary"
    assert plan.selected_source_id != "akshare"


# --- 9.5 tdx / mootdx ---


def test_mootdx_port_mockFetch_independentSourceId() -> None:
    """覆盖范围：mootdx 独立 source_id
    测试对象：create_mootdx_fetch_port
    目的/目标：mootdx 与 tdx_pytdx 无 silent fallback
    验证点：body.source_id == mootdx
    失败含义：mootdx 未独立登记
    """
    from backend.app.datasources.fetch_ports.mootdx_port import create_mootdx_fetch_port

    port = create_mootdx_fetch_port(symbols=("sh.600519",), max_rows=3)
    body = json.loads(
        port.fetch_payload(_cn_req("mootdx", "cn_equity_daily_bar", "sh.600519")).content.decode()
    )
    assert body["source_id"] == "mootdx"


def test_mootdx_port_rejectsMinuteBars() -> None:
    """覆盖范围：mootdx 分钟线拒绝
    测试对象：MootdxMockFetchPort minute domain
    目的/目标：minute_bars_enabled=false
    验证点：minute domain PortError
    失败含义：mootdx 默认分钟线
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.mootdx_port import create_mootdx_fetch_port

    port = create_mootdx_fetch_port(symbols=("sh.600519",), max_rows=3)
    with pytest.raises(PortError, match="minute"):
        port.fetch_payload(_cn_req("mootdx", "cn_equity_minute_bar", "sh.600519"))


def test_tdx_pytdx_port_stillRequiresGateAuth(tmp_path: Path) -> None:
    """覆盖范围：tdx_pytdx 仍须 gate 授权
    测试对象：TdxPytdxFetchPort 无 authorization
    目的/目标：tdx_pytdx 与 mootdx 并存且无 silent enable
    验证点：无 token 时 USER_AUTH_REQUIRED
    失败含义：tdx_pytdx 可无授权拉数
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.tdx_pytdx_port import TdxPytdxFetchPort

    port = TdxPytdxFetchPort(("sh.600519",), 3)
    with pytest.raises(PortError) as exc_info:
        port.fetch_payload(_cn_req("tdx_pytdx", "cn_equity_daily_bar", "sh.600519"))
    assert exc_info.value.status == "USER_AUTH_REQUIRED"


def test_mootdx_port_capOverflow_blocksOverMaxRows() -> None:
    """覆盖范围：mootdx 行数 cap 溢出
    测试对象：MootdxMockFetchPort max_rows 超 EQUITY_INDEX_MAX_ROWS
    目的/目标：G2 frozen §7 3 bars cap 有 pytest 回归
    验证点：max_rows 超 cap 时 PortError
    失败含义：mootdx cap 可被绕过
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.mootdx_port import (
        EQUITY_INDEX_MAX_ROWS,
        create_mootdx_fetch_port,
    )

    port = create_mootdx_fetch_port(symbols=("sh.600519",), max_rows=EQUITY_INDEX_MAX_ROWS + 1)
    with pytest.raises(PortError, match="cap"):
        port.fetch_payload(_cn_req("mootdx", "cn_equity_daily_bar", "sh.600519"))


def test_tdx_pytdx_port_capOverflow_blocksOverMaxRows() -> None:
    """覆盖范围：tdx_pytdx 行数 cap 溢出
    测试对象：TdxPytdxFetchPort max_rows 超上限（先于 auth 检查）
    目的/目标：G2 tdx family cap 有登记对抗测
    验证点：max_rows 超 cap 时 PortError
    失败含义：tdx_pytdx cap 可被绕过
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.tdx_pytdx_port import (
        EQUITY_INDEX_MAX_ROWS,
        TdxPytdxFetchPort,
    )

    port = TdxPytdxFetchPort(("sh.600519",), EQUITY_INDEX_MAX_ROWS + 1)
    with pytest.raises(PortError, match="cap"):
        port.fetch_payload(_cn_req("tdx_pytdx", "cn_equity_daily_bar", "sh.600519"))


# --- 9.6 eastmoney / sina ---


def test_eastmoney_port_conflictEvidencePresent() -> None:
    """覆盖范围：eastmoney conflict_evidence 字段
    测试对象：create_eastmoney_fetch_port
    目的/目标：validation 源须记录 primary 对照
    验证点：conflict_evidence.primary_source_id == baostock
    失败含义：eastmoney 无 conflict 证据
    """
    from backend.app.datasources.fetch_ports.eastmoney_port import create_eastmoney_fetch_port

    port = create_eastmoney_fetch_port(symbols=("sh.600519",), max_rows=3)
    body = json.loads(
        port.fetch_payload(_cn_req("eastmoney", "cn_equity_daily_bar", "sh.600519")).content.decode()
    )
    assert body["conflict_evidence"]["primary_source_id"] == "baostock"
    assert body.get("quality_flags")


def test_sina_port_conflictEvidencePresent() -> None:
    """覆盖范围：sina_finance conflict_evidence 字段
    测试对象：create_sina_finance_fetch_port
    目的/目标：sina validation 不得 silent 替换 primary
    验证点：conflict_evidence.validation_source_id == sina_finance
    失败含义：sina 无 conflict 证据
    """
    from backend.app.datasources.fetch_ports.sina_finance_port import create_sina_finance_fetch_port

    port = create_sina_finance_fetch_port(symbols=("sh.600519",), max_rows=3)
    body = json.loads(
        port.fetch_payload(_cn_req("sina_finance", "cn_equity_daily_bar", "sh.600519")).content.decode()
    )
    assert body["conflict_evidence"]["validation_source_id"] == "sina_finance"


def test_eastmoney_port_capOverflow_blocksOverMaxRows() -> None:
    """覆盖范围：eastmoney 行数 cap 溢出
    测试对象：EastmoneyMockFetchPort max_rows 超上限
    目的/目标：G1 aggregator cap 有登记对抗测
    验证点：max_rows 超 MAX_ROWS 时 PortError
    失败含义：eastmoney cap 可被绕过
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.eastmoney_port import MAX_ROWS, create_eastmoney_fetch_port

    port = create_eastmoney_fetch_port(symbols=("sh.600519",), max_rows=MAX_ROWS + 1)
    with pytest.raises(PortError, match="cap"):
        port.fetch_payload(_cn_req("eastmoney", "cn_equity_daily_bar", "sh.600519"))


def test_sina_port_capOverflow_blocksOverMaxRows() -> None:
    """覆盖范围：sina_finance 行数 cap 溢出
    测试对象：SinaFinanceMockFetchPort max_rows 超上限
    目的/目标：G1 aggregator cap 有登记对抗测
    验证点：max_rows 超 MAX_ROWS 时 PortError
    失败含义：sina cap 可被绕过
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.sina_finance_port import (
        MAX_ROWS,
        create_sina_finance_fetch_port,
    )

    port = create_sina_finance_fetch_port(symbols=("sh.600519",), max_rows=MAX_ROWS + 1)
    with pytest.raises(PortError, match="cap"):
        port.fetch_payload(_cn_req("sina_finance", "cn_equity_daily_bar", "sh.600519"))


def test_eastmoney_validationOnly_blockedAsPrimaryWhenForced(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：eastmoney validation-only 不得作为 Primary
    测试对象：SourceRoutePlanner + extra_candidates Primary
    目的/目标：G4 eastmoney 路由对抗登记
    验证点：skip_reason=validation_only_cannot_be_primary
    失败含义：eastmoney 可 silent 升格 primary
    """
    from tests.service_path_support import enable_source_route

    planner = enable_source_route(
        tmp_path,
        source_id="eastmoney",
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
    )
    plan = planner.plan(
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        run_id="r3h03-eastmoney-val",
        job_id="eastmoney-val",
        extra_candidates=[("eastmoney", "Primary")],
    )
    candidate = next(
        c for c in plan.candidates if c.source_id == "eastmoney" and c.role == "Primary"
    )
    assert candidate.skip_reason == "validation_only_cannot_be_primary"


def test_sina_validationOnly_blockedAsPrimaryWhenForced(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：sina_finance validation-only 不得作为 Primary
    测试对象：SourceRoutePlanner + extra_candidates Primary
    目的/目标：G4 sina 路由对抗登记
    验证点：skip_reason=validation_only_cannot_be_primary
    失败含义：sina 可 silent 升格 primary
    """
    from tests.service_path_support import enable_source_route

    planner = enable_source_route(
        tmp_path,
        source_id="sina_finance",
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
    )
    plan = planner.plan(
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        run_id="r3h03-sina-val",
        job_id="sina-val",
        extra_candidates=[("sina_finance", "Primary")],
    )
    candidate = next(
        c for c in plan.candidates if c.source_id == "sina_finance" and c.role == "Primary"
    )
    assert candidate.skip_reason == "validation_only_cannot_be_primary"


# --- 9.7 ifind / qmt / xqshare ---


def test_ifind_port_unauthorizedBlocksByDefault(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：ths_ifind 未授权负例
    测试对象：ThsIfindMockFetchPort 无 env
    目的/目标：默认 authorization-disabled
    验证点：PortError USER_AUTH_REQUIRED
    失败含义：iFinD 无授权可拉数
    """
    _clear_license_gate_env(monkeypatch)
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.ths_ifind_port import create_ths_ifind_fetch_port

    port = create_ths_ifind_fetch_port(concepts=("白酒",), max_rows=3)
    with pytest.raises(PortError) as exc_info:
        port.fetch_payload(_cn_req("ths_ifind", "concept_theme", "白酒"))
    assert exc_info.value.status == "USER_AUTH_REQUIRED"


def test_ifind_port_authorizedFixturePasses(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：ths_ifind 授权正例
    测试对象：ThsIfindMockFetchPort + THS_IFIND_LICENSE_ARTIFACT env
    目的/目标：授权 env 齐全时可 mock fetch
    验证点：filings 非空
    失败含义：授权正例路径缺失
    """
    from backend.app.datasources.fetch_ports.ths_ifind_port import create_ths_ifind_fetch_port

    monkeypatch.setenv("THS_IFIND_LICENSE_ARTIFACT", "/tmp/ifind-license.json")
    port = create_ths_ifind_fetch_port(concepts=("白酒",), max_rows=3)
    body = json.loads(port.fetch_payload(_cn_req("ths_ifind", "concept_theme", "白酒")).content.decode())
    assert body["filings"]


def test_qmt_port_unauthorizedBlocksByDefault(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：qmt_xtdata 未授权负例
    测试对象：QmtXtdataMockFetchPort 无 env
    目的/目标：D11 默认 disabled
    验证点：PortError USER_AUTH_REQUIRED
    失败含义：QMT 无授权可拉数
    """
    _clear_license_gate_env(monkeypatch)
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.qmt_xtdata_port import create_qmt_xtdata_fetch_port

    port = create_qmt_xtdata_fetch_port(symbols=("sh.600519",), max_rows=3)
    with pytest.raises(PortError) as exc_info:
        port.fetch_payload(_cn_req("qmt_xtdata", "cn_equity_daily_bar", "sh.600519"))
    assert exc_info.value.status == "USER_AUTH_REQUIRED"


def test_qmt_port_authorizedFixturePasses(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：qmt_xtdata 授权正例
    测试对象：QmtXtdataMockFetchPort + QMT_XTDATA_AUTHORIZED env
    目的/目标：用户 env proof 后可 mock fetch
    验证点：bars 非空
    失败含义：QMT 授权正例路径缺失
    """
    from backend.app.datasources.fetch_ports.qmt_xtdata_port import create_qmt_xtdata_fetch_port

    monkeypatch.setenv("QMT_XTDATA_AUTHORIZED", "1")
    port = create_qmt_xtdata_fetch_port(symbols=("sh.600519",), max_rows=3)
    body = json.loads(
        port.fetch_payload(_cn_req("qmt_xtdata", "cn_equity_daily_bar", "sh.600519")).content.decode()
    )
    assert body["bars"]


def test_xqshare_port_unauthorizedBlocksByDefault(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：qmt_xqshare 未授权负例
    测试对象：QmtXqshareMockFetchPort 无 env
    目的/目标：xqshare 须三门 env + 授权
    验证点：PortError USER_AUTH_REQUIRED
    失败含义：xqshare 无授权可拉数
    """
    _clear_license_gate_env(monkeypatch)
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.qmt_xqshare_port import create_qmt_xqshare_fetch_port

    port = create_qmt_xqshare_fetch_port(symbols=("sh.600519",), max_rows=3)
    with pytest.raises(PortError) as exc_info:
        port.fetch_payload(_cn_req("qmt_xqshare", "cn_equity_daily_bar", "sh.600519"))
    assert exc_info.value.status == "USER_AUTH_REQUIRED"


def test_xqshare_port_authorizedFixturePasses(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：qmt_xqshare 授权正例
    测试对象：QmtXqshareMockFetchPort + 三门 env
    目的/目标：远程终端 env proof 后可 mock fetch
    验证点：bars 非空
    失败含义：xqshare 授权正例路径缺失
    """
    from backend.app.datasources.fetch_ports.qmt_xqshare_port import create_qmt_xqshare_fetch_port

    monkeypatch.setenv("XQSHARE_REMOTE_HOST", "127.0.0.1")
    monkeypatch.setenv("XQSHARE_REMOTE_PORT", "8888")
    monkeypatch.setenv("QMT_XQSHARE_AUTHORIZED", "1")
    port = create_qmt_xqshare_fetch_port(symbols=("sh.600519",), max_rows=3)
    body = json.loads(
        port.fetch_payload(_cn_req("qmt_xqshare", "cn_equity_daily_bar", "sh.600519")).content.decode()
    )
    assert body["bars"]


def test_cninfo_route_primaryReadyOnCnAnnouncements() -> None:
    """覆盖范围：cninfo cn_announcements Primary READY
    测试对象：SourceRoutePlanner.plan
    目的/目标：G4 cninfo 专用路由 pytest
    验证点：route_status=READY；selected_source_id=cninfo
    失败含义：cninfo primary 路由未 READY
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
        data_domain="cn_announcements",
        operation="fetch_filings",
        run_id="r3h03-cninfo-route",
        job_id="cninfo-route",
    )
    assert plan.route_status == "READY"
    assert plan.selected_source_id == "cninfo"


def test_ifind_route_disabledWithoutLicense(tmp_path: Path) -> None:
    """覆盖范围：ths_ifind 开关本允许后仍因未授权失败关闭（ADR-018 两层）
    测试对象：SourceRoutePlanner + concept_theme（隔离 overlay 启用后）
    目的/目标：G4 iFinD 安检层 license_gate；先问开关再查授权
    验证点：ths_ifind 候选 enabled=False；skip_reason 含 authorization/license
    失败含义：iFinD 无授权可获得 READY 路由，或未接开关本就误报禁用
    """
    from tests.service_path_support import enable_source_route

    planner = enable_source_route(
        tmp_path,
        source_id="ths_ifind",
        data_domain="concept_theme",
        operation="fetch_concept_theme",
    )
    plan = planner.plan(
        data_domain="concept_theme",
        operation="fetch_concept_theme",
        run_id="r3h03-ifind-route",
        job_id="ifind-route",
    )
    ifind = next(c for c in plan.candidates if c.source_id == "ths_ifind")
    assert ifind.enabled is False
    lowered = (ifind.skip_reason or "").lower()
    assert "authorization" in lowered or "license" in lowered or "user_authorization" in lowered


def test_xqshare_route_disabledWithoutAuthorization() -> None:
    """覆盖范围：qmt_xqshare 未授权路由 DISABLED
    测试对象：SourceRoutePlanner + cn_equity_daily_bar extra candidate
    目的/目标：G4 xqshare 路由层 license_gate 负例
    验证点：xqshare 候选 skip_reason 含 user_authorization_required
    失败含义：xqshare 无授权路由可 READY
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
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        run_id="r3h03-xqshare-route",
        job_id="xqshare-route",
        extra_candidates=[("qmt_xqshare", "Primary")],
    )
    xq = next(c for c in plan.candidates if c.source_id == "qmt_xqshare")
    assert xq.skip_reason in {
        "user_authorization_required",
        "source_disabled_by_default",
        "missing_env:XQSHARE_REMOTE_HOST",
        "missing_env:XQSHARE_REMOTE_PORT",
        "missing_env:QMT_XQSHARE_AUTHORIZED",
    }


# --- 9.8 registry (subset in this module) ---


# CN 十源 capabilities 终态：phase-scripts/check_cn_market_capabilities_registry.py --strict


def test_akshare_registry_validationOnlyPermanent() -> None:
    """覆盖范围：akshare validation_only 永久
    测试对象：SourceRegistry
    目的/目标：§2.8 #6 akshare 不可升格 primary
    验证点：validation_only is True
    失败含义：akshare validation_only 被移除
    """
    from backend.app.datasources.source_registry import SourceRegistry

    registry = SourceRegistry()
    registry.load()
    assert registry.get("akshare").validation_only is True


# --- 9.9 layer_cn ---


def test_layer_cn_baostockReplay_layer5FactualSourceProvenance() -> None:
    """覆盖范围：baostock replay → Layer5 factual_source 溯源
    测试对象：cn_market_bundle_layer5_provenance
    目的/目标：CN replay 具备 Layer5 契约溯源（smoke）
    验证点：provenance 非空；foundation 校验通过
    失败含义：CN 证据无法挂接 Layer5 链
    """
    from backend.app.datasources.normalizers.cn_market import (
        cn_market_bundle_layer5_provenance,
        read_cn_market_evidence_bundle,
    )
    from backend.app.layer5_evidence.models import InstrumentEvidenceRef
    from tests.conftest_layer_smoke import assert_layer5_factual_source_record

    bundle = read_cn_market_evidence_bundle(_BAOSTOCK_REPLAY)
    prov_fields = cn_market_bundle_layer5_provenance(bundle)
    assert_layer5_factual_source_record(
        prov_fields,
        evidence_id="EV-R3H03-BAOSTOCK-SMOKE",
        target_id="CN-600519",
        target_type="cn_equity",
        trade_date=date(2024, 6, 25),
        evidence_summary="Baostock daily bar replay smoke",
        created_by="r3h03_cn_layer_smoke",
        instrument_ref=InstrumentEvidenceRef(
            instrument_id="sh.600519",
            symbol="600519",
            asset_type="equity",
            market_id="CN",
            exchange="SSE",
            currency="CNY",
            is_active=True,
        ),
    )


def test_layer_cn_cninfoReplay_layer2IngestionPreview() -> None:
    """覆盖范围：cninfo replay → Layer2 ingestion 预览
    测试对象：cn_market_bundle_layer2_preview
    目的/目标：CN filings 证据可被 Layer2 摄取链消费
    验证点：preview 含 source_fetch_id、content_hash
    失败含义：Layer2 无法绑定 CN replay 证据
    """
    from backend.app.datasources.normalizers.cn_market import (
        cn_market_bundle_layer2_preview,
        read_cn_market_evidence_bundle,
    )

    bundle = read_cn_market_evidence_bundle(_CNINFO_REPLAY)
    preview = cn_market_bundle_layer2_preview(bundle)
    assert preview["source_fetch_id"] == "cninfo-replay-600519"
    assert preview["content_hash"]


def test_layer_cn_baostockReplay_layer4MarketStructurePreview() -> None:
    """覆盖范围：baostock replay → Layer4 market structure 预览
    测试对象：cn_market_bundle_layer4_preview
    目的/目标：R3H-03 CN Layer4 smoke
    验证点：preview 含 sample_instrument、source_fetch_id
    失败含义：CN 证据无法被 Layer4 结构链消费
    """
    from backend.app.datasources.normalizers.cn_market import (
        cn_market_bundle_layer4_preview,
        read_cn_market_evidence_bundle,
    )

    bundle = read_cn_market_evidence_bundle(_BAOSTOCK_REPLAY)
    preview = cn_market_bundle_layer4_preview(bundle)
    assert preview["source_fetch_id"]
    assert preview["sample_instrument"] == "sh.600519"


def test_layer_cn_baostockReplay_layer3ShockAnchorPreview() -> None:
    """覆盖范围：baostock replay → Layer3 shock-anchor 预览
    测试对象：cn_market_bundle_layer3_preview
    目的/目标：G3 frozen §9.9 Layer3 smoke 绑定
    验证点：anchor_instrument_id、anchor_trade_date、source_fetch_id 非空
    失败含义：CN 证据无法挂接 Layer3 产业链锚点链
    """
    from backend.app.datasources.normalizers.cn_market import (
        cn_market_bundle_layer3_preview,
        read_cn_market_evidence_bundle,
    )

    bundle = read_cn_market_evidence_bundle(_BAOSTOCK_REPLAY)
    preview = cn_market_bundle_layer3_preview(bundle)
    assert preview["anchor_instrument_id"] == "sh.600519"
    assert preview["anchor_trade_date"] == "2024-06-25"
    assert preview["source_fetch_id"]
    assert preview["content_hash"]


def test_layer_cn_calendarGapProfile_failsOnMissingTradingDaysWithAuthority() -> None:
    """覆盖范围：cn_market 完整 G2/G17 calendar_gap profile
    测试对象：check_cn_market_bars + cn_trading_calendar
    目的/目标：用户 Q12 — L2 EasyXT TradingCalendar → QMD 日历 FAIL 缺口
    验证点：缺交易日时 FAIL MISSING_TRADING_DAY（非 weekday proxy WARN）
    失败含义：CN 交易日历仍用 weekday proxy，未闭合 G2/G17
    """
    from backend.app.ops.data_health_profiles.cn_market import check_cn_market_bars

    bars = [
        {"trade_date": "2024-06-24", "open": 1.0, "high": 1.1, "low": 0.9, "close": 1.0, "volume": 100},
        {"trade_date": "2024-06-26", "open": 1.0, "high": 1.1, "low": 0.9, "close": 1.0, "volume": 100},
    ]
    results = check_cn_market_bars(bars, domain="cn_equity_daily_bar", source_id="baostock")
    gap = [r for r in results if r.rule_id == "MISSING_TRADING_DAY"]
    assert gap
    assert gap[0].severity == "FAIL"
    assert gap[0].status == "FAIL"


def test_layer_cn_ohlcvIntegrity_invalidOhlcFails() -> None:
    """覆盖范围：cn_market OHLCV 完整性（L2 data_integrity_checker 语义）
    测试对象：check_cn_market_bars
    目的/目标：EasyXT data_integrity_checker 价量关系迁入 cn_market profile
    验证点：high<low 时 FAIL INVALID_OHLC
    失败含义：CN health profile 缺 OHLCV 完整性检查
    """
    from backend.app.ops.data_health_profiles.cn_market import check_cn_market_bars

    bars = [
        {
            "trade_date": "2024-06-24",
            "open": 10.0,
            "high": 5.0,
            "low": 8.0,
            "close": 9.0,
            "volume": 100,
        },
        {
            "trade_date": "2024-06-25",
            "open": 9.0,
            "high": 11.0,
            "low": 8.5,
            "close": 10.0,
            "volume": 120,
        },
    ]
    results = check_cn_market_bars(bars, domain="cn_equity_daily_bar", source_id="baostock")
    invalid = [r for r in results if r.rule_id == "INVALID_OHLC"]
    assert invalid
    assert invalid[0].status == "FAIL"


def test_cninfo_port_pdfLiveSmoke_cappedWithinLimit() -> None:
    """覆盖范围：cninfo capped PDF live smoke（用户 Q13）
    测试对象：create_cninfo_pdf_live_fetch_port
    目的/目标：Tier-B PDF 路径在 cap 内可产出证据
    验证点：pdf_document.capped=True；byte_length ≤ MAX_PDF_BYTES
    失败含义：cninfo PDF live smoke 未接 capped 路径
    """
    from backend.app.datasources.fetch_ports.cninfo_port import (
        MAX_PDF_BYTES,
        create_cninfo_pdf_live_fetch_port,
    )

    port = create_cninfo_pdf_live_fetch_port(symbols=("sh.600519",), pdf_bytes=2048)
    body = json.loads(
        port.fetch_payload(_cn_req("cninfo", "cn_pdf_reports", "sh.600519")).content.decode()
    )
    pdf_doc = body["pdf_document"]
    assert pdf_doc["capped"] is True
    assert pdf_doc["byte_length"] <= MAX_PDF_BYTES
    assert body["source_id"] == "cninfo"


def test_mootdx_port_extendsTdxPytdxCaps() -> None:
    """覆盖范围：mootdx 扩展 tdx_pytdx_port 共享 cap（非 L3 重写）
    测试对象：mootdx_port + tdx_pytdx_port
    目的/目标：R3FR-03 MIT 模式共享 SECURITY_LIST_MAX_ROWS / MINUTE_BARS_ENABLED
    验证点：mootdx 复用 tdx cap 常量；分钟线拒绝
    失败含义：mootdx 与 tdx_pytdx 生命周期未对齐
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports import mootdx_port, tdx_pytdx_port
    from backend.app.datasources.fetch_ports.mootdx_port import create_mootdx_fetch_port

    assert mootdx_port.SECURITY_LIST_MAX_ROWS == tdx_pytdx_port.SECURITY_LIST_MAX_ROWS
    assert mootdx_port.MINUTE_BARS_ENABLED is tdx_pytdx_port.MINUTE_BARS_ENABLED
    port = create_mootdx_fetch_port(symbols=("sh.600519",), max_rows=3)
    with pytest.raises(PortError, match="minute"):
        port.fetch_payload(_cn_req("mootdx", "cn_equity_minute_bar", "sh.600519"))
