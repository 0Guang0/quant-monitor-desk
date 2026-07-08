"""006 迁移：同步作业表结构测试（Batch D）。

覆盖范围：全新库建表、重复迁移幂等、不得篡改既有 004/005 迁移脚本。
"""

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
        "watermark_before",
        "watermark_after",
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
    """覆盖范围：全新库首次应用 006 迁移后的同步表结构
    测试对象：migration 006_ingestion_sync
    目的/目标：第一次建库时，同步任务表和事件日志表及约定字段都要建好
    验证点：两表存在；列集覆盖契约字段；schema_version 含 006
    失败含义：同步任务没法落库或缺事件表，编排层根本起不来
    """
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
    """覆盖范围：已迁移库再次执行 apply_migrations 的幂等行为
    测试对象：apply_migrations 对已应用 006 的库
    目的/目标：重复初始化不应报错，也不应重复记录同一版本
    验证点：第二次返回空列表；006 在 schema_version 中仅一条
    失败含义：重复迁移报错或版本重复，运维脚本和 CI 初始化不可靠
    """
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
    """覆盖范围：应用 006 不得篡改既有 004/005 迁移文件
    测试对象：MIGRATIONS_DIR 下 004、005 SQL 文件
    目的/目标：新迁移只增表，不能回头改历史迁移脚本内容
    验证点：迁移前后 004/005 文件 SHA256 不变；schema_version 仍含 004、005
    失败含义：历史迁移被静默改写，已部署库的校验和会与仓库漂移
    """
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
