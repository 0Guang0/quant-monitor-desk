"""Sync job spec and state machine (Batch D §8.2).

Job event messages and ``data_sync_job.error_message`` are redacted at persistence
via ``redact_error_message`` (MASTER §7 / Batch C policy).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import yaml

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

MAX_TRADING_DAYS_PER_SHARD = 5
ABSOLUTE_MAX_TRADING_DAYS = 20
DEFAULT_MAX_BACKFILL_SHARDS = 1
ABSOLUTE_MAX_BACKFILL_SHARDS = 12
# ponytail: legacy alias for tests/docs mid-migration; prefer MAX_TRADING_DAYS_PER_SHARD
ECO_MAX_BACKFILL_DAYS_PER_TASK = MAX_TRADING_DAYS_PER_SHARD
_BOUNDED_BACKFILL_CAP_PATH = (
    Path(__file__).resolve().parents[3] / "specs" / "contracts" / "bounded_backfill_cap.yaml"
)


class BackfillShardCapExceededError(ValueError):
    """Raised when a backfill window exceeds max_shards without truncate_to_cap."""


def load_bounded_backfill_cap() -> dict:
    raw = yaml.safe_load(_BOUNDED_BACKFILL_CAP_PATH.read_text(encoding="utf-8")) or {}
    return raw


def _apply_bounded_cap_ssot() -> None:
    global MAX_TRADING_DAYS_PER_SHARD
    global ABSOLUTE_MAX_TRADING_DAYS
    global DEFAULT_MAX_BACKFILL_SHARDS
    global ABSOLUTE_MAX_BACKFILL_SHARDS
    global ECO_MAX_BACKFILL_DAYS_PER_TASK
    caps = load_bounded_backfill_cap().get("caps") or {}
    MAX_TRADING_DAYS_PER_SHARD = int(caps.get("max_trading_days_per_shard", 5))
    ABSOLUTE_MAX_TRADING_DAYS = int(caps.get("absolute_max_trading_days", 20))
    DEFAULT_MAX_BACKFILL_SHARDS = int(caps.get("default_max_backfill_shards", 1))
    ABSOLUTE_MAX_BACKFILL_SHARDS = int(caps.get("absolute_max_backfill_shards", 12))
    ECO_MAX_BACKFILL_DAYS_PER_TASK = MAX_TRADING_DAYS_PER_SHARD


_apply_bounded_cap_ssot()

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
    data_domain: str,
    max_trading_days_per_shard: int = MAX_TRADING_DAYS_PER_SHARD,
    max_shards: int | None = None,
    truncate_to_cap: bool = False,
) -> list[tuple[str, date, date]]:
    from backend.app.datasources.fetch_window import backfill_trading_days

    if date_end < date_start:
        raise ValueError("date_end must be on or after date_start")
    if max_trading_days_per_shard < 1:
        raise ValueError("max_trading_days_per_shard must be at least 1")
    if max_shards is not None and max_shards < 1:
        raise ValueError("max_shards must be at least 1")

    trading_days = backfill_trading_days(data_domain, date_start, date_end)
    if not trading_days:
        raise ValueError("no trading days in backfill window")

    effective_max_trading_days = ABSOLUTE_MAX_TRADING_DAYS
    if max_shards is not None:
        effective_max_trading_days = min(
            ABSOLUTE_MAX_TRADING_DAYS,
            max_shards * max_trading_days_per_shard,
        )
    if len(trading_days) > effective_max_trading_days:
        if truncate_to_cap:
            trading_days = trading_days[:effective_max_trading_days]
        else:
            if max_shards is not None:
                raise BackfillShardCapExceededError(
                    f"backfill window exceeds max_shards={max_shards}; "
                    "use truncate_to_cap or reduce date range"
                )
            raise BackfillShardCapExceededError(
                f"backfill window exceeds absolute cap of {ABSOLUTE_MAX_TRADING_DAYS} "
                "trading days; use truncate_to_cap or reduce date range"
            )

    shards: list[tuple[str, date, date]] = []
    for index in range(0, len(trading_days), max_trading_days_per_shard):
        chunk = trading_days[index : index + max_trading_days_per_shard]
        shards.append((f"task-{len(shards):04d}", chunk[0], chunk[-1]))
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
    requested_by: str = "orchestrator"


@dataclass(frozen=True)
class SyncJobResult:
    job_id: str
    status: str
    validation_report_id: str | None = None
    conflict_report_id: str | None = None
    write_id: str | None = None
    message: str | None = None


_JOB_TYPE_TRANSITION_EXTRAS: dict[str, dict[str, frozenset[str]]] = {
    "data_quality": {("PLANNED",): frozenset({"VALIDATING"})},
    "revision_audit": {("PLANNED",): frozenset({"VALIDATING"})},
    "backfill": {
        ("STAGED",): frozenset({"PLANNED", "COMPLETED"}),
        ("WRITING",): frozenset({"PLANNED", "COMPLETED"}),
    },
    "full_load": {
        ("STAGED",): frozenset({"PLANNED", "COMPLETED"}),
        ("WRITING",): frozenset({"PLANNED", "COMPLETED"}),
    },
    "reconcile": {
        ("PLANNED",): frozenset({"WAITING_RECONCILE"}),
        ("READY_TO_WRITE",): frozenset({"COMPLETED"}),
    },
}


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
            existing = con.execute(
                "SELECT job_id FROM data_sync_job WHERE job_id = ?",
                [spec.job_id],
            ).fetchone()
            if existing is not None:
                return spec.job_id
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
        extras = _JOB_TYPE_TRANSITION_EXTRAS.get(job_type, {})
        for statuses, targets in extras.items():
            if old_status in statuses:
                allowed.update(targets)
        return new_status in allowed
