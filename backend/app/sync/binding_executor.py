"""Binding → orchestrator depth module (M-G1-03 §9.2 · P1-06′)."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Literal

from backend.app.db.connection import ConnectionManager
from backend.app.ops.sandbox_clean_write.clean_write_targets import (
    BAR_DOMAINS,
    MACRO_DOMAINS,
    resolve_clean_write_target,
)
from backend.app.sync.indicator_binding import IndicatorBinding
from backend.app.sync.jobs import SyncJobResult, SyncJobSpec
from backend.app.sync.orchestrator import DataSyncOrchestrator
from backend.app.sync.watermark import (
    _BAR_WATERMARK_DOMAINS,
    _MACRO_WATERMARK_DOMAINS,
    compute_incremental_window,
    compute_since_date,
    read_watermark,
)

JobType = Literal["incremental", "backfill", "full_load"]

_MACRO_REQUIRED_FIELDS = ("raw_value", "source_used")
_BAR_REQUIRED_FIELDS = ("close", "source_used")


def _build_job_spec(
    binding: IndicatorBinding,
    job_type: str,
    *,
    date_start: date | None,
    date_end: date | None,
    instrument_id: str | None = None,
) -> SyncJobSpec:
    suffix = uuid.uuid4().hex[:8]
    market_id = "GLOBAL" if binding.data_domain in _MACRO_WATERMARK_DOMAINS else "CN_A"
    return SyncJobSpec(
        run_id=f"binding-{binding.indicator_id}-{suffix}",
        job_id=f"job-{binding.indicator_id}-{suffix}",
        job_type=job_type,
        data_domain=binding.data_domain,
        market_id=market_id,
        source_id=binding.primary_source,
        adapter_id=binding.primary_source,
        date_start=date_start,
        date_end=date_end,
        instrument_id=instrument_id or binding.incremental_watermark,
        partition_key=None,
        trigger_reason=f"binding:{binding.indicator_id}",
    )


def _resolve_connection_manager(
    *,
    connection_manager: ConnectionManager | None,
    orchestrator: DataSyncOrchestrator | None,
) -> ConnectionManager | None:
    if connection_manager is not None:
        return connection_manager
    if orchestrator is not None:
        return orchestrator._jobs.connection_manager
    return None


def _watermark_preview(
    binding: IndicatorBinding,
    cm: ConnectionManager,
    *,
    job_type: str,
    watermark_key: str | None = None,
) -> tuple[date | None, date | None]:
    key = watermark_key or binding.incremental_watermark
    with cm.writer() as con:
        watermark = read_watermark(con, binding.data_domain, key)
    since: date | None = None
    if job_type == "incremental":
        if binding.data_domain in _BAR_WATERMARK_DOMAINS:
            since = compute_incremental_window(watermark).date_start
        elif binding.data_domain in _MACRO_WATERMARK_DOMAINS:
            since = compute_since_date(watermark)
    return watermark, since


def execute_binding(
    binding: IndicatorBinding,
    job_type: JobType,
    *,
    dry_run: bool = True,
    date_start: date | None = None,
    date_end: date | None = None,
    instrument_id: str | None = None,
    connection_manager: ConnectionManager | None = None,
    orchestrator: DataSyncOrchestrator | None = None,
    datasource_service=None,
) -> SyncJobResult:
    """唯一 binding→orchestrator 编排：SyncJobSpec → watermark → mapper → orchestrator."""
    spec = _build_job_spec(
        binding,
        job_type,
        date_start=date_start,
        date_end=date_end,
        instrument_id=instrument_id,
    )
    cm = _resolve_connection_manager(
        connection_manager=connection_manager, orchestrator=orchestrator
    )

    watermark: date | None = None
    since: date | None = None
    if cm is not None and job_type == "incremental":
        watermark, since = _watermark_preview(
            binding,
            cm,
            job_type=job_type,
            watermark_key=instrument_id or binding.incremental_watermark,
        )

    if dry_run:
        return SyncJobResult(
            job_id=spec.job_id,
            status="SKIPPED",
            message=(
                "dry-run only; watermark="
                f"{watermark.isoformat() if watermark else None}; "
                f"since={since.isoformat() if since else None}"
            ),
        )

    if orchestrator is None:
        if cm is None:
            raise ValueError(
                "execute_binding dry_run=False requires connection_manager or orchestrator"
            )
        orchestrator = DataSyncOrchestrator(cm)
    if datasource_service is None:
        raise ValueError("execute_binding dry_run=False requires datasource_service=")

    target = resolve_clean_write_target(binding.data_domain)
    if job_type == "full_load":
        if date_start is None or date_end is None:
            raise ValueError("full_load requires date_start and date_end")
        required_fields = (
            _MACRO_REQUIRED_FIELDS
            if binding.data_domain in MACRO_DOMAINS
            else _BAR_REQUIRED_FIELDS
        )
        if binding.data_domain in MACRO_DOMAINS:
            from backend.app.ops.macro_incremental_common import macro_incremental_validation_patch

            with macro_incremental_validation_patch():
                results = orchestrator.run_full_load(
                    spec,
                    datasource_service=datasource_service,
                    clean_table=target.target_table,
                    write_mode=target.write_mode,
                    primary_keys=target.primary_keys,
                    required_fields=required_fields,
                )
        else:
            results = orchestrator.run_full_load(
                spec,
                datasource_service=datasource_service,
                clean_table=target.target_table,
                write_mode=target.write_mode,
                primary_keys=target.primary_keys,
                required_fields=required_fields,
            )
        if not results:
            return SyncJobResult(
                job_id=spec.job_id, status="FAILED_FINAL", message="full_load produced no shards"
            )
        last = results[-1]
        return SyncJobResult(
            job_id=last.job_id,
            status=last.status,
            validation_report_id=last.validation_report_id,
            conflict_report_id=last.conflict_report_id,
            write_id=last.write_id,
            message=last.message,
        )

    if job_type == "backfill":
        if date_start is None or date_end is None:
            raise ValueError("backfill requires date_start and date_end")
        required_fields = (
            _MACRO_REQUIRED_FIELDS
            if binding.data_domain in MACRO_DOMAINS
            else _BAR_REQUIRED_FIELDS
        )
        if binding.data_domain in MACRO_DOMAINS:
            from backend.app.ops.macro_incremental_common import macro_incremental_validation_patch

            with macro_incremental_validation_patch():
                results = orchestrator.run_backfill(
                    spec,
                    datasource_service=datasource_service,
                    clean_table=target.target_table,
                    write_mode=target.write_mode,
                    primary_keys=target.primary_keys,
                    required_fields=required_fields,
                )
        elif binding.data_domain in BAR_DOMAINS:
            results = orchestrator.run_backfill(
                spec,
                datasource_service=datasource_service,
                clean_table=target.target_table,
                write_mode=target.write_mode,
                primary_keys=target.primary_keys,
                required_fields=required_fields,
            )
        else:
            raise ValueError(
                f"unsupported data_domain for execute_binding backfill: {binding.data_domain!r}"
            )
        if not results:
            return SyncJobResult(
                job_id=spec.job_id, status="FAILED_FINAL", message="backfill produced no shards"
            )
        last = results[-1]
        return SyncJobResult(
            job_id=last.job_id,
            status=last.status,
            validation_report_id=last.validation_report_id,
            conflict_report_id=last.conflict_report_id,
            write_id=last.write_id,
            message=last.message,
        )

    if binding.data_domain in MACRO_DOMAINS:
        from backend.app.ops.macro_incremental_common import macro_incremental_validation_patch

        with macro_incremental_validation_patch():
            return orchestrator.run_incremental(
                spec,
                datasource_service=datasource_service,
                clean_table=target.target_table,
                write_mode=target.write_mode,
                primary_keys=target.primary_keys,
                required_fields=_MACRO_REQUIRED_FIELDS,
            )
    if binding.data_domain in BAR_DOMAINS:
        return orchestrator.run_incremental(
            spec,
            datasource_service=datasource_service,
            clean_table=target.target_table,
            write_mode=target.write_mode,
            primary_keys=target.primary_keys,
            required_fields=_BAR_REQUIRED_FIELDS,
        )
    raise ValueError(f"unsupported data_domain for execute_binding: {binding.data_domain!r}")
