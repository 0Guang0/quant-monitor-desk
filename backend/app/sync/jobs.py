"""Sync job spec and state machine (Batch D §8.2).

Job event messages and ``data_sync_job.error_message`` are redacted at persistence
via ``redact_error_message`` (MASTER §7 / Batch C policy).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from backend.app.db.connection import ConnectionManager
from backend.app.sync.event_payload import build_event_payload
from backend.app.util.error_redaction import redact_error_message

SYNC_JOB_STATUSES: frozenset[str] = frozenset(
    {
        "CREATED",
        "PLANNED",
        "FETCHING",
        "STAGED",
        "VALIDATING",
        "WAITING_RECONCILE",
        "RECONCILING",
        "READY_TO_WRITE",
        "WRITING",
        "COMPLETED",
        "FAILED_FINAL",
        "SKIPPED",
        "CANCELLED",
        "MANUAL_REVIEW_REQUIRED",
        "FAILED_RETRYABLE",
    }
)

TERMINAL_STATUSES: frozenset[str] = frozenset(
    {
        "COMPLETED",
        "FAILED_FINAL",
        "SKIPPED",
        "CANCELLED",
        "MANUAL_REVIEW_REQUIRED",
    }
)

ECO_MAX_BACKFILL_DAYS_PER_TASK = 31

# docs/modules/data_sync_orchestrator.md §13.4.3 + eco default (MASTER §6.3)
BACKFILL_TRIGGER_REASONS: frozenset[str] = frozenset(
    {
        "network_failure",
        "source_lag",
        "missing_partition",
        "corporate_action_update",
        "revision_detected",
        "manual_request",
        "eco_catchup",
    }
)


def normalize_backfill_trigger_reason(trigger_reason: str | None) -> str:
    value = trigger_reason or "eco_catchup"
    if value not in BACKFILL_TRIGGER_REASONS:
        allowed = ", ".join(sorted(BACKFILL_TRIGGER_REASONS))
        raise ValueError(f"unsupported backfill trigger_reason: {value!r}; allowed: {allowed}")
    return value


def _coalesce_payload(
    payload_json: str | None,
    *,
    task_id: str | None = None,
    error_type: str | None = None,
    decision: str | None = None,
) -> str:
    if payload_json is not None:
        return payload_json
    return build_event_payload(
        task_id=task_id,
        error_code=error_type,
        decision=decision or "status_change",
    )


def _safe_event_message(message: str) -> str:
    if not message:
        return ""
    return redact_error_message(message) or ""


def _insert_job_event(
    con,
    *,
    job_id: str,
    run_id: str,
    task_id: str | None,
    event_type: str,
    old_status: str | None,
    new_status: str,
    message: str,
    payload_json: str | None,
    now: datetime | None = None,
) -> str:
    event_id = str(uuid.uuid4())
    ts = now or datetime.now(UTC)
    con.execute(
        """
        INSERT INTO job_event_log (
            event_id, run_id, job_id, task_id, event_type,
            old_status, new_status, message, payload_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            event_id,
            run_id,
            job_id,
            task_id,
            event_type,
            old_status,
            new_status,
            _safe_event_message(message),
            payload_json,
            ts,
        ],
    )
    return event_id


def plan_backfill_shards(
    date_start: date,
    date_end: date,
    *,
    max_days: int = ECO_MAX_BACKFILL_DAYS_PER_TASK,
) -> list[tuple[str, date, date]]:
    if date_end < date_start:
        raise ValueError("date_end must be on or after date_start")
    shards: list[tuple[str, date, date]] = []
    cursor = date_start
    index = 0
    while cursor <= date_end:
        shard_end = min(cursor + timedelta(days=max_days - 1), date_end)
        task_id = f"task-{index:04d}"
        shards.append((task_id, cursor, shard_end))
        cursor = shard_end + timedelta(days=1)
        index += 1
    return shards


