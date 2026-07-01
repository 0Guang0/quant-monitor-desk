"""L3/L4/L5 建模表 migration 覆盖矩阵门禁（B3V-L5R / VR-MODEL-001 closure test）。"""

from __future__ import annotations

from pathlib import Path

import duckdb
from backend.app.db.migrate import MIGRATIONS_DIR, apply_migrations

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

L3_DESIGNED_TABLES = frozenset(
    {
        "industry_chain_registry",
        "industry_chain_anchor",
        "industry_chain_node",
        "industry_chain_edge",
        "industry_chain_cross_edge",
        "industry_chain_instrument_map",
        "industry_chain_event_anchor",
        "industry_chain_daily_snapshot",
    }
)

L4_DESIGNED_TABLES = frozenset(
    {
        "market_registry",
        "market_calendar",
        "market_index_snapshot",
        "market_sector_snapshot",
        "market_breadth_snapshot",
        "market_rule_event",
    }
)

L5_DEFERRED_MIGRATION_TABLES = frozenset()

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

MODELING_TABLES_WITHOUT_MIGRATION = (
    L3_DESIGNED_TABLES | L4_DESIGNED_TABLES
)


def _all_migration_sql_text() -> str:
    parts: list[str] = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def test_migrationCoverage_l3DesignedTables_haveNoMigration() -> None:
    """覆盖范围：第三层产业链表设计态 vs 已落地 migration
    测试对象：backend/app/db/migrations/*.sql DDL 文本
    目的/目标：L3 设计表不得在无 Round 3F 所有权时悄悄出现在 migration
    验证点：每张 L3_DESIGNED_TABLES 表名不出现在任何 migration SQL 中
    失败含义：建模表 migration 与 reconcile 矩阵/文档声称不一致
    """
    migration_text = _all_migration_sql_text()
    for table in L3_DESIGNED_TABLES:
        assert table not in migration_text, f"{table} found in migration SQL"


def test_migrationCoverage_l4DesignedTables_haveNoMigration() -> None:
    """覆盖范围：第四层市场结构表设计态 vs 已落地 migration
    测试对象：backend/app/db/migrations/*.sql DDL 文本
    目的/目标：L4 设计表须保持 staged-runtime-only，直到 Round 3F
    验证点：每张 L4_DESIGNED_TABLES 表名不出现在任何 migration SQL 中
    失败含义：市场结构表被提前迁移，VR-MODEL-001 矩阵与 MIGRATION_COVERAGE 失真
    """
    migration_text = _all_migration_sql_text()
    for table in L4_DESIGNED_TABLES:
        assert table not in migration_text, f"{table} found in migration SQL"


def test_migrationCoverage_l5DeferredTables_haveNoMigration() -> None:
    """覆盖范围：第五层 instrument/bar 设计表 vs migration 013（R3H-06）
    测试对象：backend/app/db/migrations/*.sql
    目的/目标：L5 bar 表由 013 落地后不再标 deferred
    验证点：L5_MIGRATED_TABLES 出现在 migration SQL；L5_DEFERRED 为空
    失败含义：L5 迁移与矩阵文档不一致
    """
    assert not L5_DEFERRED_MIGRATION_TABLES
    migration_text = _all_migration_sql_text()
    for table in L5_MIGRATED_TABLES:
        assert table in migration_text, f"{table} missing from migration SQL"


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


def test_migrationCoverage_futurePhaseTables_absentAfterFullMigrate() -> None:
    """覆盖范围：全量迁移后 L3/L4/L5 设计表仍不存在于 DuckDB
    测试对象：apply_migrations 后的表清单
    目的/目标：designed 表不得被误标为 implemented(migration)
    验证点：MODELING_TABLES_WITHOUT_MIGRATION 与 tables 无交集
    失败含义：reconcile 矩阵 deferred 行与真实库结构矛盾
    """
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    overlap = MODELING_TABLES_WITHOUT_MIGRATION.intersection(tables)
    assert not overlap, f"unexpected modeling tables migrated: {sorted(overlap)}"


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


def test_migrationCoverage_matrixDocPath_exists() -> None:
    """覆盖范围：VR-MODEL-001 矩阵 SSOT 文件可达
    测试对象：.trellis/tasks/archive/2026-07/round3v-layer5-model-schema-reconcile/research/l5-reconcile-matrix.md
    目的/目标：closure test 须能指向落盘矩阵，防止仅 pytest 过关无文档
    验证点：矩阵文件存在且含 VR-MODEL-001 与 VR-L5-001 关键字
    失败含义：registry proposed delta 引用的矩阵路径断裂
    """
    repo_root = Path(__file__).resolve().parents[1]
    matrix = (
        repo_root
        / ".trellis/tasks/archive/2026-07/round3v-layer5-model-schema-reconcile/research/l5-reconcile-matrix.md"
    )
    assert matrix.is_file()
    text = matrix.read_text(encoding="utf-8")
    assert "VR-MODEL-001" in text
    assert "VR-L5-001" in text
