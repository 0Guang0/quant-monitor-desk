"""Tier-A live evidence loading for data health profiles (M-DATA-03 S-R2-F0)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.app.datasources.normalizers.cn_market import bars_from_baostock_staged_payload
from backend.app.datasources.normalizers.official_macro import (
    OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION,
    fred_observations_from_live_payload,
)
from backend.app.ops.data_health import (
    DataHealthLoadError,
    _resolve_payload_path,
    load_evidence_bundle,
    require_evidence_bundle,
)
from backend.app.ops.staged_pilot import _equity_bar_rows

_STANDALONE_BAR_SCHEMAS = frozenset(
    {"cn_market_evidence_v1", "market_data_evidence_v1"}
)
_LAYER1_SCHEMA = OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION
_DISCLOSURE_SCHEMAS = frozenset({"sec_edgar_evidence_v1", "cn_market_evidence_v1"})
_CRYPTO_SCHEMA = "crypto_market_evidence_v1"


def _newest_json(evidence_dir: Path) -> Path | None:
    candidates = [p for p in evidence_dir.rglob("*.json") if p.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _bar_rows_from_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get("bars"):
        rows: list[dict[str, Any]] = []
        for row in payload["bars"]:
            if not isinstance(row, dict):
                continue
            mapped = dict(row)
            if "symbol" not in mapped and mapped.get("instrument_id"):
                mapped["symbol"] = mapped["instrument_id"]
            if "trade_date" not in mapped and mapped.get("date"):
                mapped["trade_date"] = mapped["date"]
            rows.append(mapped)
        return rows
    return _equity_bar_rows(payload) if payload.get("rows") else bars_from_baostock_staged_payload(payload)


def _lineage_from_bundle(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "source_used": payload.get("source_id"),
            "source_fetch_id": payload.get("source_fetch_id"),
            "content_hash": payload.get("content_hash"),
            "as_of_timestamp": payload.get("as_of_timestamp") or payload.get("retrieved_at"),
        }
    ]


def _bars_from_manifest_bundle(
    evidence_dir: Path,
    *,
    max_rows: int,
) -> tuple[list[dict[str, Any]], str | None, list[dict[str, Any]]]:
    bundle = require_evidence_bundle(evidence_dir)
    raw = bundle.raw_manifest or {}
    source_id = str(raw.get("source_id")) if raw.get("source_id") else None
    entries = [
        item
        for item in (raw.get("manifest_entries") or raw.get("fetches") or [])
        if isinstance(item, dict)
    ]
    bars: list[dict[str, Any]] = []
    for entry in entries:
        paths = entry.get("relative_paths") or []
        fetch_result = entry.get("fetch_result") or {}
        paths = paths or fetch_result.get("raw_file_paths") or []
        for rel in paths:
            resolved = _resolve_payload_path(str(rel), evidence_dir=evidence_dir)
            if resolved is None:
                continue
            try:
                payload = _read_json(resolved)
            except (OSError, json.JSONDecodeError) as exc:
                raise DataHealthLoadError(f"invalid bar payload {rel}: {exc}") from exc
            bars.extend(_equity_bar_rows(payload))
            if len(bars) > max_rows:
                raise DataHealthLoadError(
                    f"bar ingest exceeds max_rows cap ({max_rows})"
                )
    return bars, source_id, entries


def load_market_bar_evidence(
    evidence_dir: Path,
    *,
    max_rows: int,
) -> tuple[list[dict[str, Any]], str | None, list[dict[str, Any]]]:
    """Load bars + lineage from manifest bundle or standalone bar JSON."""
    bundle = load_evidence_bundle(evidence_dir)
    if bundle.load_error is None and bundle.raw_manifest:
        return _bars_from_manifest_bundle(evidence_dir, max_rows=max_rows)

    path = _newest_json(evidence_dir)
    if path is None:
        raise DataHealthLoadError(f"no bar evidence under {evidence_dir}")
    try:
        payload = _read_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        raise DataHealthLoadError(f"invalid bar evidence {path.name}: {exc}") from exc
    schema = str(payload.get("schema_version") or "")
    if schema not in _STANDALONE_BAR_SCHEMAS and not payload.get("bars") and not payload.get("rows"):
        raise DataHealthLoadError(
            f"unsupported bar evidence schema {schema!r} in {path.name}"
        )
    bars = _bar_rows_from_payload(payload)
    if len(bars) > max_rows:
        raise DataHealthLoadError(f"bar ingest exceeds max_rows cap ({max_rows})")
    source_id = str(payload.get("source_id")) if payload.get("source_id") else None
    return bars, source_id, _lineage_from_bundle(payload)


def _normalize_layer1_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("schema_version") == _LAYER1_SCHEMA:
        return payload
    if payload.get("series"):
        observations = fred_observations_from_live_payload(payload)
        if not observations:
            raise DataHealthLoadError("fred live payload has no observations")
        series_block = (payload.get("series") or [{}])[0]
        return {
            "schema_version": _LAYER1_SCHEMA,
            "source_id": str(payload.get("source_id") or "fred"),
            "series_id": str(observations[0].get("series_id") or "unknown"),
            "observations": observations,
            "source_fetch_id": str(series_block.get("source_fetch_id") or "live-fetch"),
            "content_hash": str(series_block.get("content_hash") or "live-hash"),
            "as_of_timestamp": str(
                series_block.get("as_of_timestamp")
                or series_block.get("retrieved_at")
                or "1970-01-01T00:00:00Z"
            ),
            "retrieved_at": str(
                series_block.get("retrieved_at")
                or series_block.get("as_of_timestamp")
                or "1970-01-01T00:00:00Z"
            ),
        }
    raise DataHealthLoadError(
        "layer1 evidence missing official_macro_evidence_v1 or fred live series block"
    )


def load_layer1_evidence(evidence_dir: Path) -> dict[str, Any]:
    named = evidence_dir / "fred_evidence.json"
    path = named if named.is_file() else _newest_json(evidence_dir)
    if path is None:
        raise DataHealthLoadError(f"no layer1 evidence under {evidence_dir}")
    try:
        payload = _read_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        raise DataHealthLoadError(f"invalid layer1 evidence {path.name}: {exc}") from exc
    return _normalize_layer1_payload(payload)


def load_disclosure_evidence(evidence_dir: Path, *, domain: str) -> dict[str, Any]:
    path = _newest_json(evidence_dir)
    if path is None:
        raise DataHealthLoadError(f"no disclosure evidence under {evidence_dir}")
    try:
        payload = _read_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        raise DataHealthLoadError(f"invalid disclosure evidence {path.name}: {exc}") from exc
    schema = str(payload.get("schema_version") or "")
    if schema not in _DISCLOSURE_SCHEMAS:
        raise DataHealthLoadError(f"unsupported disclosure schema {schema!r}")
    expected_domain = (
        "cn_announcements" if domain == "cn_disclosure" else "us_filings"
    )
    data_domain = str(payload.get("data_domain") or expected_domain)
    if domain == "cn_disclosure" and data_domain not in {"cn_announcements", "cn_disclosure"}:
        raise DataHealthLoadError(f"cn_disclosure domain mismatch: {data_domain}")
    if domain == "us_disclosure" and data_domain not in {"us_filings", "us_disclosure"}:
        raise DataHealthLoadError(f"us_disclosure domain mismatch: {data_domain}")
    return payload


def load_crypto_derivative_evidence(evidence_dir: Path) -> dict[str, Any]:
    path = _newest_json(evidence_dir)
    if path is None:
        raise DataHealthLoadError(f"no crypto derivative evidence under {evidence_dir}")
    try:
        payload = _read_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        raise DataHealthLoadError(f"invalid crypto evidence {path.name}: {exc}") from exc
    if str(payload.get("schema_version") or "") != _CRYPTO_SCHEMA:
        raise DataHealthLoadError("crypto evidence requires crypto_market_evidence_v1")
    return payload
