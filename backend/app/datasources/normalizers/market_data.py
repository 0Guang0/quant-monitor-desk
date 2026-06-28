"""Market data evidence normalizer (R3H-02)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.app.datasources.normalizers.evidence_bundle import (
    attach_bundle_metadata,
    bundle_layer5_provenance,
    finalize_bundle,
)
from backend.app.layer4_markets.market_structure import FORBIDDEN_LAYER5_HISTORY_FIELDS

MARKET_DATA_EVIDENCE_SCHEMA_VERSION = "market_data_evidence_v1"


class MarketDataEvidenceError(ValueError):
    """Market daily-bar evidence bundle is invalid or incomplete."""


def _normalize_daily_bar(row: dict[str, Any]) -> dict[str, Any]:
    trade_date = str(row.get("trade_date") or row.get("date") or "")
    return {
        "instrument_id": str(row.get("instrument_id") or row.get("symbol") or ""),
        "trade_date": trade_date,
        "open": row.get("open"),
        "high": row.get("high"),
        "low": row.get("low"),
        "close": row.get("close"),
        "volume": row.get("volume"),
        "source_used": str(row.get("source_used") or ""),
    }


def build_daily_bar_evidence_bundle(
    *,
    bars: list[dict[str, Any]],
    data_domain: str,
    source_fetch_id: str,
    content_hash: str,
    as_of_timestamp: str,
    retrieved_at: str | None = None,
    source_id: str = "unknown",
    window_kind: str = "calendar_days",
) -> dict[str, Any]:
    norm_bars = [_normalize_daily_bar(bar) for bar in bars]
    if not norm_bars:
        raise MarketDataEvidenceError("market data evidence bundle requires bars")
    return {
        "schema_version": MARKET_DATA_EVIDENCE_SCHEMA_VERSION,
        "source_id": source_id,
        "data_domain": data_domain,
        "bars": norm_bars,
        "source_fetch_id": source_fetch_id,
        "content_hash": content_hash,
        "as_of_timestamp": as_of_timestamp,
        "retrieved_at": retrieved_at or as_of_timestamp,
        "window_kind": window_kind,
    }


def read_daily_bar_evidence_bundle(path: Path | str) -> dict[str, Any]:
    evidence_path = Path(path)
    if evidence_path.is_dir():
        evidence_path = evidence_path / "market_data_evidence.json"
    if not evidence_path.is_file():
        raise MarketDataEvidenceError(f"missing market data evidence: {evidence_path}")
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    bars = [_normalize_daily_bar(bar) for bar in payload.get("bars") or []]
    if not bars:
        raise MarketDataEvidenceError("market data evidence bundle has no bars")
    fetch_id = payload.get("source_fetch_id")
    content_hash = payload.get("content_hash")
    if not fetch_id or not content_hash:
        raise MarketDataEvidenceError("market data evidence missing source_fetch_id or content_hash")
    bundle = build_daily_bar_evidence_bundle(
        bars=bars,
        data_domain=str(payload.get("data_domain") or "us_equity_daily_bar"),
        source_id=str(payload.get("source_id") or "unknown"),
        source_fetch_id=str(fetch_id),
        content_hash=str(content_hash),
        as_of_timestamp=str(payload.get("as_of_timestamp") or payload.get("retrieved_at") or ""),
        retrieved_at=str(payload.get("retrieved_at") or payload.get("as_of_timestamp") or ""),
        window_kind=str(payload.get("window_kind") or "calendar_days"),
    )
    return attach_bundle_metadata(bundle)


def write_daily_bar_evidence_bundle(out_dir: Path | str, bundle: dict[str, Any]) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    canonical = build_daily_bar_evidence_bundle(
        bars=bundle.get("bars") or [],
        data_domain=str(bundle.get("data_domain") or "us_equity_daily_bar"),
        source_id=str(bundle.get("source_id") or "unknown"),
        source_fetch_id=str(bundle.get("source_fetch_id") or "market-unknown"),
        content_hash=str(bundle.get("content_hash") or "market-unknown-hash"),
        as_of_timestamp=str(
            bundle.get("as_of_timestamp") or bundle.get("retrieved_at") or "1970-01-01T00:00:00Z"
        ),
        retrieved_at=str(bundle.get("retrieved_at") or bundle.get("as_of_timestamp") or None),
        window_kind=str(bundle.get("window_kind") or "calendar_days"),
    )
    finalized = finalize_bundle(canonical)
    (out_dir / "market_data_evidence.json").write_text(
        json.dumps(finalized, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return out_dir.resolve()


def market_data_bundle_layer2_preview(bundle: dict[str, Any]) -> dict[str, Any]:
    """Map market_data_evidence_v1 to minimal Layer2 ingestion evidence preview."""
    if not bundle.get("source_fetch_id") or not bundle.get("content_hash"):
        raise ValueError("market data bundle missing source_fetch_id or content_hash")
    bars = bundle.get("bars") or []
    sample = bars[0] if bars else {}
    return {
        "source_id": bundle.get("source_id"),
        "data_domain": bundle.get("data_domain"),
        "source_fetch_id": bundle.get("source_fetch_id"),
        "content_hash": bundle.get("content_hash"),
        "as_of_timestamp": bundle.get("as_of_timestamp"),
        "retrieved_at": bundle.get("retrieved_at"),
        "bar_count": len(bars),
        "sample_trade_date": sample.get("trade_date"),
        "window_kind": bundle.get("window_kind"),
    }


def market_data_bundle_layer4_preview(bundle: dict[str, Any]) -> dict[str, Any]:
    """Map market_data_evidence_v1 to Layer4 market-structure sample fields (no L5 OHLCV history)."""
    preview = market_data_bundle_layer2_preview(bundle)
    bars = bundle.get("bars") or []
    sample = bars[0] if bars else {}
    layer4 = {
        "market_id": bundle.get("data_domain"),
        "sample_instrument_id": sample.get("instrument_id"),
        "as_of_trade_date": sample.get("trade_date"),
        "bar_count": len(bars),
        "source_fetch_id": preview["source_fetch_id"],
        "content_hash": preview["content_hash"],
    }
    forbidden = set(layer4) & FORBIDDEN_LAYER5_HISTORY_FIELDS
    if forbidden:
        raise ValueError(f"layer4 preview must not expose forbidden fields: {sorted(forbidden)}")
    return layer4


def market_data_bundle_layer5_provenance(bundle: dict[str, Any]) -> dict[str, Any]:
    """Extract Layer5 factual_source provenance fields from market data replay bundle."""
    return bundle_layer5_provenance(bundle)
