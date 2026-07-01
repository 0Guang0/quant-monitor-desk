"""DCP-05 S03 — US Treasury incremental watermark unit tests."""

from __future__ import annotations

from datetime import date

import duckdb

from backend.app.db.migrate import apply_migrations
from backend.app.datasources.fetch_ports.fred_port import MAX_WINDOW_DAYS
from backend.app.ops.us_treasury_incremental_watermark import (
    compute_since_date,
    read_observation_date_watermark,
    read_since_dates_for_instruments,
)
from tests.fred_macro_incremental_support import insert_axis_observation


def test_usTreasuryWatermark_emptyTable_returnsCappedColdStart() -> None:
    """覆盖范围：空 axis_observation 冷启动水位
    测试对象：compute_since_date + read_since_dates_for_instruments
    目的/目标：无历史行时 since = today - MAX_WINDOW_DAYS
    验证点：since == today - cap 天
    失败含义：冷启动无界拉取，违反 cap 与水位语义
    """
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    today = date(2026, 6, 30)
    since = compute_since_date(None, cap_days=MAX_WINDOW_DAYS, today=today)
    assert since == today - __import__("datetime").timedelta(days=MAX_WINDOW_DAYS)
    mapping = read_since_dates_for_instruments(con, ("10Y",), today=today)
    assert mapping["10Y"] == since.isoformat()


def test_usTreasuryWatermark_existingObservation_returnsNextDay() -> None:
    """覆盖范围：单 tenor 已有最新观测日
    测试对象：read_observation_date_watermark + compute_since_date
    目的/目标：有水位时 since = max(observation_date) + 1 日历日
    验证点：watermark=2026-06-10 → since=2026-06-11
    失败含义：重复全量拉取或漏拉新观测点
    """
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    insert_axis_observation(
        con,
        observation_id="obs-10y",
        indicator_id="10Y",
        obs_date=date(2026, 6, 10),
    )
    wm = read_observation_date_watermark(con, "10Y")
    assert wm == date(2026, 6, 10)
    since = compute_since_date(wm, today=date(2026, 6, 30))
    assert since == date(2026, 6, 11)
