"""Tests for migration 006 ingestion sync tables (Batch D §8.1)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import duckdb
from backend.app.db.migrate import MIGRATIONS_DIR, apply_migrations, verify_applied_checksums

MIGRATION_006 = "006_ingestion_sync"

DATA_SYNC_JOB_COLUMNS = frozenset(
    {
        "job_id",
        "run_id",
        "job_type",
        "data_domain",
        "market_id",
        "instrument_id",
        "partition_key",
        "date_start",
        "date_end",
        "source_id",
        "adapter_id",
        "status",
        "priority",
        "retry_count",
        "max_retries",
        "cursor_before",
        "cursor_after",
        "validation_report_id",
        "conflict_report_id",
        "write_id",
        "error_type",
        "error_message",
        "created_at",
        "started_at",
        "finished_at",
        "updated_at",
    }
)

JOB_EVENT_LOG_COLUMNS = frozenset(
    {
        "event_id",
        "run_id",
        "job_id",
        "task_id",
        "event_type",
        "old_status",
        "new_status",
        "message",
        "payload_json",
        "created_at",
    }
)


def _table_columns(con: duckdb.DuckDBPyConnection, table_name: str) -> set[str]:
    rows = con.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = ?
        """,
        [table_name],
    ).fetchall()
    return {row[0] for row in rows}


def _file_checksum(sql_path: Path) -> str:
    return hashlib.sha256(sql_path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def test_migration006_freshDb_createsSyncTables(migrated_con, tmp_path) -> None:
    """tables data_sync_job and job_event_log exist with expected columns."""
    con = migrated_con(tmp_path)
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    assert "data_sync_job" in tables
    assert "job_event_log" in tables
    assert DATA_SYNC_JOB_COLUMNS.issubset(_table_columns(con, "data_sync_job"))
    assert JOB_EVENT_LOG_COLUMNS.issubset(_table_columns(con, "job_event_log"))
    versions = {row[0] for row in con.execute("SELECT version_id FROM schema_version").fetchall()}
    assert MIGRATION_006 in versions
    con.close()


def test_migration006_initDbTwice_isIdempotent(migrated_con, tmp_path) -> None:
    """second init_db does not fail."""
    con = migrated_con(tmp_path)
    second = apply_migrations(con)
    assert second == []
    cnt = con.execute(
        "SELECT COUNT(*) FROM schema_version WHERE version_id = ?",
        [MIGRATION_006],
    ).fetchone()[0]
    con.close()
    assert cnt == 1


def test_migration006_doesNotModify004Or005Checksum(tmp_path) -> None:
    """004/005 migration files unchanged."""
    before_004 = _file_checksum(MIGRATIONS_DIR / "004_ingestion_sources.sql")
    before_005 = _file_checksum(MIGRATIONS_DIR / "005_ingestion_validation.sql")
    con = duckdb.connect(str(tmp_path / "t.duckdb"))
    apply_migrations(con)
    verify_applied_checksums(con)
    versions = {row[0] for row in con.execute("SELECT version_id FROM schema_version").fetchall()}
    con.close()
    after_004 = _file_checksum(MIGRATIONS_DIR / "004_ingestion_sources.sql")
    after_005 = _file_checksum(MIGRATIONS_DIR / "005_ingestion_validation.sql")
    assert before_004 == after_004
    assert before_005 == after_005
    assert "004_ingestion_sources" in versions
    assert "005_ingestion_validation" in versions
