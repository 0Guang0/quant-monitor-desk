"""Tests for DataSyncOrchestrator core (Batch D §8.3)."""

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


def test_orchestrator_fetchFailure_redactsErrorInJobEventLog(tmp_path) -> None:
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


def test_orchestrator_fetchBlockedOnHardStop_setsFailedRetryable(
    tmp_path, monkeypatch
) -> None:
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


def test_orchestrator_fetchAllowedWhenGuardOk_proceedsToFetching(
    tmp_path, monkeypatch
) -> None:
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
    from datetime import date

    from backend.app.core.resource_guard import Decision, ResourceGuard
    from backend.app.sync.jobs import ECO_MAX_BACKFILL_DAYS_PER_TASK, plan_backfill_shards

    shards = plan_backfill_shards(date(2026, 1, 1), date(2026, 3, 31))
    assert len(shards) >= 3
    assert all(
        (end - start).days + 1 <= ECO_MAX_BACKFILL_DAYS_PER_TASK
        for _tid, start, end in shards
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
    results = orch.run_backfill(spec, adapter=_BackfillCountAdapter())
    assert len(results) >= 3


def test_backfillJob_recordsTriggerReason(tmp_path, monkeypatch) -> None:
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
    orch.run_backfill(spec, adapter=_BackfillCountAdapter())
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


def test_backfillJob_eachShard_callsResourceGuardBeforeFetching(
    tmp_path, monkeypatch
) -> None:
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
    orch.run_backfill(spec, adapter=_BackfillCountAdapter())
    assert len(calls) >= 3


def test_backfillJob_midShardFailure_preservesCompletedTasks(tmp_path, monkeypatch) -> None:
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
    results = orch.run_backfill(spec, adapter=_BackfillFailOnSecondAdapter())
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
    """Minimal adapter for backfill shard counting tests."""

    source_id = "baostock"
    supported_domains = frozenset({"market_bar_1d"})

    def fetch(self, req, *, con, job_id=None):
        from backend.app.datasources.fetch_result import FetchResult

        return FetchResult(
            run_id=req.run_id,
            source_id=self.source_id,
            data_domain=req.data_domain,
            status="SUCCESS",
            row_count=1,
            fetch_time="2026-06-17T10:00:00Z",
            staging_table="stg_backfill",
            raw_file_paths=["/tmp/bf.parquet"],
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


def test_reconcileJob_severeConflict_entersWaitingReconcile(
    tmp_path, registry_yaml_fixture, monkeypatch
) -> None:
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
