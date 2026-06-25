"""数据同步编排器测试（Batch D）。

覆盖范围：作业创建与事件、资源门禁、历史回补分片、多源冲突、注册表引导及生产路由守卫。
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from backend.app.datasources.source_registry import SourceRegistry
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.sync.jobs import SyncJobSpec
from backend.app.sync.orchestrator import DataSyncOrchestrator

# ponytail: smallest span with ≥3 shards at ECO_MAX_BACKFILL_DAYS_PER_TASK (64d); satisfies shard/backfill assertions
_BACKFILL_3SHARD_START = date(2026, 1, 1)
_BACKFILL_3SHARD_END = date(2026, 3, 5)
# ponytail: 1 shard (15d) — enough when test only needs one BACKFILL_SHARD event
_BACKFILL_1SHARD_END = date(2026, 1, 15)
# ponytail: 2 shards (46d) — min for _BackfillFailOnSecondAdapter (fail on 2nd fetch)
_BACKFILL_2SHARD_END = date(2026, 2, 15)


def _orchestrator(tmp_path) -> DataSyncOrchestrator:
    db = tmp_path / "orch.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    return DataSyncOrchestrator(cm)


def test_orchestrator_createJob_persistsDataSyncJob(tmp_path) -> None:
    """覆盖范围：编排器创建同步作业并写入 data_sync_job
    测试对象：DataSyncOrchestrator.create_job
    目的/目标：提交同步任务后，系统里应能查到该任务且处于「已创建」状态
    验证点：返回 job-orch；库内 run_id、job_type、status 与 spec 一致
    失败含义：任务创建后没记下来，后续无法跟踪这次同步的运行过程
    """
    orch = _orchestrator(tmp_path)
    spec = SyncJobSpec(
        run_id="run-orch",
        job_id="job-orch",
        job_type="incremental",
        data_domain="market_bar_1d",
        market_id="CN_A",
        source_id="baostock",
        adapter_id=None,
        date_start=None,
        date_end=None,
        instrument_id=None,
        partition_key=None,
        trigger_reason=None,
    )
    job_id = orch.create_job(spec)
    assert job_id == "job-orch"
    with orch._cm.writer() as con:
        row = con.execute(
            """
            SELECT run_id, job_type, status
            FROM data_sync_job WHERE job_id = ?
            """,
            [job_id],
        ).fetchone()
    assert row == ("run-orch", "incremental", "CREATED")


def test_orchestrator_emitEvent_linksRunJobTask(tmp_path) -> None:
    """覆盖范围：自定义事件写入 job_event_log 并关联运行、任务与子任务
    测试对象：DataSyncOrchestrator.emit_event
    目的/目标：运维自定义事件要能挂在对应的运行、任务和子任务上，方便串联审计
    验证点：event_id 自洽；run_id=run-ev；job_id=job-ev；task_id=task-1
    失败含义：事件缺少关联信息，分片任务和主任务对不上号
    """
    orch = _orchestrator(tmp_path)
    spec = SyncJobSpec(
        run_id="run-ev",
        job_id="job-ev",
        job_type="incremental",
        data_domain="market_bar_1d",
        market_id="CN_A",
        source_id="baostock",
        adapter_id=None,
        date_start=None,
        date_end=None,
        instrument_id=None,
        partition_key=None,
        trigger_reason=None,
    )
    orch.create_job(spec)
    event_id = orch.emit_event(
        "job-ev",
        task_id="task-1",
        event_type="CUSTOM",
        message="test event",
    )
    with orch._cm.writer() as con:
        row = con.execute(
            """
            SELECT event_id, run_id, job_id, task_id
            FROM job_event_log WHERE event_id = ?
            """,
            [event_id],
        ).fetchone()
    assert row[0] == event_id
    assert row[1] == "run-ev"
    assert row[2] == "job-ev"
    assert row[3] == "task-1"


def test_orchestrator_fetchBlockedWhenGuardPaused_setsFailedRetryable(
    tmp_path, monkeypatch
) -> None:
    """覆盖范围：资源不足被要求暂停时，begin_fetching 应阻断抓取
    测试对象：DataSyncOrchestrator.begin_fetching
    目的/目标：磁盘或内存吃紧时不应开始抓取，应标记为可稍后重试的失败
    验证点：begin_fetching 返回 False；status=FAILED_RETRYABLE；message 含 RESOURCE_GUARD_PAUSED
    失败含义：资源告警仍强行抓数据，可能在环境吃紧时把主机拖垮
    """
    from backend.app.core.resource_guard import Decision, ResourceGuard, ResourceSnapshot

    orch = _orchestrator(tmp_path)
    spec = SyncJobSpec(
        run_id="run-g",
        job_id="job-g",
        job_type="incremental",
        data_domain="market_bar_1d",
        market_id="CN_A",
        source_id="baostock",
        adapter_id=None,
        date_start=None,
        date_end=None,
        instrument_id=None,
        partition_key=None,
        trigger_reason=None,
    )
    orch.create_job(spec)
    orch._jobs.transition("job-g", "PLANNED")
    snap = ResourceSnapshot(
        available_memory_gb=1.0,
        disk_free_gb=1.0,
        process_rss_mb=100.0,
        project_size_gb=0.1,
    )

    def _pause(self):
        return Decision.PAUSE, "disk free space below threshold"

    monkeypatch.setattr(ResourceGuard, "snapshot", lambda self: snap)
    monkeypatch.setattr(ResourceGuard, "check", _pause)
    assert orch.begin_fetching("job-g") is False
    with orch._cm.writer() as con:
        status = con.execute(
            "SELECT status FROM data_sync_job WHERE job_id = ?", ["job-g"]
        ).fetchone()[0]
        msg = con.execute(
            "SELECT message FROM job_event_log WHERE job_id = ? ORDER BY created_at DESC LIMIT 1",
            ["job-g"],
        ).fetchone()[0]
    assert status == "FAILED_RETRYABLE"
    assert "RESOURCE_GUARD_PAUSED" in msg
    assert status != "RESOURCE_GUARD_PAUSED"


class _SecretLeakAdapter:
    source_id = "baostock"
    supported_domains = frozenset({"market_bar_1d"})

    def fetch(self, req, *, con, job_id=None):
        from backend.app.datasources.fetch_result import FetchResult

        return FetchResult(
            run_id=req.run_id,
            source_id=self.source_id,
            data_domain=req.data_domain,
            status="AUTH_FAILED",
            row_count=0,
            fetch_time="2026-06-17T10:00:00Z",
            error_message="token=live-secret api_key=k123",
        )


def test_orchestrator_fetchFailure_redactsErrorInJobEventLog(tmp_path, monkeypatch) -> None:
    """覆盖范围：抓取失败时作业事件日志须脱敏错误信息
    测试对象：DataSyncOrchestrator.run_incremental 错误落库
    目的/目标：抓取失败写入日志时，不能把 token、api_key 等敏感信息明文落库
    验证点：status=FAILED_FINAL；message 不含 live-secret/k123；含 REDACTED
    失败含义：凭证泄漏进审计表，合规与密钥轮转都会受影响
    """
    from backend.app.core.resource_guard import Decision, ResourceGuard

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    orch = _orchestrator(tmp_path)
    spec = SyncJobSpec(
        run_id="run-redact",
        job_id="job-redact",
        job_type="incremental",
        data_domain="market_bar_1d",
        market_id="CN_A",
        source_id="baostock",
        adapter_id=None,
        date_start=None,
        date_end=None,
        instrument_id=None,
        partition_key=None,
        trigger_reason=None,
    )
    result = orch.run_incremental(
        spec,
        adapter=_SecretLeakAdapter(),
        clean_table="clean_redact",
        conflict_staging_table=None,
    )
    assert result.status == "FAILED_FINAL"
    with orch._cm.writer() as con:
        msg = con.execute(
            "SELECT message FROM job_event_log WHERE job_id = ? ORDER BY created_at DESC LIMIT 1",
            ["job-redact"],
        ).fetchone()[0]
    assert "live-secret" not in msg
    assert "k123" not in msg
    assert "REDACTED" in msg.upper() or "[REDACTED]" in msg


def test_orchestrator_fetchBlockedOnHardStop_setsFailedRetryable(tmp_path, monkeypatch) -> None:
    """覆盖范围：内存等硬阈值触发时 begin_fetching 应阻断抓取
    测试对象：DataSyncOrchestrator.begin_fetching
    目的/目标：资源严重不足时不应开始抓取，应标记为可稍后重试的失败
    验证点：begin_fetching 返回 False；status=FAILED_RETRYABLE；事件含 RESOURCE_GUARD_PAUSED
    失败含义：硬停条件仍强行抓数据，有 OOM 或数据损坏风险
    """
    from backend.app.core.resource_guard import Decision, ResourceGuard, ResourceSnapshot

    orch = _orchestrator(tmp_path)
    orch.create_job(
        SyncJobSpec(
            run_id="run-hs",
            job_id="job-hs",
            job_type="incremental",
            data_domain="market_bar_1d",
            market_id="CN_A",
            source_id="baostock",
            adapter_id=None,
            date_start=None,
            date_end=None,
            instrument_id=None,
            partition_key=None,
            trigger_reason=None,
        )
    )
    orch._jobs.transition("job-hs", "PLANNED")
    snap = ResourceSnapshot(
        available_memory_gb=0.1,
        disk_free_gb=0.1,
        process_rss_mb=100.0,
        project_size_gb=0.1,
    )

    def _hard(self):
        return Decision.HARD_STOP, "available memory below threshold"

    monkeypatch.setattr(ResourceGuard, "snapshot", lambda self: snap)
    monkeypatch.setattr(ResourceGuard, "check", _hard)
    assert orch.begin_fetching("job-hs") is False
    with orch._cm.writer() as con:
        status, msg = con.execute(
            """
            SELECT j.status, e.message
            FROM data_sync_job j
            JOIN job_event_log e ON j.job_id = e.job_id
            WHERE j.job_id = ?
            ORDER BY e.created_at DESC LIMIT 1
            """,
            ["job-hs"],
        ).fetchone()
    assert status == "FAILED_RETRYABLE"
    assert "RESOURCE_GUARD_PAUSED" in msg


def test_orchestrator_fetchAllowedWhenGuardOk_proceedsToFetching(tmp_path, monkeypatch) -> None:
    """覆盖范围：资源正常时 begin_fetching 允许进入抓取态
    测试对象：DataSyncOrchestrator.begin_fetching
    目的/目标：机器资源充足时，已规划好的任务应能正常开始抓取
    验证点：begin_fetching 返回 True；data_sync_job.status == FETCHING
    失败含义：资源正常仍挡抓取，日常增量同步主路径无法启动
    """
    from backend.app.core.resource_guard import Decision, ResourceGuard

    orch = _orchestrator(tmp_path)
    orch.create_job(
        SyncJobSpec(
            run_id="run-ok",
            job_id="job-ok",
            job_type="incremental",
            data_domain="market_bar_1d",
            market_id="CN_A",
            source_id="baostock",
            adapter_id=None,
            date_start=None,
            date_end=None,
            instrument_id=None,
            partition_key=None,
            trigger_reason=None,
        )
    )
    orch._jobs.transition("job-ok", "PLANNED")
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    assert orch.begin_fetching("job-ok") is True
    with orch._cm.writer() as con:
        status = con.execute(
            "SELECT status FROM data_sync_job WHERE job_id = ?", ["job-ok"]
        ).fetchone()[0]
    assert status == "FETCHING"


def test_backfillJob_largeRange_splitsIntoTasks(tmp_path, monkeypatch) -> None:
    """覆盖范围：大日期区间历史回补自动拆成多个子任务
    测试对象：plan_backfill_shards 与 DataSyncOrchestrator.run_backfill
    目的/目标：跨度太大的回补应按天上限拆片，实际跑多个分片而不是一次抓完
    验证点：shards≥3；每片天数≤ECO_MAX_BACKFILL_DAYS_PER_TASK；run_backfill 返回 results≥3
    失败含义：大区间单次抓取，容易超时或占满内存，也无法按片重试
    """
    from backend.app.core.resource_guard import Decision, ResourceGuard
    from backend.app.sync.jobs import ECO_MAX_BACKFILL_DAYS_PER_TASK, plan_backfill_shards

    shards = plan_backfill_shards(_BACKFILL_3SHARD_START, _BACKFILL_3SHARD_END)
    assert len(shards) >= 3
    assert all(
        (end - start).days + 1 <= ECO_MAX_BACKFILL_DAYS_PER_TASK for _tid, start, end in shards
    )

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    orch = _orchestrator(tmp_path)
    spec = SyncJobSpec(
        run_id="run-bf",
        job_id="job-bf",
        job_type="backfill",
        data_domain="market_bar_1d",
        market_id="CN_A",
        source_id="baostock",
        adapter_id=None,
        date_start=_BACKFILL_3SHARD_START,
        date_end=_BACKFILL_3SHARD_END,
        instrument_id=None,
        partition_key=None,
        trigger_reason="eco_catchup",
    )
    results = orch.run_backfill(
        spec,
        adapter=_BackfillCountAdapter(),
        clean_table=_BackfillCountAdapter.CLEAN,
    )
    assert len(results) >= 3


def test_backfillJob_recordsTriggerReason(tmp_path, monkeypatch) -> None:
    """覆盖范围：历史回补分片事件里记录触发原因
    测试对象：DataSyncOrchestrator.run_backfill 事件写入
    目的/目标：审计日志要能看出这次回补是人工发起还是自动追赶等
    验证点：BACKFILL_SHARD 事件 payload_json 含 manual_request
    失败含义：回补原因丢失，运维无法按触发类型统计和排障
    """
    from datetime import date

    from backend.app.core.resource_guard import Decision, ResourceGuard

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    orch = _orchestrator(tmp_path)
    spec = SyncJobSpec(
        run_id="run-tr",
        job_id="job-tr",
        job_type="backfill",
        data_domain="market_bar_1d",
        market_id="CN_A",
        source_id="baostock",
        adapter_id=None,
        date_start=_BACKFILL_3SHARD_START,
        date_end=_BACKFILL_1SHARD_END,
        instrument_id=None,
        partition_key=None,
        trigger_reason="manual_request",
    )
    orch.run_backfill(
        spec,
        adapter=_BackfillCountAdapter(),
        clean_table=_BackfillCountAdapter.CLEAN,
    )
    with orch._cm.writer() as con:
        row = con.execute(
            """
            SELECT payload_json FROM job_event_log
            WHERE job_id = ? AND event_type = 'BACKFILL_SHARD' LIMIT 1
            """,
            ["job-tr"],
        ).fetchone()
    assert row is not None
    assert "manual_request" in row[0]


def test_backfillJob_eachShard_callsResourceGuardBeforeFetching(tmp_path, monkeypatch) -> None:
    """覆盖范围：每个历史回补分片抓取前都做资源检查
    测试对象：DataSyncOrchestrator.run_backfill 分片循环
    目的/目标：多分片连续抓取时，每一片开始前都要再看一眼机器资源
    验证点：guard check 调用次数 ≥3（与分片数一致量级）
    失败含义：只有第一片检查资源，后续分片可能在环境恶化时硬跑
    """
    from datetime import date

    from backend.app.core.resource_guard import Decision, ResourceGuard

    calls: list[str] = []

    def _track(self):
        calls.append("check")
        return Decision.OK, ""

    monkeypatch.setattr(ResourceGuard, "check", _track)
    orch = _orchestrator(tmp_path)
    spec = SyncJobSpec(
        run_id="run-guard-bf",
        job_id="job-guard-bf",
        job_type="backfill",
        data_domain="market_bar_1d",
        market_id="CN_A",
        source_id="baostock",
        adapter_id=None,
        date_start=_BACKFILL_3SHARD_START,
        date_end=_BACKFILL_3SHARD_END,
        instrument_id=None,
        partition_key=None,
        trigger_reason="eco_catchup",
    )
    orch.run_backfill(
        spec,
        adapter=_BackfillCountAdapter(),
        clean_table=_BackfillCountAdapter.CLEAN,
    )
    assert len(calls) >= 3


def test_backfillJob_midShardFailure_preservesCompletedTasks(tmp_path, monkeypatch) -> None:
    """覆盖范围：历史回补中途某分片失败时，已完成分片结果应保留
    测试对象：DataSyncOrchestrator.run_backfill 部分失败语义
    目的/目标：后面一片失败不应抹掉前面已经成功的分片进度
    验证点：results 含 FAILED_RETRYABLE；job_event_log 至少一条 shard completed
    失败含义：一片失败就要从头重来，回补成本和等待时间都会放大
    """
    from datetime import date

    from backend.app.core.resource_guard import Decision, ResourceGuard

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    orch = _orchestrator(tmp_path)
    spec = SyncJobSpec(
        run_id="run-fail-bf",
        job_id="job-fail-bf",
        job_type="backfill",
        data_domain="market_bar_1d",
        market_id="CN_A",
        source_id="baostock",
        adapter_id=None,
        date_start=_BACKFILL_3SHARD_START,
        date_end=_BACKFILL_2SHARD_END,
        instrument_id=None,
        partition_key=None,
        trigger_reason="eco_catchup",
    )
    results = orch.run_backfill(
        spec,
        adapter=_BackfillFailOnSecondAdapter(),
        clean_table=_BackfillCountAdapter.CLEAN,
    )
    assert any(r.status == "FAILED_RETRYABLE" for r in results)
    with orch._cm.writer() as con:
        completed_tasks = con.execute(
            """
            SELECT COUNT(*) FROM job_event_log
            WHERE job_id = ? AND message LIKE 'shard % completed'
            """,
            ["job-fail-bf"],
        ).fetchone()[0]
    assert completed_tasks >= 1


class _BackfillCountAdapter:
    """Minimal adapter for backfill shard tests with validate+write path."""

    source_id = "baostock"
    supported_domains = frozenset({"market_bar_1d"})
    STG = "stg_backfill"
    CLEAN = "stg_backfill_clean"

    def fetch(self, req, *, con, job_id=None):
        from backend.app.datasources.fetch_result import FetchResult

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
            ["AAPL", "2026-06-15", 100.0, "baostock", "bf1", "baostock"],
        )
        return FetchResult(
            run_id=req.run_id,
            source_id=self.source_id,
            data_domain=req.data_domain,
            status="SUCCESS",
            row_count=1,
            fetch_time="2026-06-17T10:00:00Z",
            staging_table=self.STG,
            raw_file_paths=["/tmp/bf.parquet"],
            content_hash="abc",
            schema_hash="def",
        )


class _BackfillFailOnSecondAdapter(_BackfillCountAdapter):
    def __init__(self) -> None:
        self._calls = 0

    def fetch(self, req, *, con, job_id=None):
        from backend.app.datasources.fetch_result import FetchResult

        self._calls += 1
        if self._calls >= 2:
            return FetchResult(
                run_id=req.run_id,
                source_id=self.source_id,
                data_domain=req.data_domain,
                status="NETWORK_ERROR",
                row_count=0,
                fetch_time="2026-06-17T10:00:00Z",
                error_message="shard 2 failed",
            )
        return super().fetch(req, con=con, job_id=job_id)


def test_backfillJob_severeConflict_blocksCleanWriteAndPersistsConflictReportId(
    tmp_path, registry_yaml_fixture, monkeypatch
) -> None:
    """覆盖范围：历史回补遇严重多源冲突时阻断写入正式表
    测试对象：DataSyncOrchestrator.run_backfill 冲突路径
    目的/目标：两个数据源价差过大时，不应把脏数据写进 clean 表，应挂起等待调和
    验证点：results 含 WAITING_RECONCILE；clean_rows=0；conflict_report_id 非空
    失败含义：冲突数据仍进生产表，下游计算会基于不一致行情
    """
    from datetime import date

    from backend.app.core.resource_guard import Decision, ResourceGuard
    from tests.test_batch_d_orchestration_flow import (
        CONFLICT_STG,
        BatchDIncrementalAdapter,
        _orch_stack,
    )

    class SevereBackfillAdapter(BatchDIncrementalAdapter):
        _conflict_peer_rows = (
            ("baostock", "AAPL", "2026-06-15", 100.0),
            ("qmt_xtdata", "AAPL", "2026-06-15", 150.0),
        )

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    orch, _ = _orch_stack(tmp_path, registry_yaml_fixture)
    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    adapter = SevereBackfillAdapter(reg)
    spec = SyncJobSpec(
        run_id="run-bf-severe",
        job_id="job-bf-severe",
        job_type="backfill",
        data_domain="market_bar_1d",
        market_id="CN_A",
        source_id="baostock",
        adapter_id=None,
        date_start=date(2026, 1, 1),
        date_end=date(2026, 1, 15),
        instrument_id=None,
        partition_key=None,
        trigger_reason="eco_catchup",
    )
    results = orch.run_backfill(
        spec,
        adapter=adapter,
        clean_table="clean_batch_d_flow",
        conflict_staging_table=CONFLICT_STG,
    )
    assert any(r.status == "WAITING_RECONCILE" for r in results)
    with orch._cm.writer() as con:
        clean_rows = con.execute("SELECT COUNT(*) FROM clean_batch_d_flow").fetchone()[0]
        conflict_report_id = con.execute(
            "SELECT conflict_report_id FROM data_sync_job WHERE job_id = ?",
            ["job-bf-severe"],
        ).fetchone()[0]
    assert clean_rows == 0
    assert conflict_report_id is not None


def test_reconcileJob_severeConflict_entersWaitingReconcile(
    tmp_path, registry_yaml_fixture, monkeypatch
) -> None:
    """覆盖范围：增量同步遇严重多源冲突时应挂起等待调和
    测试对象：DataSyncOrchestrator.run_incremental 冲突检测
    目的/目标：两个行情源对同一标的给出差异过大的价格时，不应直接标完成
    验证点：result.status == WAITING_RECONCILE
    失败含义：严重冲突仍标完成，脏价会进入下游计算
    """
    from backend.app.core.resource_guard import Decision, ResourceGuard
    from tests.test_batch_d_orchestration_flow import (
        CLEAN_TABLE,
        CONFLICT_STG,
        BatchDIncrementalAdapter,
        _incremental_spec,
        _orch_stack,
    )

    class SevereConflictAdapter(BatchDIncrementalAdapter):
        _conflict_peer_rows = (
            ("baostock", "AAPL", "2026-06-15", 100.0),
            ("qmt_xtdata", "AAPL", "2026-06-15", 150.0),
        )

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    orch, _ = _orch_stack(tmp_path, registry_yaml_fixture)
    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    adapter = SevereConflictAdapter(reg)
    result = orch.run_incremental(
        _incremental_spec("job-severe"),
        adapter=adapter,
        conflict_staging_table=CONFLICT_STG,
        clean_table=CLEAN_TABLE,
    )
    assert result.status == "WAITING_RECONCILE"


def test_reconcileJob_afterReconcile_resolvesOrManualReview(tmp_path) -> None:
    """覆盖范围：对已登记的严重冲突执行调和流程
    测试对象：DataSyncOrchestrator.run_reconcile
    目的/目标：需要人工复核的冲突不能静默自动关闭，应明确提示人工介入
    验证点：预插 source_conflict manual_review_required=True；result.status=MANUAL_REVIEW_REQUIRED
    失败含义：该人工看的冲突被自动关掉，风控和审计都会留缺口
    """
    from datetime import UTC, datetime

    orch = _orchestrator(tmp_path)
    conflict_id = "conflict-1"
    with orch._cm.writer() as con:
        con.execute(
            """
            INSERT INTO source_conflict (
                conflict_id, run_id, job_id, data_domain, market_id,
                field_name, primary_source, primary_value,
                competing_source, competing_value, normalized_diff,
                severity, reconcile_status, manual_review_required, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                conflict_id,
                "run-rc",
                "job-rc",
                "market_bar_1d",
                "CN_A",
                "close",
                "baostock",
                "100",
                "qmt_xtdata",
                "150",
                0.5,
                "severe",
                "UNRESOLVED",
                True,
                datetime.now(UTC),
            ],
        )
    result = orch.run_reconcile(conflict_id, adapter=_BackfillCountAdapter())
    assert result.status == "MANUAL_REVIEW_REQUIRED"


