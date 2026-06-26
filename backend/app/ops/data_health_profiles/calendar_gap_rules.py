"""Calendar gap rules for market_bar_p0 (R3FR-02)."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from backend.app.ops.data_health import DataHealthCheckResult


def _parse_trade_date(value: object) -> date | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _weekdays_between(start: date, end: date) -> list[date]:
    # ponytail: Mon–Fri proxy when no QMD official calendar artifact
    days: list[date] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def check_missing_trading_day(
    bars: list[dict[str, Any]],
    *,
    domain: str,
    source_id: str | None = None,
    calendar_authority: bool = False,
) -> list[DataHealthCheckResult]:
    """WARN when weekdays missing and no official calendar; FAIL only with authority."""
    if not bars:
        return []
    dates: list[date] = []
    for row in bars:
        parsed = _parse_trade_date(row.get("trade_date") or row.get("date"))
        if parsed is not None:
            dates.append(parsed)
    if not dates:
        return []
    start, end = min(dates), max(dates)
    present = {d.isoformat() for d in dates}
    expected = _weekdays_between(start, end)
    missing = [d for d in expected if d.isoformat() not in present]
    if not missing:
        return []
    sample = ", ".join(d.isoformat() for d in missing[:5])
    suffix = " (and more)" if len(missing) > 5 else ""
    if calendar_authority:
        return [
            DataHealthCheckResult(
                rule_id="MISSING_TRADING_DAY",
                severity="FAIL",
                status="FAIL",
                source_id=source_id,
                domain=domain,
                evidence_path=None,
                row_count=len(bars),
                message=f"missing trading days: {sample}{suffix}",
            )
        ]
    return [
        DataHealthCheckResult(
            rule_id="MISSING_TRADING_DAY",
            severity="WARN",
            status="WARN",
            source_id=source_id,
            domain=domain,
            evidence_path=None,
            row_count=len(bars),
            message=(
                f"possible missing weekdays (no official calendar): {sample}{suffix}"
            ),
        )
    ]
