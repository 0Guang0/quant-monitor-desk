"""Structured stderr events for WriteManager outcomes (operator scripts / log shippers)."""

from __future__ import annotations

import json
import os
import sys
from typing import Any

_WRITE_EVENT_FIELDS = frozenset(
    {
        "event",
        "run_id",
        "write_id",
        "job_id",
        "status",
        "reason_code",
        "rows_inserted",
        "rows_updated",
        "data_domain",
        "target_table",
        "requested_by",
    }
)

_WRITE_EVENTS = frozenset({"write_completed", "write_failed"})


def emit_write_telemetry(payload: dict[str, Any]) -> None:
    if os.environ.get("QMD_WRITE_TELEMETRY", "1") == "0":
        return
    event = payload.get("event")
    if event not in _WRITE_EVENTS:
        return
    filtered = {
        key: value
        for key, value in payload.items()
        if key in _WRITE_EVENT_FIELDS and value is not None
    }
    print(json.dumps(filtered, ensure_ascii=False), file=sys.stderr)


def telemetry_for_write(
    *,
    run_id: str,
    write_id: str,
    job_id: str,
    status: str,
    rows_inserted: int,
    rows_updated: int,
    data_domain: str,
    target_table: str,
    requested_by: str,
) -> None:
    event = "write_completed" if status == "SUCCESS" else "write_failed"
    emit_write_telemetry(
        {
            "event": event,
            "run_id": run_id,
            "write_id": write_id,
            "job_id": job_id,
            "status": status,
            "reason_code": None if status == "SUCCESS" else "WRITE_FAILED",
            "rows_inserted": rows_inserted if status == "SUCCESS" else None,
            "rows_updated": rows_updated if status == "SUCCESS" else None,
            "data_domain": data_domain,
            "target_table": target_table,
            "requested_by": requested_by,
        }
    )
