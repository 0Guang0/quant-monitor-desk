"""Live tier router — PASS §2.1 source_id → Tier A/B/C (R3H-08 · ADR-008)."""

from __future__ import annotations

from typing import Literal

LiveTier = Literal["A", "B", "C"]

TIER_A_SOURCES = frozenset(
    {
        "fred",
        "us_treasury",
        "sec_edgar",
        "cftc_cot",
        "bis",
        "world_bank",
        "alpha_vantage",
        "deribit",
        "baostock",
        "cninfo",
        "mootdx",
    }
)

TIER_B_SOURCES = frozenset(
    {
        "yahoo_finance",
        "akshare",
        "stooq",
        "coingecko",
        "eastmoney",
        "sina_finance",
        "tdx_pytdx",
        "ths_ifind",
        "qmt_xtdata",
        "qmt_xqshare",
    }
)

TIER_C_SOURCES = frozenset(
    {
        "kalshi",
        "polymarket",
        "web_search",
    }
)


class UnknownLiveTierError(ValueError):
    """source_id not in LIVE-PROD-24 tier table."""


def resolve_live_tier(source_id: str) -> LiveTier:
    """Map source_id to Tier A/B/C per R3H_PASS_EXECUTION_PLAN §2.1."""
    if source_id in TIER_A_SOURCES:
        return "A"
    if source_id in TIER_B_SOURCES:
        return "B"
    if source_id in TIER_C_SOURCES:
        return "C"
    raise UnknownLiveTierError(f"unknown live tier for source_id={source_id!r}")
