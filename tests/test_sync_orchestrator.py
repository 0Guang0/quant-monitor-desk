"""数据同步编排器测试（Batch D）。

覆盖范围：作业创建与事件、资源门禁、历史回补分片、多源冲突、注册表引导及生产路由守卫。
"""

from __future__ import annotations

from pathlib import Path

from backend.app.datasources.source_registry import SourceRegistry
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.sync.jobs import SyncJobSpec
from backend.app.sync.orchestrator import DataSyncOrchestrator


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
    from datetime import date

    from backend.app.core.resource_guard import Decision, ResourceGuard
    from backend.app.sync.jobs import ECO_MAX_BACKFILL_DAYS_PER_TASK, plan_backfill_shards

    shards = plan_backfill_shards(date(2026, 1, 1), date(2026, 3, 31))
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
        date_start=date(2026, 1, 1),
        date_end=date(2026, 3, 31),
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
        date_start=date(2026, 1, 1),
        date_end=date(2026, 2, 15),
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
        date_start=date(2026, 1, 1),
        date_end=date(2026, 3, 31),
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
        date_start=date(2026, 1, 1),
        date_end=date(2026, 3, 31),
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
    env = os.environ.copy()
    proc = subprocess.run(
        [sys.executable, "scripts/sync_registry.py", "--yaml", str(registry_yaml_fixture)],
        cwd=str(Path(__file__).resolve().parents[1]),
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
        con.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {STG} (
                instrument_id VARCHAR, trade_date VARCHAR, close DOUBLE,
                source_used VARCHAR, batch_id VARCHAR, source_id VARCHAR
            )
            """
        )
        con.execute(f"CREATE TABLE IF NOT EXISTS clean_route AS SELECT * FROM {STG} WHERE 1=0")

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
