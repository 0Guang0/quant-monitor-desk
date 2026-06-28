"""CN market evidence normalizer (R3H-03 G11/G16)."""

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

CN_MARKET_EVIDENCE_SCHEMA_VERSION = "cn_market_evidence_v1"

AGGREGATOR_QUALITY_FLAGS = frozenset(
    {"AGGREGATOR_VALIDATION", "NOT_PRIMARY_CANDIDATE", "SOURCE_CONFLICT_CHECK_REQUIRED"}
)


class CnMarketEvidenceError(ValueError):
    """CN market evidence bundle is invalid or incomplete."""


def _normalize_daily_bar(row: dict[str, Any], *, default_source: str) -> dict[str, Any]:
    trade_date = str(row.get("trade_date") or row.get("date") or "")
    return {
        "instrument_id": str(row.get("instrument_id") or row.get("code") or row.get("symbol") or ""),
        "trade_date": trade_date,
        "open": row.get("open"),
        "high": row.get("high"),
        "low": row.get("low"),
        "close": row.get("close"),
        "volume": row.get("volume"),
        "amount": row.get("amount"),
        "source_used": str(row.get("source_used") or default_source),
    }


def _normalize_filing(row: dict[str, Any], *, default_source: str) -> dict[str, Any]:
    return {
        "filing_id": str(row.get("filing_id") or row.get("announcement_id") or row.get("id") or ""),
        "instrument_id": str(row.get("instrument_id") or row.get("symbol") or ""),
        "title": str(row.get("title") or row.get("公告标题") or ""),
        "publish_timestamp": row.get("publish_timestamp") or row.get("公告时间"),
        "url": row.get("url"),
        "observation_date": str(row.get("observation_date") or row.get("publish_timestamp") or ""),
        "source_used": str(row.get("source_used") or default_source),
    }


def bars_from_baostock_staged_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """L2 migrate baostock staged pilot rows into canonical bars."""
    symbol = str(payload.get("symbol") or "")
    bars: list[dict[str, Any]] = []
    for row in payload.get("rows") or []:
        if isinstance(row, list) and len(row) >= 7:
            bars.append(
                _normalize_daily_bar(
                    {
                        "instrument_id": symbol or row[1],
                        "trade_date": row[0],
                        "open": row[2],
                        "high": row[3],
                        "low": row[4],
                        "close": row[5],
                        "volume": row[6],
                        "source_used": "baostock",
                    },
                    default_source="baostock",
                )
            )
        elif isinstance(row, dict):
            bars.append(_normalize_daily_bar({**row, "instrument_id": row.get("instrument_id") or symbol}, default_source="baostock"))
    return bars


def filings_from_cninfo_metadata_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """L2 migrate cninfo staged metadata rows into canonical filings."""
    symbol = str(payload.get("symbol") or "")
    filings: list[dict[str, Any]] = []
    for row in payload.get("rows") or []:
        if not isinstance(row, dict):
            continue
        filings.append(
            _normalize_filing(
                {
                    **row,
                    "instrument_id": row.get("instrument_id") or symbol,
                    "title": row.get("title") or row.get("公告标题"),
                    "publish_timestamp": row.get("publish_timestamp") or row.get("公告时间"),
                },
                default_source="cninfo",
            )
        )
    return filings


