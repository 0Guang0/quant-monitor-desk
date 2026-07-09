"""Shared date-window helpers for datasources fetch ports (R3H-10 layer fix)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

US_EQUITY_BAR_DOMAINS = frozenset({"us_equity_daily_bar"})
CN_EQUITY_BAR_DOMAINS = frozenset({"cn_equity_daily_bar", "market_bar_1d"})


def _us_trading_calendar():
    # ponytail: lazy import breaks data_health_profiles ↔ datasources import cycle
    import backend.app.ops.data_health_profiles.us_trading_calendar as us_trading_calendar

    return us_trading_calendar


def recent_window_start(*, calendar_days: int = 14) -> date:
    """Return UTC calendar start date for recent-window fetches."""
    return datetime.now(UTC).date() - timedelta(days=calendar_days)


def is_us_equity_bar_fetch(*, data_domain: str, instrument_id: str = "") -> bool:
    """True when fetch should use US equity trading-session calendar (CAL-US)."""
    if data_domain in US_EQUITY_BAR_DOMAINS:
        return True
    return instrument_id.endswith(".US")


def recent_trading_window_start(
    *,
    trading_sessions: int = 14,
    end: date | None = None,
) -> date:
    """Return earliest date so [result, end] spans `trading_sessions` US trading days."""
    if trading_sessions < 1:
        raise ValueError("trading_sessions must be >= 1")
    cal = _us_trading_calendar()
    anchor = end or datetime.now(UTC).date()
    collected = 0
    current = anchor
    while collected < trading_sessions:
        if cal.is_trading_day(current):
            collected += 1
            if collected == trading_sessions:
                return current
        current -= timedelta(days=1)
        if current < cal._RANGE_START:  # noqa: SLF001
            return cal._RANGE_START  # noqa: SLF001
    return current


def _cn_trading_calendar():
    import backend.app.ops.data_health_profiles.cn_trading_calendar as cn_trading_calendar

    return cn_trading_calendar


def backfill_trading_days(data_domain: str, start: date, end: date) -> list[date]:
    """Trading days in [start, end] for backfill shard planning (ADR-011 / §8).

    股类域（cn_equity_daily_bar / us_equity_daily_bar 等）使用 ADR-007 交易所日历。
    macro / filings 等无交易所日历时按日历日计数（ponytail 兜底）；默认 5 / 硬顶 20
    仍适用，但单位为日历日。见 ADR-011 §1.1。
    """
    if end < start:
        return []
    if is_us_equity_bar_fetch(data_domain=data_domain):
        return _us_trading_calendar().get_trading_days(start, end)
    if data_domain in CN_EQUITY_BAR_DOMAINS:
        return _cn_trading_calendar().get_trading_days(start, end)
    # ponytail: macro/non-equity domains count calendar days until exchange calendars exist
    days: list[date] = []
    current = start
    while current <= end:
        days.append(current)
        current += timedelta(days=1)
    return days


def us_equity_window_kind(*, data_domain: str, instrument_id: str = "") -> str:
    """Evidence window_kind for US equity bar fetches vs calendar-day domains."""
    return (
        "trading_sessions"
        if is_us_equity_bar_fetch(data_domain=data_domain, instrument_id=instrument_id)
        else "calendar_days"
    )


def mock_us_equity_daily_bars(
    *,
    symbol: str,
    count: int,
    source_used: str,
    open_: float = 100.0,
    high: float | None = None,
    low: float | None = None,
    close: float | None = None,
    volume: int = 10000,
) -> list[dict[str, Any]]:
    """Deterministic US equity mock bars on recent trading dates only."""
    trade_dates = recent_trading_dates(count=count)
    hi = high if high is not None else open_ + 1.0
    lo = low if low is not None else open_ - 0.5
    cl = close if close is not None else open_ + 0.5
    bars = [
        {
            "instrument_id": symbol,
            "trade_date": trade_date.isoformat(),
            "open": open_,
            "high": hi,
            "low": lo,
            "close": cl,
            "volume": volume,
            "source_used": source_used,
        }
        for trade_date in trade_dates
    ]
    return filter_us_trading_day_bars(bars)


def reject_fetch_window_span_over_cap(
    *,
    start_time: str | None,
    end_time: str | None,
    cap: int,
    data_domain: str,
    instrument_id: str = "",
    label: str = "max_window_days",
) -> None:
    """Reject explicit windows wider than cap (trading sessions for US equity bar domains)."""
    if not start_time or not end_time:
        return
    if data_domain not in US_EQUITY_BAR_DOMAINS:
        from backend.app.datasources.normalizers.evidence_bundle import reject_window_span_over_cap

        reject_window_span_over_cap(
            start_time=start_time,
            end_time=end_time,
            cap=cap,
            label=label,
        )
        return
    from backend.app.datasources.normalizers.evidence_bundle import reject_over_cap

    start = datetime.fromisoformat(start_time.replace("Z", "+00:00")).astimezone(UTC).date()
    end = datetime.fromisoformat(end_time.replace("Z", "+00:00")).astimezone(UTC).date()
    lo, hi = min(start, end), max(start, end)
    cal = _us_trading_calendar()
    session_count = len(cal.get_trading_days(lo, hi))
    earliest = recent_trading_window_start(trading_sessions=cap, end=hi)
    if lo < earliest or session_count > cap:
        reject_over_cap(value=session_count, cap=cap, label=label)


def recent_trading_dates(*, count: int, end: date | None = None) -> list[date]:
    """Most recent `count` US trading days ending at `end` (default UTC today)."""
    if count < 1:
        return []
    cal = _us_trading_calendar()
    anchor = end or datetime.now(UTC).date()
    dates: list[date] = []
    current = anchor
    while len(dates) < count and current >= cal._RANGE_START:  # noqa: SLF001
        if cal.is_trading_day(current):
            dates.append(current)
        current -= timedelta(days=1)
    return dates


def filter_us_trading_day_bars(bars: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop bars whose trade_date falls on US non-trading days."""
    cal = _us_trading_calendar()
    kept: list[dict[str, Any]] = []
    for bar in bars:
        raw = bar.get("trade_date") or bar.get("date")
        if not raw:
            continue
        trade_date = date.fromisoformat(str(raw)[:10])
        if cal.is_trading_day(trade_date):
            kept.append(bar)
    return kept
