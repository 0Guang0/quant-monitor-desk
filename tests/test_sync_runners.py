"""Sync job runner wiring tests (B3F-BR / playbook §8.5).

覆盖范围：runner 类与 orchestrator 接线。
分片规划见 test_sync_orchestrator.test_backfillJob_largeRange_splitsIntoTasks。
"""

from __future__ import annotations

from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.sync.jobs import SyncJobSpec
from backend.app.sync.orchestrator import DataSyncOrchestrator, orchestrator_handler_registry
from backend.app.sync.runners import (
    BackfillShardRunner,
    IncrementalJobRunner,
    ReconcileJobRunner,
)


def test_syncRunners_orchestratorWiresRunnerAttributes(tmp_path) -> None:
    """覆盖范围：orchestrator 内部 runner 实例接线与 registry runner_attr 一致
    测试对象：DataSyncOrchestrator.__init__ · orchestrator_handler_registry
    目的/目标：三类已实现 job 的 runner 在编排器内可访问且与 registry 单源对齐
    验证点：_incremental/_backfill/_reconcile isinstance；registry runner_attr getattr 一致
    失败含义：runner 未接线或 registry 与实例分叉会导致运行期 AttributeError
    """
    db = tmp_path / "runners.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    orch = DataSyncOrchestrator(cm)
    registry = orchestrator_handler_registry()

    assert isinstance(orch._incremental, IncrementalJobRunner)
    assert isinstance(orch._backfill, BackfillShardRunner)
    assert isinstance(orch._reconcile, ReconcileJobRunner)

    for attr_name, expected_type in (
        ("_incremental", IncrementalJobRunner),
        ("_backfill", BackfillShardRunner),
        ("_reconcile", ReconcileJobRunner),
    ):
        row = next(r for r in registry.values() if r.runner_attr == attr_name)
        assert getattr(orch, row.runner_attr) is getattr(orch, attr_name)
        assert isinstance(getattr(orch, row.runner_attr), expected_type)


def test_incrementalRunner_injectsDateWindowIntoFetchRequest(tmp_path) -> None:
    """覆盖范围：IncrementalJobRunner 将 spec 日期注入 FetchRequest
    测试对象：IncrementalJobRunner.run fetch_callable 收到的 req
    目的/目标：date_start/date_end 应映射为 start_time/end_time ISO 字符串
    验证点：捕获的 req.start_time/end_time 与 spec 一致
    失败含义：runner 不传窗会导致 port 无法做增量过滤
    """
    from datetime import date

    db = tmp_path / "incr_dates.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    orch = DataSyncOrchestrator(cm)
    captured: list[FetchRequest] = []

    def _capture_fetch(req, con, job_id, operation=None):
        captured.append(req)
        from backend.app.datasources.fetch_result import FetchResult

        return FetchResult(
            run_id=req.run_id,
            source_id=req.source_id,
            data_domain=req.data_domain,
            status="FAILED",
            row_count=0,
            fetch_time="2026-06-30T00:00:00Z",
            error_message="stop after capture",
        )

    spec = SyncJobSpec(
        run_id="run-date-inj",
        job_id="job-date-inj",
        job_type="incremental",
        data_domain="cn_equity_daily_bar",
        market_id="CN_A",
        source_id="baostock",
        adapter_id="baostock",
        date_start=date(2024, 6, 25),
        date_end=date(2024, 6, 30),
        instrument_id="sh.600519",
        partition_key=None,
        trigger_reason=None,
    )
    from backend.app.sync.runners import PipelineConfig

    config = PipelineConfig(
        clean_table="security_bar_1d",
        conflict_staging_table=None,
        write_mode="upsert_by_pk",
        primary_keys=("instrument_id", "trade_date", "adjustment_type"),
        required_fields=("close", "source_used"),
    )
    orch._incremental.run(spec, fetch_callable=_capture_fetch, config=config)
    assert len(captured) == 1
    assert captured[0].start_time == "2024-06-25"
    assert captured[0].end_time == "2024-06-30"


def test_incrementalRunner_caughtUp_skipsFetch(tmp_path) -> None:
    """覆盖范围：IncrementalJobRunner caught-up 早退
    测试对象：IncrementalJobRunner.run date_start > date_end
    目的/目标：追平窗不应调用 fetch_callable
    验证点：status==COMPLETED；fetch 未触发
    失败含义：runner 仍 fetch 会重拉已落库日
    """
    from datetime import date

    from backend.app.sync.runners import PipelineConfig

    db = tmp_path / "incr_caught_up.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    orch = DataSyncOrchestrator(cm)
    calls: list[FetchRequest] = []

    def _should_not_fetch(req, con, job_id, operation=None):
        calls.append(req)
        from backend.app.datasources.fetch_result import FetchResult

        return FetchResult(
            run_id=req.run_id,
            source_id=req.source_id,
            data_domain=req.data_domain,
            status="FAILED",
            row_count=0,
            fetch_time="2026-06-30T00:00:00Z",
            error_message="unexpected fetch",
        )

    spec = SyncJobSpec(
        run_id="run-caught-up",
        job_id="job-caught-up",
        job_type="incremental",
        data_domain="cn_equity_daily_bar",
        market_id="CN_A",
        source_id="baostock",
        adapter_id="baostock",
        date_start=date(2026, 7, 1),
        date_end=date(2026, 6, 30),
        instrument_id="sh.600519",
        partition_key=None,
        trigger_reason=None,
    )
    config = PipelineConfig(
        clean_table="security_bar_1d",
        conflict_staging_table=None,
        write_mode="upsert_by_pk",
        primary_keys=("instrument_id", "trade_date", "adjustment_type"),
        required_fields=("close", "source_used"),
    )
    result = orch._incremental.run(
        spec,
        fetch_callable=_should_not_fetch,
        config=config,
    )
    assert result.status == "SKIPPED"
    assert "caught-up" in (result.message or "")
    assert calls == []
