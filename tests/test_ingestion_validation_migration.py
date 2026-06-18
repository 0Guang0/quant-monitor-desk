"""Tests for migration 005 ingestion validation tables (Batch C §8.1)."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations, verify_applied_checksums

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "backend/app/db/migrations"


def _fresh_con(tmp_path: Path) -> duckdb.DuckDBPyConnection:
    db = tmp_path / "t.duckdb"
    con = duckdb.connect(str(db))
    apply_migrations(con)
    return con


# --- table existence -----------------------------------------------------


@pytest.mark.parametrize(
    "table_name",
    ["validation_report", "data_quality_log", "source_conflict", "manual_review_queue"],
)
def test_initDb_createsValidationTables(tmp_path: Path, table_name: str) -> None:
    con = _fresh_con(tmp_path)
    rows = con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_name = ?",
        [table_name],
    ).fetchall()
    con.close()
    assert rows, f"migration 005 must create table {table_name!r}"


def test_initDb_runTwice_isIdempotent(tmp_path: Path) -> None:
    con = _fresh_con(tmp_path)
    # second apply must be a no-op (already-applied versions skipped)
    second = apply_migrations(con)
    assert second == [], f"second apply should skip applied migrations, got {second}"
    # schema_version records 005 exactly once
    cnt = con.execute(
        "SELECT COUNT(*) FROM schema_version WHERE version_id = '005_ingestion_validation'"
    ).fetchone()[0]
    con.close()
    assert cnt == 1


def test_initDb_doesNotModifyMigration004Checksum(tmp_path: Path) -> None:
    con = _fresh_con(tmp_path)
    # 004 must be applied and unchanged; verify_applied_checksums must not raise
    verify_applied_checksums(con)
    versions = con.execute("SELECT version_id FROM schema_version").fetchall()
    con.close()
    vlist = {r[0] for r in versions}
    assert "004_ingestion_sources" in vlist
    assert "005_ingestion_validation" in vlist


# --- validation_report column / constraint enforcement -------------------


def test_validationReport_requiredFieldsEnforced(tmp_path: Path) -> None:
    """status enum guard + NOT NULL on key columns enforced at DB layer."""
    con = _fresh_con(tmp_path)
    with pytest.raises(duckdb.Error):
        con.execute("INSERT INTO validation_report (validation_report_id) VALUES (?)", ["x"])
    con.close()


def test_validationReport_statusCheck_rejectsInvalidStatus(tmp_path: Path) -> None:
    """DB CHECK must reject unknown status values (not PASSED/WARNING/FAILED)."""
    con = _fresh_con(tmp_path)
    with pytest.raises(duckdb.Error):
        con.execute(
            """
            INSERT INTO validation_report (
                validation_report_id, run_id, data_domain, source_id,
                status, checked_rows, failed_rows, warning_rows,
                can_write_clean, needs_manual_review
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ["vr-1", "r1", "market_bar_1d", "qmt", "BOGUS", 1, 0, 0, True, False],
        )
    con.close()


def test_validationReport_validRows_accepted(tmp_path: Path) -> None:
    con = _fresh_con(tmp_path)
    for status, can_write, needs_review in [
        ("PASSED", True, False),
        ("WARNING", True, False),
        ("FAILED", False, True),
    ]:
        con.execute(
            """
            INSERT INTO validation_report (
                validation_report_id, run_id, data_domain, source_id,
                status, checked_rows, failed_rows, warning_rows,
                can_write_clean, needs_manual_review
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                f"vr-{status}",
                "r1",
                "market_bar_1d",
                "qmt",
                status,
                1,
                0,
                0,
                can_write,
                needs_review,
            ],
        )
    cnt = con.execute("SELECT COUNT(*) FROM validation_report").fetchone()[0]
    con.close()
    assert cnt == 3


# --- source_conflict -----------------------------------------------------


def test_sourceConflict_requiredFieldsEnforced(tmp_path: Path) -> None:
    con = _fresh_con(tmp_path)
    with pytest.raises(duckdb.Error):
        con.execute("INSERT INTO source_conflict (conflict_id) VALUES (?)", ["c-1"])
    con.close()


def test_sourceConflict_validRow_accepted(tmp_path: Path) -> None:
    con = _fresh_con(tmp_path)
    con.execute(
        """
        INSERT INTO source_conflict (
            conflict_id, run_id, data_domain, field_name,
            primary_source, primary_value, competing_source, competing_value,
            normalized_diff, tolerance_warning, tolerance_severe,
            severity, manual_review_required
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            "c-1",
            "r1",
            "market_bar_1d",
            "close",
            "qmt",
            "10.0",
            "baostock",
            "10.5",
            0.05,
            0.0005,
            0.002,
            "severe",
            True,
        ],
    )
    cnt = con.execute("SELECT COUNT(*) FROM source_conflict").fetchone()[0]
    con.close()
    assert cnt == 1


