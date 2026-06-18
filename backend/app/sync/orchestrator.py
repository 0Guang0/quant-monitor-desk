"""DataSyncOrchestrator — ingestion job orchestration (Batch D)."""

from __future__ import annotations

import json

from backend.app.core.resource_guard import Decision, ResourceGuard, format_pause_event
from backend.app.datasources.base_adapter import BaseDataAdapter
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.db.connection import ConnectionManager
from backend.app.db.validation_gate import DbValidationGate
from backend.app.db.write_manager import WriteManager, WriteRequest
from backend.app.sync.jobs import (
    SyncJobResult,
    SyncJobSpec,
    SyncJobStateMachine,
    normalize_backfill_trigger_reason,
    plan_backfill_shards,
)
from backend.app.validators.data_quality import DataQualityRequest, DataQualityValidator
from backend.app.validators.source_conflict import SourceConflictRequest, SourceConflictValidator


class DataSyncOrchestrator:
    def __init__(self, connection_manager: ConnectionManager) -> None:
        self._cm = connection_manager
        self._jobs = SyncJobStateMachine(connection_manager)

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
                raise ValueError(
                    f"job {job_id!r} must be PLANNED before fetching, got {row[0]!r}"
                )
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
        job_id = self.create_job(spec)
        self._jobs.transition(job_id, "PLANNED")
        if not self.begin_fetching(job_id):
            return SyncJobResult(
                job_id=job_id,
                status="FAILED_RETRYABLE",
                message="resource guard blocked",
            )
        req = FetchRequest(
            run_id=spec.run_id,
            source_id=spec.source_id,
            data_domain=spec.data_domain,
            market_id=spec.market_id,
            instrument_id=spec.instrument_id,
        )
        with self._cm.writer() as con:
            fetch_result = adapter.fetch(req, con=con, job_id=job_id)
        if fetch_result.status != "SUCCESS" or not fetch_result.staging_table:
            self._jobs.transition(
                job_id,
                "FAILED_FINAL",
                message=fetch_result.error_message or fetch_result.status,
            )
            return SyncJobResult(
                job_id=job_id,
                status="FAILED_FINAL",
                message=fetch_result.error_message,
            )
        staging_table = fetch_result.staging_table
        self._jobs.transition(job_id, "STAGED")
        self._jobs.transition(job_id, "VALIDATING")
        with self._cm.writer() as con:
            quality = DataQualityValidator().validate_table(
                con,
                DataQualityRequest(
                    run_id=spec.run_id,
                    job_id=job_id,
                    data_domain=spec.data_domain,
                    source_id=spec.source_id,
                    staging_table=staging_table,
                    primary_keys=primary_keys,
                    required_fields=required_fields,
                    rule_set_id="p0_round_1",
                ),
                expected_columns=primary_keys + required_fields + ("batch_id", "source_id"),
                timestamp_fields=("trade_date",),
            )
            self._update_job_report_ids(
                con, job_id, validation_report_id=quality.validation_report_id
            )
            if quality.status == "FAILED" or not quality.can_write_clean:
                self._jobs.transition(
                    job_id, "MANUAL_REVIEW_REQUIRED", message="data quality failed", con=con
                )
                return SyncJobResult(
                    job_id=job_id,
                    status="MANUAL_REVIEW_REQUIRED",
                    validation_report_id=quality.validation_report_id,
                    message="data quality failed",
                )
            conflict_report_id: str | None = None
            if conflict_staging_table is not None:
                validation_sources = tuple(
                    s for s in ("qmt_xtdata", "baostock") if s != spec.source_id
                ) or ("qmt_xtdata",)
                conflict = SourceConflictValidator().validate_table(
                    con,
                    SourceConflictRequest(
                        run_id=spec.run_id,
                        job_id=job_id,
                        data_domain=spec.data_domain,
                        primary_source=spec.source_id,
                        validation_sources=validation_sources,
                        key_fields=primary_keys,
                        comparable_fields=("close",),
                        tolerance_rule_set_id="p0_round_1",
                    ),
                    staging_table=conflict_staging_table,
                )
                conflict_report_id = conflict.conflict_report_id
                self._update_job_report_ids(con, job_id, conflict_report_id=conflict_report_id)
                if conflict.status == "SEVERE_CONFLICT":
                    self._jobs.transition(
                        job_id, "WAITING_RECONCILE", message="severe conflict", con=con
                    )
                    return SyncJobResult(
                        job_id=job_id,
                        status="WAITING_RECONCILE",
                        validation_report_id=quality.validation_report_id,
                        conflict_report_id=conflict_report_id,
                    )
            self._jobs.transition(job_id, "READY_TO_WRITE", con=con)
            self._jobs.transition(job_id, "WRITING", con=con)
            write_result = WriteManager(self._cm, DbValidationGate(self._cm)).write(
                WriteRequest(
                    run_id=spec.run_id,
                    job_id=job_id,
                    target_table=clean_table,
                    staging_table=staging_table,
                    write_mode=write_mode,
                    primary_keys=primary_keys,
                    validation_report_id=quality.validation_report_id,
                    source_used=spec.source_id,
                ),
                con=con,
                own_transaction=False,
            )
            self._update_job_report_ids(con, job_id, write_id=write_result.write_id)
            if write_result.status != "SUCCESS":
                self._jobs.transition(job_id, "FAILED_FINAL", message="write failed", con=con)
                return SyncJobResult(
                    job_id=job_id,
                    status="FAILED_FINAL",
                    validation_report_id=quality.validation_report_id,
                    conflict_report_id=conflict_report_id,
                    message="write failed",
                )
        # COMPLETED after writer txn closes: write path already committed; status audit is separate.
        self._jobs.transition(job_id, "COMPLETED")
        return SyncJobResult(
            job_id=job_id,
            status="COMPLETED",
            validation_report_id=quality.validation_report_id,
            conflict_report_id=conflict_report_id,
            write_id=write_result.write_id,
        )

    def run_backfill(
        self,
        spec: SyncJobSpec,
        *,
        adapter: BaseDataAdapter,
    ) -> list[SyncJobResult]:
        if spec.date_start is None or spec.date_end is None:
            raise ValueError("backfill requires date_start and date_end")
        trigger_reason = normalize_backfill_trigger_reason(spec.trigger_reason)
        shards = plan_backfill_shards(spec.date_start, spec.date_end)
        job_id = self.create_job(spec)
        self._jobs.transition(job_id, "PLANNED")
        results: list[SyncJobResult] = []
        for idx, (task_id, shard_start, shard_end) in enumerate(shards):
            payload = json.dumps({"trigger_reason": trigger_reason})
            self.emit_event(
                job_id,
                task_id=task_id,
                event_type="BACKFILL_SHARD",
                payload_json=payload,
            )
            if not self.begin_fetching(job_id):
                self._jobs.transition(
                    job_id,
                    "FAILED_RETRYABLE",
                    task_id=task_id,
                    message="resource guard blocked",
                )
                results.append(
                    SyncJobResult(job_id=job_id, status="FAILED_RETRYABLE", message="guard")
                )
                return results
            req = FetchRequest(
                run_id=spec.run_id,
                source_id=spec.source_id,
                data_domain=spec.data_domain,
                market_id=spec.market_id,
                instrument_id=spec.instrument_id,
                start_time=shard_start.isoformat(),
                end_time=shard_end.isoformat(),
            )
            with self._cm.writer() as con:
                fetch_result = adapter.fetch(req, con=con, job_id=job_id)
            if fetch_result.status != "SUCCESS":
                self._jobs.transition(
                    job_id,
                    "FAILED_RETRYABLE",
                    task_id=task_id,
                    message=fetch_result.error_message or "shard failed",
                )
                results.append(
                    SyncJobResult(
                        job_id=job_id,
                        status="FAILED_RETRYABLE",
                        message=fetch_result.error_message,
                    )
                )
                return results
            self._jobs.transition(job_id, "STAGED", task_id=task_id)
            self.emit_event(
                job_id,
                task_id=task_id,
                event_type="SHARD_COMPLETE",
                message=f"shard {task_id} completed",
            )
            if idx < len(shards) - 1:
                self._jobs.transition(
                    job_id,
                    "PLANNED",
                    task_id=task_id,
                    message=f"continue backfill after {task_id}",
                )
                results.append(
                    SyncJobResult(job_id=job_id, status="PLANNED", message=task_id)
                )
            else:
                self._jobs.transition(job_id, "COMPLETED", task_id=task_id)
                results.append(SyncJobResult(job_id=job_id, status="COMPLETED"))
        return results

    def run_reconcile(self, conflict_id: str, *, adapter: BaseDataAdapter) -> SyncJobResult:
        # adapter reserved for Round 3 vendor fetch during reconcile (MASTER §4.2 skeleton).
        with self._cm.writer() as con:
            row = con.execute(
                """
                SELECT job_id, data_domain, run_id
                FROM source_conflict WHERE conflict_id = ?
                """,
                [conflict_id],
            ).fetchone()
        if row is None:
            raise ValueError(f"unknown conflict_id: {conflict_id!r}")
        _src_job_id, data_domain, run_id = row[0], row[1], row[2]
        spec = SyncJobSpec(
            run_id=run_id or f"reconcile-{conflict_id[:8]}",
            job_id=f"reconcile-{conflict_id[:8]}",
            job_type="reconcile",
            data_domain=data_domain,
            market_id="CN_A",
            source_id=adapter.source_id,
            adapter_id=adapter.source_id,
            date_start=None,
            date_end=None,
            instrument_id=None,
            partition_key=None,
            trigger_reason=None,
        )
        job_id = self.create_job(spec)
        self._jobs.transition(job_id, "PLANNED")
        self._jobs.transition(job_id, "WAITING_RECONCILE", message=f"conflict {conflict_id}")
        self._jobs.transition(job_id, "RECONCILING", message="reconcile delegate")
        with self._cm.writer() as con:
            status_row = con.execute(
                """
                SELECT reconcile_status, manual_review_required
                FROM source_conflict WHERE conflict_id = ?
                """,
                [conflict_id],
            ).fetchone()
            if status_row and (
                status_row[0] == "UNRESOLVED" or status_row[1] is True
            ):
                SourceConflictValidator().record_unresolved_reconcile(
                    con, conflict_id, title="reconcile unresolved"
                )
                self._jobs.transition(
                    job_id, "MANUAL_REVIEW_REQUIRED", con=con, message="unresolved after reconcile"
                )
                return SyncJobResult(job_id=job_id, status="MANUAL_REVIEW_REQUIRED")
            self._jobs.transition(job_id, "READY_TO_WRITE", con=con)
            self._jobs.transition(job_id, "COMPLETED", con=con, message="reconcile resolved")
        return SyncJobResult(job_id=job_id, status="COMPLETED")

    @staticmethod
    def _update_job_report_ids(
        con,
        job_id: str,
        *,
        validation_report_id: str | None = None,
        conflict_report_id: str | None = None,
        write_id: str | None = None,
    ) -> None:
        if validation_report_id is not None:
            con.execute(
                "UPDATE data_sync_job SET validation_report_id = ? WHERE job_id = ?",
                [validation_report_id, job_id],
            )
        if conflict_report_id is not None:
            con.execute(
                "UPDATE data_sync_job SET conflict_report_id = ? WHERE job_id = ?",
                [conflict_report_id, job_id],
            )
        if write_id is not None:
            con.execute(
                "UPDATE data_sync_job SET write_id = ? WHERE job_id = ?",
                [write_id, job_id],
            )