def test_syncRegistry_cli_syncsYamlToDb(tmp_path, registry_yaml_fixture, monkeypatch) -> None:
    """覆盖范围：CLI 脚本把 YAML 数据源注册表同步进 DuckDB
    测试对象：sync_registry 子进程入口
    目的/目标：运维跑同步脚本后，数据库里应有与 YAML 一致的数据源登记
    验证点：returncode=0；source_registry COUNT≥1
    失败含义：注册表文件和库不同步，路由和能力判断会读错配置
    """
    import os
    import subprocess
    import sys

    data_root = tmp_path / "data"
    data_root.mkdir()
    (data_root / "duckdb").mkdir()
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    project_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)
    proc = subprocess.run(
        [sys.executable, "scripts/sync_registry.py", "--yaml", str(registry_yaml_fixture)],
        cwd=str(project_root),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    db = data_root / "duckdb" / "quant_monitor.duckdb"
    cm = ConnectionManager(db)
    with cm.reader() as con:
        count = con.execute("SELECT COUNT(*) FROM source_registry").fetchone()[0]
    assert count >= 1


def test_orchestratorBootstrap_callsSyncToDb(tmp_path, registry_yaml_fixture, monkeypatch) -> None:
    """覆盖范围：编排器启动引导时把 YAML 注册表加载进库
    测试对象：DataSyncOrchestrator.bootstrap
    目的/目标：应用启动时应把数据源注册表写入当前连接的数据库
    验证点：bootstrap 后 source_registry COUNT≥1
    失败含义：启动后注册表是空的或旧的，服务内路由会选错数据源
    """
    from backend.app.datasources.source_registry import SourceRegistry

    monkeypatch.setenv("QMD_DATA_ROOT", str(tmp_path / "data"))
    orch = _orchestrator(tmp_path)
    monkeypatch.setattr(
        SourceRegistry,
        "DEFAULT_YAML",
        registry_yaml_fixture,
    )
    orch.bootstrap(sync_registry=True)
    with orch._cm.writer() as con:
        count = con.execute("SELECT COUNT(*) FROM source_registry").fetchone()[0]
    assert count >= 1


def test_plannedJobWritesRoutePlanBeforeFetching(tmp_path, monkeypatch) -> None:
    """覆盖范围：经 DataSourceService 路径时，路由计划事件应早于开始抓取
    测试对象：DataSyncOrchestrator.run_incremental 与 DataSourceService
    目的/目标：开始抓数据之前，系统应先记下「打算用哪个源、路由是否就绪」
    验证点：COMPLETED；ROUTE_PLAN 事件索引 < FETCHING；payload route_status=READY、selected_source_id=baostock
    失败含义：没规划就先抓，多源路由顺序和审计链都会乱
    """
    from backend.app.core.resource_guard import Decision, ResourceGuard
    from backend.app.datasources.service import DataSourceService
    from backend.app.datasources.source_registry import SourceRegistry
    from backend.app.sync.event_payload import parse_event_payload
    from tests.service_path_support import (
        ensure_bar_staging_tables,
        make_fixture_port,
        patch_create_test_adapter_for_staging,
        write_bar_fixture,
    )

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    orch = _orchestrator(tmp_path)
    fixture = tmp_path / "route_fixture.json"
    write_bar_fixture(fixture)
    reg = SourceRegistry()
    reg.load()
    STG = "stg_route_plan_test"
    with orch._cm.writer() as con:
        ensure_bar_staging_tables(con, STG, clean_name="clean_route")

    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    port = make_fixture_port(fixture)
    patch_create_test_adapter_for_staging(
        monkeypatch,
        staging_table=STG,
        registry=reg,
        raw_root=raw_root,
        fetch_port=port,
    )
    service = DataSourceService(
        source_registry=reg,
        data_root=raw_root,
        fetch_port=port,
        job_events=orch._jobs,
    )
    spec = SyncJobSpec(
        run_id="run-route",
        job_id="job-route",
        job_type="incremental",
        data_domain="cn_equity_daily_bar",
        market_id="CN_A",
        source_id="baostock",
        adapter_id="baostock",
        date_start=None,
        date_end=None,
        instrument_id="000001",
        partition_key=None,
        trigger_reason=None,
    )
    result = orch.run_incremental(spec, datasource_service=service, clean_table="clean_route")
    assert result.status == "COMPLETED"
    with orch._cm.writer() as con:
        rows = con.execute(
            """
            SELECT event_type, payload_json, new_status, created_at
            FROM job_event_log
            WHERE job_id = ? ORDER BY created_at ASC
            """,
            [result.job_id],
        ).fetchall()
    route_idx = next(i for i, row in enumerate(rows) if row[0] == "ROUTE_PLAN")
    fetching_idx = next(i for i, row in enumerate(rows) if row[2] == "FETCHING")
    assert route_idx < fetching_idx
    route_payload = parse_event_payload(rows[route_idx][1])
    assert route_payload.get("route_status") == "READY"
    assert route_payload.get("selected_source_id") == "baostock"


def test_servicePath_guardBlocked_setsFailedRetryableWithFormattedMessage(
    tmp_path, monkeypatch
) -> None:
    """覆盖范围：经 DataSourceService 路径且资源不足时的失败语义
    测试对象：run_incremental + DataSourceService + 资源暂停
    目的/目标：资源挡下抓取时，应标可重试失败、路由事件写明暂停原因，且不应留下抓取记录
    验证点：result.status=FAILED_RETRYABLE 且 message 含 RESOURCE_GUARD_PAUSED；两条 ROUTE_PLAN；fetch_log COUNT=0
    失败含义：明明没抓到数据却留下抓取日志，或路由事件不完整，排障会被误导
    """
    from backend.app.core.resource_guard import Decision, ResourceGuard, ResourceSnapshot
    from backend.app.datasources.service import DataSourceService
    from backend.app.datasources.source_registry import SourceRegistry
    from backend.app.sync.event_payload import parse_event_payload

    snap = ResourceSnapshot(
        available_memory_gb=0.1,
        disk_free_gb=0.1,
        process_rss_mb=100.0,
        project_size_gb=0.1,
    )

    def _pause(self):
        return Decision.PAUSE, "disk free space below threshold"

    monkeypatch.setattr(ResourceGuard, "snapshot", lambda self: snap)
    monkeypatch.setattr(ResourceGuard, "check", _pause)

    orch = _orchestrator(tmp_path)
    reg = SourceRegistry()
    reg.load()
    service = DataSourceService(
        source_registry=reg,
        data_root=tmp_path / "raw",
        job_events=orch._jobs,
    )
    spec = SyncJobSpec(
        run_id="run-svc-guard",
        job_id="job-svc-guard",
        job_type="incremental",
        data_domain="cn_equity_daily_bar",
        market_id="CN_A",
        source_id="baostock",
        adapter_id="baostock",
        date_start=None,
        date_end=None,
        instrument_id="000001",
        partition_key=None,
        trigger_reason=None,
    )
    result = orch.run_incremental(spec, datasource_service=service, clean_table="clean_guard")
    assert result.status == "FAILED_RETRYABLE"
    assert "RESOURCE_GUARD_PAUSED" in (result.message or "")
    with orch._cm.writer() as con:
        route_rows = con.execute(
            """
            SELECT payload_json FROM job_event_log
            WHERE job_id = ? AND event_type = 'ROUTE_PLAN'
            ORDER BY created_at ASC
            """,
            [result.job_id],
        ).fetchall()
    assert len(route_rows) == 2
    blocked = parse_event_payload(route_rows[1][0])
    assert blocked.get("route_status") == "RESOURCE_GUARD_PAUSED"
    with orch._cm.writer() as con:
        fetch_log_count = con.execute(
            "SELECT COUNT(*) FROM fetch_log WHERE job_id = ?", [result.job_id]
        ).fetchone()[0]
    assert fetch_log_count == 0


def test_servicePath_disabledRoute_setsFailedFinalWithFetchLog(tmp_path, monkeypatch) -> None:
    """覆盖范围：路由规划发现数据源能力不足时的终态失败
    测试对象：run_incremental + 禁用 SourceRoutePlanner
    目的/目标：没有可用数据源时，应明确失败并在抓取日志里记下「源被禁用」
    验证点：result.status=FAILED_FINAL；fetch_log.status=DISABLED_SOURCE
    失败含义：能力缺失仍去抓或日志缺失，运维看不出是源被禁用
    """
    from backend.app.core.resource_guard import Decision, ResourceGuard
    from backend.app.datasources.route_models import SourceRouteCandidate, SourceRoutePlan
    from backend.app.datasources.service import DataSourceService
    from backend.app.datasources.source_registry import SourceRegistry

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))

    class DisabledPlanner:
        def plan(self, **kwargs):
            return SourceRoutePlan(
                route_plan_id=SourceRoutePlan.new_id(),
                run_id=kwargs["run_id"],
                job_id=kwargs["job_id"],
                data_domain=kwargs["data_domain"],
                operation=kwargs["operation"],
                route_status="CAPABILITY_MISSING",
                selected_source_id=None,
                candidates=[
                    SourceRouteCandidate(
                        source_id="baostock",
                        role="Primary",
                        enabled=False,
                        allowed_domain=kwargs["data_domain"],
                        capability_declared=False,
                        disabled_reason="capability_missing",
                        skip_reason="capability_missing",
                    )
                ],
            )

    orch = _orchestrator(tmp_path)
    reg = SourceRegistry()
    reg.load()
    service = DataSourceService(
        source_registry=reg,
        data_root=tmp_path / "raw",
        route_planner=DisabledPlanner(),
        job_events=orch._jobs,
    )
    spec = SyncJobSpec(
        run_id="run-dis-svc",
        job_id="job-dis-svc",
        job_type="incremental",
        data_domain="cn_equity_realtime",
        market_id="CN_A",
        source_id="baostock",
        adapter_id="baostock",
        date_start=None,
        date_end=None,
        instrument_id="000001",
        partition_key=None,
        trigger_reason=None,
    )
    result = orch.run_incremental(spec, datasource_service=service, clean_table="clean_disabled")
    assert result.status == "FAILED_FINAL"
    with orch._cm.writer() as con:
        log_row = con.execute(
            "SELECT status FROM fetch_log WHERE job_id = ?", [result.job_id]
        ).fetchone()
    assert log_row is not None
    assert log_row[0] == "DISABLED_SOURCE"