_BASE_TRANSITIONS: dict[str, frozenset[str]] = {
    "CREATED": frozenset({"PLANNED", "CANCELLED"}),
    "PLANNED": frozenset(
        {
            "FETCHING",
            "CANCELLED",
            "FAILED_RETRYABLE",
            "FAILED_FINAL",
            "SKIPPED",
        }
    ),
    "FETCHING": frozenset({"STAGED", "FAILED_RETRYABLE", "FAILED_FINAL", "CANCELLED"}),
    "STAGED": frozenset({"VALIDATING", "FAILED_RETRYABLE", "FAILED_FINAL", "CANCELLED"}),
    "VALIDATING": frozenset(
        {
            "WAITING_RECONCILE",
            "READY_TO_WRITE",
            "MANUAL_REVIEW_REQUIRED",
            "FAILED_RETRYABLE",
            "FAILED_FINAL",
            "COMPLETED",
            "CANCELLED",
        }
    ),
    "WAITING_RECONCILE": frozenset(
        {
            "RECONCILING",
            "MANUAL_REVIEW_REQUIRED",
            "FAILED_RETRYABLE",
            "FAILED_FINAL",
            "CANCELLED",
        }
    ),
    "RECONCILING": frozenset(
        {
            "READY_TO_WRITE",
            "MANUAL_REVIEW_REQUIRED",
            "FAILED_RETRYABLE",
            "FAILED_FINAL",
            "CANCELLED",
        }
    ),
    "READY_TO_WRITE": frozenset({"WRITING", "FAILED_RETRYABLE", "FAILED_FINAL", "CANCELLED"}),
    "WRITING": frozenset({"COMPLETED", "FAILED_RETRYABLE", "FAILED_FINAL", "CANCELLED"}),
    "FAILED_RETRYABLE": frozenset({"PLANNED", "CANCELLED"}),
}


class InvalidTransitionError(ValueError):
    """Raised when a job status transition violates the sync contract."""


@dataclass(frozen=True)
class SyncJobSpec:
    run_id: str
    job_id: str
    job_type: str
    data_domain: str
    market_id: str
    source_id: str
    adapter_id: str | None
    date_start: date | None
    date_end: date | None
    instrument_id: str | None
    partition_key: str | None
    trigger_reason: str | None


@dataclass(frozen=True)
class SyncJobResult:
    job_id: str
    status: str
    validation_report_id: str | None = None
    conflict_report_id: str | None = None
    write_id: str | None = None
    message: str | None = None


