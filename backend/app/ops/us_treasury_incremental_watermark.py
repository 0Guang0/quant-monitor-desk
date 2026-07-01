"""US Treasury macro incremental watermark (DCP-05 S03)."""

from __future__ import annotations

from backend.app.ops.macro_incremental_common import (
    compute_since_date,
    enabled_source_registry,
    read_observation_date_watermark,
    read_since_dates_for_instruments,
)

SOURCE_ID = "us_treasury"
DATA_DOMAIN = "us_treasury_yield_curve"
DEFAULT_TENORS = ("10Y",)


def enabled_us_treasury_source_registry():
    return enabled_source_registry(source_id=SOURCE_ID, data_domain=DATA_DOMAIN)


__all__ = [
    "SOURCE_ID",
    "DATA_DOMAIN",
    "DEFAULT_TENORS",
    "compute_since_date",
    "enabled_us_treasury_source_registry",
    "read_observation_date_watermark",
    "read_since_dates_for_instruments",
]
