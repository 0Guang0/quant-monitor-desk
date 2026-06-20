"""Map staged micro-fetch evidence to axis_observation staging rows (Batch 2.5 Phase 4)."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import TYPE_CHECKING

from backend.app.layer1_axes.models import AxisObservation

if TYPE_CHECKING:
    from backend.app.layer1_axes.ingestion import MicroFetchResult
from backend.app.layer1_axes.observation_contract import AXIS_OBSERVATION_DDL_COLUMNS


class ObservationMappingError(ValueError):
    """Fetch evidence cannot be mapped to a clean observation row."""


def _as_of_datetime(as_of: date) -> datetime:
    return datetime.combine(as_of, time(16, 0), tzinfo=UTC)


def _deterministic_observation_id(indicator_id: str, as_of: date, content_hash: str) -> str:
    key = f"{indicator_id}|{as_of.isoformat()}|{content_hash}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, key))


def _load_raw_evidence_payload(micro: MicroFetchResult, data_root: Path) -> dict[str, object]:
    paths = micro.fetch_result.raw_file_paths
    if not paths:
        raise ObservationMappingError("missing raw_file_paths on fetch result")
    from backend.app.storage.path_compat import is_file, read_bytes

    raw_path = (data_root / paths[0]).resolve()
    if not is_file(raw_path):
        raise ObservationMappingError(f"raw fetch file missing: {raw_path}")
    payload = json.loads(read_bytes(raw_path).decode("utf-8"))
    if not isinstance(payload, dict):
        raise ObservationMappingError("raw fetch payload must be a JSON object")
    return payload


def _assert_fixture_binding_consistent(
    payload: dict[str, object],
    fixture_path: Path,
    micro: MicroFetchResult,
) -> None:
    if not fixture_path.is_file():
        raise ObservationMappingError(f"fixture missing: {fixture_path}")
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    if str(payload.get("indicator_id")) != micro.indicator_id:
        raise ObservationMappingError("raw payload indicator_id does not match micro-fetch binding")
    if str(payload.get("as_of")) != micro.as_of.isoformat():
        raise ObservationMappingError("raw payload as_of does not match micro-fetch as_of")
    if str(fixture.get("indicator_id")) != micro.indicator_id:
        raise ObservationMappingError("fixture indicator_id does not match micro-fetch binding")
    if str(fixture.get("series_id")) != str(payload.get("series_id")):
        raise ObservationMappingError("fixture series_id does not match raw payload")


def _resolve_source_used(micro: MicroFetchResult, payload: dict[str, object]) -> str:
    selected = micro.route_plan.selected_source_id
    if selected:
        return str(selected)
    if micro.fetch_result.source_id:
        return str(micro.fetch_result.source_id)
    raw_source = payload.get("source_used")
    if raw_source:
        return str(raw_source)
    raise ObservationMappingError("cannot resolve source_used from route or fetch evidence")


def map_micro_fetch_to_observation_row(
    micro: MicroFetchResult,
    *,
    data_root: Path,
    fixture_path: Path | None = None,
) -> dict[str, object]:
    """Build one axis_observation staging row from Phase 3 micro-fetch raw evidence."""
    if micro.fetch_result.status != "SUCCESS":
        raise ObservationMappingError(
            f"fetch status {micro.fetch_result.status!r} cannot map to observation"
        )

    payload = _load_raw_evidence_payload(micro, data_root)
    if fixture_path is not None:
        _assert_fixture_binding_consistent(payload, fixture_path, micro)

    observations = payload.get("observations") or []
    if not observations:
        raise ObservationMappingError("raw payload has no observations")

    metric = observations[0]
    if not isinstance(metric, dict):
        raise ObservationMappingError("raw observation entry must be an object")
    raw_value = metric.get("metric_value")
    if raw_value is None:
        raise ObservationMappingError("raw observation missing metric_value")

    as_of_dt = _as_of_datetime(micro.as_of)
    publish_dt = datetime.combine(micro.as_of, time(0, 0), tzinfo=UTC)
    if publish_dt > as_of_dt:
        raise ObservationMappingError("publish_timestamp cannot be after as_of_timestamp")

    fetch_time_raw = micro.fetch_result.fetch_time
    if isinstance(fetch_time_raw, str):
        fetch_time = datetime.fromisoformat(fetch_time_raw.replace("Z", "+00:00"))
        if fetch_time.tzinfo is None:
            fetch_time = fetch_time.replace(tzinfo=UTC)
    else:
        fetch_time = datetime.now(UTC)

    content_hash = micro.fetch_result.content_hash or ""
    source_used = _resolve_source_used(micro, payload)
    return {
        "observation_id": _deterministic_observation_id(
            micro.indicator_id, micro.as_of, content_hash
        ),
        "indicator_id": micro.indicator_id,
        "as_of_timestamp": as_of_dt,
        "publish_timestamp": publish_dt,
        "fetch_time": fetch_time,
        "raw_value": float(raw_value),
        "raw_unit": micro.binding.unit,
        "frequency": micro.binding.frequency,
        "source_used": source_used,
        "source_channel_id": micro.fetch_result.source_id,
        "data_lag_days": 0.0,
        "stale_reason": None,
        "quality_flags": "STAGED_FIXTURE",
        "content_hash": content_hash,
        "schema_hash": micro.fetch_result.schema_hash,
        "source_switched": False,
        "created_at": datetime.now(UTC),
    }


def observation_row_to_db_tuple(row: dict[str, object]) -> list[object]:
    return [row[col] for col in AXIS_OBSERVATION_DDL_COLUMNS]


def observation_row_to_domain(row: dict[str, object]) -> AxisObservation:
    flags_raw = row.get("quality_flags")
    if isinstance(flags_raw, str):
        flags = tuple(f for f in flags_raw.split(",") if f)
    elif isinstance(flags_raw, (list, tuple)):
        flags = tuple(str(f) for f in flags_raw)
    else:
        flags = ()
    return AxisObservation(
        indicator_id=str(row["indicator_id"]),
        as_of_timestamp=row["as_of_timestamp"],  # type: ignore[arg-type]
        publish_timestamp=row["publish_timestamp"],  # type: ignore[arg-type]
        raw_value=row.get("raw_value"),  # type: ignore[arg-type]
        source_used=str(row["source_used"]),
        source_switched=bool(row.get("source_switched")),
        fallback_policy=None,
        quality_flags=flags,
    )
