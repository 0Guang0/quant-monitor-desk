"""R3-DCP-05 S07 — CNINFO metadata incremental e2e tests."""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest

from backend.app.ops.cninfo_incremental_run import run_cninfo_incremental
from tests.cninfo_incremental_support import (
    ANNOUNCEMENT_ID,
    FIXTURE_DATE,
    SYMBOL,
    cninfo_incremental_e2e_ctx,
    seed_watermark_row,
)


def test_cninfoIncremental_e2e_writesCnAnnouncementClean(
    cninfo_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：replay fixture 经服务路径增量写入 cn_announcement_clean
    测试对象：run_cninfo_incremental + metadata watermark
    目的/目标：watermark 窗内公告应 upsert 到 clean 表
    验证点：COMPLETED；clean 含 fixture announcement_id
    失败含义：cninfo 增量链断则 metadata clean 无法落库
    """
    ctx = cninfo_incremental_e2e_ctx
    with ctx["cm"].writer() as con:
        seed_watermark_row(con, "2024-06-24")
    report = run_cninfo_incremental(
        ctx["orch"],
        service=ctx["service"],
        symbols=(SYMBOL,),
        source_registry=ctx["registry"],
    )
    assert report.instrument_results[0]["status"] == "COMPLETED"
    with ctx["cm"].reader() as con:
        row = con.execute(
            "SELECT announcement_id FROM cn_announcement_clean WHERE announcement_id = ?",
            [ANNOUNCEMENT_ID],
        ).fetchone()
    assert row is not None


def test_cninfoIncremental_repeatRun_noRowGrowth(
    cninfo_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：连续两次相同增量 sync
    测试对象：upsert_by_pk 幂等
    目的/目标：重复跑同一窗不应增加 cn_announcement_clean 行数
    验证点：两次 COMPLETED；行数保持 2（seed + fixture）
    失败含义：幂等失败会导致日常 sync 数据膨胀
    """
    ctx = cninfo_incremental_e2e_ctx
    with ctx["cm"].writer() as con:
        seed_watermark_row(con, "2024-06-24")
    run_cninfo_incremental(ctx["orch"], service=ctx["service"], source_registry=ctx["registry"])
    with ctx["cm"].writer() as con:
        first = con.execute(
            "SELECT COUNT(*) FROM cn_announcement_clean WHERE instrument_id = ?", [SYMBOL]
        ).fetchone()[0]
    run_cninfo_incremental(ctx["orch"], service=ctx["service"], source_registry=ctx["registry"])
    with ctx["cm"].writer() as con:
        second = con.execute(
            "SELECT COUNT(*) FROM cn_announcement_clean WHERE instrument_id = ?", [SYMBOL]
        ).fetchone()[0]
    assert first == second
    assert first >= 2


def test_cninfoIncremental_emptyResponse_whenWatermarkCurrent(
    cninfo_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：水位已最新时 replay 返回 EMPTY_RESPONSE
    测试对象：metadata staging adapter + run_cninfo_incremental
    目的/目标：since 之后无新公告时不写假行
    验证点：status==EMPTY_RESPONSE；行数不变
    失败含义：水位追上仍写入，增量语义错误
    """
    ctx = cninfo_incremental_e2e_ctx
    with ctx["cm"].writer() as con:
        seed_watermark_row(con, FIXTURE_DATE.isoformat())
        before = con.execute("SELECT COUNT(*) FROM cn_announcement_clean").fetchone()[0]
    report = run_cninfo_incremental(
        ctx["orch"], service=ctx["service"], source_registry=ctx["registry"]
    )
    assert report.instrument_results[0]["status"] == "EMPTY_RESPONSE"
    with ctx["cm"].reader() as con:
        after = con.execute("SELECT COUNT(*) FROM cn_announcement_clean").fetchone()[0]
    assert before == after
