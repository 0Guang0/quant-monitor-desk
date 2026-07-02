"""Layer4 Tier A clean read — US_EQ breadth from security_bar_1d."""

from __future__ import annotations

import hashlib
from datetime import date, datetime

from backend.app.layer4_markets.market_structure import Layer4MarketError
from backend.app.layer4_markets.models import MarketBreadthSnapshotRow, MarketCalendarRow
from backend.app.ops.data_health_profiles.us_trading_calendar import is_trading_day

US_EQ_MARKET_ID = "US_EQ"
BREADTH_SOURCE = "tier_a_clean:security_bar_1d"
CALENDAR_SOURCE = "us_trading_calendar_ssot"


def _breadth_label(advancers: int, decliners: int) -> str:
    if advancers > decliners:
        return "positive_breadth"
    if advancers < decliners:
        return "negative_breadth"
    return "balanced"


def _fetch_clean_bar_rows(
    con,
    *,
    market_id: str,
    trade_date: date,
) -> list[tuple]:
    """Fetch one trade_date's clean bars for breadth + lineage (single round-trip)."""
    rows = con.execute(
        """
        SELECT b.instrument_id, b.close, b.pre_close, b.volume, b.amount, b.batch_id
        FROM security_bar_1d b
        INNER JOIN instrument_registry r ON b.instrument_id = r.instrument_id
        WHERE r.market_id = ?
          AND b.trade_date = ?
          AND b.adjustment_type = 'none'
        ORDER BY b.instrument_id
        """,
        [market_id, trade_date.isoformat()],
    ).fetchall()
    if not rows:
        raise Layer4MarketError(
            f"no clean security_bar_1d rows for market_id={market_id!r} trade_date={trade_date}"
        )
    return rows


def aggregate_breadth_from_bars(
    con,
    *,
    market_id: str,
    trade_date: date,
    as_of: datetime,
) -> MarketBreadthSnapshotRow:
    """Aggregate advancers/decliners from clean security_bar_1d for one trade_date."""
    rows = _fetch_clean_bar_rows(con, market_id=market_id, trade_date=trade_date)

    advancers = 0
    decliners = 0
    total_amount = 0.0
    for _instrument_id, close_raw, pre_close_raw, volume_raw, amount_raw, _batch_id in rows:
        if pre_close_raw is None:
            raise Layer4MarketError("missing pre_close for breadth aggregation")
        close = float(close_raw)
        pre_close = float(pre_close_raw)
        if close > pre_close:
            advancers += 1
        elif close < pre_close:
            decliners += 1
        if amount_raw is not None:
            total_amount += float(amount_raw)
        else:
            total_amount += float(volume_raw or 0.0) * close

    if advancers < 0 or decliners < 0 or total_amount < 0:
        raise Layer4MarketError("breadth volume fields must be non-negative")

    return MarketBreadthSnapshotRow(
        market_id=market_id,
        trade_date=trade_date,
        advancers=advancers,
        decliners=decliners,
        total_amount=total_amount,
        breadth_label=_breadth_label(advancers, decliners),
        source=BREADTH_SOURCE,
        quality_flag="ok",
        as_of_timestamp=as_of,
    )


def build_calendar_row(
    *,
    market_id: str,
    trade_date: date,
    as_of: datetime,
) -> MarketCalendarRow:
    """Build one calendar row from US trading calendar SSOT."""
    if market_id != US_EQ_MARKET_ID:
        raise Layer4MarketError(
            f"build_calendar_row only supports {US_EQ_MARKET_ID!r}, got {market_id!r}"
        )
    trading = is_trading_day(trade_date)
    return MarketCalendarRow(
        market_id=market_id,
        trade_date=trade_date,
        is_trading_day=trading,
        session_type="regular" if trading else "closed",
        timezone="America/New_York",
        source=CALENDAR_SOURCE,
        quality_flag="ok",
        as_of_timestamp=as_of,
    )


def collect_clean_lineage_provenance(
    con,
    *,
    market_id: str,
    trade_date: date,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """Return source_dataset_ids, source_fetch_ids, source_content_hashes for clean read."""
    rows = _fetch_clean_bar_rows(con, market_id=market_id, trade_date=trade_date)

    fetch_ids = tuple(sorted({str(row[5]) for row in rows if row[5]}))
    if not fetch_ids:
        fetch_ids = (f"clean-read:{market_id}:{trade_date.isoformat()}",)

    content_hashes = tuple(
        hashlib.sha256(f"{row[0]}|{trade_date.isoformat()}|{row[1]}".encode()).hexdigest()
        for row in rows
    )
    source_dataset_ids = ("clean:security_bar_1d", "clean:us_trading_calendar")
    return source_dataset_ids, fetch_ids, content_hashes


class USEquityCleanMarketAdapter:
    """Read US_EQ calendar + breadth from Tier A clean tables (read-only)."""

    def __init__(self, con) -> None:
        self._con = con

    def load_calendar(self, trade_date: date, as_of: datetime) -> tuple[MarketCalendarRow, ...]:
        return (build_calendar_row(market_id=US_EQ_MARKET_ID, trade_date=trade_date, as_of=as_of),)

    def load_breadth(self, trade_date: date, as_of: datetime) -> MarketBreadthSnapshotRow:
        return aggregate_breadth_from_bars(
            self._con,
            market_id=US_EQ_MARKET_ID,
            trade_date=trade_date,
            as_of=as_of,
        )
