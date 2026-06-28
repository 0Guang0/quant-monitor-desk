"""DbValidationGate：依据 validation_report 等库内状态决定是否允许 WriteManager 写入。"""

from __future__ import annotations

from pathlib import Path

import pytest
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.db.validation_gate import (
    DbValidationGate,
    ValidationGateError,
    ValidationRejected,
)


def _setup(tmp_path: Path) -> ConnectionManager:
    db = tmp_path / "gate.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    return cm


def _insert_report(
    cm: ConnectionManager,
    report_id: str,
    *,
    status: str,
    can_write_clean: bool,
    needs_manual_review: bool,
    checked_rows: int = 1,
    failed_rows: int = 0,
    warning_rows: int = 0,
    run_id: str = "r1",
) -> None:
    with cm.writer() as con:
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
                report_id,
                run_id,
                "market_bar_1d",
                "qmt",
                status,
                checked_rows,
                failed_rows,
                warning_rows,
                can_write_clean,
                needs_manual_review,
                "p0_round_1",
                "p0_round_1",
            ],
        )


def test_missingReport_raisesGateError(tmp_path: Path) -> None:
    """覆盖范围：validation_report 行不存在
    测试对象：DbValidationGate.assert_can_write
    目的/目标：没有校验报告时，一律禁止往正式表写入
    验证点：未知 ID 触发 ValidationGateError，且 exc.validation_report_id 与入参一致
    失败含义：缺失报告仍可能写库，校验门形同虚设
    """
    cm = _setup(tmp_path)
    gate = DbValidationGate(cm)
    with pytest.raises(ValidationGateError) as exc:
        gate.assert_can_write("does-not-exist", "append_only")
    assert exc.value.validation_report_id == "does-not-exist"


def test_failedReport_rejected(tmp_path: Path) -> None:
    """覆盖范围：status=FAILED 的校验报告
    测试对象：DbValidationGate 对 FAILED 行
    目的/目标：失败报告必须拒绝任何 clean 写入
    验证点：vr-failed 触发 ValidationRejected，异常携带同一 report_id
    失败含义：校验已判失败仍能落库，脏数据可能进入正式表
    """
    cm = _setup(tmp_path)
    _insert_report(
        cm,
        "vr-failed",
        status="FAILED",
        can_write_clean=False,
        needs_manual_review=True,
        failed_rows=1,
    )
    gate = DbValidationGate(cm)
    with pytest.raises(ValidationRejected) as exc:
        gate.assert_can_write("vr-failed", "append_only")
    assert exc.value.validation_report_id == "vr-failed"


def test_canWriteCleanFalse_rejected(tmp_path: Path) -> None:
    """覆盖范围：can_write_clean=false 非 FAILED 报告
    测试对象：DbValidationGate 对 WARNING 且不可写行
    目的/目标：报告标明不可写入时，不论表面状态如何都必须拒绝
    验证点：can_write_clean=false 的 WARNING 行触发 ValidationRejected
    失败含义：质量未达标却被允许写入，数据质量合约失效
    """
    cm = _setup(tmp_path)
    _insert_report(
        cm,
        "vr-no-write",
        status="WARNING",
        can_write_clean=False,
        needs_manual_review=False,
    )
    gate = DbValidationGate(cm)
    with pytest.raises(ValidationRejected):
        gate.assert_can_write("vr-no-write", "append_only")


def test_needsManualReviewTrue_rejected(tmp_path: Path) -> None:
    """覆盖范围：needs_manual_review=true
    测试对象：DbValidationGate 对手工复核标记
    目的/目标：需要人工复核的数据，不得自动写入正式表
    验证点：vr-review 触发 ValidationRejected
    失败含义：待复核数据自动落库，审计与合规链路断裂
    """
    cm = _setup(tmp_path)
    _insert_report(
        cm,
        "vr-review",
        status="WARNING",
        can_write_clean=True,
        needs_manual_review=True,
    )
    gate = DbValidationGate(cm)
    with pytest.raises(ValidationRejected):
        gate.assert_can_write("vr-review", "append_only")


def test_passedReport_canWriteCleanTrue_allows(tmp_path: Path) -> None:
    """覆盖范围：PASSED 且可写报告
    测试对象：DbValidationGate.assert_can_write 正常放行
    目的/目标：校验全部通过且允许写入时，应放行写入
    验证点：vr-pass 调用成功且返回 status == 'PASSED'
    失败含义：合格报告被误拒，正常数据同步无法推进
    """
    cm = _setup(tmp_path)
    _insert_report(
        cm,
        "vr-pass",
        status="PASSED",
        can_write_clean=True,
        needs_manual_review=False,
    )
    gate = DbValidationGate(cm)
    status = gate.assert_can_write("vr-pass", "append_only")
    assert status == "PASSED"