def build_cn_market_evidence_bundle(
    *,
    bars: list[dict[str, Any]] | None = None,
    filings: list[dict[str, Any]] | None = None,
    data_domain: str,
    source_fetch_id: str,
    content_hash: str,
    as_of_timestamp: str,
    retrieved_at: str | None = None,
    source_id: str = "unknown",
    quality_flags: list[str] | None = None,
    conflict_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    norm_bars = [_normalize_daily_bar(bar, default_source=source_id) for bar in (bars or [])]
    norm_filings = [_normalize_filing(row, default_source=source_id) for row in (filings or [])]
    if not norm_bars and not norm_filings:
        raise CnMarketEvidenceError("cn market evidence requires bars or filings")
    bundle: dict[str, Any] = {
        "schema_version": CN_MARKET_EVIDENCE_SCHEMA_VERSION,
        "source_id": source_id,
        "data_domain": data_domain,
        "source_fetch_id": source_fetch_id,
        "content_hash": content_hash,
        "as_of_timestamp": as_of_timestamp,
        "retrieved_at": retrieved_at or as_of_timestamp,
    }
    if norm_bars:
        bundle["bars"] = norm_bars
        bundle["trade_date"] = norm_bars[-1].get("trade_date")
    if norm_filings:
        bundle["filings"] = norm_filings
        bundle["observation_date"] = norm_filings[-1].get("observation_date") or norm_filings[-1].get("publish_timestamp")
    if quality_flags:
        bundle["quality_flags"] = list(quality_flags)
    if conflict_evidence:
        bundle["conflict_evidence"] = conflict_evidence
    return bundle


def read_cn_market_evidence_bundle(path: Path | str) -> dict[str, Any]:
    evidence_path = Path(path)
    if evidence_path.is_dir():
        evidence_path = evidence_path / "cn_market_evidence.json"
    if not evidence_path.is_file():
        raise CnMarketEvidenceError(f"missing cn market evidence: {evidence_path}")
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    fetch_id = payload.get("source_fetch_id")
    content_hash = payload.get("content_hash")
    if not fetch_id or not content_hash:
        raise CnMarketEvidenceError("cn market evidence missing source_fetch_id or content_hash")
    bundle = build_cn_market_evidence_bundle(
        bars=payload.get("bars"),
        filings=payload.get("filings"),
        data_domain=str(payload.get("data_domain") or "cn_equity_daily_bar"),
        source_id=str(payload.get("source_id") or "unknown"),
        source_fetch_id=str(fetch_id),
        content_hash=str(content_hash),
        as_of_timestamp=str(payload.get("as_of_timestamp") or payload.get("retrieved_at") or ""),
        retrieved_at=str(payload.get("retrieved_at") or payload.get("as_of_timestamp") or ""),
        quality_flags=list(payload.get("quality_flags") or []) or None,
        conflict_evidence=payload.get("conflict_evidence"),
    )
    return attach_bundle_metadata(bundle)


def write_cn_market_evidence_bundle(out_dir: Path | str, bundle: dict[str, Any]) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    canonical = build_cn_market_evidence_bundle(
        bars=bundle.get("bars"),
        filings=bundle.get("filings"),
        data_domain=str(bundle.get("data_domain") or "cn_equity_daily_bar"),
        source_id=str(bundle.get("source_id") or "unknown"),
        source_fetch_id=str(bundle.get("source_fetch_id") or "cn-unknown"),
        content_hash=str(bundle.get("content_hash") or "cn-unknown-hash"),
        as_of_timestamp=str(
            bundle.get("as_of_timestamp") or bundle.get("retrieved_at") or "1970-01-01T00:00:00Z"
        ),
        retrieved_at=str(bundle.get("retrieved_at") or bundle.get("as_of_timestamp") or None),
        quality_flags=list(bundle.get("quality_flags") or []) or None,
        conflict_evidence=bundle.get("conflict_evidence"),
    )
    finalized = finalize_bundle(canonical)
    (out_dir / "cn_market_evidence.json").write_text(
        json.dumps(finalized, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return out_dir.resolve()


def aggregator_quality_flags(*, source_id: str, primary_source_id: str = "baostock") -> list[str]:
    return sorted(
        AGGREGATOR_QUALITY_FLAGS
        | {f"VALIDATION_AGAINST_{primary_source_id.upper()}", f"SOURCE_USED_{source_id}"}
    )


def cn_market_bundle_layer2_preview(bundle: dict[str, Any]) -> dict[str, Any]:
    if not bundle.get("source_fetch_id") or not bundle.get("content_hash"):
        raise ValueError("cn market bundle missing source_fetch_id or content_hash")
    bars = bundle.get("bars") or []
    filings = bundle.get("filings") or []
    sample = (bars or filings)[0] if (bars or filings) else {}
    return {
        "source_id": bundle.get("source_id"),
        "data_domain": bundle.get("data_domain"),
        "source_fetch_id": bundle.get("source_fetch_id"),
        "content_hash": bundle.get("content_hash"),
        "as_of_timestamp": bundle.get("as_of_timestamp"),
        "retrieved_at": bundle.get("retrieved_at"),
        "bar_count": len(bars),
        "filing_count": len(filings),
        "sample_trade_date": sample.get("trade_date") or sample.get("observation_date"),
    }


def cn_market_bundle_layer3_preview(bundle: dict[str, Any]) -> dict[str, Any]:
    """Minimal Layer3 shock-anchor binding preview from CN market evidence (§9.9 smoke)."""
    preview = cn_market_bundle_layer2_preview(bundle)
    bars = bundle.get("bars") or []
    sample = bars[0] if bars else {}
    if not sample.get("instrument_id") or not sample.get("trade_date"):
        raise ValueError("cn market bundle missing anchor instrument_id or trade_date for layer3")
    return {
        "anchor_instrument_id": sample.get("instrument_id"),
        "anchor_trade_date": sample.get("trade_date"),
        "anchor_close": sample.get("close"),
        "source_fetch_id": preview["source_fetch_id"],
        "content_hash": preview["content_hash"],
        "source_id": bundle.get("source_id"),
    }


def cn_market_bundle_layer5_provenance(bundle: dict[str, Any]) -> dict[str, Any]:
    return bundle_layer5_provenance(bundle)


def cn_market_bundle_layer4_preview(bundle: dict[str, Any]) -> dict[str, Any]:
    preview = cn_market_bundle_layer2_preview(bundle)
    bars = bundle.get("bars") or []
    filings = bundle.get("filings") or []
    sample = (bars or filings)[0] if (bars or filings) else {}
    layer4 = {
        "market_id": bundle.get("data_domain"),
        "sample_instrument": sample.get("instrument_id"),
        "source_fetch_id": preview["source_fetch_id"],
        "content_hash": preview["content_hash"],
        "instrument_count": len(bars) + len(filings),
    }
    forbidden = set(layer4) & FORBIDDEN_LAYER5_HISTORY_FIELDS
    if forbidden:
        raise ValueError(f"layer4 preview must not expose forbidden fields: {sorted(forbidden)}")
    return layer4
