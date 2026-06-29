"""QMD-owned US equity trading calendar (R3H-07 CAL-US).

L2 SSOT for NYSE/Nasdaq combined US equity non-trading days — mirrors cn_trading_calendar API.
"""

from __future__ import annotations

from datetime import date, timedelta

_RANGE_START = date(2000, 1, 1)
_RANGE_END = date(2030, 12, 31)

# ponytail: bounded federal/NYSE holiday table ceiling — beyond 2030 or ad-hoc exchange
# closures need exchange-authoritative feed or ADR extension (symmetric CAL-CN-TAIL).


def _observed(d: date) -> date:
    if d.weekday() == 5:
        return d - timedelta(days=1)
    if d.weekday() == 6:
        return d + timedelta(days=1)
    return d


def _nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> date:
    """Return nth weekday in month (weekday 0=Mon; n=1 first, n=-1 last)."""
    if n > 0:
        first = date(year, month, 1)
        offset = (weekday - first.weekday()) % 7
        return first + timedelta(days=offset + 7 * (n - 1))
    if month == 12:
        last = date(year, month, 31)
    else:
        last = date(year, month + 1, 1) - timedelta(days=1)
    offset = (last.weekday() - weekday) % 7
    return last - timedelta(days=offset)


def _easter_sunday(year: int) -> date:
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    ell = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * ell) // 451
    month = (h + ell - 7 * m + 114) // 31
    day = ((h + ell - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _federal_market_holidays(year: int) -> set[date]:
    holidays = {
        _observed(date(year, 1, 1)),
        _nth_weekday_of_month(year, 1, 0, 3),
        _nth_weekday_of_month(year, 2, 0, 3),
        _easter_sunday(year) - timedelta(days=2),
        _nth_weekday_of_month(year, 5, 0, -1),
        _observed(date(year, 7, 4)),
        _nth_weekday_of_month(year, 9, 0, 1),
        _nth_weekday_of_month(year, 11, 3, 4),
        _observed(date(year, 12, 25)),
    }
    if year >= 2021:
        holidays.add(_observed(date(year, 6, 19)))
    return holidays


def _load_non_trading_days() -> frozenset[date]:
    holidays: set[date] = set()
    current = _RANGE_START
    while current <= _RANGE_END:
        if current.weekday() >= 5:
            holidays.add(current)
        current += timedelta(days=1)
    for year in range(_RANGE_START.year, _RANGE_END.year + 1):
        holidays.update(_federal_market_holidays(year))
    return frozenset(holidays)


_NON_TRADING_DAYS = _load_non_trading_days()


def is_trading_day(check_date: date) -> bool:
    """True when check_date is a US equity trading day per QMD calendar artifact."""
    if check_date < _RANGE_START or check_date > _RANGE_END:
        return False
    return check_date not in _NON_TRADING_DAYS


def get_trading_days(start_date: date, end_date: date) -> list[date]:
    """Trading days inclusive between start_date and end_date."""
    if end_date < start_date:
        return []
    days: list[date] = []
    current = start_date
    while current <= end_date:
        if is_trading_day(current):
            days.append(current)
        current += timedelta(days=1)
    return days


def get_missing_trading_days(
    start_date: date,
    end_date: date,
    existing_dates: list[date],
) -> list[date]:
    """Trading days in range absent from existing_dates."""
    expected = set(get_trading_days(start_date, end_date))
    present = set(existing_dates)
    return sorted(expected - present)
