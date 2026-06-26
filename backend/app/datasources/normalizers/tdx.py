"""TDX/pytdx raw evidence normalizers (R3FR-03).

MIT attribution: manifest shape ideas adapted from EasyXT tdx_provider.py (MIT);
QMD rewrite only; no runtime import from external reference trees.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def build_equity_bar_manifest(symbol: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Normalize pytdx equity daily bars into raw evidence manifest."""
    return {
        "source_id": "tdx_pytdx",
        "symbol": symbol,
        "operation": "fetch_daily_bar",
        "vendor_api": "pytdx.get_security_bars",
        "rows": rows,
        "fields": [
            "instrument_id",
            "trade_date",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "amount",
        ],
    }


def build_index_bar_manifest(index_id: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Normalize pytdx index daily bars into raw evidence manifest."""
    return {
        "source_id": "tdx_pytdx",
        "index_id": index_id,
        "operation": "fetch_index_daily_bar",
        "vendor_api": "pytdx.get_index_bars",
        "rows": rows,
        "fields": ["index_id", "trade_date", "open", "high", "low", "close", "volume", "amount"],
    }


def build_security_list_manifest(market: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Normalize pytdx security list into raw evidence manifest."""
    return {
        "source_id": "tdx_pytdx",
        "market": market,
        "operation": "fetch_security_list",
        "vendor_api": "pytdx.get_security_list",
        "rows": rows,
        "fields": ["instrument_id", "market", "name", "security_type", "source_used"],
    }


def manifest_schema_hash(manifest: dict[str, Any]) -> str:
    """Stable hash over manifest field list + operation (schema fingerprint)."""
    schema = {
        "source_id": manifest.get("source_id"),
        "operation": manifest.get("operation"),
        "fields": manifest.get("fields"),
    }
    payload = json.dumps(schema, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def manifest_content_hash(manifest: dict[str, Any]) -> str:
    """Stable hash over full manifest body for raw evidence lineage."""
    payload = json.dumps(manifest, sort_keys=True, ensure_ascii=False, default=str).encode(
        "utf-8"
    )
    return hashlib.sha256(payload).hexdigest()
