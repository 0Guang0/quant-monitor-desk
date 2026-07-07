"""同步校验与写入流水线接缝测试（Round2 审计 A7-02）。

覆盖范围：staging 质量校验通过后才允许进入 clean 写入路径。
"""

from __future__ import annotations

from pathlib import Path

from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.sync.pipeline import SyncValidationPipeline, SyncWritePipeline
from backend.app.validators.data_quality import DataQualityRequest
from backend.app.db.write_manager import WriteRequest


def test_syncValidationPipeline_validateStaging_beforeWrite(tmp_path: Path) -> None:
    """覆盖范围：同步流水线中校验与写入的顺序
    测试对象：SyncValidationPipeline.validate_staging 与 SyncWritePipeline
    目的/目标：staging 里的数据要先过质量校验，通过后才允许写入 clean 正式表
    验证点：can_write_clean 为 True；WritePipeline.write_clean 可调用
    失败含义：校验和写入顺序乱了，脏数据可能直接进正式表
    """
    db = tmp_path / "pipeline.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
        con.execute(
            """
            CREATE TABLE stg_pipeline (
                instrument_id VARCHAR, trade_date VARCHAR, close DOUBLE,
                source_used VARCHAR, batch_id VARCHAR, source_id VARCHAR
            )
            """
        )
        con.execute(
            "INSERT INTO stg_pipeline VALUES (?, ?, ?, ?, ?, ?)",
            ["AAPL", "2026-06-15", 100.0, "baostock", "b1", "baostock"],
        )
        validation = SyncValidationPipeline(cm)
        result = validation.validate_staging(
            con,
            quality_request=DataQualityRequest(
                run_id="run-pipe",
                job_id="job-pipe",
                data_domain="market_bar_1d",
                source_id="baostock",
                staging_table="stg_pipeline",
                primary_keys=("instrument_id", "trade_date"),
                required_fields=("close", "source_used"),
                rule_set_id="p0_round_1",
            ),
            expected_columns=(
                "instrument_id",
                "trade_date",
                "close",
                "source_used",
                "batch_id",
                "source_id",
            ),
            timestamp_fields=("trade_date",),
        )
        assert result.quality.can_write_clean is True
        write = SyncWritePipeline(cm)
        con.execute(
            "CREATE TABLE security_bar_pipeline_clean AS SELECT * FROM stg_pipeline WHERE 1=0"
        )
        write_result = write.write_clean(
            con,
            WriteRequest(
                run_id="run-pipe",
                job_id="job-pipe",
                target_table="security_bar_pipeline_clean",
                staging_table="stg_pipeline",
                write_mode="append_only",
                primary_keys=("instrument_id", "trade_date"),
                validation_report_id=result.quality.validation_report_id,
                source_used="baostock",
                data_domain="market_bar_1d",
            ),
        )
        assert write_result.status == "SUCCESS"
        row = con.execute(
            "SELECT COUNT(*) FROM security_bar_pipeline_clean WHERE instrument_id = 'AAPL'"
        ).fetchone()
        assert row is not None and row[0] == 1


def test_syncValidationPipeline_qualityFail_blocksCleanWrite(tmp_path: Path) -> None:
    """覆盖范围：staging 质量校验失败时阻断 clean 写入
    测试对象：SyncValidationPipeline.validate_staging
    目的/目标：缺必填字段的 staging 不得进入 write_clean 路径
    验证点：can_write_clean=False；status=FAILED；clean 表行数保持 0
    失败含义：质量失败仍写 clean，脏数据进入正式表
    """
    db = tmp_path / "pipeline-fail.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
        con.execute(
            """
            CREATE TABLE stg_pipeline_fail (
                instrument_id VARCHAR, trade_date VARCHAR, close DOUBLE,
                source_used VARCHAR, batch_id VARCHAR, source_id VARCHAR
            )
            """
        )
        con.execute(
            "INSERT INTO stg_pipeline_fail VALUES (?, ?, ?, ?, ?, ?)",
            ["AAPL", "2026-06-15", None, "baostock", "b1", "baostock"],
        )
        con.execute(
            "CREATE TABLE security_bar_pipeline_fail_clean AS "
            "SELECT * FROM stg_pipeline_fail WHERE 1=0"
        )
        validation = SyncValidationPipeline(cm)
        result = validation.validate_staging(
            con,
            quality_request=DataQualityRequest(
                run_id="run-pipe-fail",
                job_id="job-pipe-fail",
                data_domain="market_bar_1d",
                source_id="baostock",
                staging_table="stg_pipeline_fail",
                primary_keys=("instrument_id", "trade_date"),
                required_fields=("close", "source_used"),
                rule_set_id="p0_round_1",
            ),
            expected_columns=(
                "instrument_id",
                "trade_date",
                "close",
                "source_used",
                "batch_id",
                "source_id",
            ),
            timestamp_fields=("trade_date",),
        )
        assert result.quality.can_write_clean is False
        assert result.quality.status == "FAILED"
        clean_count = con.execute(
            "SELECT COUNT(*) FROM security_bar_pipeline_fail_clean"
        ).fetchone()[0]
    assert clean_count == 0
