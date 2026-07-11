"""Phase 1 production-equivalent CLI acceptance envelope (task-02-layer1-full)."""

from __future__ import annotations

import json
import uuid
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Literal

from backend.app.cli.errors import (
    CliFailure,
    DOCS_ANCHOR_DATA_SYNC_CLI,
    DOCS_ANCHOR_LAYER1_INDICATOR_BINDING,
    DOCS_ANCHOR_LIVE_ENV_GATE,
)
from backend.app.cli.run_context import cli_requested_by, new_cli_run_id
from backend.app.datasources.service import DataSourceService
from backend.app.db.connection import ConnectionManager
from backend.app.ops.acceptance_isolation import AcceptanceIsolationError, ensure_isolated_db
from backend.app.ops.source_route_db_acceptance import (
    AcceptanceReport,
    AcceptanceRequest,
    SourceRouteDbAcceptanceSpine,
    write_acceptance_report,
)
from backend.app.ops.source_route_db_acceptance_matrix import (
    SOURCE_ROUTE_DB_SANDBOX_SEGMENT,
    find_matrix_target,
    preview_route_payload,
    resolve_matrix_data_root,
)
from backend.app.sync.binding_executor import execute_binding
from backend.app.sync.indicator_binding import IndicatorBinding, bindings_for_source
from backend.app.sync.jobs import SyncJobResult, SyncJobSpec
from backend.app.sync.orchestrator import DataSyncOrchestrator
from backend.app.sync.runners import resolve_conflict_staging_table

REPORT_VERSION = "phase1_acceptance_v1"
OFFICIAL_JOB_KINDS = frozenset({"sync", "backfill", "full-load", "scheduler"})

DOMAIN_FETCH_OPERATIONS: dict[str, str] = {
    "cn_equity_daily_bar": "fetch_daily_bar",
    "macro_series": "fetch_macro_series",
    "us_treasury_yield_curve": "fetch_yield_curve",
    "central_bank_policy": "fetch_policy_rate",
    "development_indicator": "fetch_development_indicator",
    "cot_positioning": "fetch_cot_report",
    "cn_announcements": "fetch_announcement_index",
    "us_filings": "fetch_company_filings",
    "us_equity_daily_bar": "fetch_daily_bar",
    "crypto_options_surface": "fetch_options_surface",
}

JobKind = Literal["sync", "backfill", "full-load", "scheduler"]

def is_production_equivalent_acceptance_root(data_root: Path | str) -> bool:
    posix = Path(data_root).expanduser().resolve().as_posix()
    return ".audit-sandbox" in posix and SOURCE_ROUTE_DB_SANDBOX_SEGMENT in posix


def compute_gate_eligible(*, job_kind: str, data_root: Path, dry_run: bool) -> bool:
    if dry_run or job_kind not in OFFICIAL_JOB_KINDS:
        return False
    return is_production_equivalent_acceptance_root(data_root)


def resolve_cli_data_root() -> Path:
    from backend.app.config import PROJECT_ROOT, _path_env

    return Path(_path_env("QMD_DATA_ROOT", PROJECT_ROOT / "data"))


def try_resolve_phase1_data_root(data_root: Path | str) -> Path | None:
    try:
        return resolve_matrix_data_root(data_root)
    except AcceptanceIsolationError:
        return None


def require_phase1_data_root_for_live(data_root: Path | str) -> Path:
    try:
        return resolve_matrix_data_root(data_root)
    except AcceptanceIsolationError as exc:
        raise CliFailure(
            error_code=exc.code,
            message=str(exc),
            docs_anchor=DOCS_ANCHOR_LIVE_ENV_GATE,
        ) from exc


def domain_fetch_operation(data_domain: str) -> str:
    try:
        return DOMAIN_FETCH_OPERATIONS[data_domain]
    except KeyError as exc:
        raise CliFailure(
            error_code="CAPABILITY_MISSING",
            message=f"no fetch operation for data_domain={data_domain!r}",
            docs_anchor=DOCS_ANCHOR_DATA_SYNC_CLI,
        ) from exc


def acceptance_request_for_domain(
    *,
    source_id: str,
    data_domain: str,
    start: str | None = None,
    end: str | None = None,
) -> AcceptanceRequest:
    return AcceptanceRequest(
        data_domain=data_domain,
        source_id=source_id,
        operation=domain_fetch_operation(data_domain),
        start=start,
        end=end,
    )


def live_authorized_from_env() -> bool:
    import os

    return os.environ.get("QMD_ALLOW_LIVE_FETCH", "0") == "1"


def _chain_status(
    report: AcceptanceReport,
    *,
    dry_run: bool,
    extra: dict[str, Any] | None = None,
) -> dict[str, str]:
    if dry_run:
        return {
            "route_status": "PLANNED",
            "fetch_status": "NOT_RUN",
            "raw_status": "NOT_RUN",
            "staging_status": "NOT_RUN",
            "validation_status": report.validation_status,
            "conflict_status": report.conflict_status,
            "write_status": "NOT_RUN",
            "clean_status": "NOT_RUN",
            "downstream_layer_read_status": report.downstream_layer_read_status,
        }
    payload = extra or {}
    blocked = report.failure_class == "BLOCKED"
    route_ok = report.route_plan_id is not None and report.route_grade != "blocked"
    write_ok = report.write_grade in {"primary_grade_clean", "degraded_clean"}
    if report.validation_status == "FAILED" or report.conflict_status in {
        "SEVERE",
        "SEVERE_CONFLICT",
    }:
        write_ok = False
    raw_present = bool(payload.get("raw_file_paths") or payload.get("raw_file_ids"))
    fetch_log_present = bool(payload.get("fetch_log_ids"))
    staging_present = bool(
        payload.get("staging_table")
        or (payload.get("rows_staged") or 0) > 0
        or payload.get("validation_report_id")
        or payload.get("validation_run_ids")
    )
    fetch_ok = report.status == "PASS" and (
        fetch_log_present or raw_present or staging_present
    )
    if blocked:
        fetch_status = "BLOCKED"
    elif fetch_ok:
        fetch_status = "SUCCESS"
    elif report.failure_class == "FAIL_EXTERNAL":
        fetch_status = "FAIL"
    else:
        fetch_status = "FAIL"
    raw_status = (
        "PRESENT"
        if raw_present or fetch_log_present
        else ("NOT_RUN" if blocked else "FAIL")
    )
    staging_status = (
        "PRESENT"
        if staging_present
        else ("NOT_RUN" if blocked else "FAIL")
    )
    return {
        "route_status": "READY" if route_ok else ("BLOCKED" if blocked else "FAIL"),
        "fetch_status": fetch_status,
        "raw_status": raw_status,
        "staging_status": staging_status,
        "validation_status": report.validation_status,
        "conflict_status": report.conflict_status,
        "write_status": "COMMITTED" if write_ok else "NOT_RUN",
        "clean_status": "WRITTEN" if write_ok else "NOT_RUN",
        "downstream_layer_read_status": report.downstream_layer_read_status,
    }


