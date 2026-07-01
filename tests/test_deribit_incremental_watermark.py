"""R3-DCP-05 S11 — Deribit crypto incremental watermark tests."""

from __future__ import annotations

from datetime import date

import duckdb

from backend.app.db.migrate import apply_migrations
from backend.app.ops.deribit_incremental_watermark import (
    SURFACE_LOOKBACK_DAYS,
    compute_since_date,
    read_as_of_date_watermark,
    read_since_date_for_instrument,
)
from tests.deribit_incremental_support import INSTRUMENT, bootstrap_db, seed_watermark_row


def test_deribitWatermark_emptyTable_returnsCappedColdStart() -> None:
    """覆盖范围：空 crypto_derivative_clean 冷启动水位
    测试对象：compute_since_date + read_since_date_for_instrument
    目的/目标：无历史 surface 时 since 有界回溯
    验证点：since == today - SURFACE_LOOKBACK_DAYS
    失败含义：冷启动无界拉取破坏 deribit incremental 语义
    """
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    today = date(2026, 6, 30)
    since = compute_since_date(None, cap_days=SURFACE_LOOKBACK_DAYS, today=today)
    assert since == today - __import__("datetime").timedelta(days=SURFACE_LOOKBACK_DAYS)
    mapping = read_since_date_for_instrument(con, INSTRUMENT, today=today)
    assert mapping == since.isoformat()


def test_deribitWatermark_existingAsOf_returnsNextDay(tmp_path) -> None:
    """覆盖范围：已有 as_of_timestamp 水位
    测试对象：read_as_of_date_watermark + compute_since_date
    目的/目标：有水位时 since = max(as_of_date) + 1 日历日
    验证点：seed 2024-06-24 → since=2024-06-25
    失败含义：未 +1 会重复拉已落库 surface
    """
    cm = bootstrap_db(tmp_path)
    with cm.writer() as con:
        seed_watermark_row(con, "2024-06-24")
        wm = read_as_of_date_watermark(con, INSTRUMENT)
    assert wm == date(2024, 6, 24)
    since = compute_since_date(wm, today=date(2024, 6, 30))
    assert since == date(2024, 6, 25)
