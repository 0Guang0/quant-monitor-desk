"""R3-DCP-05 S10 — Alpha Vantage bar incremental watermark tests."""

from __future__ import annotations

from datetime import date

from backend.app.sync.watermark import compute_incremental_window, read_bar_trade_date_watermark
from tests.alpha_vantage_incremental_support import SYMBOL, bootstrap_db, seed_watermark_row


def test_alphaVantageWatermark_emptyTable_returnsLookbackWindow(tmp_path) -> None:
    """覆盖范围：空 security_bar_1d 冷启动窗
    测试对象：read_bar_trade_date_watermark + compute_incremental_window
    目的/目标：空表应无 watermark，窗起点为 end 往前 30 日历日
    验证点：watermark is None；date_end=给定 end
    失败含义：空表误读水位会导致 bar 增量窗错误
    """
    cm = bootstrap_db(tmp_path)
    with cm.reader() as con:
        wm = read_bar_trade_date_watermark(con, instrument_id=SYMBOL)
        window = compute_incremental_window(wm, end=date(2024, 1, 3), empty_table_lookback_days=30)
    assert wm is None
    assert window.date_end == date(2024, 1, 3)


def test_alphaVantageWatermark_withData_returnsMaxPlusOne(tmp_path) -> None:
    """覆盖范围：有 bar 数据的 watermark 窗
    测试对象：read_bar_trade_date_watermark + compute_incremental_window
    目的/目标：有数据时 date_start = max(trade_date) + 1
    验证点：seed 2024-01-02 → date_start=2024-01-03
    失败含义：未 +1 会重复拉已落库 bar
    """
    cm = bootstrap_db(tmp_path)
    with cm.writer() as con:
        seed_watermark_row(con, "2024-01-02")
        wm = read_bar_trade_date_watermark(con, instrument_id=SYMBOL)
        window = compute_incremental_window(wm, end=date(2024, 1, 3))
    assert wm == date(2024, 1, 2)
    assert window.date_start == date(2024, 1, 3)
