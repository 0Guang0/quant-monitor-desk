"""R3-DCP-05 S09 — SEC EDGAR incremental watermark tests."""

from __future__ import annotations

from datetime import date

import duckdb

from backend.app.db.migrate import apply_migrations
from backend.app.ops.sec_edgar_incremental_watermark import (
    FILING_LOOKBACK_DAYS,
    compute_since_date,
    read_filing_date_watermark,
    read_since_date_for_cik,
)
from tests.sec_edgar_incremental_support import CIK, bootstrap_db, seed_watermark_row


def test_secEdgarWatermark_emptyTable_returnsCappedColdStart() -> None:
    """覆盖范围：空 us_disclosure_clean 冷启动水位
    测试对象：compute_since_date + read_since_date_for_cik
    目的/目标：无历史 filing 时 since 有界回溯
    验证点：since 不晚于 today - FILING_LOOKBACK_DAYS
    失败含义：冷启动无界拉取破坏 SEC incremental 语义
    """
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    today = date(2026, 6, 30)
    since = compute_since_date(None, cap_days=FILING_LOOKBACK_DAYS, today=today)
    assert since <= today
    mapping = read_since_date_for_cik(con, CIK, today=today)
    assert mapping == since.isoformat()


def test_secEdgarWatermark_existingFiling_returnsNextDay(tmp_path) -> None:
    """覆盖范围：已有 filing_date 水位
    测试对象：read_filing_date_watermark + compute_since_date
    目的/目标：有水位时 since = max(filing_date) + 1 日历日
    验证点：seed 2025-08-01 → since=2025-08-02
    失败含义：未 +1 会重复拉已落库披露
    """
    cm = bootstrap_db(tmp_path)
    with cm.writer() as con:
        seed_watermark_row(con, "2025-08-01")
        wm = read_filing_date_watermark(con, CIK)
    assert wm == date(2025, 8, 1)
    since = compute_since_date(wm, today=date(2025, 12, 1))
    assert since == date(2025, 8, 2)
