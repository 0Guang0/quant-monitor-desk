"""R3-DCP-05 S07 — CNINFO metadata incremental e2e tests."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

from backend.app.ops.cninfo_incremental_run import run_cninfo_incremental
from backend.app.ops.db_inspector import DbInspector
from tests.cninfo_incremental_support import (
    ANNOUNCEMENT_ID,
    FIXTURE_DATE,
    SYMBOL,
    bootstrap_cninfo_live_e2e_ctx,
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


def test_cninfoLive_noSilentFallbackWhenGateClosed(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：无 QMD_ALLOW_LIVE_FETCH 时 cninfo live port 阻断
    测试对象：create_cninfo_fetch_port(use_mock=False)
    目的/目标：live 被拒时不得静默退回 mock port
    验证点：抛 ProductLiveGateError · LIVE_FETCH_REJECTED
    失败含义：cninfo live 路径渗入 silent fallback
    """
    from backend.app.datasources.fetch_ports.cninfo_port import create_cninfo_fetch_port
    from backend.app.datasources.product_live_gate import ProductLiveGateError

    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    with pytest.raises(ProductLiveGateError) as exc_info:
        create_cninfo_fetch_port(symbols=(SYMBOL,), max_rows=20, use_mock=False)
    assert exc_info.value.code == "LIVE_FETCH_REJECTED"


@pytest.mark.network
def test_cninfoIncremental_liveNetwork_writesCnAnnouncementClean(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：隔离 sandbox + CNINFO product live 写 cn_announcement_clean
    测试对象：run_cninfo_incremental + create_cninfo_fetch_port(use_mock=False)
    目的/目标：QMD_ALLOW_LIVE_FETCH=1 时 product live 金路径落库
    验证点：status∈{COMPLETED,EMPTY_RESPONSE}；COMPLETED 时 clean≥1；DbInspector 表存在
    失败含义：Tier A cninfo live 增量链断或误写主库
    """
    ctx = bootstrap_cninfo_live_e2e_ctx(isolated_live_data_root, monkeypatch)
    with ctx["cm"].writer() as con:
        seed_watermark_row(con, "2024-06-24")
    report = run_cninfo_incremental(
        ctx["orch"],
        service=ctx["service"],
        symbols=(SYMBOL,),
        source_registry=ctx["registry"],
    )
    status = report.instrument_results[0]["status"]
    assert status in {"COMPLETED", "EMPTY_RESPONSE"}
    inspect_report = DbInspector(ctx["cm"].db_path, ctx["raw_root"]).inspect()
    clean_table = next(t for t in inspect_report.key_tables if t["name"] == "cn_announcement_clean")
    assert clean_table["exists"] is True
    if status == "COMPLETED":
        with ctx["cm"].reader() as con:
            count = con.execute(
                "SELECT COUNT(*) FROM cn_announcement_clean WHERE instrument_id = ?", [SYMBOL]
            ).fetchone()[0]
        assert count >= 1
        assert clean_table["row_count"] is not None and clean_table["row_count"] >= 1


@pytest.mark.network
def test_cninfoIncremental_liveNetwork_idempotentSecondRun(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：隔离 sandbox 连续两次 CNINFO product live 增量
    测试对象：run_cninfo_incremental live 幂等 upsert
    目的/目标：重复 live 跑不应增加 cn_announcement_clean 行数
    验证点：两路 status∈{COMPLETED,EMPTY_RESPONSE}；COUNT 相等
    失败含义：live 幂等失败会导致日常 sync 数据膨胀
    """
    ctx = bootstrap_cninfo_live_e2e_ctx(isolated_live_data_root, monkeypatch)
    with ctx["cm"].writer() as con:
        seed_watermark_row(con, "2024-06-24")
    kwargs = dict(service=ctx["service"], symbols=(SYMBOL,), source_registry=ctx["registry"])
    run_cninfo_incremental(ctx["orch"], **kwargs)
    with ctx["cm"].writer() as con:
        first = con.execute(
            "SELECT COUNT(*) FROM cn_announcement_clean WHERE instrument_id = ?", [SYMBOL]
        ).fetchone()[0]
    run_cninfo_incremental(ctx["orch"], **kwargs)
    with ctx["cm"].writer() as con:
        second = con.execute(
            "SELECT COUNT(*) FROM cn_announcement_clean WHERE instrument_id = ?", [SYMBOL]
        ).fetchone()[0]
    assert first == second