def _simulate_production_profile(monkeypatch) -> None:
    """Drop pytest/test-hook signals so sync entry behaves like production profile."""
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("QMD_SYNC_ALLOW_ADAPTER", raising=False)


def test_r3ySync001_incremental_rejectsAdapterBypassInProductionProfile(
    tmp_path, monkeypatch
) -> None:
    """覆盖范围：生产环境下增量同步禁止直接注入 adapter 旁路
    测试对象：DataSyncOrchestrator.run_incremental(..., adapter=X) 无 datasource_service
    目的/目标：模拟生产配置时，必须走 DataSourceService 统一路由，不能跳过服务层直插适配器
    验证点：抛 ValueError match DataSourceService
    失败含义：生产入口可绕过路由和抓取审计，多源治理形同虚设
    """
    import pytest

    _simulate_production_profile(monkeypatch)
    orch = _orchestrator(tmp_path)
    spec = SyncJobSpec(
        run_id="run-r3y-inc",
        job_id="job-r3y-inc",
        job_type="incremental",
        data_domain="market_bar_1d",
        market_id="CN_A",
        source_id="baostock",
        adapter_id=None,
        date_start=None,
        date_end=None,
        instrument_id=None,
        partition_key=None,
        trigger_reason=None,
    )
    with pytest.raises(ValueError, match="DataSourceService"):
        orch.run_incremental(
            spec,
            adapter=_BackfillCountAdapter(),
            clean_table=_BackfillCountAdapter.CLEAN,
        )


