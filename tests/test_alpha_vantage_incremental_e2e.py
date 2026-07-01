"""R3-DCP-05 S10 — Alpha Vantage bar incremental e2e tests."""

from __future__ import annotations

from datetime import date
from typing import Any

from backend.app.ops.alpha_vantage_incremental_run import run_alpha_vantage_incremental
from tests.alpha_vantage_incremental_support import (
    FIXTURE_END,
    SYMBOL,
    TRADE_DATE,
    alpha_vantage_incremental_e2e_ctx,
    seed_watermark_row,
)


def test_alphaVantageIncremental_e2e_writesSecurityBar1d(
    alpha_vantage_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：replay fixture 经服务路径增量写入 security_bar_1d
    测试对象：run_alpha_vantage_incremental + bar watermark
    目的/目标：watermark 窗内 bar 应 upsert 到 clean 表
    验证点：COMPLETED；clean 含 fixture trade_date
    失败含义：alpha_vantage 增量链断则 US bar clean 无法落库
    """
    ctx = alpha_vantage_incremental_e2e_ctx
    with ctx["cm"].writer() as con:
        seed_watermark_row(con, "2024-01-02")
    report = run_alpha_vantage_incremental(
        ctx["orch"],
        service=ctx["service"],
        symbols=(SYMBOL,),
        end=FIXTURE_END,
        source_registry=ctx["registry"],
    )
    assert report.symbol_results[0]["status"] == "COMPLETED"
    with ctx["cm"].reader() as con:
        row = con.execute(
            """
            SELECT close FROM security_bar_1d
            WHERE instrument_id = ? AND trade_date = ?
            """,
            [SYMBOL, TRADE_DATE],
        ).fetchone()
    assert row is not None
    assert float(row[0]) == 186.2


def test_alphaVantageIncremental_repeatRun_noRowGrowth(
    alpha_vantage_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：连续两次相同增量 sync
    测试对象：upsert_by_pk 幂等
    目的/目标：重复跑同一窗不应增加 security_bar_1d 行数
    验证点：两次 COMPLETED 后 COUNT 相等
    失败含义：幂等失败会导致日常 sync 数据膨胀
    """
    ctx = alpha_vantage_incremental_e2e_ctx
    with ctx["cm"].writer() as con:
        seed_watermark_row(con, "2024-01-02")
    run_alpha_vantage_incremental(
        ctx["orch"],
        service=ctx["service"],
        end=FIXTURE_END,
        source_registry=ctx["registry"],
    )
    with ctx["cm"].writer() as con:
        first = con.execute(
            "SELECT COUNT(*) FROM security_bar_1d WHERE instrument_id = ?", [SYMBOL]
        ).fetchone()[0]
    run_alpha_vantage_incremental(
        ctx["orch"],
        service=ctx["service"],
        end=FIXTURE_END,
        source_registry=ctx["registry"],
    )
    with ctx["cm"].writer() as con:
        second = con.execute(
            "SELECT COUNT(*) FROM security_bar_1d WHERE instrument_id = ?", [SYMBOL]
        ).fetchone()[0]
    assert first == second
    assert first >= 2


def test_alphaVantageIncremental_emptyResponse_whenWatermarkCurrent(
    alpha_vantage_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：水位已追平 end 时 EMPTY_RESPONSE
    测试对象：bar staging + run_alpha_vantage_incremental
    目的/目标：窗内无新 bar 时不写假行
    验证点：status==EMPTY_RESPONSE；行数不变
    失败含义：追平仍写入，增量语义错误
    """
    ctx = alpha_vantage_incremental_e2e_ctx
    with ctx["cm"].writer() as con:
        seed_watermark_row(con, TRADE_DATE)
        before = con.execute(
            "SELECT COUNT(*) FROM security_bar_1d WHERE instrument_id = ?", [SYMBOL]
        ).fetchone()[0]
    report = run_alpha_vantage_incremental(
        ctx["orch"],
        service=ctx["service"],
        end=date(2024, 1, 3),
        source_registry=ctx["registry"],
    )
    assert report.symbol_results[0]["status"] == "EMPTY_RESPONSE"
    with ctx["cm"].reader() as con:
        after = con.execute(
            "SELECT COUNT(*) FROM security_bar_1d WHERE instrument_id = ?", [SYMBOL]
        ).fetchone()[0]
    assert before == after
