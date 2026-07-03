"""Round 3F B3F-MIG：migration 残余校验（R3F-MIG-01..06）。"""

from __future__ import annotations

import re
from pathlib import Path

import duckdb
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.db.migrate import MIGRATIONS_DIR, apply_migrations

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MIGRATION_009 = MIGRATIONS_DIR / "009_status_check_constraints.sql"
MIGRATION_012 = MIGRATIONS_DIR / "012_migration_residuals.sql"
ADR_002 = PROJECT_ROOT / "docs/decisions/ADR-002-db-check-vs-app-validation.md"
MIGRATION_COVERAGE = PROJECT_ROOT / "docs/schema/MIGRATION_COVERAGE.md"
MIGRATION_008_PLAN = PROJECT_ROOT / "docs/schema/MIGRATION_008_PLAN.md"
ROADMAP = PROJECT_ROOT / "PROJECT_IMPLEMENTATION_ROADMAP.md"
from tests.repo_paths import ROUND3_BATCH_IMPLEMENTATION_MAP as ROUND3_MAP


def test_r3fMig01_migration009_statusChecks_present_verifyOnly() -> None:
    """覆盖范围：009 已落地的 status CHECK 不得被 B3F-MIG 重复实现
    测试对象：009_status_check_constraints.sql 与 012 迁移目录
    目的/目标：R3F-MIG-01 仅 verify；009 的 CHECK 仍存在于磁盘且无第二份重复 migration
    验证点：009 含 fetch_log/manual_review_queue CHECK；不存在 013 重复 status CHECK 文件
    失败含义：重复实现已关 CHECK，与 playbook §8.1 负向边界冲突
    """
    text_009 = MIGRATION_009.read_text(encoding="utf-8")
    assert "fetch_log_v2" in text_009
    assert "manual_review_queue_v2" in text_009
    assert "CHECK" in text_009
    duplicate = MIGRATIONS_DIR / "013_status_check_constraints.sql"
    assert not duplicate.is_file()


def test_r3fMig02_manualReviewPriority_appLayerOnly_documented() -> None:
    """覆盖范围：manual_review_queue.priority 应用层校验策略
    测试对象：ADR-002 与 DuckDB manual_review_queue DDL
    目的/目标：R3F-MIG-02 接受 app-layer：DB 无 priority CHECK 且 ADR 明文记录
    验证点：012 重建 DDL 无 priority CHECK；ADR-002 含 priority 与 R2-RISK-4 说明
    失败含义：priority 策略未闭合，registry A9-P2-01/R2-RISK-4 仍悬空
    """
    assert MIGRATION_012.is_file()
    text_012 = MIGRATION_012.read_text(encoding="utf-8")
    mrq_match = re.search(
        r"CREATE TABLE IF NOT EXISTS manual_review_queue_v3\s*\((.*?)\);",
        text_012,
        re.DOTALL,
    )
    assert mrq_match is not None
    mrq_ddl = mrq_match.group(1)
    assert "priority            VARCHAR" in mrq_ddl
    assert not re.search(r"priority\s+VARCHAR\s+CHECK", mrq_ddl, re.IGNORECASE)
    adr = ADR_002.read_text(encoding="utf-8")
    assert "manual_review_queue.priority" in adr
    assert "R2-RISK-4" in adr
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    con.execute(
        """
        INSERT INTO manual_review_queue (
            review_id, source_object_type, source_object_id, priority, status
        ) VALUES (?, ?, ?, ?, ?)
        """,
        ["mr-priority-app", "conflict", "c-1", "not_a_db_enum", "OPEN"],
    )
    row = con.execute(
        "SELECT priority FROM manual_review_queue WHERE review_id = ?", ["mr-priority-app"]
    ).fetchone()
    assert row[0] == "not_a_db_enum"


def test_r3fMig03_fetchLogAndManualReview_rebuildUsesExplicitColumns() -> None:
    """覆盖范围：fetch_log 与 manual_review_queue 的 012 重建 hygiene
    测试对象：012_migration_residuals.sql
    目的/目标：R3F-MIG-03 关闭 A9-P3-01 残余；重建不得使用 SELECT *
    验证点：012 含显式列 INSERT；不含 fetch_log/manual_review 的 SELECT * 回放
    失败含义：列漂移时 SELECT * 静默丢列，migration review 无法 sign-off
    """
    text = MIGRATION_012.read_text(encoding="utf-8")
    assert "INSERT INTO fetch_log_v3" in text
    assert "INSERT INTO manual_review_queue_v3" in text
    assert re.search(r"INSERT INTO fetch_log_v3\s*\([^)]+\)\s*SELECT", text, re.DOTALL)
    assert re.search(
        r"INSERT INTO manual_review_queue_v3\s*\([^)]+\)\s*SELECT", text, re.DOTALL
    )
    for block in ("fetch_log", "manual_review_queue"):
        section = text.split(f"INSERT INTO {block}_v3", maxsplit=1)[-1].split(
            "DROP TABLE", maxsplit=1
        )[0]
        assert "SELECT *" not in section, f"{block} rebuild still uses SELECT *"


