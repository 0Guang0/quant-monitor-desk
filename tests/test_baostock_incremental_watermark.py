"""R3-DCP-01 baostock incremental watermark unit tests."""

from __future__ import annotations

from datetime import date

import duckdb
import pytest

from backend.app.sync.watermark import (
    compute_incremental_window,
    incremental_window_is_empty,
    read_bar_trade_date_watermark,
)


def _con_with_bars(rows: list[tuple[str, str]]) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute(
        """
        CREATE TABLE security_bar_1d (
            instrument_id VARCHAR,
            trade_date VARCHAR,
            adjustment_type VARCHAR,
            close DOUBLE,
            source_used VARCHAR
        )
        """
    )
    for instrument_id, trade_date in rows:
        con.execute(
            """
            INSERT INTO security_bar_1d
            (instrument_id, trade_date, adjustment_type, close, source_used)
            VALUES (?, ?, 'none', 10.0, 'baostock')
            """,
            [instrument_id, trade_date],
        )
    return con


def test_watermark_emptyTable_returnsNullAndLookbackWindow() -> None:
    """覆盖范围：空 clean 表 watermark 与默认窗
    测试对象：read_bar_trade_date_watermark · compute_incremental_window
    目的/目标：空表应无 watermark，窗起点为 end 往前 N 日历日
    验证点：watermark is None；date_start=end-30；date_end=给定 end
    失败含义：空表误读水位会导致重复全量或漏拉历史
    """
    con = duckdb.connect()
    con.execute(
        "CREATE TABLE security_bar_1d (instrument_id VARCHAR, trade_date VARCHAR, adjustment_type VARCHAR, close DOUBLE, source_used VARCHAR)"
    )
    wm = read_bar_trade_date_watermark(con)
    window = compute_incremental_window(wm, end=date(2026, 6, 30), empty_table_lookback_days=30)
    assert wm is None
    assert window.watermark is None
    assert window.date_start == date(2026, 5, 31)
    assert window.date_end == date(2026, 6, 30)


def test_watermark_withData_returnsMaxPlusOne() -> None:
    """覆盖范围：有数据的 clean 表 watermark 与增量窗
    测试对象：read_bar_trade_date_watermark · compute_incremental_window
    目的/目标：有数据时 watermark=max(trade_date)，窗从次日开始
    验证点：watermark=2026-06-20；date_start=2026-06-21
    失败含义：未 +1 会重复拉已落库 bar
    """
    con = _con_with_bars([("sh.600519", "2026-06-20")])
    wm = read_bar_trade_date_watermark(con, instrument_id="sh.600519")
    window = compute_incremental_window(wm, end=date(2026, 6, 30))
    assert wm == date(2026, 6, 20)
    assert window.date_start == date(2026, 6, 21)
    assert window.date_end == date(2026, 6, 30)


def test_watermark_boundaryDay_startIsDayAfterMax() -> None:
    """覆盖范围：边界日 max(trade_date) 紧邻 end
    测试对象：compute_incremental_window
    目的/目标：max=2026-06-28 时 date_start 必须为 2026-06-29（inclusive end）
    验证点：date_start == max + 1 day
    失败含义：边界 off-by-one 会漏最后一天或重复拉取
    """
    con = _con_with_bars([("sh.600519", "2026-06-28")])
    wm = read_bar_trade_date_watermark(con)
    window = compute_incremental_window(wm, end=date(2026, 6, 30))
    assert wm == date(2026, 6, 28)
    assert window.date_start == date(2026, 6, 29)
    assert window.date_end == date(2026, 6, 30)


def test_watermark_instrumentFilter_ignoresOtherSymbols() -> None:
    """覆盖范围：按 instrument_id 过滤 watermark
    测试对象：read_bar_trade_date_watermark(instrument_id=...)
    目的/目标：单票增量只读该票最大 trade_date
    验证点：sh.600519 的 max 不随 sz.000001 更晚日期变化
    失败含义：全表 max 会导致单票窗错误
    """
    con = _con_with_bars(
        [
            ("sh.600519", "2026-06-10"),
            ("sz.000001", "2026-06-25"),
        ]
    )
    wm = read_bar_trade_date_watermark(con, instrument_id="sh.600519")
    assert wm == date(2026, 6, 10)


def test_watermark_caughtUp_windowIsEmpty() -> None:
    """覆盖范围：watermark 已追平 end 日（caught-up）
    测试对象：compute_incremental_window · incremental_window_is_empty
    目的/目标：max(trade_date)==end 时窗应倒置且无拉取日
    验证点：date_start > date_end；incremental_window_is_empty 为 True
    失败含义：追平仍拉 fetch 会重复处理已落库 bar
    """
    con = _con_with_bars([("sh.600519", "2026-06-30")])
    wm = read_bar_trade_date_watermark(con, instrument_id="sh.600519")
    window = compute_incremental_window(wm, end=date(2026, 6, 30))
    assert wm == date(2026, 6, 30)
    assert window.date_start == date(2026, 7, 1)
    assert window.date_end == date(2026, 6, 30)
    assert incremental_window_is_empty(window) is True


def test_watermark_cleanTableRejectsUnknownTable() -> None:
    """覆盖范围：watermark clean_table SQL 纵深防御
    测试对象：read_bar_trade_date_watermark(clean_table=...)
    目的/目标：非 allowlist 表名应拒绝，防 SQL 注入
    验证点：恶意 clean_table 抛 ValueError
    失败含义：f-string 表名可被滥用拼接任意 SQL
    """
    con = duckdb.connect()
    con.execute(
        "CREATE TABLE security_bar_1d (instrument_id VARCHAR, trade_date VARCHAR, adjustment_type VARCHAR, close DOUBLE, source_used VARCHAR)"
    )
    with pytest.raises(ValueError, match="unsupported clean_table"):
        read_bar_trade_date_watermark(con, clean_table="evil; DROP TABLE security_bar_1d;--")
