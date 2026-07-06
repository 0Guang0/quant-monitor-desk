"""macro_series evidence bundle → axis_observation staging rows (pure mapper)."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time
from typing import Any


def map_macro_series_bundle_to_axis_observations(
    bundle: dict[str, Any],
    *,
    series_id: str,
    start_date: str | None = None,
) -> list[dict[str, object]]:
    """Map official_macro_evidence_v1 payload → axis_observation staging rows."""
    content_hash = str(bundle.get("content_hash") or "macro-hash")
    schema_hash = str(bundle.get("schema_hash") or "macro-schema")
    fetch_time_raw = bundle.get("retrieved_at") or bundle.get("as_of_timestamp")
    if isinstance(fetch_time_raw, str):
        fetch_time = datetime.fromisoformat(fetch_time_raw.replace("Z", "+00:00"))
        if fetch_time.tzinfo is None:
            fetch_time = fetch_time.replace(tzinfo=UTC)
    else:
        fetch_time = datetime.now(UTC)
    rows: list[dict[str, object]] = []
    for obs in bundle.get("observations") or []:
        obs_date = str(obs.get("observation_date") or "")
        if not obs_date:
            continue
        if start_date and obs_date < start_date:
            continue
        raw_value = obs.get("value")
        if raw_value in (None, ".", ""):
            continue
        indicator_id = str(obs.get("series_id") or series_id)
        as_of = date.fromisoformat(obs_date)
        as_of_dt = datetime.combine(as_of, time(16, 0), tzinfo=UTC)
        publish_dt = datetime.combine(as_of, time(0, 0), tzinfo=UTC)
        obs_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{indicator_id}|{obs_date}"))
        rows.append(
            {
                "observation_id": obs_id,
                "indicator_id": indicator_id,
                "as_of_timestamp": as_of_dt,
                "publish_timestamp": publish_dt,
                "fetch_time": fetch_time,
                "raw_value": float(raw_value),
                "raw_unit": "index",
                "frequency": "daily",
                "source_used": str(bundle.get("source_id") or "fred"),
                "source_channel_id": str(bundle.get("source_id") or "fred"),
                "data_lag_days": 0.0,
                "stale_reason": None,
                "quality_flags": "INCREMENTAL",
                "content_hash": content_hash,
                "schema_hash": schema_hash,
                "source_switched": False,
                "created_at": datetime.now(UTC),
            }
        )
    return rows
