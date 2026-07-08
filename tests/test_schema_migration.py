"""基础 schema 迁移（apply_migrations）行为与完整性测试。"""

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

ALL_MIGRATION_VERSIONS = frozenset(
    {
        "001_foundation",
        "002_registry_hardening",
        "003_resource_guard_metrics",
        "004_ingestion_sources",
        "005_ingestion_validation",
        "006_ingestion_sync",
        "007_sync_constraints_audit",
        "008_lineage_version_fields",
        "009_status_check_constraints",
        "010_lineage_not_null",
        "011_layer1_tables",
        "012_migration_residuals",
        "013_clean_domain_tables",
        "014_stg_bar_ohlcv",
        "015_dcp05_tier_a_clean",
        "016_sync_job_watermark_columns",
    }
)


def test_applyMigrations_freshDb_createsFoundationTables() -> None:
    """覆盖范围：空库首次 apply_migrations
    测试对象：apply_migrations 与 SHOW TABLES
    目的/目标：新库应跑完前三版基础迁移并建好 foundation 表集
    验证点：applied 含 001–003；FOUNDATION_TABLES 及 stg_file_registry 均存在
    失败含义：空库无法 bootstrap，后续写入与审计链路无表可用
    """
    con = duckdb.connect(":memory:")
    applied = apply_migrations(con)
    assert "001_foundation" in applied
    assert "002_registry_hardening" in applied
    assert "003_resource_guard_metrics" in applied
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    assert FOUNDATION_TABLES.issubset(tables)
    assert "stg_file_registry" in tables


def test_applyMigrations_runTwice_isIdempotent() -> None:
    """覆盖范围：重复执行迁移
    测试对象：apply_migrations 第二次调用
    目的/目标：已应用版本不得重复执行或重复记 schema_version
    验证点：second == []；001_foundation 在 schema_version 仅一行
    失败含义：迁移非幂等，重启或重跑会双写 DDL 或版本脏数据
    """
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    second = apply_migrations(con)
    assert second == []
    count = con.execute(
        "SELECT COUNT(*) FROM schema_version WHERE version_id='001_foundation'"
    ).fetchone()[0]
    assert count == 1


def test_appliedVersions_emptyDb_returnsEmptySet() -> None:
    """覆盖范围：未迁移库的 applied_versions
    测试对象：applied_versions
    目的/目标：空库应报告无任何已应用版本
    验证点：applied_versions(con) == set()
    失败含义：空库误报已迁移，跳过或重复应用判断失真
    """
    con = duckdb.connect(":memory:")
    assert applied_versions(con) == set()


def test_appliedVersions_afterMigration_containsFoundation() -> None:
    """覆盖范围：全量迁移后的版本集合
    测试对象：applied_versions 在 apply_migrations 之后
    目的/目标：当前仓库应登记 001–015 全部已实现迁移 ID
    验证点：返回集合等于 001_foundation 至 015_dcp05_tier_a_clean
    失败含义：版本登记与磁盘迁移文件不一致，升级路径不可追踪
    """
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    assert applied_versions(con) == ALL_MIGRATION_VERSIONS


INGESTION_TABLES = frozenset({"source_registry", "fetch_log"})


def test_applyMigrations_freshDb_includesIngestionTables() -> None:
    """覆盖范围：摄取层表随全量迁移创建
    测试对象：apply_migrations 后的表清单
    目的/目标：004 摄取迁移应创建 source_registry 与 fetch_log
    验证点：applied 含 004_ingestion_sources；INGESTION_TABLES ⊆ tables
    失败含义：摄取元数据表缺失，数据源登记与抓取日志无法落库
    """
    con = duckdb.connect(":memory:")
    applied = apply_migrations(con)
    assert "004_ingestion_sources" in applied
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    assert INGESTION_TABLES.issubset(tables)


def test_applyMigrations_modifiedFile_raisesChecksumError(tmp_path: Path) -> None:
    """覆盖范围：已应用迁移文件被篡改
    测试对象：apply_migrations 校验和逻辑
    目的/目标：磁盘 SQL 与 schema_version 记录不一致时必须拒绝继续
    验证点：篡改 001 后再次 apply 抛出 MigrationChecksumError（checksum mismatch）
    失败含义：迁移内容可静默变更，环境间 schema 不可复现
    """
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
    """覆盖范围：已登记版本对应 SQL 文件缺失
    测试对象：apply_migrations 文件存在性检查
    目的/目标：schema_version 有记录但迁移文件被删时必须 fail-closed
    验证点：删除 001_foundation.sql 后抛出 MigrationChecksumError（migration file missing）
    失败含义：版本记录与文件脱节仍继续运行，无法重建库
    """
    migrations_dir = tmp_path / "migrations"
    shutil.copytree(MIGRATIONS_DIR, migrations_dir)
    db = tmp_path / "t.duckdb"
    con = duckdb.connect(str(db))
    apply_migrations(con, migrations_dir=migrations_dir)
    (migrations_dir / "001_foundation.sql").unlink()
    with pytest.raises(MigrationChecksumError, match="migration file missing"):
        apply_migrations(con, migrations_dir=migrations_dir)


def test_applyMigrations_badSqlInFile_raisesAndLeavesNoVersionRow(tmp_path: Path) -> None:
    """覆盖范围：单文件含非法 SQL 的失败原子性
    测试对象：apply_migrations 对坏 SQL 的事务语义
    目的/目标：执行失败时不应留下 schema_version 行或半建表
    验证点：duckdb.Error(Parser|syntax) 抛出；applied_versions 为空；ok 表不存在
    失败含义：坏迁移部分生效，库处于不可预测中间态
    """
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()
    (migrations_dir / "001_bad.sql").write_text(
        "CREATE TABLE ok(id INT); THIS IS NOT VALID SQL;",
        encoding="utf-8",
    )
    con = duckdb.connect(":memory:")
    with pytest.raises(duckdb.Error, match="Parser|syntax"):
        apply_migrations(con, migrations_dir=migrations_dir)
    assert applied_versions(con) == set()
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    assert "ok" not in tables


SCHEMA_PHASE_MATRIX = {
    "001_foundation": ("implemented", {"write_audit_log", "file_registry"}),
    "005_ingestion_validation": ("implemented", {"validation_report", "source_conflict"}),
    "006_ingestion_sync": ("implemented", {"data_sync_job", "job_event_log"}),
    "007_sync_constraints_audit": ("implemented", {"data_sync_job", "write_audit_log"}),
    "011_layer1_tables": ("implemented", {"axis_registry", "axis_snapshot_lineage"}),
}


def test_schemaPhaseMatrix_documentsImplementedVsPlanned() -> None:
    """覆盖范围：已实现 schema 阶段矩阵与真实表存在性
    测试对象：SCHEMA_PHASE_MATRIX 对照迁移后 SHOW TABLES
    目的/目标：已实现阶段的关键表必须存在
    验证点：implemented 阶段 expected_subset ⊆ tables
    失败含义：阶段文档与库结构脱节
    """
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    for phase, (_status, expected_subset) in SCHEMA_PHASE_MATRIX.items():
        assert expected_subset.issubset(tables), f"{phase} missing {expected_subset - tables}"
