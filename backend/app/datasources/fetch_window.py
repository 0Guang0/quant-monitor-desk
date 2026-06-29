"""Shared date-window helpers for datasources fetch ports (R3H-10 layer fix)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta


def recent_window_start(*, calendar_days: int = 14) -> date:
    """Return UTC calendar start date for recent-window fetches."""
    return datetime.now(UTC).date() - timedelta(days=calendar_days)
