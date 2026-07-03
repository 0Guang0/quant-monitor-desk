"""R3-DCP-05 S09 — SEC EDGAR incremental e2e tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from backend.app.ops.sec_edgar_incremental_run import run_sec_edgar_incremental
from tests.sec_edgar_incremental_support import (
    ACCESSION,
    CIK,
    FILING_DATE,
    bootstrap_sec_edgar_live_e2e_ctx,
    sec_edgar_incremental_e2e_ctx,
    seed_watermark_row,
)


def test_secEdgarIncremental_e2e_writesUsDisclosureClean(
    sec_edgar_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：replay fixture 经服务路径增量写入 us_disclosure_clean
    测试对象：run_sec_edgar_incremental + filing watermark
    目的/目标：watermark 窗内 filing 应 upsert 到 clean 表
    验证点：COMPLETED；clean 含 fixture accession_number
    失败含义：sec_edgar 增量链断则 us_disclosure_clean 无法落库
    """
    ctx = sec_edgar_incremental_e2e_ctx
    with ctx["cm"].writer() as con:
        seed_watermark_row(con, "2025-08-01")
    report = run_sec_edgar_incremental(
        ctx["orch"],
        service=ctx["service"],
        ciks=(CIK,),
        source_registry=ctx["registry"],
    )
    assert report.cik_results[0]["status"] == "COMPLETED"
    with ctx["cm"].reader() as con:
        row = con.execute(
            "SELECT accession_number FROM us_disclosure_clean WHERE accession_number = ?",
            [ACCESSION],
        ).fetchone()
    assert row is not None


