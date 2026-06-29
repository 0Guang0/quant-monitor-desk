"""DataSyncOrchestrator — ingestion job orchestration facade (Batch D)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from backend.app.core.resource_guard import Decision, ResourceGuard, format_pause_event
from backend.app.datasources.base_adapter import BaseDataAdapter
from backend.app.db.connection import ConnectionManager
from backend.app.sync.contract import raise_deferred_job_type
from backend.app.sync.jobs import SyncJobResult, SyncJobSpec, SyncJobStateMachine
from backend.app.sync.pipeline import SyncValidationPipeline, SyncWritePipeline
from backend.app.sync.runners import (
    BackfillShardRunner,
    IncrementalJobRunner,
    PipelineConfig,
    QualityJobRunner,
    ReconcileJobRunner,
    guard_production_adapter_bypass,
    guard_production_datasource_service_required,
)


@dataclass(frozen=True, slots=True)
class OrchestratorJobHandler:
    """Registry row for orchestrator job-type → runner/deferred entry (R3F-BR-04 / D7-P1-1)."""

    job_type: str
    entrypoint: str
    kind: Literal["runner", "deferred", "utility"]
    runner_attr: str | None = None


ORCHESTRATOR_HANDLER_REGISTRY: dict[str, OrchestratorJobHandler] = {
    "incremental": OrchestratorJobHandler(
        "incremental", "run_incremental", "runner", "_incremental"
    ),
    "backfill": OrchestratorJobHandler("backfill", "run_backfill", "runner", "_backfill"),
    "reconcile": OrchestratorJobHandler("reconcile", "run_reconcile", "runner", "_reconcile"),
    "full_load": OrchestratorJobHandler("full_load", "run_full_load", "deferred"),
    "data_quality": OrchestratorJobHandler(
        "data_quality", "run_data_quality", "runner", "_quality"
    ),
    "revision_audit": OrchestratorJobHandler(
        "revision_audit", "run_revision_audit", "runner", "_quality"
    ),
    "recover_stuck_writing_job": OrchestratorJobHandler(
        "recover_stuck_writing_job", "recover_stuck_writing_job", "utility"
    ),
}


def orchestrator_handler_registry() -> dict[str, OrchestratorJobHandler]:
    """Return a copy of the frozen handler registry (R3F-BR-04)."""
    return dict(ORCHESTRATOR_HANDLER_REGISTRY)


def _default_pipeline_config(
    *,
    clean_table: str,
    conflict_staging_table: str | None = None,
    write_mode: str = "append_only",
    primary_keys: tuple[str, ...] = ("instrument_id", "trade_date"),
    required_fields: tuple[str, ...] = ("close", "source_used"),
) -> PipelineConfig:
    """Shared PipelineConfig factory for incremental/backfill (SY-06)."""
    return PipelineConfig(
        clean_table=clean_table,
        conflict_staging_table=conflict_staging_table,
        write_mode=write_mode,
        primary_keys=primary_keys,
        required_fields=required_fields,
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
        self._quality = QualityJobRunner(self._jobs, self._validation)

    def handler_registry(self) -> dict[str, OrchestratorJobHandler]:
        """Expose job-type handler map for ops/CLI matrix (R3F-BR-04)."""
        return orchestrator_handler_registry()

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
        blocked_event_type: str = "RESOURCE_GUARD_PAUSED"
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
                blocked_event_type = (
                    "RESOURCE_GUARD_HARD_STOP"
                    if decision == Decision.HARD_STOP
                    else "RESOURCE_GUARD_PAUSED"
                )
        if blocked_message is not None:
            self._jobs.transition(
                job_id,
                "FAILED_RETRYABLE",
                message=blocked_message,
                event_type=blocked_event_type,
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
        adapter: BaseDataAdapter | None = None,
        datasource_service=None,
        clean_table: str,
        conflict_staging_table: str | None = None,
        write_mode: str = "append_only",
        primary_keys: tuple[str, ...] = ("instrument_id", "trade_date"),
        required_fields: tuple[str, ...] = ("close", "source_used"),
    ) -> SyncJobResult:
        guard_production_adapter_bypass(
            adapter=adapter,
            datasource_service=datasource_service,
            entry="run_incremental",
        )
        guard_production_datasource_service_required(
            adapter=adapter,
            datasource_service=datasource_service,
            entry="run_incremental",
        )
        fetch_callable = None
        if datasource_service is not None:
            jobs = self._jobs

            def _service_fetch(req, con, job_id, operation=None):
                return datasource_service.fetch(
                    req,
                    con=con,
                    job_id=job_id,
                    operation=operation,
                    on_enter_fetching=lambda: jobs.transition(job_id, "FETCHING", con=con),
                )

            fetch_callable = _service_fetch
        return self._incremental.run(
            spec,
            adapter=adapter,
            fetch_callable=fetch_callable,
            config=_default_pipeline_config(
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
        adapter: BaseDataAdapter | None = None,
        datasource_service=None,
        clean_table: str,
        conflict_staging_table: str | None = None,
        write_mode: str = "append_only",
        primary_keys: tuple[str, ...] = ("instrument_id", "trade_date"),
        required_fields: tuple[str, ...] = ("close", "source_used"),
    ) -> list[SyncJobResult]:
        guard_production_adapter_bypass(
            adapter=adapter,
            datasource_service=datasource_service,
            entry="run_backfill",
        )
        guard_production_datasource_service_required(
            adapter=adapter,
            datasource_service=datasource_service,
            entry="run_backfill",
        )
        fetch_callable = None
        if datasource_service is not None:
            jobs = self._jobs

            def _service_fetch(req, con, job_id, operation=None):
                return datasource_service.fetch(
                    req,
                    con=con,
                    job_id=job_id,
                    operation=operation,
                    on_enter_fetching=lambda: jobs.transition(job_id, "FETCHING", con=con),
                )

            fetch_callable = _service_fetch
        config = _default_pipeline_config(
            clean_table=clean_table,
            conflict_staging_table=conflict_staging_table,
            write_mode=write_mode,
            primary_keys=primary_keys,
            required_fields=required_fields,
        )
        return self._backfill.run(
            spec,
            adapter=adapter,
            fetch_callable=fetch_callable,
            config=config,
        )

    def run_reconcile(self, conflict_id: str, *, adapter: BaseDataAdapter) -> SyncJobResult:
        guard_production_adapter_bypass(
            adapter=adapter,
            datasource_service=None,
            entry="run_reconcile",
        )
        return self._reconcile.run(conflict_id, adapter=adapter)

    def run_full_load(self, spec: SyncJobSpec, **kwargs) -> SyncJobResult:
        """Reserved job type — stable deferred error (D2-P1-1 / VR-SYNC-002)."""
        raise_deferred_job_type(spec.job_type, entrypoint="run_full_load")

    def run_data_quality(self, spec: SyncJobSpec, **kwargs) -> SyncJobResult:
        """Data quality runner (R3F-SH-03)."""
        return self._quality.run_data_quality(spec)

    def run_revision_audit(self, spec: SyncJobSpec, **kwargs) -> SyncJobResult:
        """Revision audit runner (R3F-SH-02)."""
        return self._quality.run_revision_audit(spec)

    def recover_stuck_writing_job(self, job_id: str) -> SyncJobResult:
        """Complete a job stuck in WRITING after write commit (ADR-001 crash-window)."""
        with self._cm.reader() as con:
            row = con.execute(
                "SELECT status, write_id FROM data_sync_job WHERE job_id = ?",
                [job_id],
            ).fetchone()
        if row is None:
            raise KeyError(f"unknown job_id: {job_id!r}")
        status, write_id = row
        if status != "WRITING" or not write_id:
            raise ValueError(
                f"job {job_id!r} must be WRITING with write_id set for recovery, "
                f"got status={status!r} write_id={write_id!r}"
            )
        self._jobs.transition(job_id, "COMPLETED", message="recovered after crash-window")
        return SyncJobResult(job_id=job_id, status="COMPLETED", write_id=write_id)
