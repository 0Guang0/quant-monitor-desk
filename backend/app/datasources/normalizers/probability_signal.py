"""Prediction-market probability signal evidence normalizer (R3H-04)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_RESOLUTION_SOURCE_URL = re.compile(r"^https?://", re.IGNORECASE)

from backend.app.datasources.normalizers.evidence_bundle import (
    attach_bundle_metadata,
    bundle_layer5_provenance,
    finalize_bundle,
)

PROBABILITY_SIGNAL_EVIDENCE_SCHEMA_VERSION = "probability_signal_evidence_v1"

FORBIDDEN_RESOLUTION_FIELDS = frozenset(
    {
        "resolved_outcome",
        "fact_confirmed",
        "clean_write_target",
        "factual_resolution",
        "resolved",
    }
)


class ProbabilitySignalEvidenceError(ValueError):
    """Probability signal evidence bundle is invalid or incomplete."""


def reject_forbidden_resolution_fields(payload: dict[str, Any]) -> None:
    """Reject bundles that attempt to resolve factual outcomes from market prices."""
    for key in payload:
        if key in FORBIDDEN_RESOLUTION_FIELDS:
            raise ProbabilitySignalEvidenceError(
                f"forbidden factual resolution field: {key!r}"
            )
    for signal in payload.get("signals") or []:
        if not isinstance(signal, dict):
            continue
        for key in signal:
            if key in FORBIDDEN_RESOLUTION_FIELDS:
                raise ProbabilitySignalEvidenceError(
                    f"forbidden factual resolution field on signal: {key!r}"
                )


def _normalize_resolution_source(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if not _RESOLUTION_SOURCE_URL.match(text):
        raise ProbabilitySignalEvidenceError(
            f"resolution_source must be http(s) URL metadata, got {text!r}"
        )
    return text


def _normalize_signal(row: dict[str, Any]) -> dict[str, Any]:
    reject_forbidden_resolution_fields(row)
    # ponytail: read path re-canonicalizes signals — O(n) over capped signal list (≤5)
    return {
        "market_ticker": row.get("market_ticker"),
        "market_slug": row.get("market_slug"),
        "event_ticker": row.get("event_ticker"),
        "yes_bid": row.get("yes_bid"),
        "yes_ask": row.get("yes_ask"),
        "probability": row.get("probability"),
        "volume": row.get("volume"),
        "liquidity": row.get("liquidity"),
        "spread": row.get("spread"),
        "resolution_source": _normalize_resolution_source(row.get("resolution_source")),
        "source_used": str(row.get("source_used") or ""),
    }


def build_probability_signal_evidence_bundle(
    *,
    signals: list[dict[str, Any]],
    data_domain: str,
    source_fetch_id: str,
    content_hash: str,
    as_of_timestamp: str,
    retrieved_at: str | None = None,
    source_id: str = "unknown",
) -> dict[str, Any]:
    norm = [_normalize_signal(row) for row in signals]
    if not norm:
        raise ProbabilitySignalEvidenceError("probability signal bundle requires signals")
    bundle = {
        "schema_version": PROBABILITY_SIGNAL_EVIDENCE_SCHEMA_VERSION,
        "source_id": source_id,
        "data_domain": data_domain,
        "signals": norm,
        "source_fetch_id": source_fetch_id,
        "content_hash": content_hash,
        "as_of_timestamp": as_of_timestamp,
        "retrieved_at": retrieved_at or as_of_timestamp,
    }
    reject_forbidden_resolution_fields(bundle)
    return bundle


def read_probability_signal_evidence_bundle(path: Path | str) -> dict[str, Any]:
    evidence_path = Path(path)
    if evidence_path.is_dir():
        evidence_path = evidence_path / "probability_signal_evidence.json"
    if not evidence_path.is_file():
        raise ProbabilitySignalEvidenceError(
            f"missing probability signal evidence: {evidence_path}"
        )
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    reject_forbidden_resolution_fields(payload)
    signals = [_normalize_signal(row) for row in payload.get("signals") or []]
    if not signals:
        raise ProbabilitySignalEvidenceError("probability signal bundle has no signals")
    fetch_id = payload.get("source_fetch_id")
    content_hash = payload.get("content_hash")
    if not fetch_id or not content_hash:
        raise ProbabilitySignalEvidenceError(
            "probability signal evidence missing source_fetch_id or content_hash"
        )
    bundle = build_probability_signal_evidence_bundle(
        signals=signals,
        data_domain=str(payload.get("data_domain") or "prediction_market_probability"),
        source_id=str(payload.get("source_id") or "unknown"),
        source_fetch_id=str(fetch_id),
        content_hash=str(content_hash),
        as_of_timestamp=str(payload.get("as_of_timestamp") or payload.get("retrieved_at") or ""),
        retrieved_at=str(payload.get("retrieved_at") or payload.get("as_of_timestamp") or ""),
    )
    return attach_bundle_metadata(bundle)


def write_probability_signal_evidence_bundle(out_dir: Path | str, bundle: dict[str, Any]) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    canonical = build_probability_signal_evidence_bundle(
        signals=bundle.get("signals") or [],
        data_domain=str(bundle.get("data_domain") or "prediction_market_probability"),
        source_id=str(bundle.get("source_id") or "unknown"),
        source_fetch_id=str(bundle.get("source_fetch_id") or "prob-unknown"),
        content_hash=str(bundle.get("content_hash") or "prob-unknown-hash"),
        as_of_timestamp=str(
            bundle.get("as_of_timestamp") or bundle.get("retrieved_at") or "1970-01-01T00:00:00Z"
        ),
        retrieved_at=str(bundle.get("retrieved_at") or bundle.get("as_of_timestamp") or None),
    )
    finalized = finalize_bundle(canonical)
    (out_dir / "probability_signal_evidence.json").write_text(
        json.dumps(finalized, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return out_dir.resolve()


def probability_signal_bundle_layer5_provenance(bundle: dict[str, Any]) -> dict[str, Any]:
    return bundle_layer5_provenance(bundle)