def test_r3ySync001_backfill_rejectsAdapterBypassInProductionProfile(
    tmp_path, monkeypatch
) -> None:
    """覆盖范围：生产环境下历史回补禁止直接注入 adapter 旁路
    测试对象：DataSyncOrchestrator.run_backfill(..., adapter=X) 无 datasource_service
    目的/目标：与增量同步一样，生产配置下回补也必须经 DataSourceService 路由
    验证点：抛 ValueError match DataSourceService
    失败含义：回补可绕过统一路由和门禁，分片抓取脱离治理
    """
    from datetime import date

    import pytest

    _simulate_production_profile(monkeypatch)
    orch = _orchestrator(tmp_path)
    spec = SyncJobSpec(
        run_id="run-r3y-bf",
        job_id="job-r3y-bf",
        job_type="backfill",
        data_domain="market_bar_1d",
        market_id="CN_A",
        source_id="baostock",
        adapter_id=None,
        date_start=date(2026, 1, 1),
        date_end=date(2026, 1, 15),
        instrument_id=None,
        partition_key=None,
        trigger_reason="eco_catchup",
    )
    with pytest.raises(ValueError, match="DataSourceService"):
        orch.run_backfill(
            spec,
            adapter=_BackfillCountAdapter(),
            clean_table=_BackfillCountAdapter.CLEAN,
        )


