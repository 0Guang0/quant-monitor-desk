"""Shared official-macro evidence bundle helpers (R3H-01 audit repair)."""

from __future__ import annotations

import hashlib
import json
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


def reject_over_cap(*, value: int, cap: int, label: str = "max_rows") -> None:
    if value <= 0:
        raise PortError("FAILED", f"invalid {label}={value}; must be positive")
    if value > cap:
        raise PortError("FAILED", f"requested {label}={value} exceeds cap={cap}")
