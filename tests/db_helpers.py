"""Test helpers for database write paths."""

from __future__ import annotations

from pathlib import Path

from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.db.validation_gate import StubValidationGate
from backend.app.db.write_manager import WriteManager, WriteRequest


def create_test_write_manager(conn_manager) -> WriteManager:
    """Explicit stub gate for tests — production must inject a real ValidationGate."""
    return WriteManager(conn_manager, StubValidationGate())


def insert_ohlcv_bar_row(
    con,
    instrument_id: str,
    trade_date: str,
    close: float,
    *,
    table: str = "stg_foundation_smoke",
    source_used: str = "qmt",
    batch_id: str = "b1",
    adjustment_type: str = "none",
) -> None:
    """Insert one OHLCV-aligned bar row (matches migration 014 layout)."""
    con.execute(
        f"""
        INSERT INTO {table} (
            instrument_id, trade_date, open, high, low, close, pre_close, volume, amount,
            adjustment_type, source_used, batch_id, quality_flags, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, NULL, ?, ?, ?, NULL, CURRENT_TIMESTAMP)
        """,
        [
            instrument_id,
            trade_date,
            close,
            close,
            close,
            close,
            adjustment_type,
            source_used,
            batch_id,
        ],
    )


def insert_stg_foundation_smoke_row(
    con,
    instrument_id: str,
    trade_date: str,
    close: float,
    *,
    source_used: str = "qmt",
    batch_id: str = "b1",
    adjustment_type: str = "none",
) -> None:
    """Insert one OHLCV-aligned staging row (matches migration 014 layout)."""
    insert_ohlcv_bar_row(
        con,
        instrument_id,
        trade_date,
        close,
        table="stg_foundation_smoke",
        source_used=source_used,
        batch_id=batch_id,
        adjustment_type=adjustment_type,
    )


def insert_smoke_clean_row(
    con,
    instrument_id: str,
    trade_date: str,
    close: float,
    *,
    source_used: str = "qmt",
    batch_id: str = "b0",
    adjustment_type: str = "none",
    table: str = "security_bar_smoke_clean",
) -> None:
    """Insert one row into CTAS clean smoke table (same layout as stg_foundation_smoke)."""
    insert_ohlcv_bar_row(
        con,
        instrument_id,
        trade_date,
        close,
        table=table,
        source_used=source_used,
        batch_id=batch_id,
        adjustment_type=adjustment_type,
    )


def setup_write_smoke_db(tmp_path: Path, *, with_clean_table: bool = False) -> ConnectionManager:
    """Migrated DuckDB with stg_foundation_smoke seed row (write-manager test fixture)."""
    cm = ConnectionManager(tmp_path / "t.duckdb")
    with cm.writer() as con:
        apply_migrations(con)
        insert_stg_foundation_smoke_row(con, "AAPL", "2026-06-15", 195.0)
        if with_clean_table:
            empty_clean_table(con)
    return cm


def empty_clean_table(writer, table: str = "security_bar_smoke_clean") -> None:
    writer.execute(f"CREATE TABLE {table} AS SELECT * FROM stg_foundation_smoke WHERE 1=0")


def write_smoke_request(mode: str = "append_only", report: str = "stub-pass-1") -> WriteRequest:
    return WriteRequest(
        run_id="r1",
        job_id="j1",
        target_table="security_bar_smoke_clean",
        staging_table="stg_foundation_smoke",
        write_mode=mode,
        primary_keys=("instrument_id", "trade_date", "adjustment_type"),
        validation_report_id=report,
        source_used="qmt",
        data_domain="cn_equity_daily_bar",
    )
