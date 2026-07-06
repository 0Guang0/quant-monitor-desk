"""Official macro replay bundle → Layer1/Layer5 evidence helpers (S05 extract)."""

from __future__ import annotations

from typing import Any


def official_macro_bundle_layer1_preview(bundle: dict[str, Any]) -> dict[str, Any]:
    """Map official_macro_evidence_v1 to minimal Layer1 ingestion evidence preview (R3H-01 §9.7)."""
    if not bundle.get("source_fetch_id") or not bundle.get("content_hash"):
        raise ValueError("official macro bundle missing source_fetch_id or content_hash")
    observations = bundle.get("observations") or []
    sample = observations[0] if observations else {}
    return {
        "source_id": bundle.get("source_id"),
        "data_domain": bundle.get("data_domain") or bundle.get("series_id"),
        "source_fetch_id": bundle.get("source_fetch_id"),
        "content_hash": bundle.get("content_hash"),
        "as_of_timestamp": bundle.get("as_of_timestamp"),
        "retrieved_at": bundle.get("retrieved_at"),
        "observation_count": len(observations),
        "sample_observation_date": sample.get("observation_date") or sample.get("report_date"),
    }


def official_macro_bundle_layer5_provenance(bundle: dict[str, Any]) -> dict[str, Any]:
    """Extract Layer5 factual_source provenance fields from official macro replay bundle."""
    fid, ch = str(bundle.get("source_fetch_id") or ""), str(bundle.get("content_hash") or "")
    return {"source_fetch_ids": (fid,) if fid else (), "source_content_hashes": (ch,) if ch else ()}
