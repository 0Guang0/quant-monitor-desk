"""schema.sql 契约与迁移脚本列定义对齐测试。"""

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


def _alter_add_columns(sql_text: str, table: str) -> set[str]:
    pattern = rf"ALTER TABLE {re.escape(table)} ADD COLUMN IF NOT EXISTS (\w+)"
    return {match.group(1) for match in re.finditer(pattern, sql_text, re.IGNORECASE)}


def test_foundationMigrationColumns_existInSchemaContract() -> None:
    """覆盖范围：001–003 基础迁移与 schema.sql 契约的列对齐
    测试对象：FOUNDATION_TABLES 在迁移与 schema.sql 中的列集合
    目的/目标：基础表迁移新增列必须全部出现在 schema 契约里，避免契约落后于库结构
    验证点：每张基础表的 mig_cols 非空且为 contract_cols 的子集
    失败含义：迁移已加列但 schema.sql 未登记，下游契约校验会漏检
    """
    schema_text = SCHEMA_SQL.read_text(encoding="utf-8")
    migration_names = (
        "001_foundation.sql",
        "002_registry_hardening.sql",
        "003_resource_guard_metrics.sql",
    )
    migration_text = "\n".join(
        (MIGRATIONS / name).read_text(encoding="utf-8") for name in migration_names
    )
    for table in FOUNDATION_TABLES:
        mig_cols = _table_columns(migration_text, table) or set()
        mig_cols |= _alter_add_columns(migration_text, table)
        assert mig_cols, f"{table} missing from migrations"
        contract_cols = _table_columns(schema_text, table)
        assert contract_cols, f"{table} missing from schema.sql contract"
        assert mig_cols.issubset(contract_cols), (
            f"{table}: migration columns missing from schema.sql: {mig_cols - contract_cols}"
        )


INGESTION_CONTRACT_TABLES = ("source_registry", "fetch_log")

SYNC_AUDIT_TABLES = ("write_audit_log",)


def test_syncAuditMigrationColumns_existInSchemaContract() -> None:
    """覆盖范围：007 同步审计迁移与 schema.sql 契约的列对齐
    测试对象：write_audit_log 在 007 迁移与 schema.sql 中的列集合
    目的/目标：同步约束审计迁移引入的列须在 schema 契约中可查
    验证点：mig_cols 非空且为 contract_cols（含 ALTER ADD）的子集
    失败含义：审计表列漂移未写入契约，写入审计字段可能对不上
    """
    schema_text = SCHEMA_SQL.read_text(encoding="utf-8")
    migration_text = (MIGRATIONS / "007_sync_constraints_audit.sql").read_text(encoding="utf-8")
    for table in SYNC_AUDIT_TABLES:
        mig_cols = _table_columns(migration_text, table) or set()
        mig_cols |= _alter_add_columns(migration_text, table)
        assert mig_cols, f"{table} missing from 007 migration"
        contract_cols = _table_columns(schema_text, table) or set()
        contract_cols |= _alter_add_columns(schema_text, table)
        assert contract_cols, f"{table} missing from schema.sql"
        assert mig_cols.issubset(contract_cols), (
            f"{table}: migration columns missing from schema.sql: {mig_cols - contract_cols}"
        )


def test_ingestionMigrationColumns_existInSchemaContract() -> None:
    """覆盖范围：004 摄取源迁移与 schema.sql 契约的列对齐
    测试对象：source_registry、fetch_log 在迁移与 schema.sql 中的列集合
    目的/目标：摄取层表结构变更须同步反映在 schema 契约
    验证点：每张摄取表的 mig_cols 非空且为 contract_cols 的子集
    失败含义：摄取表列在契约中缺失，gate 与文档会引用过时结构
    """
    schema_text = SCHEMA_SQL.read_text(encoding="utf-8")
    migration_text = (MIGRATIONS / "004_ingestion_sources.sql").read_text(encoding="utf-8")
    for table in INGESTION_CONTRACT_TABLES:
        mig_cols = _table_columns(migration_text, table)
        assert mig_cols, f"{table} missing from 004 migration"
        contract_cols = _table_columns(schema_text, table)
        assert contract_cols, f"{table} missing from schema.sql"
        assert mig_cols.issubset(contract_cols), (
            f"{table}: migration columns missing from schema.sql: {mig_cols - contract_cols}"
        )


CHECK_CONTRACT_TABLES = (
    "fetch_log",
    "source_registry",
    "manual_review_queue",
    "source_conflict",
    "data_sync_job",
)


def test_schemaContract_includesStatusCheckConstraints() -> None:
    """覆盖范围：schema.sql 中状态类 CHECK 约束
    测试对象：CHECK_CONTRACT_TABLES 各表的 CREATE TABLE 定义体
    目的/目标：契约表须声明 CHECK 约束以锁定合法状态枚举
    验证点：每张表在 schema.sql 中存在且 DDL 体含 CHECK 关键字
    失败含义：状态约束未写入契约，非法状态可能落库而不被文档覆盖
    """
    schema_text = SCHEMA_SQL.read_text(encoding="utf-8")
    for table in CHECK_CONTRACT_TABLES:
        pattern = rf"CREATE TABLE IF NOT EXISTS {re.escape(table)}\s*\((.*?)\);"
        match = re.search(pattern, schema_text, re.DOTALL | re.IGNORECASE)
        assert match is not None, f"{table} missing from schema.sql"
        body = match.group(1)
        assert "CHECK" in body, f"{table} missing CHECK constraints in schema.sql contract"
