"""R3-DCP-05 S07 — CNINFO metadata incremental watermark tests."""

from __future__ import annotations

from datetime import date

import duckdb

from backend.app.db.migrate import apply_migrations
from backend.app.ops.cninfo_incremental_watermark import (
    METADATA_LOOKBACK_DAYS,
    compute_since_date,
    read_metadata_publish_watermark,
    read_since_date_for_instrument,
)
from tests.cninfo_incremental_support import SYMBOL, bootstrap_db, seed_watermark_row


def test_cninfoWatermark_emptyTable_returnsCappedColdStart() -> None:
    """覆盖范围：空 cn_announcement_clean 冷启动水位
    测试对象：compute_since_date + read_since_date_for_instrument
    目的/目标：无历史 metadata 时 since = today - METADATA_LOOKBACK_DAYS
    验证点：since 为 30 日历日前（today=2026-06-30）
    失败含义：冷启动无界拉取破坏 metadata incremental 语义
    """
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    today = date(2026, 6, 30)
    since = compute_since_date(None, cap_days=METADATA_LOOKBACK_DAYS, today=today)
    assert since == today - __import__("datetime").timedelta(days=METADATA_LOOKBACK_DAYS)
    mapping = read_since_date_for_instrument(con, SYMBOL, today=today)
    assert mapping == since.isoformat()


def test_cninfoWatermark_existingPublish_returnsNextDay(tmp_path) -> None:
    """覆盖范围：已有公告 publish 水位
    测试对象：read_metadata_publish_watermark + compute_since_date
    目的/目标：有水位时 since = max(publish_date) + 1 日历日
    验证点：seed 2024-06-24 → since=2024-06-25
    失败含义：未 +1 会重复拉已落库公告
    """
    cm = bootstrap_db(tmp_path)
    with cm.writer() as con:
        seed_watermark_row(con, "2024-06-24")
        wm = read_metadata_publish_watermark(con, SYMBOL)
    assert wm == date(2024, 6, 24)
    since = compute_since_date(wm, today=date(2024, 6, 30))
    assert since == date(2024, 6, 25)
