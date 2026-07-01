"""BIS macro incremental watermark (DCP-05 S04)."""

from __future__ import annotations

from backend.app.ops.macro_incremental_common import (
    compute_since_date,
    enabled_source_registry,
    read_observation_date_watermark,
    read_since_dates_for_instruments,
)

SOURCE_ID = "bis"
DATA_DOMAIN = "central_bank_policy"
DEFAULT_COUNTRIES = ("US",)


def enabled_bis_source_registry():
    return enabled_source_registry(source_id=SOURCE_ID, data_domain=DATA_DOMAIN)


def watermark_start_year(since_iso: str) -> int:
    """L2: digital-oracle bis.py startPeriod from macro watermark year."""
    return int(since_iso[:4])


__all__ = [
    "SOURCE_ID",
    "DATA_DOMAIN",
    "DEFAULT_COUNTRIES",
    "compute_since_date",
    "enabled_bis_source_registry",
    "read_observation_date_watermark",
    "read_since_dates_for_instruments",
    "watermark_start_year",
]
