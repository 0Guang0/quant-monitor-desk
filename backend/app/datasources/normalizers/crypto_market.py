"""Crypto market evidence normalizer (R3H-02)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.app.datasources.normalizers.evidence_bundle import (
    attach_bundle_metadata,
    bundle_layer5_provenance,
    finalize_bundle,
)

CRYPTO_MARKET_EVIDENCE_SCHEMA_VERSION = "crypto_market_evidence_v1"


class CryptoMarketEvidenceError(ValueError):
    """Crypto market evidence bundle is invalid or incomplete."""


def _normalize_instrument(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "instrument_name": str(row.get("instrument_name") or row.get("symbol") or ""),
        "expiration_timestamp": row.get("expiration_timestamp"),
        "strike": row.get("strike"),
        "option_type": row.get("option_type"),
        "mark_iv": row.get("mark_iv"),
        "asset_id": str(row.get("asset_id") or ""),
        "symbol": str(row.get("symbol") or ""),
        "price_usd": row.get("price_usd"),
        "market_cap_usd": row.get("market_cap_usd"),
        "volume_24h_usd": row.get("volume_24h_usd"),
        "source_used": str(row.get("source_used") or ""),
        "content_hash": row.get("content_hash"),
    }


def build_crypto_market_evidence_bundle(
    *,
    instruments: list[dict[str, Any]],
    data_domain: str,
    source_fetch_id: str,
    content_hash: str,
    as_of_timestamp: str,
    retrieved_at: str | None = None,
    source_id: str = "unknown",
) -> dict[str, Any]:
    norm = [_normalize_instrument(row) for row in instruments]
    if not norm:
        raise CryptoMarketEvidenceError("crypto market evidence bundle requires instruments")
    return {
        "schema_version": CRYPTO_MARKET_EVIDENCE_SCHEMA_VERSION,
        "source_id": source_id,
        "data_domain": data_domain,
        "instruments": norm,
        "source_fetch_id": source_fetch_id,
        "content_hash": content_hash,
        "as_of_timestamp": as_of_timestamp,
        "retrieved_at": retrieved_at or as_of_timestamp,
    }


def read_crypto_market_evidence_bundle(path: Path | str) -> dict[str, Any]:
    evidence_path = Path(path)
    if evidence_path.is_dir():
        evidence_path = evidence_path / "crypto_market_evidence.json"
    if not evidence_path.is_file():
        raise CryptoMarketEvidenceError(f"missing crypto market evidence: {evidence_path}")
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    instruments = [_normalize_instrument(row) for row in payload.get("instruments") or []]
    if not instruments:
        raise CryptoMarketEvidenceError("crypto market evidence bundle has no instruments")
    fetch_id = payload.get("source_fetch_id")
    content_hash = payload.get("content_hash")
    if not fetch_id or not content_hash:
        raise CryptoMarketEvidenceError(
            "crypto market evidence missing source_fetch_id or content_hash"
        )
    bundle = build_crypto_market_evidence_bundle(
        instruments=instruments,
        data_domain=str(payload.get("data_domain") or "crypto_spot_market"),
        source_id=str(payload.get("source_id") or "unknown"),
        source_fetch_id=str(fetch_id),
        content_hash=str(content_hash),
        as_of_timestamp=str(payload.get("as_of_timestamp") or payload.get("retrieved_at") or ""),
        retrieved_at=str(payload.get("retrieved_at") or payload.get("as_of_timestamp") or ""),
    )
    return attach_bundle_metadata(bundle)


def write_crypto_market_evidence_bundle(out_dir: Path | str, bundle: dict[str, Any]) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    canonical = build_crypto_market_evidence_bundle(
        instruments=bundle.get("instruments") or [],
        data_domain=str(bundle.get("data_domain") or "crypto_spot_market"),
        source_id=str(bundle.get("source_id") or "unknown"),
        source_fetch_id=str(bundle.get("source_fetch_id") or "crypto-unknown"),
        content_hash=str(bundle.get("content_hash") or "crypto-unknown-hash"),
        as_of_timestamp=str(
            bundle.get("as_of_timestamp") or bundle.get("retrieved_at") or "1970-01-01T00:00:00Z"
        ),
        retrieved_at=str(bundle.get("retrieved_at") or bundle.get("as_of_timestamp") or None),
    )
    finalized = finalize_bundle(canonical)
    (out_dir / "crypto_market_evidence.json").write_text(
        json.dumps(finalized, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return out_dir.resolve()


def crypto_market_bundle_layer2_preview(bundle: dict[str, Any]) -> dict[str, Any]:
    if not bundle.get("source_fetch_id") or not bundle.get("content_hash"):
        raise ValueError("crypto market bundle missing source_fetch_id or content_hash")
    instruments = bundle.get("instruments") or []
    sample = instruments[0] if instruments else {}
    return {
        "source_id": bundle.get("source_id"),
        "data_domain": bundle.get("data_domain"),
        "source_fetch_id": bundle.get("source_fetch_id"),
        "content_hash": bundle.get("content_hash"),
        "as_of_timestamp": bundle.get("as_of_timestamp"),
        "retrieved_at": bundle.get("retrieved_at"),
        "instrument_count": len(instruments),
        "sample_instrument": sample.get("instrument_name") or sample.get("symbol"),
    }


def crypto_market_bundle_layer5_provenance(bundle: dict[str, Any]) -> dict[str, Any]:
    return bundle_layer5_provenance(bundle)


def crypto_market_bundle_layer4_preview(bundle: dict[str, Any]) -> dict[str, Any]:
    """Map crypto_market_evidence_v1 to Layer4 market-structure sample (no trade history)."""
    preview = crypto_market_bundle_layer2_preview(bundle)
    instruments = bundle.get("instruments") or []
    sample = instruments[0] if instruments else {}
    return {
        "market_id": bundle.get("data_domain"),
        "sample_instrument": sample.get("instrument_name") or sample.get("asset_id"),
        "source_fetch_id": preview["source_fetch_id"],
        "content_hash": preview["content_hash"],
        "instrument_count": len(instruments),
    }
