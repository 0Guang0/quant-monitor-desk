"""Incremental sync watermark — unified read entry (M-G1-03 P1-05).

ponytail: calendar-day window for bars; macro uses publish_timestamp on axis_observation.
CN trading calendar deferred to R3H-03 follow-up.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

from backend.app.db.sql_identifiers import quote_ident
from backend.app.datasources.fetch_ports.fred_port import MAX_WINDOW_DAYS

_BAR_CLEAN_TABLES = frozenset({"security_bar_1d"})

_BAR_WATERMARK_DOMAINS = frozenset(
    {
        "cn_equity_daily_bar",
        "us_equity_daily_bar",
        "etf_daily_bar",
        "fx_daily_bar",
        "commodity_daily_bar",
    }
)

_MACRO_WATERMARK_DOMAINS = frozenset(
    {
        "macro_series",
        "us_treasury_yield_curve",
        "inflation_expectation",
        "central_bank_policy",
        "credit_gap",
        "development_indicator",
        "global_macro_reference",
        "cot_positioning",
    }
)


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


def read_observation_date_watermark(con, indicator_id: str) -> date | None:
    """Return max publish date for one macro indicator in axis_observation."""
    row = con.execute(
        """
        SELECT MAX(CAST(publish_timestamp AS DATE))
        FROM axis_observation
        WHERE indicator_id = ?
        """,
        [indicator_id],
    ).fetchone()
    return _coerce_date(row[0] if row else None)


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


def read_watermark(con, domain: str, key: str) -> date | None:
    """Single watermark read entry for macro and bar domains."""
    if domain in _MACRO_WATERMARK_DOMAINS:
        return read_observation_date_watermark(con, key)
    if domain in _BAR_WATERMARK_DOMAINS:
        return read_bar_trade_date_watermark(con, instrument_id=key)
    raise ValueError(f"unsupported watermark domain: {domain!r}")


def compute_since_date(
    watermark: date | None,
    *,
    cap_days: int = MAX_WINDOW_DAYS,
    today: date | None = None,
    advance_days: int = 1,
) -> date:
    """Next macro fetch window start: watermark+advance_days or capped cold-start."""
    ref = today or datetime.now(UTC).date()
    if watermark is None:
        return ref - timedelta(days=cap_days)
    return watermark + timedelta(days=advance_days)


def read_since_dates_for_series(
    con,
    series_ids: Sequence[str],
    *,
    cap_days: int = MAX_WINDOW_DAYS,
    today: date | None = None,
) -> dict[str, str]:
    """Per-series ISO since dates for FetchRequest.start_time injection."""
    return {
        series_id: compute_since_date(
            read_observation_date_watermark(con, series_id),
            cap_days=cap_days,
            today=today,
        ).isoformat()
        for series_id in series_ids
    }


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