def test_r3ySync001_reconcile_rejectsAdapterBypassInProductionProfile(
    tmp_path, monkeypatch
) -> None:
    """覆盖范围：生产环境下冲突调和禁止直接注入 adapter 旁路
    测试对象：DataSyncOrchestrator.run_reconcile(conflict_id, adapter=X)
    目的/目标：生产配置下调和也必须经 DataSourceService，与增量/回补守卫一致
    验证点：预插 source_conflict 后抛 ValueError match DataSourceService
    失败含义：调和可绕过服务层，三条主路径的守卫规则不一致
    """
    from datetime import UTC, datetime

    import pytest

    _simulate_production_profile(monkeypatch)
    orch = _orchestrator(tmp_path)
    conflict_id = "conflict-r3y"
    with orch._cm.writer() as con:
        con.execute(
            """
            INSERT INTO source_conflict (
                conflict_id, run_id, job_id, data_domain, market_id,
                field_name, primary_source, primary_value,
                competing_source, competing_value, normalized_diff,
                severity, reconcile_status, manual_review_required, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                conflict_id,
                "run-r3y-rc",
                "job-r3y-rc",
                "market_bar_1d",
                "CN_A",
                "close",
                "baostock",
                "100",
                "qmt_xtdata",
                "150",
                "0.5",
                "severe",
                "UNRESOLVED",
                True,
                datetime.now(UTC),
            ],
        )
    with pytest.raises(ValueError, match="DataSourceService"):
        orch.run_reconcile(conflict_id, adapter=_BackfillCountAdapter())


def test_r3ySync001_testHookAllowsAdapterBypassUnderPytest(
    tmp_path, monkeypatch
) -> None:
    """覆盖范围：pytest 会话内仍允许 adapter 测试路径
    测试对象：run_incremental(..., adapter=X) 在 PYTEST_CURRENT_TEST 存在时
    目的/目标：生产守卫只封线上配置，不应误伤现有 pytest 套件里的 adapter 测试
    验证点：result.status 属于 COMPLETED/FAILED_FINAL/MANUAL_REVIEW_REQUIRED/WAITING_RECONCILE
    失败含义：测试环境也被拦死，Batch D 契约测试会全面红灯
    """
    from backend.app.core.resource_guard import Decision, ResourceGuard

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    orch = _orchestrator(tmp_path)
    spec = SyncJobSpec(
        run_id="run-r3y-hook",
        job_id="job-r3y-hook",
        job_type="incremental",
        data_domain="market_bar_1d",
        market_id="CN_A",
        source_id="baostock",
        adapter_id=None,
        date_start=None,
        date_end=None,
        instrument_id=None,
        partition_key=None,
        trigger_reason=None,
    )
    result = orch.run_incremental(
        spec,
        adapter=_BackfillCountAdapter(),
        clean_table=_BackfillCountAdapter.CLEAN,
    )
    assert result.status in {
        "COMPLETED",
        "FAILED_FINAL",
        "MANUAL_REVIEW_REQUIRED",
        "WAITING_RECONCILE",
    }


def test_r3ySync001_explicitEnvDoesNotBypassProductionProfile(
    tmp_path, monkeypatch
) -> None:
    """覆盖范围：单独设置 QMD_SYNC_ALLOW_ADAPTER 不能恢复生产旁路
    测试对象：run_incremental(..., adapter=X) 模拟生产配置 + 误配环境变量
    目的/目标：运维误开环境变量开关，也不能绕过 DataSourceService 强制路由
    验证点：抛 ValueError match DataSourceService
    失败含义：一个 env 开关就能恢复 adapter 旁路，生产 fail-closed 被掏空
    """
    import pytest

    _simulate_production_profile(monkeypatch)
    monkeypatch.setenv("QMD_SYNC_ALLOW_ADAPTER", "1")
    orch = _orchestrator(tmp_path)
    spec = SyncJobSpec(
        run_id="run-r3y-env",
        job_id="job-r3y-env",
        job_type="incremental",
        data_domain="market_bar_1d",
        market_id="CN_A",
        source_id="baostock",
        adapter_id=None,
        date_start=None,
        date_end=None,
        instrument_id=None,
        partition_key=None,
        trigger_reason=None,
    )
    with pytest.raises(ValueError, match="DataSourceService"):
        orch.run_incremental(
            spec,
            adapter=_BackfillCountAdapter(),
            clean_table=_BackfillCountAdapter.CLEAN,
        )


def test_r3ySync001_privateIncrementalRunner_rejectsAdapterBypassInProductionProfile(
    tmp_path, monkeypatch
) -> None:
    """覆盖范围：私有增量 runner 入口同样拒绝生产 adapter 旁路
    测试对象：orch._incremental.run(..., adapter=X)
    目的/目标：调用方不能通过内部入口绕过公开 API 上的生产守卫
    验证点：模拟生产配置后抛 ValueError match DataSourceService
    失败含义：公开入口封住了，内部入口还能直插 adapter，守卫可被击穿
    """
    import pytest

    from backend.app.sync.orchestrator import _default_pipeline_config

    _simulate_production_profile(monkeypatch)
    orch = _orchestrator(tmp_path)
    spec = SyncJobSpec(
        run_id="run-r3y-priv",
        job_id="job-r3y-priv",
        job_type="incremental",
        data_domain="market_bar_1d",
        market_id="CN_A",
        source_id="baostock",
        adapter_id=None,
        date_start=None,
        date_end=None,
        instrument_id=None,
        partition_key=None,
        trigger_reason=None,
    )
    with pytest.raises(ValueError, match="DataSourceService"):
        orch._incremental.run(
            spec,
            adapter=_BackfillCountAdapter(),
            config=_default_pipeline_config(clean_table=_BackfillCountAdapter.CLEAN),
        )


def _reserved_job_spec(job_type: str, *, job_id: str = "job-reserved") -> SyncJobSpec:
    return SyncJobSpec(
        run_id="run-reserved",
        job_id=job_id,
        job_type=job_type,
        data_domain="market_bar_1d",
        market_id="CN_A",
        source_id="baostock",
        adapter_id=None,
        date_start=None,
        date_end=None,
        instrument_id=None,
        partition_key=None,
        trigger_reason=None,
    )


def test_syncJobContract_implementedTypes_matchRuntimeCallables() -> None:
    """覆盖范围：sync job 契约与 runtime 已实现类型 parity（VR-SYNC-002 / SYNC-01）
    测试对象：sync_job_contract.yaml · IMPLEMENTED_JOB_TYPES · DataSyncOrchestrator.run_*
    目的/目标：契约声明的已实现 job 类型须与模块常量及可调用 run_* 方法一一对应
    验证点：YAML implemented == IMPLEMENTED_JOB_TYPES；implemented run_* 集相等；reserved 分离
    失败含义：调用方或 CLI 无法从契约判断哪些 job 真正可跑，矩阵与代码漂移
    """
    from backend.app.sync.contract import (
        IMPLEMENTED_JOB_TYPES,
        RESERVED_JOB_TYPES,
        load_sync_job_contract,
    )
    from backend.app.sync.orchestrator import DataSyncOrchestrator

    contract = load_sync_job_contract()
    yaml_impl = frozenset(contract["implemented_job_types"])
    yaml_reserved = frozenset(contract["reserved_job_types"])
    assert yaml_impl == IMPLEMENTED_JOB_TYPES
    assert yaml_reserved == RESERVED_JOB_TYPES
    assert yaml_impl.isdisjoint(yaml_reserved)
    run_suffixes = frozenset(
        name[4:]
        for name in dir(DataSyncOrchestrator)
        if name.startswith("run_") and callable(getattr(DataSyncOrchestrator, name))
    )
    assert run_suffixes == IMPLEMENTED_JOB_TYPES | RESERVED_JOB_TYPES


def _assert_deferred_job_type_error(exc_info, *, job_type: str) -> None:
    from backend.app.sync.contract import (
        DEFERRED_JOB_TYPE_CODE,
        DEFERRED_OWNER,
        DEFERRED_PHASE,
        DOCS_ANCHOR_D2_P1_1,
    )

    err = exc_info.value
    assert err.code == DEFERRED_JOB_TYPE_CODE
    assert err.job_type == job_type
    assert err.owner == DEFERRED_OWNER
    assert err.phase == DEFERRED_PHASE
    assert err.docs_anchor == DOCS_ANCHOR_D2_P1_1
    assert DOCS_ANCHOR_D2_P1_1 in str(err)
    assert DEFERRED_OWNER in str(err)
    assert DEFERRED_PHASE in str(err)


def test_syncJobContract_deferredErrorYaml_parityWithRuntimeConstants() -> None:
    """覆盖范围：deferred_error 契约字段与 runtime 常量 parity（ZO-05/06）
    测试对象：sync_job_contract.yaml deferred_error · contract.py 常量
    目的/目标：owner/phase/code/docs_anchor 单源 YAML 与模块常量一致，防漂移
    验证点：load_sync_job_contract() deferred_error 各字段 == DEFERRED_* 常量
    失败含义：调用方或 registry 读到与 runtime 不一致的 deferred 元数据
    """
    from backend.app.sync.contract import (
        DEFERRED_JOB_TYPE_CODE,
        DEFERRED_OWNER,
        DEFERRED_PHASE,
        DOCS_ANCHOR_D2_P1_1,
        load_sync_job_contract,
    )

    deferred = load_sync_job_contract()["deferred_error"]
    assert deferred["code"] == DEFERRED_JOB_TYPE_CODE
    assert deferred["owner"] == DEFERRED_OWNER
    assert deferred["phase"] == DEFERRED_PHASE
    assert deferred["docs_anchor"] == DOCS_ANCHOR_D2_P1_1


def test_syncJob_reservedFullLoad_returnsDeferredJobTypeError(tmp_path) -> None:
    """覆盖范围：reserved full_load 返回稳定 deferred 错误（VR-SYNC-002 / SYNC-03）
    测试对象：DataSyncOrchestrator.run_full_load
    目的/目标：全量同步未实现时须抛 DeferredJobTypeError，不得裸 NotImplementedError
    验证点：code=DEFERRED_JOB_TYPE；docs_anchor 含 D2-P1-1
    失败含义：调用方收到 NIE 或静默成功，误以为全量同步已可用
    """
    import pytest

    from backend.app.sync.contract import DeferredJobTypeError

    orch = _orchestrator(tmp_path)
    with pytest.raises(DeferredJobTypeError) as exc_info:
        orch.run_full_load(_reserved_job_spec("full_load"))
    _assert_deferred_job_type_error(exc_info, job_type="full_load")


def test_syncJob_reservedDataQuality_returnsDeferredJobTypeError(tmp_path) -> None:
    """覆盖范围：reserved data_quality 返回稳定 deferred 错误（VR-SYNC-002 / SYNC-03）
    测试对象：DataSyncOrchestrator.run_data_quality
    目的/目标：独立质检 job 未实现时须抛 DeferredJobTypeError
    验证点：code=DEFERRED_JOB_TYPE；docs_anchor 含 D2-P1-1
    失败含义：质检入口泄漏 NIE 或空操作，生产 job 无效果
    """
    import pytest

    from backend.app.sync.contract import DeferredJobTypeError

    orch = _orchestrator(tmp_path)
    with pytest.raises(DeferredJobTypeError) as exc_info:
        orch.run_data_quality(_reserved_job_spec("data_quality"))
    _assert_deferred_job_type_error(exc_info, job_type="data_quality")


def test_syncJob_reservedRevisionAudit_returnsDeferredJobTypeError(tmp_path) -> None:
    """覆盖范围：reserved revision_audit 返回稳定 deferred 错误（VR-SYNC-002 / SYNC-03）
    测试对象：DataSyncOrchestrator.run_revision_audit
    目的/目标：修订审计 runner 未实现时须有显式 deferred 薄入口
    验证点：code=DEFERRED_JOB_TYPE；docs_anchor 含 D2-P1-1
    失败含义：revision_audit 无入口或抛 NIE，状态机可达但无法安全调用
    """
    import pytest

    from backend.app.sync.contract import DeferredJobTypeError

    orch = _orchestrator(tmp_path)
    with pytest.raises(DeferredJobTypeError) as exc_info:
        orch.run_revision_audit(_reserved_job_spec("revision_audit"))
    _assert_deferred_job_type_error(exc_info, job_type="revision_audit")


def test_syncJob_incremental_crashWindow_leavesWritingWithWriteId(tmp_path, monkeypatch) -> None:
    """覆盖范围：写提交后 COMPLETED 前 crash 窗口（VR-SYNC-001 / SYNC-05）
    测试对象：IncrementalJobRunner.run + post_write_pre_complete_hook
    目的/目标：写成功但进程在 COMPLETED 前崩溃时，job 应停在 WRITING 且 write_id 已落库
    验证点：hook 抛错后 status=WRITING 且 write_id 非空
    失败含义：过早 COMPLETED 或丢失 write_id，crash 后无法检测/恢复
    """
    import pytest

    from backend.app.core.resource_guard import Decision, ResourceGuard
    from backend.app.sync.orchestrator import _default_pipeline_config

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    orch = _orchestrator(tmp_path)
    spec = _reserved_job_spec("incremental", job_id="job-crash-window")

    def _crash_after_write(job_id: str, write_id: str) -> None:
        raise RuntimeError("simulated crash after write commit")

    with pytest.raises(RuntimeError, match="simulated crash"):
        orch._incremental.run(
            spec,
            adapter=_BackfillCountAdapter(),
            config=_default_pipeline_config(clean_table=_BackfillCountAdapter.CLEAN),
            post_write_pre_complete_hook=_crash_after_write,
        )

    with orch._cm.reader() as con:
        row = con.execute(
            "SELECT status, write_id FROM data_sync_job WHERE job_id = ?",
            [spec.job_id],
        ).fetchone()
    assert row is not None
    assert row[0] == "WRITING"
    assert row[1]


def test_syncJob_incremental_recoverStuckWriting_completesWithoutDoubleWrite(
    tmp_path, monkeypatch
) -> None:
    """覆盖范围：WRITING+write_id 卡死恢复（VR-SYNC-001 / SYNC-06 路径 A）
    测试对象：DataSyncOrchestrator.recover_stuck_writing_job
    目的/目标：crash-window 后恢复应 COMPLETED 且不重复写入 clean 表
    验证点：recovery 后 status=COMPLETED；clean 行数与 crash 后一致
    失败含义：重复写或永久 WRITING，数据重复或作业无法收尾
    """
    from backend.app.core.resource_guard import Decision, ResourceGuard
    from backend.app.sync.orchestrator import _default_pipeline_config

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    orch = _orchestrator(tmp_path)
    spec = _reserved_job_spec("incremental", job_id="job-recover-writing")
    clean = _BackfillCountAdapter.CLEAN

    def _crash_after_write(job_id: str, write_id: str) -> None:
        raise RuntimeError("simulated crash after write commit")

    try:
        orch._incremental.run(
            spec,
            adapter=_BackfillCountAdapter(),
            config=_default_pipeline_config(clean_table=clean),
            post_write_pre_complete_hook=_crash_after_write,
        )
    except RuntimeError:
        pass

    with orch._cm.reader() as con:
        rows_before = con.execute(f"SELECT COUNT(*) FROM {clean}").fetchone()[0]

    result = orch.recover_stuck_writing_job(spec.job_id)
    assert result.status == "COMPLETED"
    assert result.write_id

    with orch._cm.reader() as con:
        rows_after = con.execute(f"SELECT COUNT(*) FROM {clean}").fetchone()[0]
        status = con.execute(
            "SELECT status FROM data_sync_job WHERE job_id = ?",
            [spec.job_id],
        ).fetchone()[0]
    assert rows_after == rows_before
    assert status == "COMPLETED"


def test_syncJob_incremental_hook_rejectedOutsidePytest(tmp_path, monkeypatch) -> None:
    """覆盖范围：post_write_pre_complete_hook 非 pytest 环境 fail-closed（ZO-07）
    测试对象：IncrementalJobRunner.run + post_write_pre_complete_hook guard
    目的/目标：生产路径不得注入 crash-window hook，须显式拒绝
    验证点：sync_adapter_bypass_allowed=False 时传 hook 抛 ValueError 且含 pytest-only
    失败含义：hook 泄漏到生产，可被滥用改变 COMPLETED 时序
    """
    import pytest

    from backend.app.core.resource_guard import Decision, ResourceGuard
    from backend.app.sync.orchestrator import _default_pipeline_config

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    monkeypatch.setattr(
        "backend.app.sync.runners.guard_runner_direct_adapter_bypass",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        "backend.app.sync.runners.sync_adapter_bypass_allowed",
        lambda: False,
    )
    orch = _orchestrator(tmp_path)
    spec = _reserved_job_spec("incremental", job_id="job-hook-guard")

    with pytest.raises(ValueError, match="pytest-only"):
        orch._incremental.run(
            spec,
            adapter=_BackfillCountAdapter(),
            config=_default_pipeline_config(clean_table=_BackfillCountAdapter.CLEAN),
            post_write_pre_complete_hook=lambda _jid, _wid: None,
        )


def test_syncJob_recoverStuckWriting_rejectsInvalidState(tmp_path) -> None:
    """覆盖范围：recover_stuck_writing_job 对非法状态 fail-closed（ZO-07）
    测试对象：DataSyncOrchestrator.recover_stuck_writing_job
    目的/目标：非 WRITING+write_id 作业不得被误恢复为 COMPLETED
    验证点：CREATED 作业调用 recovery 抛 ValueError 且含 WRITING
    失败含义：recovery 误操作正常作业，掩盖真实失败或跳过写入
    """
    import pytest

    orch = _orchestrator(tmp_path)
    spec = _reserved_job_spec("incremental", job_id="job-recover-invalid")
    orch.create_job(spec)

    with pytest.raises(ValueError, match="WRITING"):
        orch.recover_stuck_writing_job(spec.job_id)