def test_warningReport_canWriteTrue_noReview_allows(tmp_path: Path) -> None:
    """覆盖范围：WARNING 显式放行策略
    测试对象：DbValidationGate 对 WARNING 可写无复核行
    目的/目标：带警告但明确允许写入、且无需人工复核时，可以落库
    验证点：can_write_clean=true 且 needs_manual_review=false 的 WARNING 返回 status=='WARNING'
    失败含义：带警告数据的放行策略与校验流程合约不一致，可能误拒或误放
    """
    cm = _setup(tmp_path)
    _insert_report(
        cm,
        "vr-warn-ok",
        status="WARNING",
        can_write_clean=True,
        needs_manual_review=False,
        warning_rows=2,
    )
    gate = DbValidationGate(cm)
    status = gate.assert_can_write("vr-warn-ok", "upsert_by_pk")
    assert status == "WARNING"


def test_openSevereConflict_rejectsEvenWhenReportPassed(tmp_path: Path) -> None:
    """覆盖范围：OPEN severe source_conflict 与 PASSED 报告并存
    测试对象：DbValidationGate 冲突表联动检查
    目的/目标：同一批次仍有未解决的严重数据源冲突时，即使校验报告通过也不得写入
    验证点：插入 severe OPEN 冲突后 assert_can_write 抛出 ValidationRejected（含 severe）
    失败含义：严重源冲突被忽略，多源 reconcile 门禁失效
    """
    cm = _setup(tmp_path)
    _insert_report(
        cm,
        "vr-conflict",
        status="PASSED",
        can_write_clean=True,
        needs_manual_review=False,
        run_id="run-blocked",
    )
    with cm.writer() as con:
        con.execute(
            """
            INSERT INTO source_conflict (
                conflict_id, run_id, job_id, data_domain, field_name,
                primary_source, competing_source, severity, reconcile_status,
                manual_review_required
            ) VALUES (
                'c1', 'run-blocked', 'j1', 'market_bar_1d', 'close',
                'qmt', 'baostock', 'severe', 'OPEN', false
            )
            """
        )
    gate = DbValidationGate(cm)
    with pytest.raises(ValidationRejected, match="severe"):
        gate.assert_can_write("vr-conflict", "append_only")


def test_warningReport_canWriteFalse_rejected(tmp_path: Path) -> None:
    """覆盖范围：WARNING 且 can_write_clean=false
    测试对象：DbValidationGate 对 WARNING 不可写行
    目的/目标：带警告且不可写入的报告，必须与通过报告一样被拒绝
    验证点：vr-warn-no 触发 ValidationRejected
    失败含义：带警告且不可写的报告仍写入，数据质量无保障
    """
    cm = _setup(tmp_path)
    _insert_report(
        cm,
        "vr-warn-no",
        status="WARNING",
        can_write_clean=False,
        needs_manual_review=False,
    )
    gate = DbValidationGate(cm)
    with pytest.raises(ValidationRejected):
        gate.assert_can_write("vr-warn-no", "append_only")


def test_dbValidationGate_isNotStubBehavior(tmp_path: Path) -> None:
    """覆盖范围：生产 gate 非 stub 短路
    测试对象：DbValidationGate 对 stub-pass 前缀 ID
    目的/目标：生产环境不得凭测试用报告编号绕过真实库校验
    验证点：无行时 stub-pass-1 抛 ValidationGateError；插入真实 PASSED 行后同 ID 允许
    失败含义：生产环境仍走测试短路，校验结果与数据库实际状态脱节
    """
    cm = _setup(tmp_path)
    gate = DbValidationGate(cm)
    # stub-style ids that StubValidationGate would pass must be unknown to DbValidationGate.
    with pytest.raises(ValidationGateError):
        gate.assert_can_write("stub-pass-1", "append_only")
    _insert_report(
        cm,
        "stub-pass-1",
        status="PASSED",
        can_write_clean=True,
        needs_manual_review=False,
    )
    # Now that a real row exists, the same id must be allowed.
    gate.assert_can_write("stub-pass-1", "append_only")


