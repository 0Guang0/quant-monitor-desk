"""Shared official-macro evidence bundle helpers (R3H-01 audit repair)."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime
from typing import Any

from backend.app.datasources.adapters.fetch_port import PortError

OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION = "official_macro_evidence_v1"


def bundle_content_hash(bundle: dict[str, Any]) -> str:
    canonical = {
        k: v
        for k, v in bundle.items()
        if k not in ("content_hash", "schema_hash")
    }
    payload = json.dumps(canonical, ensure_ascii=False, default=str, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def schema_hash_for_version(schema_version: str) -> str:
    return hashlib.sha256(schema_version.encode("utf-8")).hexdigest()


def build_fetch_log(*, source_fetch_id: str, source_id: str) -> dict[str, Any]:
    return {
        "source_fetch_id": source_fetch_id,
        "source_id": source_id,
        "status": "SUCCESS",
    }


def attach_bundle_metadata(bundle: dict[str, Any]) -> dict[str, Any]:
    """Attach schema_hash/fetch_log without recomputing stored content_hash (read/replay path)."""
    bundle = dict(bundle)
    schema_version = str(bundle.get("schema_version") or OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION)
    bundle.setdefault("schema_version", schema_version)
    bundle["schema_hash"] = schema_hash_for_version(schema_version)
    fetch_id = str(bundle.get("source_fetch_id") or "")
    source_id = str(bundle.get("source_id") or "unknown")
    if fetch_id:
        bundle["fetch_log"] = build_fetch_log(source_fetch_id=fetch_id, source_id=source_id)
    return bundle


def finalize_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    bundle = dict(bundle)
    schema_version = str(bundle.get("schema_version") or OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION)
    bundle.setdefault("schema_version", schema_version)
    bundle["schema_hash"] = schema_hash_for_version(schema_version)
    fetch_id = str(bundle.get("source_fetch_id") or "")
    source_id = str(bundle.get("source_id") or "unknown")
    if fetch_id:
        bundle["fetch_log"] = build_fetch_log(source_fetch_id=fetch_id, source_id=source_id)
    bundle["content_hash"] = bundle_content_hash(bundle)
    return bundle


def parse_fetch_window_date(value: str | None) -> date | None:
    """Parse FetchRequest start_time/end_time to calendar date (ISO / Z suffix)."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None


def reject_over_cap(*, value: int, cap: int, label: str = "max_rows") -> None:
    if value <= 0:
        raise PortError("FAILED", f"invalid {label}={value}; must be positive")
    if value > cap:
        raise PortError("FAILED", f"requested {label}={value} exceeds cap={cap}")


def reject_window_span_over_cap(
    *,
    start_time: str | None,
    end_time: str | None,
    cap: int,
    label: str = "max_window_days",
) -> None:
    """Reject explicit fetch windows wider than the declared calendar-day cap."""
    if not start_time or not end_time:
        return
    start = datetime.fromisoformat(start_time.replace("Z", "+00:00")).astimezone(UTC).date()
    end = datetime.fromisoformat(end_time.replace("Z", "+00:00")).astimezone(UTC).date()
    span_days = abs((end - start).days)
    reject_over_cap(value=span_days, cap=cap, label=label)


def bundle_layer5_provenance(bundle: dict[str, Any]) -> dict[str, Any]:
    """Extract Layer5 factual_source provenance fields from an evidence bundle."""
    fid = str(bundle.get("source_fetch_id") or "")
    ch = str(bundle.get("content_hash") or "")
    return {
        "source_fetch_ids": (fid,) if fid else (),
        "source_content_hashes": (ch,) if ch else (),
        "source_used": str(bundle.get("source_id") or ""),
    }
