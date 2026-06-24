"""数据库迁移 005：摄取校验相关表测试。

覆盖范围：校验报告、源冲突、人工复核队列、质量日志等表
是否建好、字段约束是否生效、重复执行迁移是否安全。
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations, verify_applied_checksums


@pytest.fixture(scope="module")
def validation_module_db(tmp_path_factory):
    """ponytail: one migrated DB per module for DDL/INSERT contract tests (value unchanged)."""
    root = tmp_path_factory.mktemp("ingestion_validation")
    db_path = root / "module.duckdb"
    con = duckdb.connect(str(db_path))
    apply_migrations(con)
    con.close()
    return db_path


@pytest.fixture
def validation_con(validation_module_db):
    con = duckdb.connect(str(validation_module_db))
    yield con
    con.close()


# --- table existence -----------------------------------------------------


@pytest.mark.parametrize(
    "table_name",
    ["validation_report", "data_quality_log", "source_conflict", "manual_review_queue"],
)
def test_initDb_createsValidationTables(validation_con, table_name: str) -> None:
    """覆盖范围：全新数据库执行迁移后，摄取校验相关表是否建好
    测试对象：migration 005 创建的 {table_name} 表
    目的/目标：校验报告、源冲突、人工复核等核心表必须随迁移一并落地
    验证点：information_schema 能查到对应 table_name
    失败含义：校验表缺失，后续写入门禁与 WriteManager 无表可写
    """
    rows = validation_con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_name = ?",
        [table_name],
    ).fetchall()
    assert rows, f"migration 005 must create table {table_name!r}"


def test_initDb_runTwice_isIdempotent(validation_con) -> None:
    """覆盖范围：对同一数据库重复执行迁移是否安全、不重复建表
    测试对象：apply_migrations
    目的/目标：已应用过的迁移不得再次执行或重复登记版本记录
    验证点：第二次返回空列表；schema_version 中 005 仅一条记录
    失败含义：重复迁移破坏版本表或重复执行 DDL，升级路径不可信
    """
    # ponytail: reuse validation_module_db (migrations already applied once)
    second = apply_migrations(validation_con)
    assert second == [], f"second apply should skip applied migrations, got {second}"
    cnt = validation_con.execute(
        "SELECT COUNT(*) FROM schema_version WHERE version_id = '005_ingestion_validation'"
    ).fetchone()[0]
    assert cnt == 1


def test_initDb_doesNotModifyMigration004Checksum(validation_con) -> None:
    """覆盖范围：应用新迁移后，旧迁移的校验和记录是否仍有效
    测试对象：verify_applied_checksums 与 schema_version
    目的/目标：新迁移不得篡改已应用迁移的校验和，保证迁移链完整
    验证点：verify 不抛错；004 与 005 均在 schema_version 中
    失败含义：迁移链完整性校验失败，生产库升级可能静默漂移
    """
    verify_applied_checksums(validation_con)
    versions = validation_con.execute("SELECT version_id FROM schema_version").fetchall()
    vlist = {r[0] for r in versions}
    assert "004_ingestion_sources" in vlist
    assert "005_ingestion_validation" in vlist


# --- validation_report column / constraint enforcement -------------------


def test_validationReport_requiredFieldsEnforced(validation_con) -> None:
    """覆盖范围：校验报告表对必填字段的数据库层约束
    测试对象：validation_report 表 DDL
    目的/目标：只填主键、缺其他必填列的插入必须在数据库层被拒绝
    验证点：pytest.raises(duckdb.Error)
    失败含义：残缺校验报告能入库，写入门禁失去数据库层兜底
    """
    con = validation_con
    with pytest.raises(duckdb.Error):
        con.execute("INSERT INTO validation_report (validation_report_id) VALUES (?)", ["x"])


def test_validationReport_statusCheck_rejectsInvalidStatus(validation_con) -> None:
    """覆盖范围：校验报告状态字段只允许约定枚举值
    测试对象：validation_report 表 status 列 CHECK 约束
    目的/目标：非法状态值必须在写入数据库时被拒绝，不能悄悄入库
    验证点：status 为 BOGUS 的 INSERT 触发 duckdb.Error
    失败含义：非法状态入库，下游写入门禁无法按契约分支处理
    """
    con = validation_con
    with pytest.raises(duckdb.Error):
        con.execute(
            """
            INSERT INTO validation_report (
                validation_report_id, run_id, data_domain, source_id,
                status, checked_rows, failed_rows, warning_rows,
                can_write_clean, needs_manual_review,
                rule_set_id, rule_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                "vr-1",
                "r1",
                "market_bar_1d",
                "qmt",
                "BOGUS",
                1,
                0,
                0,
                True,
                False,
                "p0_round_1",
                "p0_round_1",
            ],
        )


