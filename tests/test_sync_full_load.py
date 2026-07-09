"""M-G1-03 P1-07 — FullLoadJobRunner §13.4.1."""

from __future__ import annotations

from datetime import date

from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.sync.jobs import SyncJobSpec
from backend.app.sync.orchestrator import DataSyncOrchestrator
from tests.support.sync_adapters import (
    FULL_LOAD_2SHARD_END as _FULL_LOAD_2SHARD_END,
    FULL_LOAD_3SHARD_START as _FULL_LOAD_3SHARD_START,
    FULL_LOAD_1SHARD_END as _FULL_LOAD_1SHARD_END,
    FullLoadCountAdapter as _FullLoadCountAdapter,
    FullLoadFailOnSecondAdapter as _FullLoadFailOnSecondAdapter,
)


def _orchestrator(tmp_path) -> DataSyncOrchestrator:
    db = tmp_path / "full-load.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    return DataSyncOrchestrator(cm)


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
    验证点：首跑留下 FULL_LOAD_COMPLETE；续跑仅 fetch 未完成分片日期范围
    失败含义：断点续跑失效，全量重建成本不可控
    """
    from backend.app.core.resource_guard import Decision, ResourceGuard
    from backend.app.sync.jobs import plan_backfill_shards

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    orch = _orchestrator(tmp_path)
    spec = _full_load_spec(job_id="job-fl-resume", date_end=_FULL_LOAD_2SHARD_END)
    shards = plan_backfill_shards(
        spec.date_start,
        spec.date_end,
        data_domain=spec.data_domain,
        truncate_to_cap=True,
    )
    first_task_id, first_start, first_end = shards[0]

    fail_adapter = _FullLoadFailOnSecondAdapter()
    first = orch.run_full_load(
        spec,
        adapter=fail_adapter,
        clean_table=_FullLoadCountAdapter.CLEAN,
    )
    assert any(r.status == "FAILED_RETRYABLE" for r in first)

    with orch._cm.writer() as con:
        complete_events = con.execute(
            """
            SELECT event_type, message FROM job_event_log
            WHERE job_id = ? AND event_type = 'FULL_LOAD_COMPLETE'
            """,
            [spec.job_id],
        ).fetchall()
    assert len(complete_events) == 1
    assert first_task_id in (complete_events[0][1] or "")

    resume_adapter = _FullLoadCountAdapter()
    second = orch.run_full_load(
        spec,
        adapter=resume_adapter,
        clean_table=_FullLoadCountAdapter.CLEAN,
    )
    assert second[-1].status == "COMPLETED"
    remaining_ranges = {
        f"{shard_start.isoformat()}:{shard_end.isoformat()}"
        for _, shard_start, shard_end in shards[1:]
    }
    assert set(resume_adapter.fetched_shard_ids) == remaining_ranges
    assert f"{first_start.isoformat()}:{first_end.isoformat()}" not in resume_adapter.fetched_shard_ids
