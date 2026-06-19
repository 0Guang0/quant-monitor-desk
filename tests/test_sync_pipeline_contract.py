"""Pipeline seam contract tests (Round2 re-audit A7-02)."""

from __future__ import annotations

from pathlib import Path

from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.sync.pipeline import SyncValidationPipeline, SyncWritePipeline
from backend.app.validators.data_quality import DataQualityRequest


def test_syncValidationPipeline_validateStaging_beforeWrite(tmp_path: Path) -> None:
    """Validation pipeline must run before write pipeline on staging data."""
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
