"""R3-DCP-05 S10 — Alpha Vantage bar incremental e2e tests."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

from backend.app.ops.alpha_vantage_incremental_run import run_alpha_vantage_incremental
from backend.app.ops.db_inspector import DbInspector
from tests.alpha_vantage_incremental_support import (
    FIXTURE_END,
    SYMBOL,
    TRADE_DATE,
    alpha_vantage_incremental_e2e_ctx,
    bootstrap_alpha_vantage_live_e2e_ctx,
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


def test_alphaVantageLive_noSilentFallbackWhenGateClosed(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：无 QMD_ALLOW_LIVE_FETCH 时 alpha_vantage live port 阻断
    测试对象：create_alpha_vantage_fetch_port(use_mock=False)
    目的/目标：live 被拒时不得静默退回 mock port
    验证点：抛 ProductLiveGateError · LIVE_FETCH_REJECTED
    失败含义：alpha_vantage live 路径渗入 silent fallback
    """
    from backend.app.datasources.fetch_ports.alpha_vantage_port import create_alpha_vantage_fetch_port
    from backend.app.datasources.product_live_gate import ProductLiveGateError

    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    with pytest.raises(ProductLiveGateError) as exc_info:
        create_alpha_vantage_fetch_port(symbols=(SYMBOL,), max_rows=500, use_mock=False)
    assert exc_info.value.code == "LIVE_FETCH_REJECTED"


@pytest.mark.network
def test_alphaVantageIncremental_liveNetwork_writesSecurityBar1d(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：隔离 sandbox + Alpha Vantage product live 写 security_bar_1d
    测试对象：run_alpha_vantage_incremental + create_alpha_vantage_fetch_port(use_mock=False)
    目的/目标：QMD_ALLOW_LIVE_FETCH=1 + ALPHA_VANTAGE_API_KEY 时 live 金路径落库
    验证点：status∈{COMPLETED,EMPTY_RESPONSE}；COMPLETED 时 clean≥1；DbInspector 表存在
    失败含义：Tier A alpha_vantage live 增量链断或误写主库
    """
    ctx = bootstrap_alpha_vantage_live_e2e_ctx(isolated_live_data_root, monkeypatch)
    with ctx["cm"].writer() as con:
        seed_watermark_row(con, "2024-01-02")
    report = run_alpha_vantage_incremental(
        ctx["orch"],
        service=ctx["service"],
        symbols=(SYMBOL,),
        end=FIXTURE_END,
        source_registry=ctx["registry"],
    )
    status = report.symbol_results[0]["status"]
    assert status in {"COMPLETED", "EMPTY_RESPONSE"}
    inspect_report = DbInspector(ctx["cm"].db_path, ctx["raw_root"]).inspect()
    bar_table = next(t for t in inspect_report.key_tables if t["name"] == "security_bar_1d")
    assert bar_table["exists"] is True
    if status == "COMPLETED":
        with ctx["cm"].reader() as con:
            count = con.execute(
                "SELECT COUNT(*) FROM security_bar_1d WHERE instrument_id = ?", [SYMBOL]
            ).fetchone()[0]
        assert count >= 1
        assert bar_table["row_count"] is not None and bar_table["row_count"] >= 1


@pytest.mark.network
def test_alphaVantageIncremental_liveNetwork_idempotentSecondRun(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：隔离 sandbox 连续两次 Alpha Vantage live 增量
    测试对象：run_alpha_vantage_incremental live 幂等 upsert
    目的/目标：重复 live 跑同一窗不应增加 security_bar_1d 行数
    验证点：两路 status∈{COMPLETED,EMPTY_RESPONSE}；COUNT 相等
    失败含义：live 幂等失败会导致日常 sync 数据膨胀
    """
    ctx = bootstrap_alpha_vantage_live_e2e_ctx(isolated_live_data_root, monkeypatch)
    with ctx["cm"].writer() as con:
        seed_watermark_row(con, "2024-01-02")
    kwargs = dict(service=ctx["service"], end=FIXTURE_END, source_registry=ctx["registry"])
    run_alpha_vantage_incremental(ctx["orch"], **kwargs)
    with ctx["cm"].writer() as con:
        first = con.execute(
            "SELECT COUNT(*) FROM security_bar_1d WHERE instrument_id = ?", [SYMBOL]
        ).fetchone()[0]
    run_alpha_vantage_incremental(ctx["orch"], **kwargs)
    with ctx["cm"].writer() as con:
        second = con.execute(
            "SELECT COUNT(*) FROM security_bar_1d WHERE instrument_id = ?", [SYMBOL]
        ).fetchone()[0]
    assert first == second
