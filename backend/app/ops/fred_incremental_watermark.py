"""FRED macro incremental watermark reader (R3-DCP-02).

Re-exports unified sync/watermark SSOT (M-G1-03 P1-05).

票 06 / ADR-018：启用撬门已迁走；本模块只保留水位线读写，不再提供 enabled_fred_*。
"""

from __future__ import annotations

from backend.app.sync.watermark import (
    compute_since_date,
    read_observation_date_watermark,
    read_since_dates_for_series,
)

STAGING_TABLE = "stg_axis_observation_smoke"

__all__ = [
    "STAGING_TABLE",
    "compute_since_date",
    "read_observation_date_watermark",
    "read_since_dates_for_series",
]
