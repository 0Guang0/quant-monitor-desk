"""Incremental canonical domain registry for gold-path sources (ADR-009)."""

from __future__ import annotations

from dataclasses import dataclass

from backend.app.datasources.live_tier_router import TIER_A_SOURCES


@dataclass(frozen=True)
class TierAIncrementalEntry:
    source_id: str
    canonical_domain: str


class UnknownTierAIncrementalSourceError(KeyError):
    """source_id is not a registered Tier A incremental entry."""


def _build_registry() -> dict[str, TierAIncrementalEntry]:
    rows = {
        "baostock": "cn_equity_daily_bar",
        "mootdx": "cn_equity_daily_bar",
        "fred": "macro_series",
        "us_treasury": "us_treasury_yield_curve",
        "bis": "central_bank_policy",
        "world_bank": "development_indicator",
        "cftc_cot": "cot_positioning",
        "cninfo": "cn_announcements",
        "sec_edgar": "us_filings",
        "alpha_vantage": "us_equity_daily_bar",
        "deribit": "crypto_options_surface",
    }
    if frozenset(rows) != TIER_A_SOURCES:
        missing = TIER_A_SOURCES - frozenset(rows)
        extra = frozenset(rows) - TIER_A_SOURCES
        raise RuntimeError(
            f"Tier A incremental registry drift: missing={sorted(missing)} extra={sorted(extra)}"
        )
    return {
        sid: TierAIncrementalEntry(source_id=sid, canonical_domain=domain)
        for sid, domain in rows.items()
    }


TIER_A_INCREMENTAL_BY_SOURCE: dict[str, TierAIncrementalEntry] = _build_registry()


def resolve_tier_a_incremental(source_id: str) -> TierAIncrementalEntry:
    """Return canonical incremental domain for a Tier A source_id."""
    try:
        return TIER_A_INCREMENTAL_BY_SOURCE[source_id]
    except KeyError as exc:
        raise UnknownTierAIncrementalSourceError(
            f"no Tier A incremental entry for source_id={source_id!r}"
        ) from exc


def iter_tier_a_incremental_sources() -> tuple[str, ...]:
    return tuple(sorted(TIER_A_INCREMENTAL_BY_SOURCE))
