"""Batch C 端到端校验流（§8.8）：质量校验 → 源冲突 → 写 clean 表。"""

from __future__ import annotations

from pathlib import Path

from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.db.validation_gate import DbValidationGate
from backend.app.db.write_manager import WriteManager, WriteRequest
from backend.app.validators.data_quality import DataQualityRequest, DataQualityValidator
from backend.app.validators.source_conflict import (
    SourceConflictRequest,
    SourceConflictValidator,
)


def _cm(tmp_path: Path) -> ConnectionManager:
    cm = ConnectionManager(tmp_path / "batch_c_flow.duckdb")
    with cm.writer() as con:
        apply_migrations(con)
    return cm


def _create_flow_tables(con) -> None:
    con.execute(
        """
        CREATE TABLE stg_batch_c_flow (
            instrument_id VARCHAR,
            trade_date VARCHAR,
            close DOUBLE,
            source_used VARCHAR,
            batch_id VARCHAR,
            source_id VARCHAR
        )
        """
    )
    con.execute(
        """
        CREATE TABLE stg_batch_c_conflict_peer (
            source_id VARCHAR,
            instrument_id VARCHAR,
            trade_date VARCHAR,
            close DOUBLE
        )
        """
    )
    con.execute("CREATE TABLE clean_batch_c_flow AS SELECT * FROM stg_batch_c_flow WHERE 1=0")


def _quality_request() -> DataQualityRequest:
    return DataQualityRequest(
        run_id="run-flow",
        job_id="job-flow",
        data_domain="market_bar_1d",
        source_id="qmt",
        staging_table="stg_batch_c_flow",
        primary_keys=("instrument_id", "trade_date"),
        required_fields=("close", "source_used"),
        rule_set_id="p0_round_1",
    )


def _conflict_request() -> SourceConflictRequest:
    return SourceConflictRequest(
        run_id="run-flow",
        job_id="job-flow",
        data_domain="market_bar_1d",
        primary_source="qmt",
        validation_sources=("baostock",),
        key_fields=("instrument_id", "trade_date"),
        comparable_fields=("close",),
        tolerance_rule_set_id="p0_round_1",
    )


def _write_request(validation_report_id: str) -> WriteRequest:
    return WriteRequest(
        run_id="run-flow",
        job_id="job-flow",
        target_table="clean_batch_c_flow",
        staging_table="stg_batch_c_flow",
        write_mode="append_only",
        primary_keys=("instrument_id", "trade_date"),
        validation_report_id=validation_report_id,
        source_used="qmt",
        data_domain="market_bar_1d",
    )


FLOW_COLUMNS = (
    "instrument_id",
    "trade_date",
    "close",
    "source_used",
    "batch_id",
    "source_id",
)


def _validate_quality(con, request: DataQualityRequest | None = None):
    return DataQualityValidator().validate_table(
        con,
        request or _quality_request(),
        expected_columns=FLOW_COLUMNS,
        timestamp_fields=("trade_date",),
    )


def test_batchCFlow_validDataQualityAndNoSevereConflict_writesClean(
    tmp_path: Path,
) -> None:
    """覆盖范围：质量通过 + 冲突在容忍度内的完整写入路径
    测试对象：DataQualityValidator → SourceConflictValidator → WriteManager
    目的/目标：校验链全部通过后应成功写入 clean 表
    验证点：quality/conflict 均为 PASSED；write SUCCESS；clean 表 1 行
    失败含义：合法数据无法落库，Batch C 主路径断裂
    """
    cm = _cm(tmp_path)
    with cm.writer() as con:
        _create_flow_tables(con)
        con.execute(
            """
            INSERT INTO stg_batch_c_flow VALUES
                ('AAPL', '2026-06-15', 100.0, 'qmt', 'b1', 'qmt')
            """
        )
        con.execute(
            """
            INSERT INTO stg_batch_c_conflict_peer VALUES
                ('qmt', 'AAPL', '2026-06-15', 100.0),
                ('baostock', 'AAPL', '2026-06-15', 100.04)
            """
        )
        quality_report = _validate_quality(con)
        conflict_report = SourceConflictValidator().validate_table(
            con,
            _conflict_request(),
            staging_table="stg_batch_c_conflict_peer",
        )
        write_result = WriteManager(cm, DbValidationGate(cm)).write(
            _write_request(quality_report.validation_report_id),
            con=con,
            own_transaction=False,
        )
        clean_rows = con.execute("SELECT COUNT(*) FROM clean_batch_c_flow").fetchone()[0]

    assert quality_report.status == "PASSED"
    assert conflict_report.status == "PASSED"
    assert write_result.status == "SUCCESS"
    assert clean_rows == 1


