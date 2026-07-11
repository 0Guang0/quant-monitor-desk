#!/usr/bin/env python3
"""schema.sql ↔ migration SQL 列对齐（阶段性 · 非业务 pytest）

功能：
  用正则抽取 CREATE/ALTER 列名，核对迁移脚本列是否均为 schema.sql 契约子集，
  并抽查关键表 CHECK 枚举片段。对应原 tests/test_schema_contract.py（artifact-guard）。

业务价值：
  防止迁移已加列但 schema.sql 未登记，文档/门禁引用过时结构。

退役 / 清理时间（满足任一即可删本文件）：
  1. 正式 schema drift CLI（或 production_gate 子步）已覆盖 migration↔schema 对齐；或
  2. apply_migrations + 运行时表/列存在性测已作为唯一 SSOT，团队确认不再维护静态 regex。

运行：
  uv run python phase-scripts/check_schema_sql_migration_parity.py --strict
"""

from __future__ import annotations

import argparse
import re
import sys
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
INGESTION_CONTRACT_TABLES = ("source_registry", "fetch_log")
SYNC_AUDIT_TABLES = ("write_audit_log",)
CLEAN_DOMAIN_TABLES = (
    "instrument_registry",
    "security_bar_1d",
    "cn_announcement_clean",
)
CHECK_CONTRACT_TABLES = (
    "fetch_log",
    "source_registry",
    "manual_review_queue",
    "source_conflict",
    "data_sync_job",
)
CHECK_STATUS_FRAGMENTS = {
    "fetch_log": "'SCHEMA_DRIFT', 'FAILED'",
    "source_registry": "source_type IS NULL OR source_type IN",
    "data_sync_job": "'CREATED', 'PLANNED', 'FETCHING'",
    "source_conflict": "reconcile_status IS NULL OR reconcile_status IN",
    "manual_review_queue": "'OPEN', 'IN_PROGRESS', 'RESOLVED', 'DISMISSED', 'CANCELLED'",
}


def _table_columns(sql_text: str, table: str) -> set[str] | None:
    pattern = rf"CREATE TABLE IF NOT EXISTS {re.escape(table)}\s*\((.*?)\);"
    match = re.search(pattern, sql_text, re.DOTALL | re.IGNORECASE)
    if not match:
        return None
    columns: set[str] = set()
    for line in match.group(1).splitlines():
        line = line.strip().rstrip(",")
        if not line or line.upper().startswith(("PRIMARY", "UNIQUE", "FOREIGN", "CONSTRAINT")):
            continue
        columns.add(line.split()[0].strip('"'))
    return columns


def _alter_add_columns(sql_text: str, table: str) -> set[str]:
    pattern = rf"ALTER TABLE {re.escape(table)} ADD COLUMN IF NOT EXISTS (\w+)"
    return {m.group(1) for m in re.finditer(pattern, sql_text, re.IGNORECASE)}


def _assert_subset(schema_text: str, migration_text: str, tables: tuple[str, ...], label: str) -> list[str]:
    errors: list[str] = []
    for table in tables:
        mig_cols = _table_columns(migration_text, table) or set()
        mig_cols |= _alter_add_columns(migration_text, table)
        if not mig_cols:
            errors.append(f"{label}: {table} missing from migrations")
            continue
        contract_cols = _table_columns(schema_text, table) or set()
        contract_cols |= _alter_add_columns(schema_text, table)
        if not contract_cols:
            errors.append(f"{label}: {table} missing from schema.sql")
            continue
        missing = mig_cols - contract_cols
        if missing:
            errors.append(f"{label}: {table} missing from schema.sql: {sorted(missing)}")
    return errors


def _run() -> list[str]:
    schema_text = SCHEMA_SQL.read_text(encoding="utf-8")
    errors: list[str] = []
    foundation = "\n".join(
        (MIGRATIONS / name).read_text(encoding="utf-8")
        for name in (
            "001_foundation.sql",
            "002_registry_hardening.sql",
            "003_resource_guard_metrics.sql",
        )
    )
    errors.extend(_assert_subset(schema_text, foundation, FOUNDATION_TABLES, "foundation"))
    errors.extend(
        _assert_subset(
            schema_text,
            (MIGRATIONS / "007_sync_constraints_audit.sql").read_text(encoding="utf-8"),
            SYNC_AUDIT_TABLES,
            "007",
        )
    )
    errors.extend(
        _assert_subset(
            schema_text,
            (MIGRATIONS / "004_ingestion_sources.sql").read_text(encoding="utf-8"),
            INGESTION_CONTRACT_TABLES,
            "004",
        )
    )
    errors.extend(
        _assert_subset(
            schema_text,
            (MIGRATIONS / "013_clean_domain_tables.sql").read_text(encoding="utf-8"),
            CLEAN_DOMAIN_TABLES,
            "013",
        )
    )
    for table in CHECK_CONTRACT_TABLES:
        pattern = rf"CREATE TABLE IF NOT EXISTS {re.escape(table)}\s*\((.*?)\);"
        match = re.search(pattern, schema_text, re.DOTALL | re.IGNORECASE)
        if match is None:
            errors.append(f"CHECK: {table} missing from schema.sql")
            continue
        body = match.group(1)
        fragment = CHECK_STATUS_FRAGMENTS.get(table)
        if fragment:
            if fragment not in body:
                errors.append(f"CHECK: {table} missing fragment {fragment!r}")
        elif "CHECK" not in body:
            errors.append(f"CHECK: {table} missing CHECK keyword")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    errors = _run()
    if not errors:
        print("PASS: schema.sql ↔ migration parity")
        return 0
    print("FAIL: schema.sql ↔ migration parity")
    for err in errors:
        print(f"  - {err}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
