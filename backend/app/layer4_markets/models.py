"""Layer 4 market structure domain models (staged-only Round 3 Batch 5)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class MarketRegistryRow:
    market_id: str
    market_name_cn: str
    market_type: str
    timezone: str
    adapter_name: str
    is_enabled: bool


@dataclass(frozen=True)
class MarketCalendarRow:
    market_id: str
    trade_date: date
    is_trading_day: bool
    session_type: str
    timezone: str
    source: str
    quality_flag: str
    as_of_timestamp: datetime


@dataclass(frozen=True)
class MarketBreadthSnapshotRow:
    market_id: str
    trade_date: date
    advancers: int
    decliners: int
    total_amount: float
    breadth_label: str
    source: str
    quality_flag: str
    as_of_timestamp: datetime


@dataclass(frozen=True)
class Layer4LineageEnvelope:
    snapshot_id: str
    snapshot_type: str
    layer_id: str
    as_of_timestamp: datetime
    generated_at: datetime
    input_data_window_start: datetime
    input_data_window_end: datetime
    source_dataset_ids: tuple[str, ...]
    source_fetch_ids: tuple[str, ...]
    source_content_hashes: tuple[str, ...]
    rule_version: str
    code_version: str
    parameter_hash: str
    resource_profile: str
    upstream_snapshot_ids: tuple[str, ...]
    is_incremental: bool
    rebuild_reason: str | None = None


@dataclass(frozen=True)
class MarketStructureBuildResult:
    registry_rows: tuple[MarketRegistryRow, ...]
    calendar_rows: tuple[MarketCalendarRow, ...]
    breadth_row: MarketBreadthSnapshotRow
    lineage_envelope: Layer4LineageEnvelope
