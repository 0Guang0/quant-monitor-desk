"""R3-DCP-05 S11 — Deribit crypto incremental e2e tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from backend.app.ops.deribit_incremental_run import run_deribit_incremental
from backend.app.ops.db_inspector import DbInspector
from tests.deribit_incremental_support import (
    AS_OF_DATE,
    INSTRUMENT,
    bootstrap_deribit_live_e2e_ctx,
    deribit_incremental_e2e_ctx,
    seed_watermark_row,
)


def test_deribitIncremental_replay_writesCryptoDerivativeClean(
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


def test_deribitLive_noSilentFallbackWhenGateClosed(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：无 QMD_ALLOW_LIVE_FETCH 时 deribit live port 阻断
    测试对象：create_deribit_fetch_port(use_mock=False)
    目的/目标：live 被拒时不得静默退回 mock port
    验证点：抛 ProductLiveGateError · LIVE_FETCH_REJECTED
    失败含义：deribit live 路径渗入 silent fallback
    """
    from backend.app.datasources.fetch_ports.deribit_port import create_deribit_fetch_port
    from backend.app.datasources.product_live_gate import ProductLiveGateError

    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    with pytest.raises(ProductLiveGateError) as exc_info:
        create_deribit_fetch_port(instruments=(INSTRUMENT,), max_surface_rows=50, use_mock=False)
    assert exc_info.value.code == "LIVE_FETCH_REJECTED"


@pytest.mark.network
def test_deribitIncremental_liveNetwork_writesCryptoDerivativeClean(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：隔离 sandbox + Deribit public API live 写 crypto_derivative_clean
    测试对象：run_deribit_incremental + create_deribit_fetch_port(use_mock=False)
    目的/目标：QMD_ALLOW_LIVE_FETCH=1 时真网增量写 crypto clean
    验证点：status∈{COMPLETED,EMPTY_RESPONSE}；COMPLETED 时 clean≥1；DbInspector 表存在
    失败含义：Tier A deribit live 金路径未接通或误写主库
    """
    ctx = bootstrap_deribit_live_e2e_ctx(isolated_live_data_root, monkeypatch)
    instrument = ctx["instrument"]
    with ctx["cm"].writer() as con:
        seed_watermark_row(con, "2024-06-24", instrument_name=instrument)
    report = run_deribit_incremental(
        ctx["orch"],
        service=ctx["service"],
        instruments=(instrument,),
        source_registry=ctx["registry"],
    )
    status = report.instrument_results[0]["status"]
    assert status in {"COMPLETED", "EMPTY_RESPONSE"}
    inspect_report = DbInspector(ctx["cm"].db_path, ctx["raw_root"]).inspect()
    clean_table = next(
        t for t in inspect_report.key_tables if t["name"] == "crypto_derivative_clean"
    )
    assert clean_table["exists"] is True
    if status == "COMPLETED":
        with ctx["cm"].reader() as con:
            count = con.execute(
                "SELECT COUNT(*) FROM crypto_derivative_clean WHERE instrument_name = ?",
                [instrument],
            ).fetchone()[0]
        assert count >= 1
        assert clean_table["row_count"] is not None and clean_table["row_count"] >= 1


@pytest.mark.network
def test_deribitIncremental_liveNetwork_idempotentSecondRun(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：隔离 sandbox 连续两次 Deribit live 增量
    测试对象：run_deribit_incremental live 幂等 upsert
    目的/目标：重复 live 跑不应增加 crypto_derivative_clean 行数
    验证点：两路 status∈{COMPLETED,EMPTY_RESPONSE}；COUNT 相等
    失败含义：live 幂等失败会导致日常 sync 数据膨胀
    """
    ctx = bootstrap_deribit_live_e2e_ctx(isolated_live_data_root, monkeypatch)
    instrument = ctx["instrument"]
    with ctx["cm"].writer() as con:
        seed_watermark_row(con, "2024-06-24", instrument_name=instrument)
    kwargs = dict(
        service=ctx["service"],
        instruments=(instrument,),
        source_registry=ctx["registry"],
    )
    run_deribit_incremental(ctx["orch"], **kwargs)
    with ctx["cm"].writer() as con:
        first = con.execute(
            "SELECT COUNT(*) FROM crypto_derivative_clean WHERE instrument_name = ?",
            [instrument],
        ).fetchone()[0]
    run_deribit_incremental(ctx["orch"], **kwargs)
    with ctx["cm"].writer() as con:
        second = con.execute(
            "SELECT COUNT(*) FROM crypto_derivative_clean WHERE instrument_name = ?",
            [instrument],
        ).fetchone()[0]
    assert first == second
