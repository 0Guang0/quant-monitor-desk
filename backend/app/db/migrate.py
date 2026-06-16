"""Apply versioned SQL migrations to DuckDB."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

import duckdb

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


class MigrationChecksumError(RuntimeError):
    """Applied migration file content no longer matches stored checksum."""


def _file_checksum(sql_path: Path) -> str:
    return hashlib.sha256(sql_path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def applied_versions(con: duckdb.DuckDBPyConnection) -> set[str]:
    """Return version_ids recorded in schema_version; empty if table missing."""
    try:
        rows = con.execute("SELECT version_id FROM schema_version").fetchall()
    except duckdb.CatalogException:
        return set()
    return {row[0] for row in rows}


def verify_applied_checksums(
    con: duckdb.DuckDBPyConnection,
    migrations_dir: Path = MIGRATIONS_DIR,
) -> None:
    """Fail if any applied migration file was modified after apply."""
    try:
        rows = con.execute("SELECT version_id, checksum FROM schema_version").fetchall()
    except duckdb.CatalogException:
        return
    for version_id, stored_checksum in rows:
        sql_path = migrations_dir / f"{version_id}.sql"
        if not sql_path.is_file():
            raise MigrationChecksumError(
                f"migration file missing for applied version {version_id!r}"
            )
        current = _file_checksum(sql_path)
        if current != stored_checksum:
            raise MigrationChecksumError(
                f"migration {version_id!r} checksum mismatch: "
                f"stored={stored_checksum!r} current={current!r}"
            )


def apply_migrations(
    con: duckdb.DuckDBPyConnection,
    migrations_dir: Path = MIGRATIONS_DIR,
) -> list[str]:
    """Apply pending migrations in filename order; idempotent."""
    verify_applied_checksums(con, migrations_dir)
    already = applied_versions(con)
    newly_applied: list[str] = []

    for sql_path in sorted(migrations_dir.glob("*.sql")):
        version_id = sql_path.stem
        checksum = _file_checksum(sql_path)
        if version_id in already:
            continue

        sql_text = sql_path.read_text(encoding="utf-8")
        con.execute("BEGIN")
        try:
            con.execute(sql_text)
            con.execute(
                """
                INSERT INTO schema_version (
                    version_id, applied_at, migration_file, checksum, applied_by, notes
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    version_id,
                    datetime.now(UTC),
                    sql_path.name,
                    checksum,
                    "init_db",
                    None,
                ],
            )
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
        newly_applied.append(version_id)

    return newly_applied
