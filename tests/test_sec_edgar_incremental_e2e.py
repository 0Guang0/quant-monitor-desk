"""R3-DCP-05 S09 — SEC EDGAR incremental e2e tests."""

from __future__ import annotations

from typing import Any

from backend.app.ops.sec_edgar_incremental_run import run_sec_edgar_incremental
from tests.sec_edgar_incremental_support import (
    ACCESSION,
    CIK,
    FILING_DATE,
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
