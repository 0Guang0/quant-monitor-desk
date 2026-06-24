"""TDX / pytdx disabled candidate adapter skeleton (018C — not factory-registered)."""

from __future__ import annotations

from typing import Any

from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase


class TdxPytdxAdapter(SkeletonAdapterBase):
    source_id = "tdx_pytdx"
    supported_domains = frozenset({"security_list", "cn_equity_daily_bar", "cn_index_daily_bar"})


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
