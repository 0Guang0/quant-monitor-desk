"""DataSyncOrchestrator — ingestion job orchestration facade (Batch D)."""

from __future__ import annotations

from backend.app.core.resource_guard import Decision, ResourceGuard, format_pause_event
from backend.app.datasources.base_adapter import BaseDataAdapter
from backend.app.db.connection import ConnectionManager
from backend.app.sync.jobs import SyncJobResult, SyncJobSpec, SyncJobStateMachine
from backend.app.sync.pipeline import SyncValidationPipeline, SyncWritePipeline
from backend.app.sync.runners import (
    BackfillShardRunner,
    IncrementalJobRunner,
    PipelineConfig,
    ReconcileJobRunner,
)


class DataSyncOrchestrator:
    def __init__(self, connection_manager: ConnectionManager) -> None:
        self._cm = connection_manager
        self._jobs = SyncJobStateMachine(connection_manager)
        self._validation = SyncValidationPipeline(connection_manager)
        self._write = SyncWritePipeline(connection_manager)
        self._incremental = IncrementalJobRunner(
            self._jobs,
            self._validation,
            self._write,
            begin_fetching=self.begin_fetching,
        )
        self._backfill = BackfillShardRunner(
            self._jobs,
            self._validation,
            self._write,
            begin_fetching=self.begin_fetching,
            emit_event=self.emit_event,
        )
        self._reconcile = ReconcileJobRunner(self._jobs)

    def bootstrap(self, *, sync_registry: bool = False) -> None:
        if sync_registry:
            from backend.app.datasources.source_registry import SourceRegistry

            registry = SourceRegistry()
            registry.load()
            with self._cm.writer() as con:
                registry.sync_to_db(con, tombstone_missing=True)

    def create_job(self, spec: SyncJobSpec) -> str:
        return self._jobs.create_job(spec)

    def begin_fetching(self, job_id: str) -> bool:
        """Enter FETCHING after ResourceGuard.check(); return False if blocked."""
        blocked_message: str | None = None
        blocked_error_type: str | None = None
        with self._cm.writer() as con:
            row = con.execute(
                "SELECT status FROM data_sync_job WHERE job_id = ?", [job_id]
            ).fetchone()
            if row is None:
                raise KeyError(f"unknown job_id: {job_id!r}")
            if row[0] != "PLANNED":
                raise ValueError(f"job {job_id!r} must be PLANNED before fetching, got {row[0]!r}")
            guard = ResourceGuard(con=con)
            decision, reason = guard.check()
            if decision in (Decision.PAUSE, Decision.HARD_STOP):
                snap = guard.snapshot()
                blocked_message = format_pause_event(decision, reason, snap, guard.profile)
                blocked_error_type = decision.value
        if blocked_message is not None:
            self._jobs.transition(
                job_id,
                "FAILED_RETRYABLE",
                message=blocked_message,
                event_type="RESOURCE_GUARD_BLOCKED",
                error_type=blocked_error_type,
                error_message=blocked_message,
            )
            return False
        self._jobs.transition(job_id, "FETCHING")
        return True

    def emit_event(
        self,
        job_id: str,
        *,
        task_id: str | None = None,
        event_type: str = "CUSTOM",
        message: str = "",
        old_status: str | None = None,
        new_status: str | None = None,
        payload_json: str | None = None,
    ) -> str:
        return self._jobs.emit_custom_event(
            job_id,
            task_id=task_id,
            event_type=event_type,
            message=message,
            old_status=old_status,
            new_status=new_status,
            payload_json=payload_json,
        )

    def run_incremental(
        self,
        spec: SyncJobSpec,
        *,
        adapter: BaseDataAdapter,
        clean_table: str,
        conflict_staging_table: str | None = None,
        write_mode: str = "append_only",
        primary_keys: tuple[str, ...] = ("instrument_id", "trade_date"),
        required_fields: tuple[str, ...] = ("close", "source_used"),
    ) -> SyncJobResult:
        return self._incremental.run(
            spec,
            adapter=adapter,
            config=PipelineConfig(
                clean_table=clean_table,
                conflict_staging_table=conflict_staging_table,
                write_mode=write_mode,
                primary_keys=primary_keys,
                required_fields=required_fields,
            ),
        )

    def run_backfill(
        self,
        spec: SyncJobSpec,
        *,
        adapter: BaseDataAdapter,
        clean_table: str,
        conflict_staging_table: str | None = None,
        write_mode: str = "append_only",
        primary_keys: tuple[str, ...] = ("instrument_id", "trade_date"),
        required_fields: tuple[str, ...] = ("close", "source_used"),
    ) -> list[SyncJobResult]:
        config = PipelineConfig(
            clean_table=clean_table,
            conflict_staging_table=conflict_staging_table,
            write_mode=write_mode,
            primary_keys=primary_keys,
            required_fields=required_fields,
        )
        return self._backfill.run(spec, adapter=adapter, config=config)

    def run_reconcile(self, conflict_id: str, *, adapter: BaseDataAdapter) -> SyncJobResult:
        return self._reconcile.run(conflict_id, adapter=adapter)
