"""Shared fixtures for incremental/backfill orchestration tests."""

from __future__ import annotations

from pathlib import Path

from backend.app.datasources.base_adapter import BaseDataAdapter
from backend.app.datasources.fetch_result import FetchRequest, FetchResult
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.sync.jobs import SyncJobSpec
from backend.app.sync.orchestrator import DataSyncOrchestrator

STG_TABLE = "stg_batch_d_flow"
CONFLICT_STG = "stg_batch_d_conflict_peer"
CLEAN_TABLE = "clean_batch_d_flow"


class BatchDIncrementalAdapter(BaseDataAdapter):
    """Test adapter: seeds staging on fetch."""

    source_id = "baostock"
    supported_domains = frozenset({"market_bar_1d"})
    _seed_row: tuple = ("AAPL", "2026-06-15", 100.0, "baostock", "b1", "baostock")
    _conflict_peer_rows: tuple[tuple, ...] = (
        ("baostock", "AAPL", "2026-06-15", 100.0),
        ("qmt_xtdata", "AAPL", "2026-06-15", 100.04),
    )

    def fetch(self, req: FetchRequest, *, con, job_id: str | None = None) -> FetchResult:
        con.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {STG_TABLE} (
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
            f"""
            CREATE TABLE IF NOT EXISTS {CONFLICT_STG} (
                source_id VARCHAR,
                instrument_id VARCHAR,
                trade_date VARCHAR,
                close DOUBLE
            )
            """
        )
        con.execute(
            f"CREATE TABLE IF NOT EXISTS {CLEAN_TABLE} AS SELECT * FROM {STG_TABLE} WHERE 1=0"
        )
        con.execute(f"DELETE FROM {STG_TABLE}")
        con.execute(f"INSERT INTO {STG_TABLE} VALUES (?, ?, ?, ?, ?, ?)", list(self._seed_row))
        con.execute(f"DELETE FROM {CONFLICT_STG}")
        for row in self._conflict_peer_rows:
            con.execute(f"INSERT INTO {CONFLICT_STG} VALUES (?, ?, ?, ?)", list(row))
        return super().fetch(req, con=con, job_id=job_id)

    def _fetch_impl(self, req: FetchRequest) -> FetchResult:
        return FetchResult(
            run_id=req.run_id,
            source_id=self.source_id,
            data_domain=req.data_domain,
            status="SUCCESS",
            row_count=1,
            fetch_time="2026-06-17T10:00:00Z",
            staging_table=STG_TABLE,
            raw_file_paths=["/tmp/batch_d.parquet"],
            content_hash="abc",
            schema_hash="def",
        )


def _orch_stack(
    tmp_path: Path, registry_yaml_fixture: Path
) -> tuple[DataSyncOrchestrator, BatchDIncrementalAdapter]:
    cm = ConnectionManager(tmp_path / "batch_d.duckdb")
    with cm.writer() as con:
        apply_migrations(con)
    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    with cm.writer() as con:
        reg.sync_to_db(con, tombstone_missing=False)
    return DataSyncOrchestrator(cm), BatchDIncrementalAdapter(reg)


def _incremental_spec(job_id: str = "job-inc-d") -> SyncJobSpec:
    return SyncJobSpec(
        run_id="run-batch-d",
        job_id=job_id,
        job_type="incremental",
        data_domain="market_bar_1d",
        market_id="CN_A",
        source_id="baostock",
        adapter_id="baostock",
        date_start=None,
        date_end=None,
        instrument_id="AAPL",
        partition_key=None,
        trigger_reason=None,
    )
