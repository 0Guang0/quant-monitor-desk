"""QMD-owned A-share trading calendar (R3H-03 G2/G17).

L2 migrate from EasyXT smart_data_detector.TradingCalendar — holiday/weekend logic
rewritten without duckdb, sys.path, or reference-tree runtime imports.
"""

from __future__ import annotations

from datetime import date, timedelta

_RANGE_START = date(2000, 1, 1)
_RANGE_END = date(2030, 12, 31)

# Lunar new year (正月初一) → public holiday window (除夕..初七), EasyXT 2024–2030 table.
# ponytail: fixed-date table ceiling — lunar festivals beyond 2030 or mid-festival drift need
# exchange-authoritative calendar source (R3H-05 or ADR); do not extend generators without SSOT.
_SPRING_FESTIVAL_FIRST_DAY: dict[int, tuple[int, int]] = {
    2024: (2, 10),
    2025: (1, 29),
    2026: (2, 17),
    2027: (2, 6),
    2028: (1, 26),
    2029: (2, 13),
    2030: (2, 3),
}


def _date_range(start: date, end: date) -> list[date]:
    days: list[date] = []
    current = start
    while current <= end:
        days.append(current)
        current += timedelta(days=1)
    return days


def _spring_festival_holidays() -> set[date]:
    holidays: set[date] = set()
    for year, (month, day) in _SPRING_FESTIVAL_FIRST_DAY.items():
        festival = date(year, month, day)
        for offset in range(-1, 7):
            holidays.add(festival + timedelta(days=offset))
    return holidays


def _qingming_holidays() -> set[date]:
    # ponytail: fixed Apr 4–6 proxy; real Qingming shifts yearly — upgrade via exchange CSV
    holidays: set[date] = set()
    for year in range(_RANGE_START.year, _RANGE_END.year + 1):
        for day in (4, 5, 6):
            holidays.add(date(year, 4, day))
    return holidays


def _dragon_boat_holidays() -> set[date]:
    holidays: set[date] = set()
    for year in range(_RANGE_START.year, _RANGE_END.year + 1):
        for day in (28, 29, 30):
            try:
                holidays.add(date(year, 5, day))
            except ValueError:
                continue
    return holidays


def _mid_autumn_holidays() -> set[date]:
    holidays: set[date] = set()
    for year in range(_RANGE_START.year, _RANGE_END.year + 1):
        for day in range(15, 18):
            try:
                holidays.add(date(year, 9, day))
            except ValueError:
                continue
    return holidays


def _national_day_holidays() -> set[date]:
    holidays: set[date] = set()
    for year in range(_RANGE_START.year, _RANGE_END.year + 1):
        holidays.update(_date_range(date(year, 10, 1), date(year, 10, 7)))
    return holidays


def _load_non_trading_days() -> frozenset[date]:
    holidays: set[date] = set()
    current = _RANGE_START
    while current <= _RANGE_END:
        if current.weekday() >= 5:
            holidays.add(current)
        current += timedelta(days=1)
    holidays.update(_spring_festival_holidays())
    holidays.update(_qingming_holidays())
    holidays.update(_dragon_boat_holidays())
    holidays.update(_mid_autumn_holidays())
    holidays.update(_national_day_holidays())
    return frozenset(holidays)


_NON_TRADING_DAYS = _load_non_trading_days()


def is_trading_day(check_date: date) -> bool:
    """True when check_date is an A-share trading day per QMD calendar artifact."""
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
