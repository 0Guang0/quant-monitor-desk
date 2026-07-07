"""已落地建模表 migration 覆盖测试。"""

from __future__ import annotations

import duckdb
from backend.app.db.migrate import apply_migrations

LAYER1_AXIS_TABLES = frozenset(
    {
        "axis_registry",
        "axis_indicator_registry",
        "axis_indicator_profile",
        "axis_observation",
        "axis_feature_snapshot",
        "axis_interpretation_snapshot",
        "axis_snapshot_lineage",
    }
)

L5_MIGRATED_TABLES = frozenset(
    {
        "instrument_registry",
        "security_bar_1d",
    }
)

CLEAN_DOMAIN_MIGRATED_TABLES = frozenset(
    {
        "cn_announcement_clean",
        "stg_disclosure_smoke",
        "stg_axis_observation_smoke",
        "us_disclosure_clean",
        "stg_us_disclosure_smoke",
        "crypto_derivative_clean",
        "stg_crypto_derivative_smoke",
    }
)

def test_migrationCoverage_l5MigratedTables_existAfter013() -> None:
    """覆盖范围：013 后 L5 bar 表存在于 DuckDB
    测试对象：apply_migrations 表清单
    目的/目标：instrument_registry、security_bar_1d 可回归断言
    验证点：L5_MIGRATED_TABLES ⊆ tables
    失败含义：013 未应用或表名漂移
    """
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    assert L5_MIGRATED_TABLES.issubset(tables)


def test_migrationCoverage_l1AxisTables_existAfterMigration011() -> None:
    """覆盖范围：第一层轴表 migration 011 已落地
    测试对象：apply_migrations 与 SHOW TABLES
    目的/目标：矩阵中 L1 DONE 行须有可回归的 DuckDB 存在性断言
    验证点：LAYER1_AXIS_TABLES ⊆ tables；schema_version 含 011_layer1_tables
    失败含义：唯一已迁移建模层回退，test_layer5 与 ops inspect 基线断裂
    """
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    assert LAYER1_AXIS_TABLES.issubset(tables)
    versions = {row[0] for row in con.execute("SELECT version_id FROM schema_version").fetchall()}
    assert "011_layer1_tables" in versions


def test_migrationCoverage_cleanDomainTables_existAfter013() -> None:
    """覆盖范围：013 clean 域 disclosure/macro 表存在
    测试对象：apply_migrations 表清单
    目的/目标：R3H-06 三域 DDL 矩阵与 DuckDB 一致
    验证点：CLEAN_DOMAIN_MIGRATED_TABLES ⊆ tables
    失败含义：disclosure/macro clean 表缺失则 promote 路由无落盘表
    """
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    assert CLEAN_DOMAIN_MIGRATED_TABLES.issubset(tables)


def test_migrationCoverage_dcp05TierAClean_existsAfter015() -> None:
    """覆盖范围：015 DCP-05 Tier A clean 扩展表
    测试对象：apply_migrations + schema_version
    目的/目标：015_dcp05_tier_a_clean 落地 us_disclosure / crypto_derivative clean
    验证点：version_id 含 015；us_disclosure_clean 与 crypto_derivative_clean 存在
    失败含义：S00 015 未应用则 disclosure/crypto Tier A 增量无落盘表
    """
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    versions = {row[0] for row in con.execute("SELECT version_id FROM schema_version").fetchall()}
    assert "015_dcp05_tier_a_clean" in versions
    assert "us_disclosure_clean" in tables
    assert "crypto_derivative_clean" in tables
    assert "stg_us_disclosure_smoke" in tables
    assert "stg_crypto_derivative_smoke" in tables