@pytest.mark.parametrize(
    "suffix",
    [".csv", ".parquet", ".json"],
    ids=["csv", "parquet", "json"],
)
def test_missingSchemaHashOnStructuredFetch_rejects(
    tmp_path: Path, suffix: str
) -> None:
    """覆盖范围：结构化 fetch_log 缺 schema_hash 时 gate fail-closed（三后缀）
    测试对象：DbValidationGate._schema_hash_blocks_write
    目的/目标：AC-DATA-03 — SUCCESS 且 row_count>0 的结构化路径不得因 NULL hash 放行
    验证点：PASSED 报告 + fetch_log schema_hash=NULL + .csv/.parquet/.json 路径 → ValidationRejected
    失败含义：gate fail-open，结构化源可绕过 schema drift 检查写入 clean 表
    """
    cm = _setup(tmp_path)
    report_id = f"vr-missing-hash-{suffix.lstrip('.')}"
    _insert_report(
        cm,
        report_id,
        status="PASSED",
        can_write_clean=True,
        needs_manual_review=False,
    )
    raw_paths = f'["/data/raw/qmt/a{suffix}"]'
    with cm.writer() as con:
        con.execute(
            """
            INSERT INTO fetch_log (
                fetch_id, run_id, job_id, source_id, data_domain, status, row_count,
                schema_hash, raw_file_paths, fetch_time
            ) VALUES (
                ?, 'r1', 'j1', 'qmt', 'market_bar_1d', 'SUCCESS', 1,
                NULL, ?, CURRENT_TIMESTAMP
            )
            """,
            [f"fetch-mh-{suffix.lstrip('.')}", raw_paths],
        )
        con.execute(
            "UPDATE validation_report SET job_id = 'j1', source_id = 'qmt' "
            f"WHERE validation_report_id = '{report_id}'"
        )
    gate = DbValidationGate(cm)
    with pytest.raises(ValidationRejected, match="schema_hash"):
        gate.assert_can_write(report_id, "append_only")


def test_missingSchemaHash_registryFallback_rejects(tmp_path: Path) -> None:
    """覆盖范围：无路径后缀时 file_registry 结构化回退仍 fail-closed
    测试对象：DbValidationGate._fetch_log_is_structured registry 分支
    目的/目标：G-03 — raw_file_paths 空且 registry 有 structured file_type 时缺 hash 须拒绝
    验证点：file_registry parquet 行 + fetch_log 无后缀路径 + schema_hash=NULL → ValidationRejected
    失败含义：registry 回退分支未纳入 structured 判定，gate 对缺 hash 放行
    """
    cm = _setup(tmp_path)
    _insert_report(
        cm,
        "vr-missing-hash-reg",
        status="PASSED",
        can_write_clean=True,
        needs_manual_review=False,
    )
    with cm.writer() as con:
        con.execute(
            """
            INSERT INTO file_registry (
                file_id, file_type, source, local_path, content_hash, schema_hash,
                fetch_time, as_of_timestamp, parse_status, quality_flag
            ) VALUES (
                'f-structured', 'parquet', 'qmt', '/data/raw/qmt/legacy.parquet',
                'hash1', 'schema-v1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
                'parsed', 'ok'
            )
            """
        )
        con.execute(
            """
            INSERT INTO fetch_log (
                fetch_id, run_id, job_id, source_id, data_domain, status, row_count,
                schema_hash, raw_file_paths, fetch_time
            ) VALUES (
                'fetch-mh-reg', 'r1', 'j1', 'qmt', 'market_bar_1d', 'SUCCESS', 1,
                NULL, '[]', CURRENT_TIMESTAMP
            )
            """
        )
        con.execute(
            "UPDATE validation_report SET job_id = 'j1', source_id = 'qmt' "
            "WHERE validation_report_id = 'vr-missing-hash-reg'"
        )
    gate = DbValidationGate(cm)
    with pytest.raises(ValidationRejected, match="schema_hash"):
        gate.assert_can_write("vr-missing-hash-reg", "append_only")