def test_batchCFlow_invalidDataQuality_rejectsCleanAndPreservesAudit(
    tmp_path: Path,
) -> None:
    """覆盖范围：主键为空等质量失败时的 fail-closed 写入
    测试对象：WriteManager + DbValidationGate 对 FAILED 校验报告的处理
    目的/目标：质量不通过时禁止写 clean，但须保留审计痕迹
    验证点：quality FAILED、can_write_clean=False；clean 0 行；write_audit 记录 FAILED
    失败含义：坏数据仍能落库或审计丢失，数据质量门禁失效
    """
    cm = _cm(tmp_path)
    with cm.writer() as con:
        _create_flow_tables(con)
        con.execute(
            """
            INSERT INTO stg_batch_c_flow VALUES
                (NULL, '2026-06-15', 100.0, 'qmt', 'b1', 'qmt')
            """
        )
        quality_report = _validate_quality(con)
        write_result = WriteManager(cm, DbValidationGate(cm)).write(
            _write_request(quality_report.validation_report_id),
            con=con,
            own_transaction=False,
        )
        clean_rows = con.execute("SELECT COUNT(*) FROM clean_batch_c_flow").fetchone()[0]
        quality_log_rows = con.execute("SELECT COUNT(*) FROM data_quality_log").fetchone()[0]
        write_audit = con.execute(
            "SELECT status, validation_status FROM write_audit_log"
        ).fetchone()

    assert quality_report.status == "FAILED"
    assert quality_report.can_write_clean is False
    assert write_result.status == "FAILED"
    assert clean_rows == 0
    assert quality_log_rows >= 1
    assert write_audit == ("FAILED", "FAILED")


def test_batchCFlow_severeConflict_blocksCleanWrite(tmp_path: Path) -> None:
    """覆盖范围：质量通过但源冲突超阈值的写入阻断
    测试对象：SourceConflictValidator 严重冲突判定 + WriteManager 门禁
    目的/目标：主源与校验源价差过大时不得写 clean
    验证点：quality PASSED、conflict SEVERE_CONFLICT；write FAILED；clean 0 行
    失败含义：严重冲突数据仍能入库，多源一致性保障失效
    """
    cm = _cm(tmp_path)
    with cm.writer() as con:
        _create_flow_tables(con)
        con.execute(
            """
            INSERT INTO stg_batch_c_flow VALUES
                ('AAPL', '2026-06-15', 100.0, 'qmt', 'b1', 'qmt')
            """
        )
        con.execute(
            """
            INSERT INTO stg_batch_c_conflict_peer VALUES
                ('qmt', 'AAPL', '2026-06-15', 100.0),
                ('baostock', 'AAPL', '2026-06-15', 100.25)
            """
        )
        quality_report = _validate_quality(con)
        conflict_report = SourceConflictValidator().validate_table(
            con,
            _conflict_request(),
            staging_table="stg_batch_c_conflict_peer",
        )
        write_result = WriteManager(cm, DbValidationGate(cm)).write(
            _write_request(quality_report.validation_report_id),
            con=con,
            own_transaction=False,
        )
        clean_rows = con.execute("SELECT COUNT(*) FROM clean_batch_c_flow").fetchone()[0]

    assert quality_report.status == "PASSED"
    assert conflict_report.status == "SEVERE_CONFLICT"
    assert write_result.status == "FAILED"
    assert clean_rows == 0
