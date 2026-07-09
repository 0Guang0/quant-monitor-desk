"""ADR-011 默认 5 日 backfill 窗 — 测试用日期 fixture（非产品代码）。"""

from __future__ import annotations

from backend.app.datasources.fetch_window import CN_EQUITY_BAR_DOMAINS, US_EQUITY_BAR_DOMAINS

# 股类：5 交易日
CN_EQUITY_FIVE_TRADING_DAYS = ("2026-01-05", "2026-01-09")
CN_EQUITY_FIVE_TRADING_DAYS_2024 = ("2024-01-02", "2024-01-08")

# macro / filings 等：5 日历日
CALENDAR_FIVE_DAYS = ("2024-01-01", "2024-01-05")
CALENDAR_FIVE_DAYS_2026 = ("2026-01-01", "2026-01-05")


def default_backfill_window(data_domain: str) -> tuple[str, str]:
    """Return (start, end) within CLI default budget (5 days)."""
    if data_domain in CN_EQUITY_BAR_DOMAINS or data_domain in US_EQUITY_BAR_DOMAINS:
        return CN_EQUITY_FIVE_TRADING_DAYS
    return CALENDAR_FIVE_DAYS_2026