PRODUCTION_PIPELINE_PATH = (
    "SourceRoutePlan -> DataSourceService -> staging -> "
    "DataQualityValidator -> SourceConflictValidator -> WriteManager -> clean"
)

BACKFILL_CHECKPOINT_EVENT_TYPES = (
    "BACKFILL_SHARD",
    "SHARD_COMPLETE",
    "SHARD_SKIPPED",
    "SHARD_PARTIAL_FAIL",
)

FULL_LOAD_CHECKPOINT_EVENT_TYPES = (
    "FULL_LOAD_SHARD",
    "FULL_LOAD_COMPLETE",
    "FULL_LOAD_SKIPPED",
    "FULL_LOAD_PARTIAL_FAIL",
)


def read_watermark_iso(
    cm: ConnectionManager,
    data_domain: str,
    watermark_key: str,
) -> str | None:
    from backend.app.sync.watermark import read_watermark

    with cm.reader() as con:
        cursor = read_watermark(con, data_domain, watermark_key)
    return cursor.isoformat() if cursor else None


def _incremental_watermark_key(
    request: AcceptanceRequest,
    instrument_id: str | None,
) -> str | None:
    if instrument_id:
        return instrument_id
    binding = _optional_primary_binding(request.source_id, request.data_domain)
    if binding is not None:
        return binding.incremental_watermark
    if request.data_domain == "cn_equity_daily_bar":
        return "sh.600519"
    return None