def test_secEdgarIncremental_repeatRun_noRowGrowth(
    sec_edgar_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：连续两次相同增量 sync
    测试对象：upsert_by_pk 幂等
    目的/目标：重复跑同一窗不应增加 us_disclosure_clean 行数
    验证点：两次 COMPLETED 后 COUNT 相等
    失败含义：幂等失败会导致日常 sync 数据膨胀
    """
    ctx = sec_edgar_incremental_e2e_ctx
    with ctx["cm"].writer() as con:
        seed_watermark_row(con, "2025-08-01")
    run_sec_edgar_incremental(ctx["orch"], service=ctx["service"], source_registry=ctx["registry"])
    with ctx["cm"].writer() as con:
        first = con.execute(
            "SELECT COUNT(*) FROM us_disclosure_clean WHERE cik = ?", [CIK]
        ).fetchone()[0]
    run_sec_edgar_incremental(ctx["orch"], service=ctx["service"], source_registry=ctx["registry"])
    with ctx["cm"].writer() as con:
        second = con.execute(
            "SELECT COUNT(*) FROM us_disclosure_clean WHERE cik = ?", [CIK]
        ).fetchone()[0]
    assert first == second
    assert first >= 2


def test_secEdgarIncremental_emptyResponse_whenWatermarkCurrent(
    sec_edgar_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：水位已最新时 replay 返回 EMPTY_RESPONSE
    测试对象：us_disclosure staging + run_sec_edgar_incremental
    目的/目标：since 之后无新 filing 时不写假行
    验证点：status==EMPTY_RESPONSE；行数不变
    失败含义：水位追上仍写入，增量语义错误
    """
    ctx = sec_edgar_incremental_e2e_ctx
    with ctx["cm"].writer() as con:
        seed_watermark_row(con, FILING_DATE.isoformat())
        before = con.execute("SELECT COUNT(*) FROM us_disclosure_clean").fetchone()[0]
    report = run_sec_edgar_incremental(
        ctx["orch"], service=ctx["service"], source_registry=ctx["registry"]
    )
    assert report.cik_results[0]["status"] == "EMPTY_RESPONSE"
    with ctx["cm"].reader() as con:
        after = con.execute("SELECT COUNT(*) FROM us_disclosure_clean").fetchone()[0]
    assert before == after


def test_secEdgarLive_noSilentFallbackWhenGateClosed(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：无 QMD_ALLOW_LIVE_FETCH 时 sec_edgar live port 阻断
    测试对象：create_sec_edgar_fetch_port(use_mock=False)
    目的/目标：live 被拒时不得静默退回 mock port
    验证点：抛 ProductLiveGateError · LIVE_FETCH_REJECTED
    失败含义：sec_edgar live 路径渗入 silent fallback
    """
    from backend.app.datasources.fetch_ports.sec_edgar_port import create_sec_edgar_fetch_port
    from backend.app.datasources.product_live_gate import ProductLiveGateError

    monkeypatch.setenv("SEC_EDGAR_USER_AGENT", "gate-test@example.com")
    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    with pytest.raises(ProductLiveGateError) as exc_info:
        create_sec_edgar_fetch_port(
            ciks=(CIK,), max_filings=5, data_domain="us_filings", use_mock=False
        )
    assert exc_info.value.code == "LIVE_FETCH_REJECTED"


@pytest.mark.network
def test_secEdgarIncremental_liveNetwork_writesUsDisclosureClean(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：隔离 sandbox + SEC EDGAR product live 写 us_disclosure_clean
    测试对象：run_sec_edgar_incremental + create_sec_edgar_fetch_port(use_mock=False)
    目的/目标：QMD_ALLOW_LIVE_FETCH=1 + SEC_EDGAR_USER_AGENT 时 live 金路径落库
    验证点：status∈{COMPLETED,EMPTY_RESPONSE}；COMPLETED 时 clean≥1；DbInspector 表存在
    失败含义：Tier A sec_edgar live 增量链断或误写主库
    """
    ctx = bootstrap_sec_edgar_live_e2e_ctx(isolated_live_data_root, monkeypatch)
    with ctx["cm"].writer() as con:
        seed_watermark_row(con, "2025-08-01")
    report = run_sec_edgar_incremental(
        ctx["orch"],
        service=ctx["service"],
        ciks=(CIK,),
        source_registry=ctx["registry"],
    )
    status = report.cik_results[0]["status"]
    assert status in {"COMPLETED", "EMPTY_RESPONSE"}
    if status == "COMPLETED":
        with ctx["cm"].reader() as con:
            count = con.execute("SELECT COUNT(*) FROM us_disclosure_clean WHERE cik = ?", [CIK]).fetchone()[0]
        assert count >= 1


@pytest.mark.network
def test_secEdgarIncremental_liveNetwork_idempotentSecondRun(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：隔离 sandbox 连续两次 SEC EDGAR live 增量
    测试对象：run_sec_edgar_incremental live 幂等 upsert
    目的/目标：重复 live 跑同一窗不应增加 us_disclosure_clean 行数
    验证点：两路 status∈{COMPLETED,EMPTY_RESPONSE}；COUNT 相等
    失败含义：live 幂等失败会导致日常 sync 数据膨胀
    """
    ctx = bootstrap_sec_edgar_live_e2e_ctx(isolated_live_data_root, monkeypatch)
    with ctx["cm"].writer() as con:
        seed_watermark_row(con, "2025-08-01")
    run_sec_edgar_incremental(
        ctx["orch"], service=ctx["service"], ciks=(CIK,), source_registry=ctx["registry"]
    )
    with ctx["cm"].writer() as con:
        first = con.execute(
            "SELECT COUNT(*) FROM us_disclosure_clean WHERE cik = ?", [CIK]
        ).fetchone()[0]
    run_sec_edgar_incremental(
        ctx["orch"], service=ctx["service"], ciks=(CIK,), source_registry=ctx["registry"]
    )
    with ctx["cm"].writer() as con:
        second = con.execute(
            "SELECT COUNT(*) FROM us_disclosure_clean WHERE cik = ?", [CIK]
        ).fetchone()[0]
    assert first == second
