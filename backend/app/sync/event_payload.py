"""Structured job_event_log.payload_json schema (Round2 audit P2-03)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from backend.app.datasources.route_models import SourceRoutePlan

SCHEMA_KEYS = (
    "error_code",
    "source_id",
    "task_id",
    "retry_count",
    "decision",
    "rule_id",
    "route_plan_id",
    "run_id",
    "job_id",
    "route_status",
    "route_grade",
    "selected_source_id",
    "quality_flags",
    "candidates",
    "data_domain",
    "operation",
    "created_at",
)


def build_route_plan_payload(plan: SourceRoutePlan) -> str:
    """Serialize SourceRoutePlan for job_event_log.payload_json."""
    payload = plan.to_payload_dict()
    payload["decision"] = "route_plan"
    return build_event_payload(**payload)


_PARSE_ERROR_KEY = "_parse_error"


def build_event_payload(**fields: Any) -> str:
    """Build machine-readable payload JSON with canonical keys."""
    payload: dict[str, Any] = {}
    for key in SCHEMA_KEYS:
        if key in fields and fields[key] is not None:
            payload[key] = fields[key]
    for key, value in fields.items():
        if key not in payload and value is not None:
            payload[key] = value
    return json.dumps(payload, sort_keys=True)


def parse_event_payload(payload_json: str | None) -> dict[str, Any]:
    if not payload_json:
        return {}
    try:
        parsed = json.loads(payload_json)
    except json.JSONDecodeError as exc:
        return {_PARSE_ERROR_KEY: str(exc)}
    return parsed if isinstance(parsed, dict) else {_PARSE_ERROR_KEY: "not_a_dict"}


def payload_parse_failed(payload: dict[str, Any]) -> bool:
    return _PARSE_ERROR_KEY in payload
