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


def setup_write_smoke_db(tmp_path: Path, *, with_clean_table: bool = False) -> ConnectionManager:
    """Migrated DuckDB with stg_foundation_smoke seed row (write-manager test fixture)."""
    cm = ConnectionManager(tmp_path / "t.duckdb")
    with cm.writer() as con:
        apply_migrations(con)
        con.execute(
            "INSERT INTO stg_foundation_smoke VALUES ('AAPL','2026-06-15',195.0,'qmt','b1')"
        )
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
        primary_keys=("instrument_id", "trade_date"),
        validation_report_id=report,
        source_used="qmt",
        data_domain="cn_equity_daily_bar",
    )
