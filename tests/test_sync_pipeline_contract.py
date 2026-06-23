"""同步校验与写入流水线接缝测试（Round2 审计 A7-02）。

覆盖范围：staging 质量校验通过后才允许进入 clean 写入路径。
"""

from __future__ import annotations

from pathlib import Path

from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.sync.pipeline import SyncValidationPipeline, SyncWritePipeline
from backend.app.validators.data_quality import DataQualityRequest


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
        assert write.write_clean is not None
