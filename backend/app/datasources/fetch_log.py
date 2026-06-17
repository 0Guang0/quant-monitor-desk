"""Fetch audit log writer (Batch A)."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime

from backend.app.datasources.fetch_result import FetchRequest, FetchResult

_ERROR_TYPE_MAP: dict[str, str | None] = {
    "SUCCESS": None,
    "EMPTY_RESPONSE": "empty",
    "AUTH_FAILED": "auth",
    "RATE_LIMITED": "rate_limit",
    "NETWORK_ERROR": "network",
    "SCHEMA_DRIFT": "schema",
    "FAILED": "failed",
}


def _parse_timestamp(value: str | None) -> datetime | None:
    if value is None:
        return None
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


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
                None,
                0,
                _ERROR_TYPE_MAP[result.status],
                result.error_message,
            ],
        )
        return fetch_id
