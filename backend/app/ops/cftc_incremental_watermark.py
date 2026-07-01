"""CFTC COT macro incremental watermark (DCP-05 S06)."""

from __future__ import annotations

from backend.app.ops.macro_incremental_common import (
    compute_since_date,
    enabled_source_registry,
    read_observation_date_watermark,
    read_since_dates_for_instruments,
)

SOURCE_ID = "cftc_cot"
DATA_DOMAIN = "cot_positioning"
DEFAULT_MARKETS = ("088691",)
WEEKLY_ADVANCE_DAYS = 7


def enabled_cftc_source_registry():
    return enabled_source_registry(source_id=SOURCE_ID, data_domain=DATA_DOMAIN)


def read_since_dates_for_markets(con, market_codes, **kwargs):
    return read_since_dates_for_instruments(
        con, market_codes, advance_days=WEEKLY_ADVANCE_DAYS, **kwargs
    )


__all__ = [
    "SOURCE_ID",
    "DATA_DOMAIN",
    "DEFAULT_MARKETS",
    "WEEKLY_ADVANCE_DAYS",
    "compute_since_date",
    "enabled_cftc_source_registry",
    "read_observation_date_watermark",
    "read_since_dates_for_markets",
    "read_since_dates_for_instruments",
]
