"""R3-DCP-02 S02-01 — fred macro incremental watermark unit tests."""

from __future__ import annotations

from datetime import date

import duckdb

from backend.app.db.migrate import apply_migrations
from backend.app.datasources.fetch_ports.fred_port import MAX_WINDOW_DAYS
from backend.app.ops.fred_incremental_watermark import (
    compute_since_date,
    read_observation_date_watermark,
    read_since_dates_for_series,
)
from tests.fred_macro_incremental_support import insert_axis_observation


def test_fredWatermark_emptyTable_returnsCappedColdStart() -> None:
    """覆盖范围：空 axis_observation 冷启动水位
    测试对象：compute_since_date + read_since_dates_for_series
    目的/目标：无历史行时 since = today - MAX_WINDOW_DAYS（与 fred_port cap 对齐）
    验证点：since == (2026-06-01) 当 today=2026-06-30、cap=120
    失败含义：冷启动无界拉取，违反 ponytail cap 与 Plan 水位语义
    """
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    today = date(2026, 6, 30)
    since = compute_since_date(None, cap_days=MAX_WINDOW_DAYS, today=today)
    assert since == today - __import__("datetime").timedelta(days=MAX_WINDOW_DAYS)
    mapping = read_since_dates_for_series(con, ("DGS10",), today=today)
    assert mapping["DGS10"] == since.isoformat()


def test_fredWatermark_existingObservation_returnsNextDay() -> None:
    """覆盖范围：单 series 已有最新观测日
    测试对象：read_observation_date_watermark + compute_since_date
    目的/目标：有水位时 since = max(observation_date) + 1 日历日
    验证点：watermark=2026-06-10 → since=2026-06-11
    失败含义：重复全量拉取或漏拉新观测点
    """
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    insert_axis_observation(
        con,
        observation_id="obs-dgs10-1",
        indicator_id="DGS10",
        obs_date=date(2026, 6, 10),
    )
    wm = read_observation_date_watermark(con, "DGS10")
    assert wm == date(2026, 6, 10)
    since = compute_since_date(wm, today=date(2026, 6, 30))
    assert since == date(2026, 6, 11)


def test_fredWatermark_multiSeries_independentWatermarks() -> None:
    """覆盖范围：多 series 独立水位（A 有数据、B 空表）
    测试对象：read_since_dates_for_series
    目的/目标：每 indicator_id 独立 max(publish_timestamp)，互不影响
    验证点：DGS10 since=2026-06-11；VIXCLS 冷启动 since=2026-03-02（today=2026-06-30）
    失败含义：series 间水位串扰，导致漏拉或重复拉
    """
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    today = date(2026, 6, 30)
    insert_axis_observation(
        con,
        observation_id="obs-dgs10",
        indicator_id="DGS10",
        obs_date=date(2026, 6, 10),
    )
    mapping = read_since_dates_for_series(con, ("DGS10", "VIXCLS"), today=today)
    assert mapping["DGS10"] == "2026-06-11"
    cold = (today - __import__("datetime").timedelta(days=MAX_WINDOW_DAYS)).isoformat()
    assert mapping["VIXCLS"] == cold
