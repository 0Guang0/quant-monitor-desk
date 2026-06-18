"""Fetch audit log writer (Batch A)."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime

from backend.app.datasources.fetch_result import FetchRequest, FetchResult, FetchStatus
from backend.app.util.error_redaction import redact_error_message

_ERROR_TYPE_MAP: dict[str, str | None] = {
    "SUCCESS": None,
    "EMPTY_RESPONSE": "empty",
    "NOT_PUBLISHED_YET": "not_published",
    "AUTH_FAILED": "auth",
    "RATE_LIMITED": "rate_limit",
    "NETWORK_ERROR": "network",
    "SCHEMA_DRIFT": "schema",
    "FAILED": "failed",
}

_VALID_STATUSES: frozenset[FetchStatus] = frozenset(_ERROR_TYPE_MAP.keys())


class FetchLogValidationError(ValueError):
    """Raised when fetch_log row fails pre-insert validation."""


def _parse_timestamp(value: str | None) -> datetime | None:
    if value is None:
        return None
    if not value.strip():
        raise FetchLogValidationError("timestamp must be non-empty when provided")
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise FetchLogValidationError(f"invalid timestamp: {value!r}") from exc


def _validate_for_persist(result: FetchResult) -> None:
    """Defense-in-depth before INSERT (P1-5 app-layer guard)."""
    if result.status not in _VALID_STATUSES:
        raise FetchLogValidationError(f"invalid fetch_log status: {result.status!r}")
    if result.row_count < 0:
        raise FetchLogValidationError("row_count must be >= 0")
    if not result.run_id or not result.source_id or not result.data_domain:
        raise FetchLogValidationError("run_id, source_id, data_domain are required")
    if not result.fetch_time or not result.fetch_time.strip():
        raise FetchLogValidationError("fetch_time is required")
    if result.status not in _ERROR_TYPE_MAP:
        raise FetchLogValidationError(f"unknown status mapping: {result.status!r}")


class FetchLogWriter:
    def write(
        self,
        con,
        result: FetchResult,
        *,
        req: FetchRequest | None = None,
        job_id: str | None = None,
        market_id: str | None = None,
        instrument_id: str | None = None,
    ) -> str:
        _validate_for_persist(result)
        fetch_id = str(uuid.uuid4())
        request_params_hash = None
        if req is not None:
            request_params_hash = hashlib.sha256(req.model_dump_json().encode()).hexdigest()

        resolved_market_id = market_id
        if resolved_market_id is None and req is not None:
            resolved_market_id = req.market_id
        resolved_instrument_id = (
            instrument_id if instrument_id is not None else (req.instrument_id if req else None)
        )

        con.execute(
            """
            INSERT INTO fetch_log (
                fetch_id, run_id, job_id, source_id, data_domain,
                market_id, instrument_id, request_params_hash, status,
                row_count, raw_file_paths, content_hash, schema_hash,
                as_of_timestamp, publish_timestamp, fetch_time,
                latency_ms, retry_count, error_type, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                fetch_id,
                result.run_id,
                job_id,
                result.source_id,
                result.data_domain,
                resolved_market_id,
                resolved_instrument_id,
                request_params_hash,
                result.status,
                result.row_count,
                json.dumps(result.raw_file_paths),
                result.content_hash,
                result.schema_hash,
                _parse_timestamp(result.as_of_timestamp),
                _parse_timestamp(result.publish_timestamp),
                _parse_timestamp(result.fetch_time),
                result.latency_ms,
                result.retry_count,
                _ERROR_TYPE_MAP[result.status],
                redact_error_message(result.error_message),
            ],
        )
        return fetch_id
