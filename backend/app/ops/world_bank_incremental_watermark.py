"""World Bank macro incremental watermark (DCP-05 S05)."""

from __future__ import annotations

from backend.app.ops.macro_incremental_common import (
    compute_since_date,
    enabled_source_registry,
    read_observation_date_watermark,
    read_since_dates_for_instruments,
)

SOURCE_ID = "world_bank"
DATA_DOMAIN = "development_indicator"
DEFAULT_COUNTRIES = ("US",)
DEFAULT_INDICATOR = "NY.GDP.MKTP.CD"


def clean_indicator_id(country_code: str, *, indicator_id: str = DEFAULT_INDICATOR) -> str:
    return f"{country_code}|{indicator_id}"


def enabled_world_bank_source_registry():
    return enabled_source_registry(source_id=SOURCE_ID, data_domain=DATA_DOMAIN)


__all__ = [
    "SOURCE_ID",
    "DATA_DOMAIN",
    "DEFAULT_COUNTRIES",
    "DEFAULT_INDICATOR",
    "clean_indicator_id",
    "compute_since_date",
    "enabled_world_bank_source_registry",
    "read_observation_date_watermark",
    "read_since_dates_for_instruments",
]
