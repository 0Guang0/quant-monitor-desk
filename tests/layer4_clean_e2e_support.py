"""Shared bootstrap for Layer4 DCP-08 US_EQ clean-read e2e tests."""

from __future__ import annotations

from datetime import UTC, date, datetime

from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations

AS_OF = datetime(2024, 11, 29, 21, 0, tzinfo=UTC)
TRADE_DATE = date(2024, 11, 29)
US_MARKET_ID = "US_EQ"


def bootstrap_layer4_clean_db(tmp_path) -> ConnectionManager:
    """Create sandbox DuckDB with migrations applied."""
    db = tmp_path / "layer4_clean.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    return cm


def seed_us_instrument_registry(con, *, instruments: tuple[tuple[str, str], ...]) -> None:
    """Register US_EQ instruments (instrument_id, symbol)."""
    for instrument_id, symbol in instruments:
        con.execute(
            """
            INSERT INTO instrument_registry (
                instrument_id, symbol, name, market_id, asset_type, currency,
                exchange, is_active, source_used, updated_at
            ) VALUES (?, ?, ?, ?, 'equity', 'USD', 'NYSE', TRUE, 'alpha_vantage', CURRENT_TIMESTAMP)
            """,
            [instrument_id, symbol, symbol, US_MARKET_ID],
        )


def seed_us_equity_bar(
    con,
    *,
    instrument_id: str,
    trade_date: date,
    close: float,
    pre_close: float,
    volume: float = 1_000_000.0,
    amount: float | None = None,
    source_used: str = "alpha_vantage",
    batch_id: str | None = None,
) -> None:
    """Insert one US equity daily bar into security_bar_1d."""
    effective_amount = amount if amount is not None else volume * close
    effective_batch = batch_id or f"batch-{instrument_id}-{trade_date.isoformat()}"
    con.execute(
        """
        INSERT INTO security_bar_1d (
            instrument_id, trade_date, open, high, low, close, pre_close, volume, amount,
            adjustment_type, source_used, batch_id, quality_flags, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'none', ?, ?, NULL, CURRENT_TIMESTAMP)
        """,
        [
            instrument_id,
            trade_date.isoformat(),
            pre_close,
            max(close, pre_close) + 0.5,
            min(close, pre_close) - 0.5,
            close,
            pre_close,
            volume,
            effective_amount,
            source_used,
            effective_batch,
        ],
    )


def seed_us_breadth_fixture(
    con,
    *,
    trade_date: date = TRADE_DATE,
) -> tuple[int, int, float]:
    """Seed three US_EQ bars: 2 advancers, 1 decliner; return expected breadth tuple."""
    seed_us_instrument_registry(
        con,
        instruments=(("AAPL", "AAPL"), ("MSFT", "MSFT"), ("GOOGL", "GOOGL")),
    )
    seed_us_equity_bar(
        con, instrument_id="AAPL", trade_date=trade_date, close=190.0, pre_close=185.0
    )
    seed_us_equity_bar(
        con, instrument_id="MSFT", trade_date=trade_date, close=410.0, pre_close=415.0
    )
    seed_us_equity_bar(
        con, instrument_id="GOOGL", trade_date=trade_date, close=175.0, pre_close=170.0
    )
    total_amount = 190.0 * 1_000_000.0 + 410.0 * 1_000_000.0 + 175.0 * 1_000_000.0
    return 2, 1, total_amount
