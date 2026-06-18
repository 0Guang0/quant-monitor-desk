"""Batch D incremental orchestration E2E (§8.5)."""

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
    """Test adapter: seeds staging on fetch (§6.5 — staging only via adapter.fetch)."""

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
            f"CREATE TABLE IF NOT EXISTS {CLEAN_TABLE} "
            f"AS SELECT * FROM {STG_TABLE} WHERE 1=0"
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


class BatchDBadQualityAdapter(BatchDIncrementalAdapter):
    _seed_row = (None, "2026-06-15", 100.0, "baostock", "b1", "baostock")


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


def test_incrementalJob_happyPath_writesCleanAndCompletes(
    tmp_path: Path, registry_yaml_fixture: Path, monkeypatch
) -> None:
    from backend.app.core.resource_guard import Decision, ResourceGuard

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    orch, adapter = _orch_stack(tmp_path, registry_yaml_fixture)
    result = orch.run_incremental(
        _incremental_spec(),
        adapter=adapter,
        conflict_staging_table=CONFLICT_STG,
        clean_table=CLEAN_TABLE,
    )
    with orch._cm.writer() as con:
        clean_rows = con.execute(f"SELECT COUNT(*) FROM {CLEAN_TABLE}").fetchone()[0]
        fetch_rows = con.execute(
            "SELECT COUNT(*) FROM fetch_log WHERE job_id = ?", ["job-inc-d"]
        ).fetchone()[0]
        status = con.execute(
            "SELECT status FROM data_sync_job WHERE job_id = ?", ["job-inc-d"]
        ).fetchone()[0]
    assert result.status == "COMPLETED"
    assert clean_rows == 1
    assert fetch_rows >= 1
    assert status == "COMPLETED"


def test_incrementalJob_validationFailed_doesNotWriteClean(
    tmp_path: Path, registry_yaml_fixture: Path, monkeypatch
) -> None:
    from backend.app.core.resource_guard import Decision, ResourceGuard

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    orch, _ = _orch_stack(tmp_path, registry_yaml_fixture)
    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    bad = BatchDBadQualityAdapter(reg)
    result = orch.run_incremental(
        _incremental_spec("job-bad-dq"),
        adapter=bad,
        conflict_staging_table=CONFLICT_STG,
        clean_table=CLEAN_TABLE,
    )
    with orch._cm.writer() as con:
        clean_rows = con.execute(f"SELECT COUNT(*) FROM {CLEAN_TABLE}").fetchone()[0]
    assert result.status == "MANUAL_REVIEW_REQUIRED"
    assert clean_rows == 0


def test_incrementalJob_repeatRun_noDuplicatePrimaryKey(
    tmp_path: Path, registry_yaml_fixture: Path, monkeypatch
) -> None:
    from backend.app.core.resource_guard import Decision, ResourceGuard

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    orch, adapter = _orch_stack(tmp_path, registry_yaml_fixture)
    spec = _incremental_spec("job-repeat-d")
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    r1 = orch.run_incremental(
        spec,
        adapter=adapter,
        conflict_staging_table=CONFLICT_STG,
        clean_table=CLEAN_TABLE,
        write_mode="upsert_by_pk",
    )
    spec2 = SyncJobSpec(
        run_id="run-batch-d-2",
        job_id="job-repeat-d-2",
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
    r2 = orch.run_incremental(
        spec2,
        adapter=adapter,
        conflict_staging_table=CONFLICT_STG,
        clean_table=CLEAN_TABLE,
        write_mode="upsert_by_pk",
    )
    with orch._cm.writer() as con:
        clean_rows = con.execute(f"SELECT COUNT(*) FROM {CLEAN_TABLE}").fetchone()[0]
    assert r1.status == "COMPLETED"
    assert r2.status == "COMPLETED"
    assert clean_rows == 1
