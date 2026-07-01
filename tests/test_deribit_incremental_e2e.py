"""R3-DCP-05 S11 — Deribit crypto incremental e2e tests."""

from __future__ import annotations

from typing import Any

from backend.app.ops.deribit_incremental_run import run_deribit_incremental
from tests.deribit_incremental_support import (
    AS_OF_DATE,
    INSTRUMENT,
    deribit_incremental_e2e_ctx,
    seed_watermark_row,
)


def test_deribitIncremental_e2e_writesCryptoDerivativeClean(
    deribit_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：replay fixture 经服务路径增量写入 crypto_derivative_clean
    测试对象：run_deribit_incremental + as_of watermark
    目的/目标：watermark 窗内 surface 应 upsert 到 clean 表
    验证点：COMPLETED；clean 含 fixture instrument
    失败含义：deribit 增量链断则 crypto_derivative_clean 无法落库
    """
    ctx = deribit_incremental_e2e_ctx
    with ctx["cm"].writer() as con:
        seed_watermark_row(con, "2024-06-24")
    report = run_deribit_incremental(
        ctx["orch"],
        service=ctx["service"],
        instruments=(INSTRUMENT,),
        source_registry=ctx["registry"],
    )
    assert report.instrument_results[0]["status"] == "COMPLETED"
    with ctx["cm"].reader() as con:
        row = con.execute(
            """
            SELECT mark_iv FROM crypto_derivative_clean
            WHERE instrument_name = ? AND data_domain = 'crypto_options_surface'
              AND CAST(as_of_timestamp AS DATE) = '2024-06-25'
            """,
            [INSTRUMENT],
        ).fetchone()
    assert row is not None
    assert float(row[0]) == 0.52


def test_deribitIncremental_repeatRun_noRowGrowth(
    deribit_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：连续两次相同增量 sync
    测试对象：upsert_by_pk 幂等
    目的/目标：重复跑同一窗不应增加 crypto_derivative_clean 行数
    验证点：两次 COMPLETED 后 COUNT 相等
    失败含义：幂等失败会导致日常 sync 数据膨胀
    """
    ctx = deribit_incremental_e2e_ctx
    with ctx["cm"].writer() as con:
        seed_watermark_row(con, "2024-06-24")
    run_deribit_incremental(ctx["orch"], service=ctx["service"], source_registry=ctx["registry"])
    with ctx["cm"].writer() as con:
        first = con.execute(
            "SELECT COUNT(*) FROM crypto_derivative_clean WHERE instrument_name = ?",
            [INSTRUMENT],
        ).fetchone()[0]
    run_deribit_incremental(ctx["orch"], service=ctx["service"], source_registry=ctx["registry"])
    with ctx["cm"].writer() as con:
        second = con.execute(
            "SELECT COUNT(*) FROM crypto_derivative_clean WHERE instrument_name = ?",
            [INSTRUMENT],
        ).fetchone()[0]
    assert first == second
    assert first >= 1


def test_deribitIncremental_emptyResponse_whenWatermarkCurrent(
    deribit_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：水位已最新时 replay 返回 EMPTY_RESPONSE
    测试对象：crypto staging + run_deribit_incremental
    目的/目标：since 之后无新 surface 时不写假行
    验证点：status==EMPTY_RESPONSE；行数不变
    失败含义：水位追上仍写入，增量语义错误
    """
    ctx = deribit_incremental_e2e_ctx
    with ctx["cm"].writer() as con:
        seed_watermark_row(con, AS_OF_DATE.isoformat())
        before = con.execute(
            "SELECT COUNT(*) FROM crypto_derivative_clean WHERE instrument_name = ?",
            [INSTRUMENT],
        ).fetchone()[0]
    report = run_deribit_incremental(
        ctx["orch"], service=ctx["service"], source_registry=ctx["registry"]
    )
    assert report.instrument_results[0]["status"] == "EMPTY_RESPONSE"
    with ctx["cm"].reader() as con:
        after = con.execute(
            "SELECT COUNT(*) FROM crypto_derivative_clean WHERE instrument_name = ?",
            [INSTRUMENT],
        ).fetchone()[0]
    assert before == after
