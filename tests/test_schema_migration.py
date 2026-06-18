"""Foundation schema migration tests (Round 1 task 005)."""

from __future__ import annotations

import shutil
from pathlib import Path

import duckdb
import pytest
from backend.app.db.migrate import (
    MIGRATIONS_DIR,
    MigrationChecksumError,
    applied_versions,
    apply_migrations,
)

FOUNDATION_TABLES = {
    "schema_version",
    "file_registry",
    "write_audit_log",
    "resource_guard_log",
    "stg_foundation_smoke",
}


def test_applyMigrations_freshDb_createsFoundationTables() -> None:
    con = duckdb.connect(":memory:")
    applied = apply_migrations(con)
    assert "001_foundation" in applied
    assert "002_registry_hardening" in applied
    assert "003_resource_guard_metrics" in applied
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    assert FOUNDATION_TABLES.issubset(tables)
    assert "stg_file_registry" in tables


def test_applyMigrations_runTwice_isIdempotent() -> None:
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    second = apply_migrations(con)
    assert second == []
    count = con.execute(
        "SELECT COUNT(*) FROM schema_version WHERE version_id='001_foundation'"
    ).fetchone()[0]
    assert count == 1


def test_appliedVersions_emptyDb_returnsEmptySet() -> None:
    con = duckdb.connect(":memory:")
    assert applied_versions(con) == set()


def test_appliedVersions_afterMigration_containsFoundation() -> None:
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    assert applied_versions(con) == {
        "001_foundation",
        "002_registry_hardening",
        "003_resource_guard_metrics",
        "004_ingestion_sources",
        "005_ingestion_validation",
        "006_ingestion_sync",
        "007_sync_constraints_audit",
    }


INGESTION_TABLES = frozenset({"source_registry", "fetch_log"})


def test_applyMigrations_freshDb_includesIngestionTables() -> None:
    con = duckdb.connect(":memory:")
    applied = apply_migrations(con)
    assert "004_ingestion_sources" in applied
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    assert INGESTION_TABLES.issubset(tables)


def test_appliedVersions_afterMigration_containsIngestion() -> None:
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    assert applied_versions(con) == frozenset(
        {
            "001_foundation",
            "002_registry_hardening",
            "003_resource_guard_metrics",
            "004_ingestion_sources",
            "005_ingestion_validation",
            "006_ingestion_sync",
            "007_sync_constraints_audit",
        }
    )


def test_applyMigrations_modifiedFile_raisesChecksumError(tmp_path: Path) -> None:
    migrations_dir = tmp_path / "migrations"
    shutil.copytree(MIGRATIONS_DIR, migrations_dir)
    db = tmp_path / "t.duckdb"
    con = duckdb.connect(str(db))
    apply_migrations(con, migrations_dir=migrations_dir)
    sql_path = migrations_dir / "001_foundation.sql"
    sql_path.write_text(sql_path.read_text(encoding="utf-8") + "\n-- tampered\n", encoding="utf-8")
    with pytest.raises(MigrationChecksumError, match="checksum mismatch"):
        apply_migrations(con, migrations_dir=migrations_dir)


def test_applyMigrations_missingAppliedFile_raisesChecksumError(tmp_path: Path) -> None:
    migrations_dir = tmp_path / "migrations"
    shutil.copytree(MIGRATIONS_DIR, migrations_dir)
    db = tmp_path / "t.duckdb"
    con = duckdb.connect(str(db))
    apply_migrations(con, migrations_dir=migrations_dir)
    (migrations_dir / "001_foundation.sql").unlink()
    with pytest.raises(MigrationChecksumError, match="migration file missing"):
        apply_migrations(con, migrations_dir=migrations_dir)


def test_applyMigrations_badSqlInFile_raisesAndLeavesNoVersionRow(tmp_path: Path) -> None:
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()
    (migrations_dir / "001_bad.sql").write_text(
        "CREATE TABLE ok(id INT); THIS IS NOT VALID SQL;",
        encoding="utf-8",
    )
    con = duckdb.connect(":memory:")
    with pytest.raises(duckdb.Error):
        apply_migrations(con, migrations_dir=migrations_dir)
    assert applied_versions(con) == set()
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    assert "ok" not in tables


SCHEMA_PHASE_MATRIX = {
    "001_foundation": ("implemented", {"write_audit_log", "file_registry"}),
    "005_ingestion_validation": ("implemented", {"validation_report", "source_conflict"}),
    "006_ingestion_sync": ("implemented", {"data_sync_job", "job_event_log"}),
    "007_sync_constraints_audit": ("implemented", {"data_sync_job", "write_audit_log"}),
    "planned_round3": ("planned-later", {"source_health_snapshot"}),
}


def test_schemaPhaseMatrix_documentsImplementedVsPlanned() -> None:
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    for phase, (status, expected_subset) in SCHEMA_PHASE_MATRIX.items():
        if status == "implemented":
            assert expected_subset.issubset(tables), f"{phase} missing {expected_subset - tables}"
        else:
            assert not expected_subset.intersection(tables), f"{phase} should not exist yet"