def _parse_raw_file_paths_value(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if text.startswith("["):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                return [text]
            if isinstance(parsed, list):
                return [str(item) for item in parsed if item]
            if isinstance(parsed, str) and parsed.strip():
                return [parsed.strip()]
            return []
        return [text]
    return [str(value)]


def _lookup_raw_file_ids(
    cm: ConnectionManager,
    *,
    content_hashes: list[str],
    raw_paths: list[str],
) -> list[str]:
    ids: list[str] = []
    with cm.reader() as reader:
        for content_hash in content_hashes:
            if not content_hash:
                continue
            row = reader.execute(
                "SELECT file_id FROM file_registry WHERE content_hash = ? LIMIT 1",
                [content_hash],
            ).fetchone()
            if row and row[0]:
                ids.append(str(row[0]))
    if ids:
        return ids
    return list(raw_paths)


def _enrich_report_from_observability(
    report: AcceptanceReport,
    extra: dict[str, Any],
) -> AcceptanceReport:
    from dataclasses import replace

    updates: dict[str, Any] = {}
    if not report.schema_hash and extra.get("schema_hash"):
        updates["schema_hash"] = extra["schema_hash"]
    if not report.content_hash and extra.get("content_hash"):
        updates["content_hash"] = extra["content_hash"]
    if updates:
        return replace(report, **updates)
    return report


def _collect_observability_from_job(
    cm: ConnectionManager,
    job_result: SyncJobResult,
    *,
    route_plan_persisted: bool = False,
) -> dict[str, Any]:
    extra: dict[str, Any] = {
        "sync_job_id": job_result.job_id,
        "job_id": job_result.job_id,
        "validation_report_id": job_result.validation_report_id,
        "write_id": job_result.write_id,
        "route_plan_persisted": route_plan_persisted,
    }
    if job_result.validation_report_id:
        extra["validation_run_ids"] = [job_result.validation_report_id]
    raw_paths: list[str] = []
    staging_table: str | None = None
    content_hashes: list[str] = []
    schema_hashes: list[str] = []
    latency_total_ms = 0
    for event in collect_job_events(cm, job_result.job_id):
        if event.get("event_type") == "ROUTE_PLAN":
            extra["route_plan_persisted"] = True
        payload_raw = event.get("payload_json")
        if not payload_raw:
            continue
        try:
            payload = json.loads(payload_raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        raw_paths.extend(
            _parse_raw_file_paths_value(payload.get("raw_file_paths"))
            + _parse_raw_file_paths_value(payload.get("raw_file_path"))
            + _parse_raw_file_paths_value(payload.get("raw_path"))
        )
        if payload.get("staging_table"):
            staging_table = str(payload["staging_table"])
    if job_result.job_id:
        with cm.reader() as reader:
            event_rows = reader.execute(
                "SELECT event_id FROM job_event_log WHERE job_id = ? ORDER BY created_at ASC",
                [job_result.job_id],
            ).fetchall()
            if event_rows:
                extra["job_event_ids"] = [str(row[0]) for row in event_rows]
            fetch_rows = reader.execute(
                """
                SELECT fetch_id, row_count, raw_file_paths, content_hash, schema_hash, latency_ms
                FROM fetch_log
                WHERE job_id = ?
                ORDER BY fetch_time ASC
                """,
                [job_result.job_id],
            ).fetchall()
            if fetch_rows:
                extra["fetch_log_ids"] = [str(row[0]) for row in fetch_rows]
                extra["rows_fetched"] = sum(int(row[1] or 0) for row in fetch_rows)
                for row in fetch_rows:
                    raw_paths.extend(_parse_raw_file_paths_value(row[2]))
                    if row[3]:
                        content_hashes.append(str(row[3]))
                    if row[4]:
                        schema_hashes.append(str(row[4]))
                    if row[5] is not None:
                        latency_total_ms += int(row[5])
            validation_id = job_result.validation_report_id
            validation_row = None
            if validation_id:
                validation_row = reader.execute(
                    """
                    SELECT staging_table, checked_rows
                    FROM validation_report
                    WHERE validation_report_id = ?
                    """,
                    [validation_id],
                ).fetchone()
            if validation_row is None:
                validation_row = reader.execute(
                    """
                    SELECT staging_table, checked_rows
                    FROM validation_report
                    WHERE job_id = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    [job_result.job_id],
                ).fetchone()
            if validation_row:
                if validation_row[0]:
                    staging_table = str(validation_row[0])
                if validation_row[1] is not None:
                    extra["rows_staged"] = int(validation_row[1])
            if job_result.write_id:
                written = reader.execute(
                    """
                    SELECT rows_inserted, staging_table, rows_in_staging,
                           finished_at, started_at
                    FROM write_audit_log
                    WHERE write_id = ?
                    """,
                    [job_result.write_id],
                ).fetchone()
                if written:
                    extra["rows_written"] = int(written[0])
                    if not staging_table and written[1]:
                        staging_table = str(written[1])
                    if extra.get("rows_staged") is None and written[2] is not None:
                        extra["rows_staged"] = int(written[2])
            timing_row = reader.execute(
                """
                SELECT started_at, finished_at
                FROM data_sync_job
                WHERE job_id = ?
                """,
                [job_result.job_id],
            ).fetchone()
            if timing_row and timing_row[0] and timing_row[1]:
                started_at, finished_at = timing_row[0], timing_row[1]
                duration_ms = int((finished_at - started_at).total_seconds() * 1000)
                if duration_ms >= 0:
                    extra["duration_ms"] = duration_ms
            elif latency_total_ms > 0:
                extra["duration_ms"] = latency_total_ms
            if staging_table and extra.get("rows_staged") is None:
                staged = reader.execute(
                    f"SELECT COUNT(*) FROM {staging_table}"
                ).fetchone()
                if staged:
                    extra["rows_staged"] = int(staged[0])
    if raw_paths:
        deduped_paths = list(dict.fromkeys(raw_paths))
        extra["raw_file_paths"] = deduped_paths
        extra["raw_file_ids"] = _lookup_raw_file_ids(
            cm,
            content_hashes=content_hashes,
            raw_paths=deduped_paths,
        )
    if schema_hashes:
        extra["schema_hash"] = schema_hashes[-1]
    if content_hashes:
        extra["content_hash"] = content_hashes[-1]
    if staging_table:
        extra["staging_table"] = staging_table
    return extra


def _write_grade_from_audit(
    cm: ConnectionManager,
    write_id: str | None,
    *,
    rows: int,
) -> tuple[str, str, bool]:
    if not write_id:
        return ("primary_grade_clean" if rows > 0 else "not_written", "primary", False)
    with cm.reader() as reader:
        row = reader.execute(
            """
            SELECT source_role, source_switched
            FROM write_audit_log
            WHERE write_id = ?
            """,
            [write_id],
        ).fetchone()
    if not row:
        return ("primary_grade_clean" if rows > 0 else "not_written", "primary", False)
    source_role, source_switched = row[0], bool(row[1])
    if source_role in {"fallback", "validation"} and source_switched:
        return "degraded_clean", str(source_role), True
    return ("primary_grade_clean" if rows > 0 else "not_written", str(source_role or "primary"), False)


def collect_job_events(
    cm: ConnectionManager,
    job_id: str | None,
    *,
    event_types: tuple[str, ...] | None = None,
) -> list[dict[str, Any]]:
    if not job_id:
        return []
    query = """
        SELECT event_type, task_id, message, payload_json
        FROM job_event_log
        WHERE job_id = ?
    """
    params: list[Any] = [job_id]
    if event_types:
        placeholders = ", ".join("?" for _ in event_types)
        query += f" AND event_type IN ({placeholders})"
        params.extend(event_types)
    query += " ORDER BY created_at ASC"
    with cm.reader() as con:
        rows = con.execute(query, params).fetchall()
    return [
        {
            "event_type": row[0],
            "task_id": row[1],
            "message": row[2],
            "payload_json": row[3],
        }
        for row in rows
    ]


def shard_checkpoint_task_id(
    cm: ConnectionManager,
    job_id: str | None,
    *,
    complete_event_type: str = "SHARD_COMPLETE",
) -> str | None:
    if not job_id:
        return None
    with cm.reader() as con:
        row = con.execute(
            """
            SELECT task_id FROM job_event_log
            WHERE job_id = ? AND event_type = ? AND task_id IS NOT NULL
            ORDER BY created_at DESC LIMIT 1
            """,
            [job_id, complete_event_type],
        ).fetchone()
    return str(row[0]) if row else None


def build_incremental_evidence(
    *,
    watermark_before: str | None = None,
    watermark_after: str | None = None,
    window_date_start: str | None = None,
    window_date_end: str | None = None,
    pipeline_path: str = PRODUCTION_PIPELINE_PATH,
) -> dict[str, Any]:
    return {
        "watermark_before": watermark_before,
        "watermark_after": watermark_after,
        "window_date_start": window_date_start,
        "window_date_end": window_date_end,
        "pipeline_path": pipeline_path,
    }


def build_backfill_evidence(
    *,
    trigger_reason: str,
    shard_plan: list[dict[str, Any]] | None = None,
    checkpoint_task_id: str | None = None,
    shard_events: list[dict[str, Any]] | None = None,
    checkpoint_event_types: tuple[str, ...] = BACKFILL_CHECKPOINT_EVENT_TYPES,
    write_grade: str | None = None,
    clean_table: str | None = None,
    data_domain: str | None = None,
) -> dict[str, Any]:
    return {
        "trigger_reason": trigger_reason,
        "shard_plan": list(shard_plan or ()),
        "checkpoint_task_id": checkpoint_task_id,
        "shard_events": list(shard_events or ()),
        "checkpoint_event_types": list(checkpoint_event_types),
        "affected_snapshot_recompute": _affected_snapshot_mark(
            write_grade=write_grade,
            clean_table=clean_table,
            data_domain=data_domain,
        ),
    }


def _affected_snapshot_mark(
    *,
    write_grade: str | None = None,
    clean_table: str | None = None,
    data_domain: str | None = None,
) -> str | dict[str, Any]:
    if write_grade in {"primary_grade_clean", "degraded_clean"} and clean_table:
        return {
            "status": "pending",
            "clean_table": clean_table,
            "data_domain": data_domain or "",
            "owner": "phase2_feature_layer",
        }
    return "deferred"


def build_full_load_evidence(
    *,
    run_id: str,
    execution_scope: str = "bounded_smoke",
    shard_plan: list[dict[str, Any]] | None = None,
    checkpoint_task_id: str | None = None,
    shard_events: list[dict[str, Any]] | None = None,
    checkpoint_event_types: tuple[str, ...] = FULL_LOAD_CHECKPOINT_EVENT_TYPES,
    write_grade: str | None = None,
    clean_table: str | None = None,
    data_domain: str | None = None,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "execution_scope": execution_scope,
        "shard_plan": list(shard_plan or ()),
        "checkpoint_task_id": checkpoint_task_id,
        "shard_events": list(shard_events or ()),
        "checkpoint_event_types": list(checkpoint_event_types),
        "affected_snapshot_recompute": _affected_snapshot_mark(
            write_grade=write_grade,
            clean_table=clean_table,
            data_domain=data_domain,
        ),
    }


def attach_job_evidence(envelope: dict[str, Any], extra: dict[str, Any] | None) -> dict[str, Any]:
    if not extra:
        return envelope
    for key in ("incremental_evidence", "backfill_evidence", "full_load_evidence"):
        if key in extra:
            envelope[key] = extra[key]
    return envelope

def build_observability_evidence(
    report: AcceptanceReport,
    *,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = extra or {}
    return {
        "sync_job_id": payload.get("sync_job_id") or payload.get("job_id"),
        "route_plan_id": report.route_plan_id,
        "fetch_log_ids": list(payload.get("fetch_log_ids") or ()),
        "raw_file_ids": list(payload.get("raw_file_ids") or ()),
        "validation_run_ids": list(
            payload.get("validation_run_ids")
            or ([payload["validation_report_id"]] if payload.get("validation_report_id") else [])
        ),
        "clean_write_transaction_id": payload.get("write_id")
        or payload.get("clean_write_transaction_id"),
        "job_event_ids": list(payload.get("job_event_ids") or ()),
        "resource_guard_decision": payload.get("resource_guard_decision"),
        "rows_fetched": payload.get("rows_fetched"),
        "rows_staged": payload.get("rows_staged"),
        "rows_written": payload.get("rows_written"),
        "schema_hash": payload.get("schema_hash") or report.schema_hash,
        "content_hash": payload.get("content_hash") or report.content_hash,
        "duration_ms": payload.get("duration_ms"),
        "route_plan_persistence": (
            "job_event_log"
            if payload.get("route_plan_persisted") or report.route_plan_id
            else "route_preview_only"
        ),
        "staging_table": payload.get("staging_table"),
        "raw_file_paths": list(payload.get("raw_file_paths") or ()),
        "write_grade": report.write_grade,
    }


def build_acceptance_envelope(
    report: AcceptanceReport,
    *,
    job_kind: JobKind,
    trigger: str,
    data_root: Path,
    dry_run: bool,
    run_id: str | None = None,
    acceptance_report_path: Path | str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    run_id = run_id or f"p1-{uuid.uuid4().hex[:12]}"
    gate = compute_gate_eligible(job_kind=job_kind, data_root=data_root, dry_run=dry_run)
    if extra:
        report = _enrich_report_from_observability(report, extra)
    chain = _chain_status(report, dry_run=dry_run, extra=extra)
    envelope: dict[str, Any] = {
        "acceptance_report": report.to_dict(),
        "gate_eligible": gate,
        "report_version": REPORT_VERSION,
        "run_id": run_id,
        "job_kind": job_kind,
        "trigger": trigger,
        "data_root": str(data_root.resolve()),
        "generated_at": datetime.now(UTC).isoformat(),
        "implementation_mode": report.implementation_mode if not dry_run else "dry_run",
        "route_grade": report.route_grade,
        "write_grade": report.write_grade,
        "source_used": report.source_used,
        "source_role": report.source_role,
        "source_switched": report.source_switched,
        "failure_class": report.failure_class,
        "status": report.status if not dry_run else "DRY_RUN",
        "errors": list(report.errors),
        "warnings": list((extra or {}).get("warnings") or ()),
        "blocked_by": list((extra or {}).get("blocked_by") or ()),
        "observability_evidence": build_observability_evidence(report, extra=extra),
        **chain,
    }
    if acceptance_report_path is not None:
        envelope["acceptance_report_path"] = str(acceptance_report_path)
    return attach_job_evidence(envelope, extra)


def persist_acceptance_report(report: AcceptanceReport, data_root: Path) -> Path:
    path = data_root / "reports" / f"acceptance-{uuid.uuid4().hex[:8]}.json"
    write_acceptance_report(report, path)
    return path


def merge_payload_with_envelope(
    payload: dict[str, Any],
    envelope: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(payload)
    merged.update(envelope)
    return merged


def _primary_binding(source_id: str, data_domain: str) -> IndicatorBinding:
    bindings = tuple(
        binding
        for binding in bindings_for_source(source_id)
        if binding.data_domain == data_domain and binding.cabin == "PRIMARY"
    )
    if not bindings:
        bindings = tuple(
            binding
            for binding in bindings_for_source(source_id)
            if binding.data_domain == data_domain
        )
    if not bindings:
        raise CliFailure(
            error_code="CAPABILITY_MISSING",
            message=(
                f"no indicator binding for source_id={source_id!r} "
                f"data_domain={data_domain!r}"
            ),
            docs_anchor=DOCS_ANCHOR_LAYER1_INDICATOR_BINDING,
        )
    return bindings[0]


def _optional_primary_binding(source_id: str, data_domain: str) -> IndicatorBinding | None:
    try:
        return _primary_binding(source_id, data_domain)
    except CliFailure:
        return None


def _run_shard_job_without_binding(
    request: AcceptanceRequest,
    job_type: Literal["backfill", "full_load"],
    *,
    orch: DataSyncOrchestrator,
    service: DataSourceService,
    date_start: date,
    date_end: date,
    instrument_id: str | None,
    trigger_reason: str | None,
    resume_job_id: str | None = None,
) -> SyncJobResult:
    from backend.app.ops.sandbox_clean_write.clean_write_targets import (
        BAR_DOMAINS,
        MACRO_DOMAINS,
        resolve_clean_write_target,
    )

    target = resolve_clean_write_target(request.data_domain)
    market_id = "GLOBAL" if request.data_domain in MACRO_DOMAINS else "CN_A"
    if resume_job_id:
        job_id = resume_job_id
        run_id = (
            resume_job_id.replace("job-", "run-", 1)
            if resume_job_id.startswith("job-")
            else f"run-{resume_job_id}"
        )
    else:
        suffix = uuid.uuid4().hex[:8]
        job_id = f"job-p1-{job_type}-{suffix}"
        run_id = new_cli_run_id(job_type, prefix="p1")
    spec = SyncJobSpec(
        run_id=run_id,
        job_id=job_id,
        job_type=job_type,
        data_domain=request.data_domain,
        market_id=market_id,
        source_id=request.source_id,
        adapter_id=request.source_id,
        date_start=date_start,
        date_end=date_end,
        instrument_id=instrument_id,
        partition_key=None,
        trigger_reason=trigger_reason
        or ("eco_catchup" if job_type == "backfill" else "cold_start"),
        requested_by=cli_requested_by(f"data {job_type}"),
    )
    required_fields = (
        ("raw_value", "source_used")
        if request.data_domain in MACRO_DOMAINS
        else ("close", "source_used")
    )
    if job_type == "backfill":
        if request.data_domain in MACRO_DOMAINS:
            from backend.app.ops.macro_incremental_common import macro_incremental_validation_patch

            with macro_incremental_validation_patch():
                results = orch.run_backfill(
                    spec,
                    datasource_service=service,
                    clean_table=target.target_table,
                    write_mode=target.write_mode,
                    primary_keys=target.primary_keys,
                    required_fields=required_fields,
                )
        else:
            conflict_staging = resolve_conflict_staging_table(request.data_domain, spec.job_id)
            results = orch.run_backfill(
                spec,
                datasource_service=service,
                clean_table=target.target_table,
                write_mode=target.write_mode,
                primary_keys=target.primary_keys,
                required_fields=required_fields,
                conflict_staging_table=conflict_staging,
            )
    else:
        conflict_staging = resolve_conflict_staging_table(request.data_domain, spec.job_id)
        results = orch.run_full_load(
            spec,
            datasource_service=service,
            clean_table=target.target_table,
            write_mode=target.write_mode,
            primary_keys=target.primary_keys,
            required_fields=required_fields,
            conflict_staging_table=conflict_staging,
        )
    if not results:
        return SyncJobResult(
            job_id=spec.job_id,
            status="FAILED_FINAL",
            message=f"{job_type} produced no shards",
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


def resolve_binding_datasource_service(
    binding: IndicatorBinding,
    *,
    datasource_service: DataSourceService | None,
    dry_run: bool,
    data_root: Path | None = None,
    orchestrator: DataSyncOrchestrator | None = None,
    connection_manager: ConnectionManager | None = None,
) -> DataSourceService | None:
    if dry_run or datasource_service is not None:
        return datasource_service
    orch = orchestrator
    if orch is None and connection_manager is not None:
        orch = DataSyncOrchestrator(connection_manager)
    root = data_root or resolve_cli_data_root()
    return _build_datasource_service(
        source_id=binding.primary_source,
        data_domain=binding.data_domain,
        data_root=root,
        operation=domain_fetch_operation(binding.data_domain),
        instrument_id=binding.incremental_watermark,
        job_events=orch._jobs if orch else None,
    )


def _latest_sync_job_result(
    cm: ConnectionManager,
    *,
    source_id: str,
    data_domain: str,
    job_type: str | None = None,
) -> SyncJobResult | None:
    params: list[str] = [source_id, data_domain]
    job_type_clause = ""
    if job_type is not None:
        job_type_clause = " AND job_type = ?"
        params.append(job_type)
    with cm.reader() as reader:
        row = reader.execute(
            f"""
            SELECT job_id, status, validation_report_id, conflict_report_id, write_id
            FROM data_sync_job
            WHERE source_id = ? AND data_domain = ?{job_type_clause}
            ORDER BY created_at DESC
            LIMIT 1
            """,
            params,
        ).fetchone()
    if not row:
        return None
    return SyncJobResult(
        job_id=str(row[0]),
        status=str(row[1]),
        validation_report_id=row[2],
        conflict_report_id=row[3],
        write_id=row[4],
        message=None,
    )


def _build_datasource_service(
    *,
    source_id: str,
    data_domain: str,
    data_root: Path,
    operation: str,
    instrument_id: str | None = None,
    job_events=None,
) -> DataSourceService:
    raw_root = Path(data_root) / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    if source_id == "baostock" and data_domain == "cn_equity_daily_bar":
        from backend.app.ops.baostock_incremental_run import build_baostock_incremental_service

        return build_baostock_incremental_service(
            data_root=raw_root,
            symbol=instrument_id or "sh.600519",
            job_events=job_events,
        )
    from backend.app.datasources.product_live_ports import build_product_live_service

    return build_product_live_service(
        source_id=source_id,
        data_domain=data_domain,
        data_root=raw_root,
        operation=operation,
    )


def _prepare_phase1_connection(data_root: Path) -> tuple[ConnectionManager, DataSyncOrchestrator]:
    db_path = ensure_isolated_db(data_root)
    cm = ConnectionManager(db_path=db_path)
    return cm, DataSyncOrchestrator(cm)


def _report_from_binding_result(
    request: AcceptanceRequest,
    route_payload: dict[str, Any],
    job_result: SyncJobResult,
    *,
    cm: ConnectionManager,
    data_domain: str,
) -> AcceptanceReport:
    from backend.app.ops.source_route_db_acceptance import (
        _acceptance_job_statuses,
        _count_clean_rows,
    )

    route_report = AcceptanceReport.from_route_payload(request, route_payload)
    validation_status, conflict_status = _acceptance_job_statuses(cm, job_result.job_id)
    rows = _count_clean_rows(cm, data_domain, source_id=request.source_id)
    write_grade, source_role, source_switched = _write_grade_from_audit(
        cm, job_result.write_id, rows=rows
    )
    blocked_by_conflict = conflict_status in {"SEVERE", "SEVERE_CONFLICT"} or job_result.status == "WAITING_RECONCILE"
    blocked_by_validation = validation_status in {"FAILED", "MANUAL_REVIEW_REQUIRED"} or job_result.status == "MANUAL_REVIEW_REQUIRED"
    pass_status = (
        not blocked_by_conflict
        and not blocked_by_validation
        and job_result.status in {"COMPLETED", "PASS", "EMPTY_RESPONSE"}
        and write_grade in {"primary_grade_clean", "degraded_clean"}
    )
    failure_class: str = "NONE" if pass_status else "FAIL"
    if blocked_by_conflict:
        failure_class = "FAIL"
    elif job_result.status in {"FAILED_RETRYABLE", "FAILED_FINAL", "NETWORK_ERROR"}:
        failure_class = "FAIL_EXTERNAL"
    errors: tuple[str, ...] = ()
    if not pass_status:
        errors = (job_result.message or f"job_status={job_result.status}",)
    downstream = (
        "PRIMARY_GRADE_READ"
        if write_grade == "primary_grade_clean"
        else ("DEGRADED_READ" if write_grade == "degraded_clean" else "NO_CLEAN_ROWS")
    )
    return replace(
        route_report,
        implementation_mode="live",
        write_grade=write_grade,  # type: ignore[arg-type]
        source_role=source_role,  # type: ignore[arg-type]
        source_switched=source_switched,
        validation_status=validation_status,
        conflict_status=conflict_status,
        failure_class=failure_class,  # type: ignore[arg-type]
        downstream_layer_read_status=downstream,
        status="PASS" if pass_status else "FAIL",
        schema_hash=route_report.schema_hash,
        content_hash=route_report.content_hash,
        errors=errors,
    )


def execute_spine_or_binding_live(
    request: AcceptanceRequest,
    *,
    data_root: Path,
    live_authorized: bool,
    job_type: Literal["incremental", "backfill", "full_load"],
    date_start: date | None = None,
    date_end: date | None = None,
    instrument_id: str | None = None,
    trigger_reason: str | None = None,
    shard_plan: list[dict[str, Any]] | None = None,
    run_id: str | None = None,
    resume_job_id: str | None = None,
) -> tuple[AcceptanceReport, dict[str, Any]]:
    from backend.app.sync.jobs import normalize_backfill_trigger_reason

    spine = SourceRouteDbAcceptanceSpine()
    if find_matrix_target(request) is not None and job_type == "incremental":
        watermark_before: str | None = None
        watermark_after: str | None = None
        cm_for_spine: ConnectionManager | None = None
        if live_authorized:
            cm_for_spine, _ = _prepare_phase1_connection(data_root)
            watermark_key = _incremental_watermark_key(request, instrument_id)
            if watermark_key:
                watermark_before = read_watermark_iso(cm_for_spine, request.data_domain, watermark_key)
        report = spine.execute(
            request,
            data_root=data_root,
            live_authorized=live_authorized,
            cm=cm_for_spine,
        )
        if live_authorized and cm_for_spine is not None:
            watermark_key = _incremental_watermark_key(request, instrument_id)
            if watermark_key:
                watermark_after = read_watermark_iso(cm_for_spine, request.data_domain, watermark_key)
        extra: dict[str, Any] = {
            "sync_job_id": None,
            "route_plan_persisted": report.route_plan_id is not None,
            "incremental_evidence": build_incremental_evidence(
                watermark_before=watermark_before,
                watermark_after=watermark_after,
            ),
        }
        if live_authorized and cm_for_spine is not None:
            job_result = _latest_sync_job_result(
                cm_for_spine,
                source_id=request.source_id,
                data_domain=request.data_domain,
                job_type="incremental",
            )
            if job_result is not None:
                extra.update(
                    _collect_observability_from_job(
                        cm_for_spine,
                        job_result,
                        route_plan_persisted=report.route_plan_id is not None,
                    )
                )
        report = _enrich_report_from_observability(report, extra)
        return report, extra

    route_payload = preview_route_payload(request)
    if not live_authorized:
        report = AcceptanceReport.blocked_from_route_payload(
            request,
            route_payload,
            f"live authorization missing for {request.source_id}",
        )
        extra = _blocked_job_evidence(
            request=request,
            job_type=job_type,
            trigger_reason=trigger_reason,
            shard_plan=shard_plan,
            run_id=run_id,
        )
        return replace(report, implementation_mode="dry_run"), extra

    cm, orch = _prepare_phase1_connection(data_root)
    binding = _optional_primary_binding(request.source_id, request.data_domain)
    watermark_key = instrument_id or (binding.incremental_watermark if binding else instrument_id)
    watermark_before = (
        read_watermark_iso(cm, request.data_domain, watermark_key)
        if job_type == "incremental" and watermark_key
        else None
    )
    service = _build_datasource_service(
        source_id=request.source_id,
        data_domain=request.data_domain,
        data_root=data_root,
        operation=request.operation,
        instrument_id=watermark_key,
        job_events=orch._jobs,
    )
    if binding is not None:
        job_result = execute_binding(
            binding,
            job_type,
            dry_run=False,
            date_start=date_start,
            date_end=date_end,
            instrument_id=watermark_key,
            connection_manager=cm,
            orchestrator=orch,
            datasource_service=service,
            trigger_reason=trigger_reason,
            requested_by=cli_requested_by(f"data {job_type}"),
        )
    elif job_type in {"backfill", "full_load"} and date_start is not None and date_end is not None:
        job_result = _run_shard_job_without_binding(
            request,
            job_type,
            orch=orch,
            service=service,
            date_start=date_start,
            date_end=date_end,
            instrument_id=instrument_id,
            trigger_reason=trigger_reason,
            resume_job_id=resume_job_id if job_type == "backfill" else None,
        )
    else:
        raise CliFailure(
            error_code="CAPABILITY_MISSING",
            message=(
                f"no indicator binding for source_id={request.source_id!r} "
                f"data_domain={request.data_domain!r}"
            ),
            docs_anchor=DOCS_ANCHOR_LAYER1_INDICATOR_BINDING,
        )
    watermark_after = (
        read_watermark_iso(cm, request.data_domain, watermark_key)
        if job_type == "incremental" and watermark_key
        else None
    )
    report = _report_from_binding_result(
        request,
        route_payload,
        job_result,
        cm=cm,
        data_domain=request.data_domain,
    )
    extra = _collect_observability_from_job(cm, job_result, route_plan_persisted=True)
    if job_type == "incremental":
        extra["incremental_evidence"] = build_incremental_evidence(
            watermark_before=watermark_before,
            watermark_after=watermark_after,
        )
    elif job_type == "backfill":
        from backend.app.ops.sandbox_clean_write.clean_write_targets import resolve_clean_write_target

        normalized_trigger = normalize_backfill_trigger_reason(trigger_reason)
        shard_events = collect_job_events(
            cm, job_result.job_id, event_types=BACKFILL_CHECKPOINT_EVENT_TYPES
        )
        target = resolve_clean_write_target(request.data_domain)
        extra["backfill_evidence"] = build_backfill_evidence(
            trigger_reason=normalized_trigger,
            shard_plan=shard_plan,
            checkpoint_task_id=shard_checkpoint_task_id(cm, job_result.job_id),
            shard_events=shard_events,
            write_grade=report.write_grade,
            clean_table=target.target_table,
            data_domain=request.data_domain,
        )
    else:
        from backend.app.ops.sandbox_clean_write.clean_write_targets import resolve_clean_write_target

        fl_run_id = run_id or job_result.job_id or f"p1-fl-{uuid.uuid4().hex[:12]}"
        shard_events = collect_job_events(
            cm, job_result.job_id, event_types=FULL_LOAD_CHECKPOINT_EVENT_TYPES
        )
        target = resolve_clean_write_target(request.data_domain)
        extra["full_load_evidence"] = build_full_load_evidence(
            run_id=fl_run_id,
            shard_plan=shard_plan,
            checkpoint_task_id=shard_checkpoint_task_id(
                cm, job_result.job_id, complete_event_type="FULL_LOAD_COMPLETE"
            ),
            shard_events=shard_events,
            write_grade=report.write_grade,
            clean_table=target.target_table,
            data_domain=request.data_domain,
        )
    report = _enrich_report_from_observability(report, extra)
    return report, extra


def _blocked_job_evidence(
    *,
    request: AcceptanceRequest,
    job_type: Literal["incremental", "backfill", "full_load"],
    trigger_reason: str | None,
    shard_plan: list[dict[str, Any]] | None,
    run_id: str | None,
) -> dict[str, Any]:
    from backend.app.sync.jobs import normalize_backfill_trigger_reason

    extra: dict[str, Any] = {}
    if job_type == "incremental":
        extra["incremental_evidence"] = build_incremental_evidence(watermark_before=None)
    elif job_type == "backfill":
        extra["backfill_evidence"] = build_backfill_evidence(
            trigger_reason=normalize_backfill_trigger_reason(trigger_reason),
            shard_plan=shard_plan,
        )
    else:
        extra["full_load_evidence"] = build_full_load_evidence(
            run_id=run_id or f"p1-fl-{uuid.uuid4().hex[:12]}",
            shard_plan=shard_plan,
        )
    return extra


def run_phase1_sync_live(
    *,
    source_id: str,
    data_domain: str,
    data_root: Path,
    start: str | None = None,
    end: str | None = None,
    instrument_id: str | None = None,
) -> dict[str, Any]:
    resolved = require_phase1_data_root_for_live(data_root)
    request = acceptance_request_for_domain(
        source_id=source_id,
        data_domain=data_domain,
        start=start,
        end=end,
    )
    live_authorized = live_authorized_from_env()
    report, extra = execute_spine_or_binding_live(
        request,
        data_root=resolved,
        live_authorized=live_authorized,
        job_type="incremental",
        instrument_id=instrument_id,
    )
    report_path = persist_acceptance_report(report, resolved)
    envelope = build_acceptance_envelope(
        report,
        job_kind="sync",
        trigger=f"qmd-data data sync --source-id {source_id}",
        data_root=resolved,
        dry_run=False,
        acceptance_report_path=report_path,
        extra=extra,
    )
    payload: dict[str, Any] = {
        "command": "sync",
        "dry_run": False,
        "source_id": source_id,
        "data_domain": data_domain,
        "operation": request.operation,
        "message": "phase1 production-equivalent sync acceptance completed",
    }
    return merge_payload_with_envelope(payload, envelope)


def run_phase1_backfill_live(
    *,
    source_id: str,
    data_domain: str,
    data_root: Path,
    date_start: date,
    date_end: date,
    instrument_id: str | None = None,
    shard_plan: list[dict[str, Any]] | None = None,
    trigger_reason: str | None = None,
    resume_job_id: str | None = None,
) -> dict[str, Any]:
    resolved = require_phase1_data_root_for_live(data_root)
    request = acceptance_request_for_domain(
        source_id=source_id,
        data_domain=data_domain,
        start=date_start.isoformat(),
        end=date_end.isoformat(),
    )
    live_authorized = live_authorized_from_env()
    report, extra = execute_spine_or_binding_live(
        request,
        data_root=resolved,
        live_authorized=live_authorized,
        job_type="backfill",
        date_start=date_start,
        date_end=date_end,
        instrument_id=instrument_id,
        trigger_reason=trigger_reason,
        shard_plan=shard_plan,
        resume_job_id=resume_job_id,
    )
    report_path = persist_acceptance_report(report, resolved)
    envelope = build_acceptance_envelope(
        report,
        job_kind="backfill",
        trigger=f"qmd-data data backfill --source-id {source_id}",
        data_root=resolved,
        dry_run=False,
        acceptance_report_path=report_path,
        extra=extra,
    )
    payload: dict[str, Any] = {
        "command": "backfill",
        "dry_run": False,
        "source_id": source_id,
        "data_domain": data_domain,
        "shards": shard_plan or [],
        "shard_count": len(shard_plan or ()),
        "job_id": extra.get("job_id"),
        "message": "phase1 production-equivalent backfill acceptance completed",
    }
    return merge_payload_with_envelope(payload, envelope)


def run_phase1_full_load_live(
    *,
    source_id: str,
    data_domain: str,
    data_root: Path,
    date_start: date,
    date_end: date,
    instrument_id: str | None = None,
    shard_plan: list[dict[str, Any]] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    resolved = require_phase1_data_root_for_live(data_root)
    fl_run_id = run_id or f"p1-fl-{uuid.uuid4().hex[:12]}"
    request = acceptance_request_for_domain(
        source_id=source_id,
        data_domain=data_domain,
        start=date_start.isoformat(),
        end=date_end.isoformat(),
    )
    live_authorized = live_authorized_from_env()
    report, extra = execute_spine_or_binding_live(
        request,
        data_root=resolved,
        live_authorized=live_authorized,
        job_type="full_load",
        date_start=date_start,
        date_end=date_end,
        instrument_id=instrument_id,
        shard_plan=shard_plan,
        run_id=fl_run_id,
    )
    report_path = persist_acceptance_report(report, resolved)
    envelope = build_acceptance_envelope(
        report,
        job_kind="full-load",
        trigger=f"qmd-data data full-load --source-id {source_id}",
        data_root=resolved,
        dry_run=False,
        acceptance_report_path=report_path,
        run_id=fl_run_id,
        extra=extra,
    )
    payload: dict[str, Any] = {
        "command": "full-load",
        "dry_run": False,
        "source_id": source_id,
        "data_domain": data_domain,
        "shards": shard_plan or [],
        "job_id": extra.get("job_id"),
        "message": "phase1 production-equivalent full-load acceptance completed",
    }
    return merge_payload_with_envelope(payload, envelope)


def acceptance_report_from_sync_job(
    request: AcceptanceRequest,
    job_result: SyncJobResult,
    *,
    cm: ConnectionManager,
    data_domain: str,
    job_type: Literal["incremental", "backfill", "full_load"],
    date_start: date | None = None,
    date_end: date | None = None,
    instrument_id: str | None = None,
    trigger_reason: str | None = None,
    shard_plan: list[dict[str, Any]] | None = None,
    run_id: str | None = None,
) -> tuple[AcceptanceReport, dict[str, Any]]:
    from backend.app.sync.jobs import normalize_backfill_trigger_reason

    route_payload = preview_route_payload(request)
    report = _report_from_binding_result(
        request,
        route_payload,
        job_result,
        cm=cm,
        data_domain=data_domain,
    )
    extra = _collect_observability_from_job(cm, job_result, route_plan_persisted=True)
    watermark_key = _incremental_watermark_key(request, instrument_id)
    if job_type == "incremental" and watermark_key:
        extra["watermark_after"] = read_watermark_iso(cm, data_domain, watermark_key)
        extra["incremental_evidence"] = build_incremental_evidence(
            watermark_before=extra.get("watermark_before"),
            watermark_after=extra.get("watermark_after"),
        )
    elif job_type == "backfill":
        from backend.app.ops.sandbox_clean_write.clean_write_targets import resolve_clean_write_target

        normalized_trigger = normalize_backfill_trigger_reason(trigger_reason)
        shard_events = collect_job_events(
            cm, job_result.job_id, event_types=BACKFILL_CHECKPOINT_EVENT_TYPES
        )
        target = resolve_clean_write_target(data_domain)
        extra["backfill_evidence"] = build_backfill_evidence(
            trigger_reason=normalized_trigger,
            shard_plan=shard_plan,
            checkpoint_task_id=shard_checkpoint_task_id(cm, job_result.job_id),
            shard_events=shard_events,
            write_grade=report.write_grade,
            clean_table=target.target_table,
            data_domain=data_domain,
        )
    elif job_type == "full_load":
        from backend.app.ops.sandbox_clean_write.clean_write_targets import resolve_clean_write_target

        fl_run_id = run_id or job_result.job_id or f"p1-fl-{uuid.uuid4().hex[:12]}"
        shard_events = collect_job_events(
            cm, job_result.job_id, event_types=FULL_LOAD_CHECKPOINT_EVENT_TYPES
        )
        target = resolve_clean_write_target(data_domain)
        extra["full_load_evidence"] = build_full_load_evidence(
            run_id=fl_run_id,
            shard_plan=shard_plan,
            checkpoint_task_id=shard_checkpoint_task_id(
                cm, job_result.job_id, complete_event_type="FULL_LOAD_COMPLETE"
            ),
            shard_events=shard_events,
            write_grade=report.write_grade,
            clean_table=target.target_table,
            data_domain=data_domain,
        )
    if date_start is not None and date_end is not None and job_type == "incremental":
        extra["incremental_evidence"] = build_incremental_evidence(
            watermark_before=extra.get("watermark_before"),
            watermark_after=extra.get("watermark_after"),
            window_date_start=date_start.isoformat(),
            window_date_end=date_end.isoformat(),
        )
    report = _enrich_report_from_observability(report, extra)
    return report, extra


def build_scheduler_child_live_envelope(
    *,
    profile: str,
    job_type: str,
    source_id: str,
    data_domain: str,
    data_root: Path,
    acceptance_report: AcceptanceReport,
    acceptance_extra: dict[str, Any] | None,
    guard_decision: str,
) -> dict[str, Any]:
    extra = dict(acceptance_extra or {})
    extra["resource_guard_decision"] = guard_decision
    report_path: Path | None = None
    if is_production_equivalent_acceptance_root(data_root):
        report_path = persist_acceptance_report(acceptance_report, data_root)
    return build_acceptance_envelope(
        acceptance_report,
        job_kind="scheduler",
        trigger=f"scheduler:{profile}:{job_type}",
        data_root=data_root,
        dry_run=False,
        acceptance_report_path=report_path,
        extra=extra,
    )


def capture_scheduler_binding_child_acceptance(
    *,
    job_type: Literal["incremental", "backfill", "full_load"],
    source_id: str,
    data_domain: str,
    data_root: Path,
    cm: ConnectionManager,
    job_result: SyncJobResult,
    window: dict[str, str] | None = None,
    trigger_reason: str | None = None,
) -> tuple[AcceptanceReport, dict[str, Any]]:
    from datetime import date as date_cls

    request = acceptance_request_for_domain(
        source_id=source_id,
        data_domain=data_domain,
        start=(window or {}).get("date_start"),
        end=(window or {}).get("date_end"),
    )
    date_start = (
        date_cls.fromisoformat(window["date_start"][:10]) if window and window.get("date_start") else None
    )
    date_end = (
        date_cls.fromisoformat(window["date_end"][:10]) if window and window.get("date_end") else None
    )
    return acceptance_report_from_sync_job(
        request,
        job_result,
        cm=cm,
        data_domain=data_domain,
        job_type=job_type,
        date_start=date_start,
        date_end=date_end,
        trigger_reason=trigger_reason,
    )


def dry_run_envelope_for_plan(
    *,
    job_kind: JobKind,
    trigger: str,
    data_root: Path,
    route_payload: dict[str, Any] | None = None,
    source_id: str | None = None,
    data_domain: str | None = None,
    run_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if route_payload is None:
        if source_id is None or data_domain is None:
            raise ValueError("dry_run_envelope_for_plan requires route_payload or source/domain")
        request = acceptance_request_for_domain(
            source_id=source_id,
            data_domain=data_domain,
        )
        route_payload = preview_route_payload(request)
        report = AcceptanceReport.from_route_payload(request, route_payload)
    else:
        request = AcceptanceRequest(
            data_domain=str(route_payload.get("data_domain") or data_domain or ""),
            source_id=str(route_payload.get("selected_source_id") or source_id or ""),
            operation=str(route_payload.get("operation") or ""),
        )
        report = AcceptanceReport.from_route_payload(request, route_payload)
    return build_acceptance_envelope(
        report,
        job_kind=job_kind,
        trigger=trigger,
        data_root=data_root,
        dry_run=True,
        run_id=run_id,
        extra=extra,
    )


def aggregate_scheduler_parent_report(
    *,
    profile: str,
    data_root: Path,
    dry_run: bool,
    child_envelopes: list[dict[str, Any]],
    skipped_non_core: bool,
    resource_guard_decision: str,
) -> dict[str, Any]:
    child_reports = [
        item.get("acceptance_report")
        for item in child_envelopes
        if item.get("acceptance_report")
    ]
    required_children = [
        item
        for item in child_envelopes
        if item.get("job_type") in {"incremental", "backfill", "full_load"}
        and item.get("required", True)
    ]
    parent_status = "PASS"
    for child in required_children:
        status = str(child.get("status") or child.get("acceptance_report_status") or "FAIL")
        if status == "COMPLETED":
            status = "PASS"
        if status in {"BLOCKED", "FAIL_EXTERNAL", "CONTRACT_VIOLATION", "FAIL"}:
            parent_status = status
            break
        if status not in {"PASS", "SKIPPED", "DRY_RUN"}:
            parent_status = "FAIL"
            break
    if dry_run:
        parent_status = "DRY_RUN"
    parent_failure = "NONE" if parent_status in {"PASS", "DRY_RUN"} else parent_status
    if parent_failure not in {"NONE", "BLOCKED", "FAIL_EXTERNAL", "CONTRACT_VIOLATION"}:
        parent_failure = "FAIL"
    report = AcceptanceReport(
        source_id=profile,
        data_domain="scheduler",
        operation="run_profile",
        route_plan_id=None,
        route_grade="primary",
        implementation_mode="dry_run" if dry_run else "live",
        write_grade="not_written",
        source_used=profile,
        source_role="primary",
        source_switched=False,
        failure_class=parent_failure,
        status=parent_status,
        errors=(),
    )
    envelope = build_acceptance_envelope(
        report,
        job_kind="scheduler",
        trigger=f"qmd-data data scheduler run --profile {profile}",
        data_root=data_root,
        dry_run=dry_run,
        extra={
            "resource_guard_decision": resource_guard_decision,
            "warnings": ["skipped_non_core"] if skipped_non_core else [],
        },
    )
    envelope["child_reports"] = child_reports
    envelope["child_envelopes"] = child_envelopes
    envelope["profile"] = profile
    envelope["skipped_non_core"] = skipped_non_core
    return envelope