def test_schemaHashDriftWithoutApproval_rejects(tmp_path: Path) -> None:
    """覆盖范围：file_registry 与 fetch_log schema_hash 漂移
    测试对象：DbValidationGate write_contract schema_hash 检查
    目的/目标：历史数据结构与本次抓取结构不一致且未经审批时，必须拒绝写入
    验证点：注册 baseline schema-v1、fetch schema-v2 后抛出 ValidationRejected（含 schema_hash）
    失败含义：未审批的 schema 漂移可写入，下游表结构 silently 变化
    """
    cm = _setup(tmp_path)
    _insert_report(
        cm,
        "vr-drift",
        status="PASSED",
        can_write_clean=True,
        needs_manual_review=False,
    )
    with cm.writer() as con:
        con.execute(
            """
            INSERT INTO file_registry (
                file_id, file_type, source, local_path, content_hash, schema_hash,
                fetch_time, as_of_timestamp, parse_status, quality_flag
            ) VALUES (
                'f-baseline', 'json', 'qmt', '/data/raw/qmt/a.json', 'hash1', 'schema-v1',
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'parsed', 'ok'
            )
            """
        )
        con.execute(
            """
            INSERT INTO fetch_log (
                fetch_id, run_id, job_id, source_id, data_domain, status, row_count,
                schema_hash, fetch_time
            ) VALUES (
                'fetch-1', 'r1', 'j1', 'qmt', 'market_bar_1d', 'SUCCESS', 1,
                'schema-v2', CURRENT_TIMESTAMP
            )
            """
        )
        con.execute(
            "UPDATE validation_report SET job_id = 'j1', source_id = 'qmt' "
            "WHERE validation_report_id = 'vr-drift'"
        )
    gate = DbValidationGate(cm)
    with pytest.raises(ValidationRejected, match="schema_hash"):
        gate.assert_can_write("vr-drift", "append_only")


def test_schemaHashDriftFlagInQualityFlags_rejects(tmp_path: Path) -> None:
    """覆盖范围：quality_flags 含 SCHEMA_DRIFT
    测试对象：DbValidationGate 对 quality_flags JSON
    目的/目标：校验报告已标记数据结构漂移时，必须拒绝写入
    验证点：quality_flags='["SCHEMA_DRIFT"]' 的 PASSED 行触发 ValidationRejected（schema_hash）
    失败含义：漂移标记被忽略，gate 与 validator 语义不一致
    """
    cm = _setup(tmp_path)
    with cm.writer() as con:
        con.execute(
            """
            INSERT INTO validation_report (
                validation_report_id, run_id, job_id, data_domain, source_id,
                status, checked_rows, failed_rows, warning_rows,
                can_write_clean, needs_manual_review,
                rule_set_id, rule_version, quality_flags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                "vr-flag",
                "r1",
                "j1",
                "market_bar_1d",
                "qmt",
                "PASSED",
                1,
                0,
                0,
                True,
                False,
                "p0_round_1",
                "p0_round_1",
                '["SCHEMA_DRIFT"]',
            ],
        )
    gate = DbValidationGate(cm)
    with pytest.raises(ValidationRejected, match="schema_hash"):
        gate.assert_can_write("vr-flag", "append_only")


def test_dbValidationGate_writeManagerIntegration_rejectsFailed(tmp_path: Path) -> None:
    """覆盖范围：WriteManager 注入 DbValidationGate 集成
    测试对象：WriteManager.write + DbValidationGate
    目的/目标：校验失败的报告经写入管理器提交时，必须整体失败且正式表行数不变
    验证点：res.status=='FAILED'；target_clean 行数仍为 0
    失败含义：写入管理器绕过 DB gate，失败校验仍可能落库
    """
    from backend.app.db.write_manager import WriteManager, WriteRequest

    cm = _setup(tmp_path)
    with cm.writer() as con:
        con.execute("CREATE TABLE target_clean AS SELECT * FROM stg_foundation_smoke WHERE 1=0")
        from tests.db_helpers import insert_stg_foundation_smoke_row

        insert_stg_foundation_smoke_row(con, "AAPL", "2026-06-15", 195.0)
    _insert_report(
        cm,
        "vr-fail-2",
        status="FAILED",
        can_write_clean=False,
        needs_manual_review=True,
        failed_rows=1,
    )
    wm = WriteManager(cm, DbValidationGate(cm))
    req = WriteRequest(
        run_id="r1",
        job_id="j1",
        target_table="target_clean",
        staging_table="stg_foundation_smoke",
        write_mode="append_only",
        primary_keys=("instrument_id", "trade_date"),
        validation_report_id="vr-fail-2",
        source_used="qmt",
        data_domain="cn_equity_daily_bar",
    )
    res = wm.write(req)
    assert res.status == "FAILED"
    with cm.reader() as r:
        assert r.execute("SELECT COUNT(*) FROM target_clean").fetchone()[0] == 0