def test_validationReport_validRows_accepted(validation_con) -> None:
    """覆盖范围：合法校验报告（通过、警告、失败三种状态）能否正常写入
    测试对象：validation_report INSERT
    目的/目标：契约允许的三种状态及对应写入许可组合都应被数据库接受
    验证点：写入 3 行后 COUNT(*) == 3
    失败含义：合法校验报告无法持久化，正式提交路径永远缺报告
    """
    con = validation_con
    for status, can_write, needs_review in [
        ("PASSED", True, False),
        ("WARNING", True, False),
        ("FAILED", False, True),
    ]:
        con.execute(
            """
            INSERT INTO validation_report (
                validation_report_id, run_id, data_domain, source_id,
                status, checked_rows, failed_rows, warning_rows,
                can_write_clean, needs_manual_review,
                rule_set_id, rule_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                f"vr-{status}",
                "r1",
                "market_bar_1d",
                "qmt",
                status,
                1,
                0,
                0,
                can_write,
                needs_review,
                "p0_round_1",
                "p0_round_1",
            ],
        )
    cnt = con.execute(
        """
        SELECT COUNT(*) FROM validation_report
        WHERE validation_report_id IN ('vr-PASSED', 'vr-WARNING', 'vr-FAILED')
        """
    ).fetchone()[0]
    assert cnt == 3


# --- source_conflict -----------------------------------------------------


def test_sourceConflict_requiredFieldsEnforced(validation_con) -> None:
    """覆盖范围：源冲突表对必填字段的数据库层约束
    测试对象：source_conflict 表 DDL
    目的/目标：只填冲突编号、缺其他必填列的插入必须失败
    验证点：pytest.raises(duckdb.Error)
    失败含义：残缺冲突记录入库，写入门禁无法判断冲突严重程度
    """
    con = validation_con
    with pytest.raises(duckdb.Error):
        con.execute("INSERT INTO source_conflict (conflict_id) VALUES (?)", ["c-1"])


def test_sourceConflict_validRow_accepted(validation_con) -> None:
    """覆盖范围：完整的多源冲突记录能否正常写入数据库
    测试对象：source_conflict INSERT
    目的/目标：含严重级别标记的合法冲突行应成功持久化，供后续门禁读取
    验证点：写入后 COUNT(*) == 1
    失败含义：合法冲突无法记录，多源对账审计链断裂
    """
    con = validation_con
    con.execute(
        """
        INSERT INTO source_conflict (
            conflict_id, run_id, data_domain, field_name,
            primary_source, primary_value, competing_source, competing_value,
            normalized_diff, tolerance_warning, tolerance_severe,
            severity, manual_review_required
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            "c-1",
            "r1",
            "market_bar_1d",
            "close",
            "qmt",
            "10.0",
            "baostock",
            "10.5",
            0.05,
            0.0005,
            0.002,
            "severe",
            True,
        ],
    )
    cnt = con.execute(
        "SELECT COUNT(*) FROM source_conflict WHERE conflict_id = ?", ["c-1"]
    ).fetchone()[0]
    assert cnt == 1


