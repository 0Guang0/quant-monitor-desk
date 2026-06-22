"""Sync job runners extracted from DataSyncOrchestrator (Round2 audit P1-01)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from backend.app.datasources.base_adapter import BaseDataAdapter
from backend.app.datasources.fetch_result import FetchRequest, FetchResult
from backend.app.db.write_manager import WriteRequest
from backend.app.sync.event_payload import build_event_payload
from backend.app.sync.jobs import (
    SyncJobResult,
    SyncJobSpec,
    SyncJobStateMachine,
    normalize_backfill_trigger_reason,
    plan_backfill_shards,
)
from backend.app.sync.pipeline import SyncValidationPipeline, SyncWritePipeline
from backend.app.validators.data_quality import DataQualityRequest
from backend.app.validators.rule_contract import (
    default_conflict_rule_contract,
    default_quality_rule_contract,
)
from backend.app.validators.source_conflict import SourceConflictRequest, SourceConflictValidator

_DEFAULT_QUALITY_RULE_SET, _DEFAULT_QUALITY_RULE_VERSION = default_quality_rule_contract()
_DEFAULT_CONFLICT_RULE_SET, _DEFAULT_CONFLICT_RULE_VERSION = default_conflict_rule_contract()

FetchCallable = Callable[..., FetchResult]


class FetchGuardBlocked(Exception):
    """ResourceGuard blocked fetch before adapter/callable completed."""

    def __init__(self, message: str, *, decision=None) -> None:
        super().__init__(message)
        self.decision = decision


def _fetch_with_guard(
    *,
    begin_fetching: Callable[[str], bool],
    job_id: str,
    cm,
    req: FetchRequest,
    adapter: BaseDataAdapter | None,
    fetch_callable: FetchCallable | None,
    fetch_operation: str | None = None,
    require_begin_fetching: bool = False,
) -> FetchResult:
    """Unified fetch path: adapter uses begin_fetching; callable uses service guard."""
    from backend.app.datasources.service import ResourceGuardBlockedError

    if adapter is not None or require_begin_fetching:
        if not begin_fetching(job_id):
            raise FetchGuardBlocked("resource guard blocked")
    if adapter is not None:
        from backend.app.datasources.fetch_log import FetchLogWriter

        with cm.writer() as con:
            result = adapter.fetch(req, con=con, job_id=job_id)
            FetchLogWriter().write(con, result, req=req, job_id=job_id)
            return result
    if fetch_callable is None:
        raise ValueError("adapter or fetch_callable is required")
    try:
        with cm.writer() as con:
            if fetch_operation is not None:
                return fetch_callable(req, con, job_id, operation=fetch_operation)
            return fetch_callable(req, con, job_id)
    except ResourceGuardBlockedError as exc:
        raise FetchGuardBlocked(str(exc), decision=exc.decision) from exc


def _resolve_market_id(data_domain: str, market_id: str | None = None) -> str:
    if market_id:
        return market_id
    if data_domain.startswith("us_"):
        return "US"
    return "CN_A"


@dataclass(frozen=True)
class PipelineConfig:
    clean_table: str
    conflict_staging_table: str | None = None
    write_mode: str = "append_only"
    primary_keys: tuple[str, ...] = ("instrument_id", "trade_date")
    required_fields: tuple[str, ...] = ("close", "source_used")


class _PipelineMixin:
    _jobs: SyncJobStateMachine
    _validation: SyncValidationPipeline
    _write: SyncWritePipeline

    def _resolve_validation_sources(self, spec: SyncJobSpec) -> tuple[str, ...]:
        from backend.app.datasources.source_registry import SourceRegistry

        registry = SourceRegistry()
        if not registry._sources:
            registry.load()
        try:
            binding = registry.get_domain_roles(spec.data_domain)
        except KeyError:
            return ()
        sources: list[str] = []
        if binding.validation_source_id:
            sources.append(binding.validation_source_id)
        for fallback_id in binding.fallback_source_ids:
            if fallback_id != spec.source_id and fallback_id not in sources:
                sources.append(fallback_id)
        return tuple(s for s in sources if s != spec.source_id)

    def _validate_staging(
        self,
        con,
        *,
        spec: SyncJobSpec,
        job_id: str,
        staging_table: str,
        conflict_staging_table: str | None,
        primary_keys: tuple[str, ...],
        required_fields: tuple[str, ...],
    ):
        conflict_request = None
        if conflict_staging_table is not None:
            validation_sources = self._resolve_validation_sources(spec) or (
                "qmt_xtdata",
                "baostock",
            )
            conflict_request = SourceConflictRequest(
                run_id=spec.run_id,
                job_id=job_id,
                data_domain=spec.data_domain,
                primary_source=spec.source_id,
                validation_sources=validation_sources,
                key_fields=primary_keys,
                comparable_fields=("close",),
                tolerance_rule_set_id=_DEFAULT_CONFLICT_RULE_SET,
            )
        elif conflict_staging_table is None:
            self._jobs.emit_custom_event(
                job_id,
                event_type="CONFLICT_CHECK_SKIPPED",
                message="conflict_staging_table=None; conflict validation skipped (fail-closed audit)",
                payload_json=build_event_payload(
                    source_id=spec.source_id,
                    decision="conflict_check_skipped",
                ),
                con=con,
            )
        return self._validation.validate_staging(
            con,
            quality_request=DataQualityRequest(
                run_id=spec.run_id,
                job_id=job_id,
                data_domain=spec.data_domain,
                source_id=spec.source_id,
                staging_table=staging_table,
                primary_keys=primary_keys,
                required_fields=required_fields,
                rule_set_id=_DEFAULT_QUALITY_RULE_SET,
            ),
            expected_columns=primary_keys + required_fields + ("batch_id", "source_id"),
            timestamp_fields=("trade_date",),
            conflict_request=conflict_request,
            conflict_staging_table=conflict_staging_table,
        )

    def _write_clean(
        self,
        con,
        *,
        spec: SyncJobSpec,
        job_id: str,
        clean_table: str,
        staging_table: str,
        write_mode: str,
        primary_keys: tuple[str, ...],
        validation_report_id: str,
        conflict_report_id: str | None,
        source_used: str | None = None,
    ):
        resolved_source = source_used or spec.source_id
        return self._write.write_clean(
            con,
            WriteRequest(
                run_id=spec.run_id,
                job_id=job_id,
                target_table=clean_table,
                staging_table=staging_table,
                write_mode=write_mode,
                primary_keys=primary_keys,
                validation_report_id=validation_report_id,
                source_used=resolved_source,
                data_domain=spec.data_domain,
                conflict_report_id=conflict_report_id,
                source_role="primary",
                requested_by="orchestrator",
            ),
            own_transaction=False,
        )

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

    def _finalize_staged(
        self,
        con,
        *,
        spec: SyncJobSpec,
        job_id: str,
        staging_table: str,
        config: PipelineConfig,
        source_used: str,
        task_id: str | None = None,
    ) -> tuple[str, object, object | None, object | None, str | None]:
        """Validate staging, resolve conflicts, write clean (SY-02 shared kernel)."""
        validation = self._validate_staging(
            con,
            spec=spec,
            job_id=job_id,
            staging_table=staging_table,
            conflict_staging_table=config.conflict_staging_table,
            primary_keys=config.primary_keys,
            required_fields=config.required_fields,
        )
        quality = validation.quality
        conflict = validation.conflict
        self._update_job_report_ids(con, job_id, validation_report_id=quality.validation_report_id)

        if quality.status == "FAILED" or not quality.can_write_clean:
            return (
                "MANUAL_REVIEW_REQUIRED",
                quality,
                conflict,
                None,
                None,
            )

        conflict_report_id: str | None = None
        if conflict is not None:
            conflict_report_id = conflict.conflict_report_id
            self._update_job_report_ids(con, job_id, conflict_report_id=conflict_report_id)
            if conflict.status == "SEVERE_CONFLICT":
                return (
                    "WAITING_RECONCILE",
                    quality,
                    conflict,
                    None,
                    conflict_report_id,
                )

        transition_kwargs = {"con": con}
        if task_id is not None:
            transition_kwargs["task_id"] = task_id
        self._jobs.transition(job_id, "READY_TO_WRITE", **transition_kwargs)
        self._jobs.transition(job_id, "WRITING", **transition_kwargs)
        write_result = self._write_clean(
            con,
            spec=spec,
            job_id=job_id,
            clean_table=config.clean_table,
            staging_table=staging_table,
            write_mode=config.write_mode,
            primary_keys=config.primary_keys,
            validation_report_id=quality.validation_report_id,
            conflict_report_id=conflict_report_id,
            source_used=source_used,
        )
        self._update_job_report_ids(con, job_id, write_id=write_result.write_id)
        if write_result.status != "SUCCESS":
            return ("FAILED_FINAL", quality, conflict, write_result, conflict_report_id)
        return ("COMPLETED", quality, conflict, write_result, conflict_report_id)


class IncrementalJobRunner(_PipelineMixin):
    def __init__(
        self,
        jobs: SyncJobStateMachine,
        validation: SyncValidationPipeline,
        write: SyncWritePipeline,
        *,
        begin_fetching,
    ) -> None:
        self._jobs = jobs
        self._validation = validation
        self._write = write
        self._begin_fetching = begin_fetching

    def run(
        self,
        spec: SyncJobSpec,
        *,
        adapter: BaseDataAdapter | None = None,
        fetch_callable: FetchCallable | None = None,
        config: PipelineConfig,
        fetch_operation: str | None = None,
    ) -> SyncJobResult:
        if adapter is None and fetch_callable is None:
            raise ValueError("adapter or fetch_callable is required")
        if adapter is not None and fetch_callable is not None:
            raise ValueError("provide adapter or fetch_callable, not both")
        job_id = self._jobs.create_job(spec)
        self._jobs.transition(job_id, "PLANNED")
        req = FetchRequest(
            run_id=spec.run_id,
            source_id=spec.source_id,
            data_domain=spec.data_domain,
            market_id=spec.market_id,
            instrument_id=spec.instrument_id,
        )
        cm = self._jobs.connection_manager
        try:
            fetch_result = _fetch_with_guard(
                begin_fetching=self._begin_fetching,
                job_id=job_id,
                cm=cm,
                req=req,
                adapter=adapter,
                fetch_callable=fetch_callable,
                fetch_operation=fetch_operation,
            )
        except FetchGuardBlocked as exc:
            if exc.decision is not None:
                error_type = exc.decision.value if exc.decision else "PAUSE"
                self._jobs.transition(
                    job_id,
                    "FAILED_RETRYABLE",
                    message=str(exc),
                    event_type="RESOURCE_GUARD_BLOCKED",
                    error_type=error_type,
                    error_message=str(exc),
                )
                return SyncJobResult(
                    job_id=job_id,
                    status="FAILED_RETRYABLE",
                    message=str(exc),
                )
            return SyncJobResult(
                job_id=job_id,
                status="FAILED_RETRYABLE",
                message=str(exc),
            )
        if fetch_result.status != "SUCCESS" or not fetch_result.staging_table:
            self._jobs.transition(
                job_id,
                "FAILED_FINAL",
                message=fetch_result.error_message or fetch_result.status,
                payload_json=build_event_payload(
                    error_code=fetch_result.status,
                    source_id=spec.source_id,
                    retry_count=fetch_result.retry_count,
                    decision="fetch_failed",
                ),
            )
            return SyncJobResult(
                job_id=job_id,
                status="FAILED_FINAL",
                message=fetch_result.error_message,
            )
        staging_table = fetch_result.staging_table
        self._jobs.transition(job_id, "STAGED")
        self._jobs.transition(job_id, "VALIDATING")
        with cm.writer() as con:
            status, quality, conflict, write_result, conflict_report_id = self._finalize_staged(
                con,
                spec=spec,
                job_id=job_id,
                staging_table=staging_table,
                config=config,
                source_used=fetch_result.source_id,
            )
            if status == "MANUAL_REVIEW_REQUIRED":
                self._jobs.transition(
                    job_id,
                    "MANUAL_REVIEW_REQUIRED",
                    message="data quality failed",
                    con=con,
                    payload_json=build_event_payload(
                        source_id=spec.source_id,
                        rule_id=quality.quality_flags[0] if quality.quality_flags else None,
                        decision="quality_failed",
                    ),
                )
                return SyncJobResult(
                    job_id=job_id,
                    status="MANUAL_REVIEW_REQUIRED",
                    validation_report_id=quality.validation_report_id,
                    message="data quality failed",
                )
            if status == "WAITING_RECONCILE":
                self._jobs.transition(
                    job_id,
                    "WAITING_RECONCILE",
                    message="severe conflict",
                    con=con,
                    payload_json=build_event_payload(
                        source_id=spec.source_id,
                        decision="severe_conflict",
                    ),
                )
                return SyncJobResult(
                    job_id=job_id,
                    status="WAITING_RECONCILE",
                    validation_report_id=quality.validation_report_id,
                    conflict_report_id=conflict_report_id,
                )
            if status == "FAILED_FINAL":
                self._jobs.transition(
                    job_id,
                    "FAILED_FINAL",
                    message="write failed",
                    con=con,
                    payload_json=build_event_payload(
                        source_id=spec.source_id,
                        decision="write_failed",
                    ),
                )
                return SyncJobResult(
                    job_id=job_id,
                    status="FAILED_FINAL",
                    validation_report_id=quality.validation_report_id,
                    conflict_report_id=conflict_report_id,
                    message="write failed",
                )
        self._jobs.emit_custom_event(
            job_id,
            task_id=spec.instrument_id,
            event_type="ITEM_SUCCESS",
            message="incremental item completed",
            payload_json=build_event_payload(
                source_id=spec.source_id,
                task_id=spec.instrument_id,
                decision="item_success",
            ),
        )
        self._jobs.transition(job_id, "COMPLETED")
        return SyncJobResult(
            job_id=job_id,
            status="COMPLETED",
            validation_report_id=quality.validation_report_id,
            conflict_report_id=conflict_report_id,
            write_id=write_result.write_id,
        )


class BackfillShardRunner(_PipelineMixin):
    def __init__(
        self,
        jobs: SyncJobStateMachine,
        validation: SyncValidationPipeline,
        write: SyncWritePipeline,
        *,
        begin_fetching,
        emit_event,
    ) -> None:
        self._jobs = jobs
        self._validation = validation
        self._write = write
        self._begin_fetching = begin_fetching
        self._emit_event = emit_event

    def _backfill_checkpoint_task_id(self, job_id: str) -> str | None:
        with self._jobs.connection_manager.reader() as con:
            row = con.execute(
                """
                SELECT task_id FROM job_event_log
                WHERE job_id = ? AND event_type = 'SHARD_COMPLETE' AND task_id IS NOT NULL
                ORDER BY created_at DESC LIMIT 1
                """,
                [job_id],
            ).fetchone()
        return str(row[0]) if row else None

    def run(
        self,
        spec: SyncJobSpec,
        *,
        adapter: BaseDataAdapter | None = None,
        fetch_callable: FetchCallable | None = None,
        config: PipelineConfig,
    ) -> list[SyncJobResult]:
        if adapter is None and fetch_callable is None:
            raise ValueError("adapter or fetch_callable is required for backfill")
        if adapter is not None and fetch_callable is not None:
            raise ValueError("provide adapter or fetch_callable for backfill, not both")
        if spec.date_start is None or spec.date_end is None:
            raise ValueError("backfill requires date_start and date_end")
        trigger_reason = normalize_backfill_trigger_reason(spec.trigger_reason)
        shards = plan_backfill_shards(spec.date_start, spec.date_end)
        job_id = self._jobs.create_job(spec)
        self._jobs.transition(job_id, "PLANNED")
        checkpoint_task = self._backfill_checkpoint_task_id(job_id)
        results: list[SyncJobResult] = []
        cm = self._jobs.connection_manager
        pipeline = config

        for idx, (task_id, shard_start, shard_end) in enumerate(shards):
            if checkpoint_task is not None and task_id <= checkpoint_task:
                continue
            self._emit_event(
                job_id,
                task_id=task_id,
                event_type="BACKFILL_SHARD",
                payload_json=build_event_payload(
                    source_id=spec.source_id,
                    task_id=task_id,
                    decision="shard_start",
                    rule_id=trigger_reason,
                ),
            )
            req = FetchRequest(
                run_id=spec.run_id,
                source_id=spec.source_id,
                data_domain=spec.data_domain,
                market_id=spec.market_id,
                instrument_id=spec.instrument_id,
                start_time=shard_start.isoformat(),
                end_time=shard_end.isoformat(),
            )
            try:
                fetch_result = _fetch_with_guard(
                    begin_fetching=self._begin_fetching,
                    job_id=job_id,
                    cm=cm,
                    req=req,
                    adapter=adapter,
                    fetch_callable=fetch_callable,
                    require_begin_fetching=True,
                )
            except FetchGuardBlocked as exc:
                if exc.decision is not None:
                    error_type = exc.decision.value if exc.decision else "PAUSE"
                    self._jobs.transition(
                        job_id,
                        "FAILED_RETRYABLE",
                        task_id=task_id,
                        message=str(exc),
                        event_type="RESOURCE_GUARD_BLOCKED",
                        error_type=error_type,
                        error_message=str(exc),
                    )
                else:
                    self._jobs.transition(
                        job_id,
                        "FAILED_RETRYABLE",
                        task_id=task_id,
                        message=str(exc),
                        payload_json=build_event_payload(
                            source_id=spec.source_id,
                            task_id=task_id,
                            decision="guard_blocked",
                        ),
                    )
                results.append(
                    SyncJobResult(job_id=job_id, status="FAILED_RETRYABLE", message=str(exc))
                )
                return results
            if fetch_result.status != "SUCCESS" or not fetch_result.staging_table:
                self._jobs.transition(
                    job_id,
                    "FAILED_RETRYABLE",
                    task_id=task_id,
                    message=fetch_result.error_message or "shard failed",
                    payload_json=build_event_payload(
                        error_code=fetch_result.status,
                        source_id=spec.source_id,
                        task_id=task_id,
                        retry_count=fetch_result.retry_count,
                        decision="shard_fetch_failed",
                    ),
                )
                results.append(
                    SyncJobResult(
                        job_id=job_id,
                        status="FAILED_RETRYABLE",
                        message=fetch_result.error_message,
                    )
                )
                return results

            staging_table = fetch_result.staging_table
            self._jobs.transition(job_id, "STAGED", task_id=task_id)
            self._jobs.transition(job_id, "VALIDATING", task_id=task_id)
            write_result = None

            with cm.writer() as con:
                validation = self._validate_staging(
                    con,
                    spec=spec,
                    job_id=job_id,
                    staging_table=staging_table,
                    conflict_staging_table=pipeline.conflict_staging_table,
                    primary_keys=pipeline.primary_keys,
                    required_fields=pipeline.required_fields,
                )
                quality = validation.quality
                conflict = validation.conflict
                self._update_job_report_ids(
                    con, job_id, validation_report_id=quality.validation_report_id
                )
                if quality.status == "FAILED" or not quality.can_write_clean:
                    self._emit_event(
                        job_id,
                        task_id=task_id,
                        event_type="SHARD_SKIPPED",
                        message=f"shard {task_id} quality failed",
                        payload_json=build_event_payload(
                            source_id=spec.source_id,
                            task_id=task_id,
                            decision="shard_quality_skip",
                            rule_id=quality.quality_flags[0] if quality.quality_flags else None,
                        ),
                    )
                    if idx < len(shards) - 1:
                        self._jobs.transition(
                            job_id,
                            "PLANNED",
                            task_id=task_id,
                            message=f"continue backfill after skip {task_id}",
                            con=con,
                        )
                        results.append(
                            SyncJobResult(
                                job_id=job_id,
                                status="PLANNED",
                                message=task_id,
                                validation_report_id=quality.validation_report_id,
                            )
                        )
                        continue
                    self._jobs.transition(
                        job_id,
                        "MANUAL_REVIEW_REQUIRED",
                        task_id=task_id,
                        con=con,
                    )
                    results.append(
                        SyncJobResult(
                            job_id=job_id,
                            status="MANUAL_REVIEW_REQUIRED",
                            validation_report_id=quality.validation_report_id,
                        )
                    )
                    return results

                conflict_report_id: str | None = None
                if conflict is not None:
                    conflict_report_id = conflict.conflict_report_id
                    self._update_job_report_ids(
                        con, job_id, conflict_report_id=conflict_report_id
                    )
                    if conflict.status == "SEVERE_CONFLICT":
                        self._jobs.emit_custom_event(
                            job_id,
                            task_id=task_id,
                            event_type="SHARD_SKIPPED",
                            message=f"shard {task_id} severe conflict",
                            payload_json=build_event_payload(
                                source_id=spec.source_id,
                                task_id=task_id,
                                decision="severe_conflict",
                            ),
                            con=con,
                        )
                        self._jobs.transition(
                            job_id,
                            "WAITING_RECONCILE",
                            task_id=task_id,
                            message="severe conflict",
                            con=con,
                            payload_json=build_event_payload(
                                source_id=spec.source_id,
                                decision="severe_conflict",
                            ),
                        )
                        results.append(
                            SyncJobResult(
                                job_id=job_id,
                                status="WAITING_RECONCILE",
                                validation_report_id=quality.validation_report_id,
                                conflict_report_id=conflict_report_id,
                            )
                        )
                        return results

                self._jobs.transition(job_id, "READY_TO_WRITE", task_id=task_id, con=con)
                self._jobs.transition(job_id, "WRITING", task_id=task_id, con=con)
                write_result = self._write_clean(
                    con,
                    spec=spec,
                    job_id=job_id,
                    clean_table=pipeline.clean_table,
                    staging_table=staging_table,
                    write_mode=pipeline.write_mode,
                    primary_keys=pipeline.primary_keys,
                    validation_report_id=quality.validation_report_id,
                    conflict_report_id=conflict_report_id,
                    source_used=fetch_result.source_id,
                )
                if write_result.status != "SUCCESS":
                    self._emit_event(
                        job_id,
                        task_id=task_id,
                        event_type="SHARD_PARTIAL_FAIL",
                        message=f"shard {task_id} write failed",
                        payload_json=build_event_payload(
                            source_id=spec.source_id,
                            task_id=task_id,
                            decision="shard_write_failed",
                        ),
                    )
                    self._jobs.transition(
                        job_id,
                        "FAILED_RETRYABLE",
                        task_id=task_id,
                        con=con,
                    )
                    results.append(
                        SyncJobResult(job_id=job_id, status="FAILED_RETRYABLE", message=task_id)
                    )
                    return results

            self._emit_event(
                job_id,
                task_id=task_id,
                event_type="SHARD_COMPLETE",
                message=f"shard {task_id} completed",
                payload_json=build_event_payload(
                    source_id=spec.source_id,
                    task_id=task_id,
                    retry_count=fetch_result.retry_count,
                    decision="shard_success",
                ),
            )
            if idx < len(shards) - 1:
                self._jobs.transition(
                    job_id,
                    "PLANNED",
                    task_id=task_id,
                    message=f"continue backfill after {task_id}",
                )
                results.append(
                    SyncJobResult(
                        job_id=job_id,
                        status="PLANNED",
                        message=task_id,
                        write_id=write_result.write_id if write_result else None,
                    )
                )
            else:
                self._jobs.transition(job_id, "COMPLETED", task_id=task_id)
                results.append(
                    SyncJobResult(
                        job_id=job_id,
                        status="COMPLETED",
                        write_id=write_result.write_id if write_result else None,
                    )
                )
        return results


class ReconcileJobRunner:
    def __init__(self, jobs: SyncJobStateMachine) -> None:
        self._jobs = jobs
        self._conflict_validator = SourceConflictValidator()

    def run(self, conflict_id: str, *, adapter: BaseDataAdapter) -> SyncJobResult:
        cm = self._jobs.connection_manager
        with cm.writer() as con:
            row = con.execute(
                """
                SELECT job_id, data_domain, run_id, primary_source, competing_source,
                       instrument_id, field_name, primary_value, competing_value,
                       severity, reconcile_status, manual_review_required, market_id
                FROM source_conflict WHERE conflict_id = ?
                """,
                [conflict_id],
            ).fetchone()
        if row is None:
            raise ValueError(f"unknown conflict_id: {conflict_id!r}")
        (
            _src_job_id,
            data_domain,
            run_id,
            primary_source,
            competing_source,
            instrument_id,
            field_name,
            primary_value,
            competing_value,
            _severity,
            reconcile_status,
            manual_review_required,
            conflict_market_id,
        ) = row
        if reconcile_status in {"RESOLVED_BY_REFETCH", "RESOLVED"}:
            return SyncJobResult(
                job_id=f"reconcile-{conflict_id[:8]}",
                status="COMPLETED",
                message=f"conflict already {reconcile_status}",
            )

        resolved_market_id = _resolve_market_id(data_domain, conflict_market_id)

        spec = SyncJobSpec(
            run_id=run_id or f"reconcile-{conflict_id[:8]}",
            job_id=f"reconcile-{conflict_id[:8]}",
            job_type="reconcile",
            data_domain=data_domain,
            market_id=resolved_market_id,
            source_id=adapter.source_id,
            adapter_id=adapter.source_id,
            date_start=None,
            date_end=None,
            instrument_id=instrument_id,
            partition_key=None,
            trigger_reason=None,
        )
        job_id = self._jobs.create_job(spec)
        self._jobs.transition(job_id, "PLANNED")
        self._jobs.transition(
            job_id,
            "WAITING_RECONCILE",
            message=f"conflict {conflict_id}",
            payload_json=build_event_payload(
                source_id=adapter.source_id,
                decision="reconcile_start",
            ),
        )
        self._jobs.transition(job_id, "RECONCILING", message="reconcile re-fetch")

        compare_table = f"stg_reconcile_{conflict_id[:8]}"
        req = FetchRequest(
            run_id=spec.run_id,
            source_id=adapter.source_id,
            data_domain=data_domain,
            market_id=resolved_market_id,
            instrument_id=instrument_id,
        )
        with cm.writer() as con:
            fetch_result = adapter.fetch(req, con=con, job_id=job_id)
            if fetch_result.status != "SUCCESS" or not fetch_result.staging_table:
                self._conflict_validator.record_unresolved_reconcile(
                    con,
                    conflict_id,
                    title="reconcile re-fetch failed",
                    description=fetch_result.error_message or fetch_result.status,
                )
                self._jobs.transition(
                    job_id,
                    "MANUAL_REVIEW_REQUIRED",
                    con=con,
                    message="reconcile re-fetch failed",
                    payload_json=build_event_payload(
                        source_id=adapter.source_id,
                        error_code=fetch_result.status,
                        retry_count=fetch_result.retry_count,
                        decision="reconcile_fetch_failed",
                    ),
                )
                return SyncJobResult(job_id=job_id, status="MANUAL_REVIEW_REQUIRED")

            con.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {compare_table} (
                    source_id VARCHAR,
                    instrument_id VARCHAR,
                    trade_date VARCHAR,
                    close DOUBLE
                )
                """
            )
            con.execute(f"DELETE FROM {compare_table}")
            try:
                con.execute(
                    f"""
                    INSERT INTO {compare_table}
                    SELECT source_id, instrument_id, trade_date, close
                    FROM {fetch_result.staging_table}
                    """
                )

                conflict_request = SourceConflictRequest(
                    run_id=spec.run_id,
                    job_id=job_id,
                    data_domain=data_domain,
                    primary_source=primary_source,
                    validation_sources=(competing_source,),
                    key_fields=("instrument_id", "trade_date"),
                    comparable_fields=(field_name,),
                    tolerance_rule_set_id=_DEFAULT_CONFLICT_RULE_SET,
                )
                report = self._conflict_validator.validate_table(
                    con,
                    conflict_request,
                    staging_table=compare_table,
                )

                if report.status == "SEVERE_CONFLICT" or (
                    reconcile_status == "UNRESOLVED" and manual_review_required
                ):
                    self._conflict_validator.record_unresolved_reconcile(
                        con, conflict_id, title="reconcile unresolved after re-fetch"
                    )
                    self._jobs.transition(
                        job_id,
                        "MANUAL_REVIEW_REQUIRED",
                        con=con,
                        message="unresolved after reconcile",
                        payload_json=build_event_payload(
                            source_id=adapter.source_id,
                            decision="reconcile_manual_review",
                        ),
                    )
                    return SyncJobResult(job_id=job_id, status="MANUAL_REVIEW_REQUIRED")

                con.execute(
                    """
                    UPDATE source_conflict
                    SET reconcile_status = 'RESOLVED_BY_REFETCH',
                        manual_review_required = false,
                        resolved_at = ?
                    WHERE conflict_id = ?
                    """,
                    [datetime.now(UTC), conflict_id],
                )
                self._jobs.transition(
                    job_id,
                    "READY_TO_WRITE",
                    con=con,
                    payload_json=build_event_payload(
                        source_id=adapter.source_id,
                        decision="reconcile_resolved",
                    ),
                )
                self._jobs.transition(job_id, "COMPLETED", con=con, message="reconcile resolved")
            finally:
                con.execute(f"DROP TABLE IF EXISTS {compare_table}")
        return SyncJobResult(job_id=job_id, status="COMPLETED")
