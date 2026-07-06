"""M-G1-03 P1-07 — FullLoadJobRunner §13.4.1."""

from __future__ import annotations

from datetime import date

from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.sync.jobs import SyncJobSpec
from backend.app.sync.orchestrator import DataSyncOrchestrator

_FULL_LOAD_3SHARD_START = date(2026, 1, 1)
_FULL_LOAD_1SHARD_END = date(2026, 1, 15)
_FULL_LOAD_2SHARD_END = date(2026, 2, 15)


def _orchestrator(tmp_path) -> DataSyncOrchestrator:
    db = tmp_path / "full-load.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    return DataSyncOrchestrator(cm)


class _FullLoadCountAdapter:
    source_id = "baostock"
    supported_domains = frozenset({"market_bar_1d"})
    STG = "stg_full_load"
    CLEAN = "stg_full_load_clean"

    def __init__(self) -> None:
        self.fetch_calls = 0

    def fetch(self, req, *, con, job_id=None):
        from backend.app.datasources.fetch_result import FetchResult

        self.fetch_calls += 1
        con.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.STG} (
                instrument_id VARCHAR, trade_date VARCHAR, close DOUBLE,
                source_used VARCHAR, batch_id VARCHAR, source_id VARCHAR
            )
            """
        )
        con.execute(
            f"CREATE TABLE IF NOT EXISTS {self.CLEAN} AS SELECT * FROM {self.STG} WHERE 1=0"
        )
        con.execute(f"DELETE FROM {self.STG}")
        con.execute(
            f"INSERT INTO {self.STG} VALUES (?, ?, ?, ?, ?, ?)",
            ["AAPL", "2026-06-15", 100.0, "baostock", "fl1", "baostock"],
        )
        return FetchResult(
            run_id=req.run_id,
            source_id=self.source_id,
            data_domain=req.data_domain,
            status="SUCCESS",
            row_count=1,
            fetch_time="2026-06-17T10:00:00Z",
            staging_table=self.STG,
            raw_file_paths=["/tmp/fl.parquet"],
            content_hash="abc",
            schema_hash="def",
        )


class _FullLoadFailOnSecondAdapter(_FullLoadCountAdapter):
    def fetch(self, req, *, con, job_id=None):
        if self.fetch_calls + 1 >= 2:
            self.fetch_calls += 1
            from backend.app.datasources.fetch_result import FetchResult

            return FetchResult(
                run_id=req.run_id,
                source_id=self.source_id,
                data_domain=req.data_domain,
                status="FAILED",
                row_count=0,
                fetch_time="2026-06-17T10:00:00Z",
                error_message="shard fail",
            )
        return super().fetch(req, con=con, job_id=job_id)


def _full_load_spec(
    *,
    job_id: str = "job-fl",
    date_end: date = _FULL_LOAD_1SHARD_END,
) -> SyncJobSpec:
    return SyncJobSpec(
        run_id="run-fl",
        job_id=job_id,
        job_type="full_load",
        data_domain="market_bar_1d",
        market_id="CN_A",
        source_id="baostock",
        adapter_id=None,
        date_start=_FULL_LOAD_3SHARD_START,
        date_end=date_end,
        instrument_id=None,
        partition_key=None,
        trigger_reason="cold_start",
    )


def test_syncFullLoad_runnerSection1341_noDeferredJobTypeError(tmp_path, monkeypatch) -> None:
    """覆盖范围：FullLoad job runner
    测试对象：backend.app.sync.runners.FullLoadJobRunner · DataSyncOrchestrator.run_full_load
    目的/目标：§13.4.1 断点续跑；无 DeferredJobTypeError
    验证点：orchestrator 可调度 full_load 且返回 COMPLETED
    失败含义：sync_job_contract reserved full_load 未消除
    """
    from backend.app.core.resource_guard import Decision, ResourceGuard

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    orch = _orchestrator(tmp_path)
    results = orch.run_full_load(
        _full_load_spec(),
        adapter=_FullLoadCountAdapter(),
        clean_table=_FullLoadCountAdapter.CLEAN,
    )
    assert results
    assert results[-1].status == "COMPLETED"


def test_syncFullLoad_checkpointResume_skipsCompletedShards(tmp_path, monkeypatch) -> None:
    """覆盖范围：FullLoad 断点续跑
    测试对象：FullLoadJobRunner FULL_LOAD_COMPLETE checkpoint
    目的/目标：§13.4.1 部分失败后重跑跳过已完成分片
    验证点：续跑仅 fetch 未完成分片（fetch_calls 少于总分片数）
    失败含义：断点续跑失效，全量重建成本不可控
    """
    from backend.app.core.resource_guard import Decision, ResourceGuard
    from backend.app.sync.jobs import plan_backfill_shards

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    orch = _orchestrator(tmp_path)
    spec = _full_load_spec(job_id="job-fl-resume", date_end=_FULL_LOAD_2SHARD_END)
    total_shards = len(plan_backfill_shards(spec.date_start, spec.date_end))

    fail_adapter = _FullLoadFailOnSecondAdapter()
    first = orch.run_full_load(
        spec,
        adapter=fail_adapter,
        clean_table=_FullLoadCountAdapter.CLEAN,
    )
    assert any(r.status == "FAILED_RETRYABLE" for r in first)

    resume_adapter = _FullLoadCountAdapter()
    second = orch.run_full_load(
        spec,
        adapter=resume_adapter,
        clean_table=_FullLoadCountAdapter.CLEAN,
    )
    assert second[-1].status == "COMPLETED"
    assert resume_adapter.fetch_calls < total_shards
