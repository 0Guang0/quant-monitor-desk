"""Incremental canonical domain registry for gold-path sources (ADR-009)."""

from __future__ import annotations

from dataclasses import dataclass

from backend.app.datasources.live_prod_source_tiers import INCREMENTAL_GOLD_PATH_SOURCE_IDS


@dataclass(frozen=True)
class IncrementalGoldPathEntry:
    source_id: str
    canonical_domain: str


class UnknownIncrementalGoldPathSourceError(KeyError):
    """source_id is not a registered incremental gold-path entry."""


def _build_registry() -> dict[str, IncrementalGoldPathEntry]:
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
    if frozenset(rows) != INCREMENTAL_GOLD_PATH_SOURCE_IDS:
        missing = INCREMENTAL_GOLD_PATH_SOURCE_IDS - frozenset(rows)
        extra = frozenset(rows) - INCREMENTAL_GOLD_PATH_SOURCE_IDS
        raise RuntimeError(
            f"incremental gold-path registry drift: missing={sorted(missing)} extra={sorted(extra)}"
        )
    return {
        sid: IncrementalGoldPathEntry(source_id=sid, canonical_domain=domain)
        for sid, domain in rows.items()
    }


INCREMENTAL_GOLD_PATH_BY_SOURCE: dict[str, IncrementalGoldPathEntry] = _build_registry()


def resolve_incremental_gold_path(source_id: str) -> IncrementalGoldPathEntry:
    """Return canonical incremental domain for an ADR-009 gold-path source_id."""
    try:
        return INCREMENTAL_GOLD_PATH_BY_SOURCE[source_id]
    except KeyError as exc:
        raise UnknownIncrementalGoldPathSourceError(
            f"no incremental gold-path entry for source_id={source_id!r}"
        ) from exc


def iter_incremental_gold_path_sources() -> tuple[str, ...]:
    return tuple(sorted(INCREMENTAL_GOLD_PATH_BY_SOURCE))
