"""Schema contract vs migration alignment tests."""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_SQL = PROJECT_ROOT / "specs/schema/schema.sql"
MIGRATIONS = PROJECT_ROOT / "backend/app/db/migrations"

FOUNDATION_TABLES = (
    "schema_version",
    "file_registry",
    "write_audit_log",
    "resource_guard_log",
    "stg_foundation_smoke",
    "stg_file_registry",
)


def _table_columns(sql_text: str, table: str) -> set[str] | None:
    pattern = rf"CREATE TABLE IF NOT EXISTS {re.escape(table)}\s*\((.*?)\);"
    match = re.search(pattern, sql_text, re.DOTALL | re.IGNORECASE)
    if not match:
        return None
    body = match.group(1)
    columns: set[str] = set()
    for line in body.splitlines():
        line = line.strip().rstrip(",")
        if not line or line.upper().startswith(("PRIMARY", "UNIQUE", "FOREIGN", "CONSTRAINT")):
            continue
        col = line.split()[0].strip('"')
        columns.add(col)
    return columns


def test_foundationMigrationColumns_existInSchemaContract() -> None:
    schema_text = SCHEMA_SQL.read_text(encoding="utf-8")
    migration_text = "\n".join(
        (MIGRATIONS / name).read_text(encoding="utf-8")
        for name in ("001_foundation.sql", "002_registry_hardening.sql")
    )
    for table in FOUNDATION_TABLES:
        mig_cols = _table_columns(migration_text, table)
        assert mig_cols, f"{table} missing from migrations"
        contract_cols = _table_columns(schema_text, table)
        assert contract_cols, f"{table} missing from schema.sql contract"
        assert mig_cols.issubset(contract_cols), (
            f"{table}: migration columns missing from schema.sql: {mig_cols - contract_cols}"
        )
