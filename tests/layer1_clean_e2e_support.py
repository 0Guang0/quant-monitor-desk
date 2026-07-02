"""Shared bootstrap for Layer1 DCP-06 clean-read e2e tests."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from tests.fred_macro_incremental_support import insert_axis_observation


def bootstrap_layer1_clean_db(tmp_path: Path) -> ConnectionManager:
    db = tmp_path / "layer1_clean.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    return cm


def seed_macro_series(
    con,
    *,
    db_indicator_id: str,
    n: int,
    start: date,
    base_value: float,
    source_used: str = "fred",
    step: float = 0.01,
) -> None:
    for i in range(n):
        d = start + timedelta(days=i)
        insert_axis_observation(
            con,
            observation_id=f"{db_indicator_id}-{d.isoformat()}",
            indicator_id=db_indicator_id,
            obs_date=d,
            raw_value=base_value + step * i,
            content_hash=f"hash-{db_indicator_id}-{i}",
        )
        con.execute(
            "UPDATE axis_observation SET source_used = ? WHERE observation_id = ?",
            [source_used, f"{db_indicator_id}-{d.isoformat()}"],
        )


def seed_spy_bars(con, *, n: int, start: date, base_close: float = 400.0) -> None:
    prev = base_close
    for i in range(n):
        d = start + timedelta(days=i)
        close = base_close + i * 0.5
        vol = 1_000_000.0 + i * 10_000.0
        con.execute(
            """
            INSERT INTO security_bar_1d (
                instrument_id, trade_date, open, high, low, close, pre_close, volume, amount,
                adjustment_type, source_used, batch_id, quality_flags, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, 'none', ?, ?, NULL, CURRENT_TIMESTAMP)
            """,
            [
                "SPY",
                d.isoformat(),
                prev,
                close + 1.0,
                close - 1.0,
                close,
                prev,
                vol,
                "alpha_vantage",
                f"batch-{i}",
            ],
        )
        prev = close


AS_OF = datetime(2026, 6, 20, 16, 0, tzinfo=UTC)