def test_r3fMig04_sourceRegistry_lifecycleColumns_existAfterMigrate(
    tmp_path, migrated_con, registry_yaml_fixture
) -> None:
    """覆盖范围：source_registry 生命周期审计列 migration + sync
    测试对象：012 列与 SourceRegistry.sync_to_db
    目的/目标：R3F-MIG-04 落地 registry_generation / removed_from_yaml_at
    验证点：列存在；sync 写入 generation>0 且二次 sync 递增；tombstone 写入 removed_from_yaml_at
    失败含义：D2-P3-1 仍 DEFERRED，YAML 墓碑无审计时间戳
    """
    con = migrated_con(tmp_path)
    cols = {
        row[0]
        for row in con.execute(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'source_registry'
            """
        ).fetchall()
    }
    assert "registry_generation" in cols
    assert "removed_from_yaml_at" in cols
    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    reg.sync_to_db(con)
    gen1 = con.execute(
        "SELECT registry_generation FROM source_registry WHERE source_id='baostock'"
    ).fetchone()[0]
    assert gen1 is not None and int(gen1) >= 1
    reg.sync_to_db(con)
    gen2 = con.execute(
        "SELECT registry_generation FROM source_registry WHERE source_id='baostock'"
    ).fetchone()[0]
    assert gen2 is not None and int(gen2) > int(gen1)
    con.execute(
        """
        INSERT INTO source_registry (source_id, source_name, is_enabled)
        VALUES ('orphan_source', 'Orphan', true)
        """
    )
    reg.sync_to_db(con, tombstone_missing=True)
    row = con.execute(
        """
        SELECT is_enabled, removed_from_yaml_at
        FROM source_registry WHERE source_id='orphan_source'
        """
    ).fetchone()
    assert row[0] is False
    assert row[1] is not None


def test_r3fMig05_migrationCoverage_routes008To009To3f() -> None:
    """覆盖范围：008/009/3F migration 路由文档
    测试对象：MIGRATION_COVERAGE.md 与 MIGRATION_008_PLAN.md
    目的/目标：R3F-MIG-05 将残余项路由到 009-resolved / 3F-open / wont-fix 桶
    验证点：COVERAGE 四桶表行含 009-resolved、3F-open→closed、wont-fix、Deferred；
        008 PLAN 标明 009 superseded 且 012 闭合 Round 3F 残余
    失败含义：审计矩阵与 roadmap R3F-MIG-05 不一致，主会话无法 registry 对齐
    """
    coverage = MIGRATION_COVERAGE.read_text(encoding="utf-8")
    plan = MIGRATION_008_PLAN.read_text(encoding="utf-8")
    routing = coverage.split("## Round 3F routing", maxsplit=1)[1]
    assert "**009-resolved**" in routing
    assert "fetch_log.status" in routing
    assert "009_status_check_constraints.sql" in routing
    assert "3F-open" in routing
    assert "registry_generation" in routing
    assert "**012**" in routing
    assert "wont-fix" in routing
    assert "manual_review_queue.priority" in routing
    assert "R2-RISK-4" in routing
    assert "**Deferred**" in routing
    assert "source_health_snapshot" in routing
    assert "B3F-SH" in routing
    assert "partially superseded by **009**" in plan
    assert "**012**" in plan
    assert "closed round 3f" in plan.lower()
    assert "Closed Round 3F:" in plan


def test_r3fMig06_partial5_regressionGuard_noReopenAsActive() -> None:
    """覆盖范围：R3-PARTIAL-5 crash-window 不得被 roadmap 重开为实现任务
    测试对象：ROUND3_BATCH_IMPLEMENTATION_MAP.md R3-PARTIAL-5 行（regression guard SSOT）
    目的/目标：R3F-MIG-06 verify-only；B3V 已关 path A 仅保留 regression guard
    验证点：R3-PARTIAL-5 标记 CLOSED B3V；closure 为 do not reopen / regression guard
    失败含义：地图误导后续 agent 重复实现 crash-window，违反 BATCH_3F §3
    """
    map_text = ROUND3_MAP.read_text(encoding="utf-8")
    partial5 = map_text.split("R3-PARTIAL-5", maxsplit=1)[1].split("\n", maxsplit=1)[0]
    assert "CLOSED B3V" in partial5.upper()
    assert "do not reopen" in partial5.lower()