def test_sourceConflict_severityCheck_rejectsInvalid(tmp_path: Path) -> None:
    con = _fresh_con(tmp_path)
    with pytest.raises(duckdb.Error):
        con.execute(
            """
            INSERT INTO source_conflict (
                conflict_id, run_id, data_domain, field_name,
                primary_source, primary_value, competing_source, competing_value,
                severity, manual_review_required
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                "c-x",
                "r1",
                "market_bar_1d",
                "close",
                "qmt",
                "10.0",
                "baostock",
                "10.5",
                "totally_wrong",
                False,
            ],
        )
    con.close()


# --- manual_review_queue -------------------------------------------------


def test_manualReviewQueue_requiredFieldsEnforced(tmp_path: Path) -> None:
    con = _fresh_con(tmp_path)
    with pytest.raises(duckdb.Error):
        con.execute("INSERT INTO manual_review_queue (review_id) VALUES (?)", ["mr-1"])
    con.close()


def test_manualReviewQueue_sourceObjectTypeCheck(tmp_path: Path) -> None:
    con = _fresh_con(tmp_path)
    with pytest.raises(duckdb.Error):
        con.execute(
            """
            INSERT INTO manual_review_queue (
                review_id, source_object_type, source_object_id, priority, status
            ) VALUES (?, ?, ?, ?, ?)
            """,
            ["mr-1", "not_a_valid_type", "c-1", "high", "open"],
        )
    con.close()


def test_manualReviewQueue_validRow_accepted(tmp_path: Path) -> None:
    con = _fresh_con(tmp_path)
    con.execute(
        """
        INSERT INTO manual_review_queue (
            review_id, source_object_type, source_object_id, priority, status
        ) VALUES (?, ?, ?, ?, ?)
        """,
        ["mr-1", "conflict", "c-1", "high", "open"],
    )
    cnt = con.execute("SELECT COUNT(*) FROM manual_review_queue").fetchone()[0]
    con.close()
    assert cnt == 1


# --- data_quality_log ----------------------------------------------------


def test_dataQualityLog_validRow_accepted(tmp_path: Path) -> None:
    con = _fresh_con(tmp_path)
    con.execute(
        """
        INSERT INTO data_quality_log (
            log_id, validation_report_id, run_id, data_domain, source_id,
            table_name, rule_id, severity, message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            "dq-1",
            "vr-1",
            "r1",
            "market_bar_1d",
            "qmt",
            "stg_x",
            "MISSING_PRIMARY_KEY",
            "failed",
            "primary key is null",
        ],
    )
    cnt = con.execute("SELECT COUNT(*) FROM data_quality_log").fetchone()[0]
    con.close()
    assert cnt == 1


# --- init_db prod-path applies 005 ---------------------------------------


def test_initDb_prodPath_appliesMigration005(tmp_path: Path) -> None:
    db = tmp_path / "prod.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    with cm.reader() as con:
        versions = {r[0] for r in con.execute("SELECT version_id FROM schema_version").fetchall()}
    assert "005_ingestion_validation" in versions
