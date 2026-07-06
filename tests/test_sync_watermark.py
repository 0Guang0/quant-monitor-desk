"""M-G1-03 P1-05 — unified sync watermark entry."""

from __future__ import annotations

from datetime import date

from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.ops import fred_incremental_watermark as ops_wm
from backend.app.sync import watermark as sync_wm
from tests.fred_macro_incremental_support import insert_axis_observation
from tests.incremental_baostock_support import SYMBOL, seed_watermark_row


def test_syncWatermark_readWatermark_singleEntryMacroAndBar(tmp_path) -> None:
    """覆盖范围：sync watermark 单一读入口
    测试对象：backend.app.sync.watermark.read_watermark
    目的/目标：macro_series 与 bar domain 共用 read_watermark(domain, key)
    验证点：ops watermark 改为 re-export，无双实现
    失败含义：增量窗口不一致导致重复/漏抓
    """
    cm = ConnectionManager(db_path=tmp_path / "wm.duckdb")
    with cm.writer() as con:
        apply_migrations(con)
        insert_axis_observation(
            con,
            observation_id="obs-dgs10",
            indicator_id="DGS10",
            obs_date=date(2026, 6, 10),
        )
        seed_watermark_row(con, "2026-06-15")

    with cm.writer() as con:
        macro_wm = sync_wm.read_watermark(con, "macro_series", "DGS10")
        bar_wm = sync_wm.read_watermark(con, "cn_equity_daily_bar", SYMBOL)

    assert macro_wm == date(2026, 6, 10)
    assert bar_wm == date(2026, 6, 15)
    assert ops_wm.read_observation_date_watermark is sync_wm.read_observation_date_watermark
    assert ops_wm.compute_since_date is sync_wm.compute_since_date
    assert ops_wm.read_since_dates_for_series is sync_wm.read_since_dates_for_series