class SyncJobStateMachine:
    def __init__(self, connection_manager: ConnectionManager) -> None:
        self._cm = connection_manager

    @property
    def connection_manager(self) -> ConnectionManager:
        return self._cm

    def create_job(self, spec: SyncJobSpec) -> str:
        if spec.job_type not in {
            "full_load",
            "incremental",
            "backfill",
            "revision_audit",
            "reconcile",
            "data_quality",
        }:
            raise ValueError(f"unsupported job_type: {spec.job_type!r}")
        if spec.job_type == "backfill" and spec.trigger_reason is not None:
            normalize_backfill_trigger_reason(spec.trigger_reason)
        now = datetime.now(UTC)
        with self._cm.writer() as con:
            con.execute(
                """
                INSERT INTO data_sync_job (
                    job_id, run_id, job_type, data_domain, market_id,
                    instrument_id, partition_key, date_start, date_end,
                    source_id, adapter_id, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    spec.job_id,
                    spec.run_id,
                    spec.job_type,
                    spec.data_domain,
                    spec.market_id,
                    spec.instrument_id,
                    spec.partition_key,
                    spec.date_start,
                    spec.date_end,
                    spec.source_id,
                    spec.adapter_id,
                    "CREATED",
                    now,
                    now,
                ],
            )
        return spec.job_id

    def transition(
        self,
        job_id: str,
        new_status: str,
        *,
        task_id: str | None = None,
        message: str = "",
        event_type: str = "STATUS_CHANGE",
        payload_json: str | None = None,
        error_type: str | None = None,
        error_message: str | None = None,
        con=None,
    ) -> None:
        if new_status not in SYNC_JOB_STATUSES:
            raise InvalidTransitionError(f"unknown status: {new_status!r}")
        if con is None:
            with self._cm.writer() as writer_con:
                self._transition_on_con(
                    writer_con,
                    job_id,
                    new_status,
                    task_id=task_id,
                    message=message,
                    event_type=event_type,
                    payload_json=payload_json,
                    error_type=error_type,
                    error_message=error_message,
                )
            return
        self._transition_on_con(
            con,
            job_id,
            new_status,
            task_id=task_id,
            message=message,
            event_type=event_type,
            payload_json=payload_json,
            error_type=error_type,
            error_message=error_message,
        )

    def emit_custom_event(
        self,
        job_id: str,
        *,
        task_id: str | None = None,
        event_type: str = "CUSTOM",
        message: str = "",
        old_status: str | None = None,
        new_status: str | None = None,
        payload_json: str | None = None,
        con=None,
    ) -> str:
        if con is None:
            with self._cm.writer() as writer_con:
                return self._emit_custom_event_on_con(
                    writer_con,
                    job_id,
                    task_id=task_id,
                    event_type=event_type,
                    message=message,
                    old_status=old_status,
                    new_status=new_status,
                    payload_json=payload_json,
                )
        return self._emit_custom_event_on_con(
            con,
            job_id,
            task_id=task_id,
            event_type=event_type,
            message=message,
            old_status=old_status,
            new_status=new_status,
            payload_json=payload_json,
        )

    def _emit_custom_event_on_con(
        self,
        con,
        job_id: str,
        *,
        task_id: str | None,
        event_type: str,
        message: str,
        old_status: str | None,
        new_status: str | None,
        payload_json: str | None,
    ) -> str:
        row = con.execute(
            "SELECT run_id, status FROM data_sync_job WHERE job_id = ?",
            [job_id],
        ).fetchone()
        if row is None:
            raise KeyError(f"unknown job_id: {job_id!r}")
        run_id, current_status = row[0], row[1]
        resolved_payload = _coalesce_payload(
            payload_json,
            task_id=task_id,
            decision=event_type,
        )
        return _insert_job_event(
            con,
            job_id=job_id,
            run_id=run_id,
            task_id=task_id,
            event_type=event_type,
            old_status=old_status,
            new_status=new_status or current_status,
            message=message,
            payload_json=resolved_payload,
        )

    def _transition_on_con(
        self,
        con,
        job_id: str,
        new_status: str,
        *,
        task_id: str | None,
        message: str,
        event_type: str,
        payload_json: str | None,
        error_type: str | None = None,
        error_message: str | None = None,
    ) -> None:
        row = con.execute(
            "SELECT status, job_type FROM data_sync_job WHERE job_id = ?",
            [job_id],
        ).fetchone()
        if row is None:
            raise KeyError(f"unknown job_id: {job_id!r}")
        old_status, job_type = row[0], row[1]
        if not self._is_allowed(old_status, new_status, job_type):
            raise InvalidTransitionError(
                f"invalid transition {old_status!r} -> {new_status!r} for job_type={job_type!r}"
            )
        now = datetime.now(UTC)
        if error_type is not None or error_message is not None:
            con.execute(
                """
                UPDATE data_sync_job
                SET status = ?, updated_at = ?,
                    error_type = COALESCE(?, error_type),
                    error_message = COALESCE(?, error_message)
                WHERE job_id = ?
                """,
                [
                    new_status,
                    now,
                    error_type,
                    _safe_event_message(error_message) if error_message else None,
                    job_id,
                ],
            )
        else:
            con.execute(
                """
                UPDATE data_sync_job
                SET status = ?, updated_at = ?
                WHERE job_id = ?
                """,
                [new_status, now, job_id],
            )
        run_id = con.execute(
            "SELECT run_id FROM data_sync_job WHERE job_id = ?", [job_id]
        ).fetchone()[0]
        resolved_payload = _coalesce_payload(
            payload_json,
            task_id=task_id,
            error_type=error_type,
            decision=new_status,
        )
        _insert_job_event(
            con,
            job_id=job_id,
            run_id=run_id,
            task_id=task_id,
            event_type=event_type,
            old_status=old_status,
            new_status=new_status,
            message=message,
            payload_json=resolved_payload,
            now=now,
        )

    @staticmethod
    def _is_allowed(old_status: str, new_status: str, job_type: str) -> bool:
        if old_status in TERMINAL_STATUSES:
            return False
        allowed = set(_BASE_TRANSITIONS.get(old_status, frozenset()))
        if job_type == "data_quality" and old_status == "PLANNED":
            allowed.add("VALIDATING")
        if job_type == "backfill" and old_status == "STAGED":
            allowed.add("PLANNED")
            allowed.add("COMPLETED")
        if job_type == "backfill" and old_status == "WRITING":
            allowed.add("PLANNED")
            allowed.add("COMPLETED")
        if job_type == "reconcile" and old_status == "PLANNED":
            allowed.add("WAITING_RECONCILE")
        if job_type == "reconcile" and old_status == "READY_TO_WRITE":
            allowed.add("COMPLETED")
        return new_status in allowed
