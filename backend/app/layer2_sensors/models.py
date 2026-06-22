"""Layer 2 cross-asset domain models (staged-only Round 3 Batch 3)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class CrossAssetRegistryEntry:
    asset_id: str
    display_name: str
    display_name_cn: str
    asset_group: str
    asset_type: str
    market: str
    instrument_id: str
    layer5_instrument_id: str
    primary_source: str
    validation_source: str
    fallback_policy: str
    mapped_axis: str
    is_axis_input: bool
    display_only: bool
    eligible_for_model: bool
    double_count_guard: str
    contract_code: str = ""
    roll_rule: str = ""


@dataclass(frozen=True)
class CrossAssetLoadResult:
    assets: tuple[CrossAssetRegistryEntry, ...]
    registry_version: str
    mode: str


@dataclass(frozen=True)
class CrossAssetObservation:
    asset_id: str
    trade_time: datetime
    market: str
    asset_type: str
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    pre_close: float | None
    volume: float | None
    amount: float | None
    open_interest: float | None
    source: str
    as_of_timestamp: datetime
    fetch_time: datetime
    quality_flag: str = ""


@dataclass(frozen=True)
class CrossAssetDailySnapshot:
    snapshot_id: str
    asset_id: str
    trade_date: date
    close: float | None
    pct_change: float | None
    volume: float | None
    amount: float | None
    open_interest: float | None
    level_label: str
    change_label: str
    quality_flags: tuple[str, ...]
    source_used: str
    as_of_timestamp: datetime
    lineage_snapshot_id: str
    active_contract: str = ""


@dataclass(frozen=True)
class MainContractRollEvent:
    roll_event: bool
    asset_id: str
    old_contract: str
    new_contract: str
    roll_reason: str
    roll_date: date
    volume_old: float
    volume_new: float
    open_interest_old: float
    open_interest_new: float


@dataclass(frozen=True)
class Layer2LineageEnvelope:
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
