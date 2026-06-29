"""Incremental sync watermark — bar trade_date domain (R3-DCP-01).

ponytail: calendar-day window; CN trading calendar deferred to R3H-03 follow-up.
Macro observation_date alias reserved for R3-DCP-02 (fred track).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

from backend.app.db.sql_identifiers import quote_ident

_BAR_CLEAN_TABLES = frozenset({"security_bar_1d"})


@dataclass(frozen=True)
class IncrementalWindow:
    date_start: date
    date_end: date
    watermark: date | None


def incremental_window_is_empty(window: IncrementalWindow) -> bool:
    """True when caught-up: inclusive window has no fetchable calendar days."""
    return window.date_start > window.date_end


def _validate_clean_table(clean_table: str) -> str:
    if clean_table not in _BAR_CLEAN_TABLES:
        raise ValueError(f"unsupported clean_table: {clean_table!r}")
    return clean_table


def _coerce_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    text = str(value)[:10]
    return date.fromisoformat(text)


def read_bar_trade_date_watermark(
    con,
    *,
    clean_table: str = "security_bar_1d",
    instrument_id: str | None = None,
    adjustment_type: str = "none",
) -> date | None:
    """Return max(trade_date) for bar clean table, optionally filtered."""
    clauses = ["adjustment_type = ?"]
    params: list[Any] = [adjustment_type]
    if instrument_id is not None:
        clauses.append("instrument_id = ?")
        params.append(instrument_id)
    where = " AND ".join(clauses)
    table = quote_ident(_validate_clean_table(clean_table))
    row = con.execute(
        f"SELECT MAX(CAST(trade_date AS DATE)) FROM {table} WHERE {where}",
        params,
    ).fetchone()
    return _coerce_date(row[0] if row else None)


def compute_incremental_window(
    watermark: date | None,
    *,
    end: date | None = None,
    empty_table_lookback_days: int = 30,
) -> IncrementalWindow:
    """Compute inclusive [date_start, date_end] from watermark (calendar days)."""
    if empty_table_lookback_days < 1:
        raise ValueError("empty_table_lookback_days must be >= 1")
    date_end = end or datetime.now(UTC).date()
    if watermark is None:
        date_start = date_end - timedelta(days=empty_table_lookback_days)
    else:
        date_start = watermark + timedelta(days=1)
    return IncrementalWindow(date_start=date_start, date_end=date_end, watermark=watermark)