def test_sourceConflict_severityCheck_rejectsInvalid(validation_con) -> None:
    """覆盖范围：源冲突严重程度字段只允许约定枚举值
    测试对象：source_conflict severity 列 CHECK 约束
    目的/目标：非法严重程度值必须在数据库层被拒绝
    验证点：severity 为 totally_wrong 的 INSERT 触发 duckdb.Error
    失败含义：任意严重程度都能入库，严重冲突写入门禁失效
    """
    con = validation_con
    with pytest.raises(duckdb.Error):
        con.execute(
            """
            INSERT INTO source_conflict (
                conflict_id, run_id, data_domain, field_name,
                primary_source, primary_value, competing_source, competing_value,
                severity, manual_review_required
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                "c-x",
                "r1",
                "market_bar_1d",
                "close",
                "qmt",
                "10.0",
                "baostock",
                "10.5",
                "totally_wrong",
                False,
            ],
        )


# --- manual_review_queue -------------------------------------------------


def test_manualReviewQueue_requiredFieldsEnforced(validation_con) -> None:
    """覆盖范围：人工复核队列表对必填字段的数据库层约束
    测试对象：manual_review_queue 表 DDL
    目的/目标：只填复核编号、缺其他必填列的插入必须失败
    验证点：pytest.raises(duckdb.Error)
    失败含义：残缺复核队列项入库，运维无法追踪待审对象
    """
    con = validation_con
    with pytest.raises(duckdb.Error):
        con.execute("INSERT INTO manual_review_queue (review_id) VALUES (?)", ["mr-1"])


def test_manualReviewQueue_sourceObjectTypeCheck(validation_con) -> None:
    """覆盖范围：人工复核队列的对象类型字段只允许约定枚举值
    测试对象：manual_review_queue source_object_type 列 CHECK 约束
    目的/目标：非法对象类型必须在写入数据库时被拒绝
    验证点：source_object_type 为 not_a_valid_type 的 INSERT 触发 duckdb.Error
    失败含义：任意对象类型入库，复核界面与路由无法正确分类
    """
    con = validation_con
    with pytest.raises(duckdb.Error):
        con.execute(
            """
            INSERT INTO manual_review_queue (
                review_id, source_object_type, source_object_id, priority, status
            ) VALUES (?, ?, ?, ?, ?)
            """,
            ["mr-1", "not_a_valid_type", "c-1", "high", "open"],
        )


def test_manualReviewQueue_validRow_accepted(validation_con) -> None:
    """覆盖范围：合法的人工复核队列项能否正常写入数据库
    测试对象：manual_review_queue INSERT
    目的/目标：对象类型为冲突、字段完整的复核项应成功持久化
    验证点：写入后 COUNT(*) == 1
    失败含义：合法复核队列项无法创建，需人工复核的流程悬空
    """
    con = validation_con
    con.execute(
        """
        INSERT INTO manual_review_queue (
            review_id, source_object_type, source_object_id, priority, status
        ) VALUES (?, ?, ?, ?, ?)
        """,
        ["mr-1", "conflict", "c-1", "high", "OPEN"],
    )
    cnt = con.execute(
        "SELECT COUNT(*) FROM manual_review_queue WHERE review_id = ?", ["mr-1"]
    ).fetchone()[0]
    assert cnt == 1


# --- data_quality_log ----------------------------------------------------


def test_dataQualityLog_validRow_accepted(validation_con) -> None:
    """覆盖范围：数据质量明细日志能否正常写入数据库
    测试对象：data_quality_log INSERT
    目的/目标：关联校验报告的质量发现明细应成功持久化，供审计追溯
    验证点：写入后 COUNT(*) == 1
    失败含义：质量发现无法落库，校验报告缺少明细追溯
    """
    con = validation_con
    con.execute(
        """
        INSERT INTO data_quality_log (
            log_id, validation_report_id, run_id, data_domain, source_id,
            table_name, rule_id, severity, message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            "dq-1",
            "vr-1",
            "r1",
            "market_bar_1d",
            "qmt",
            "stg_x",
            "MISSING_PRIMARY_KEY",
            "failed",
            "primary key is null",
        ],
    )
    cnt = con.execute(
        "SELECT COUNT(*) FROM data_quality_log WHERE log_id = ?", ["dq-1"]
    ).fetchone()[0]
    assert cnt == 1


# --- init_db prod-path applies 005 ---------------------------------------


def test_initDb_prodPath_appliesMigration005(tmp_path: Path) -> None:
    """覆盖范围：用生产同款连接方式初始化数据库时，校验迁移是否生效
    测试对象：ConnectionManager 与 apply_migrations
    目的/目标：与生产一致的建库路径也必须应用 005 校验迁移
    验证点：schema_version 含 005_ingestion_validation
    失败含义：生产初始化路径漏掉校验迁移，生产库缺校验表
    """
    db = tmp_path / "prod.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    with cm.reader() as con:
        versions = {r[0] for r in con.execute("SELECT version_id FROM schema_version").fetchall()}
    assert "005_ingestion_validation" in versions
