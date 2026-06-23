"""Layer 3 industry chain domain models (staged-only Round 3 Batch 4)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class ChainEntry:
    chain_id: str
    chain_name_cn: str
    chain_name_en: str = ""
    chain_type: str = ""


@dataclass(frozen=True)
class NodeEntry:
    node_id: str
    chain_id: str
    node_name_cn: str = ""
    node_role: str = ""


@dataclass(frozen=True)
class AnchorEntry:
    anchor_id: str
    node_id: str
    chain_id: str
    instrument_type: str
    event_only: bool
    anchor_priority: str
    source_keys: tuple[str, ...]
    source_validation_status: str
    display_name_cn: str = ""
    ticker: str = ""


@dataclass(frozen=True)
class EdgeEntry:
    edge_id: str
    chain_id: str
    from_node_id: str
    to_node_id: str
    relation_type: str = ""


@dataclass(frozen=True)
class CrossChainEdgeEntry:
    edge_id: str
    from_chain_id: str
    from_node_id: str
    to_chain_id: str
    to_node_id: str
    relation_type: str = ""


@dataclass(frozen=True)
class IndustryChainLoadResult:
    chains: tuple[ChainEntry, ...]
    anchors: tuple[AnchorEntry, ...]
    nodes: tuple[NodeEntry, ...]
    edges: tuple[EdgeEntry, ...]
    cross_chain_edges: tuple[CrossChainEdgeEntry, ...]
    loader_mode: str


@dataclass(frozen=True)
class IndustryChainDailySnapshotRow:
    anchor_id: str
    trade_date: date
    as_of_timestamp: datetime
    latest_price: float | None = None
    pct_change_1d: float | None = None
    volume: float | None = None
    amount: float | None = None
    latest_event_title: str | None = None
    latest_event_time: datetime | None = None
    quality_flags: tuple[str, ...] = ()
    source_validation_status: str = ""
    open_interest: float | None = None


@dataclass(frozen=True)
class Layer5MappingView:
    instrument_id: str
    trade_date: date
    close: float
    as_of_timestamp: datetime
    volume: float | None = None


@dataclass(frozen=True)
class Layer3LineageEnvelope:
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
class IndustryChainSnapshotBuildResult:
    snapshots: tuple[IndustryChainDailySnapshotRow, ...]
    lineage_envelopes: tuple[Layer3LineageEnvelope, ...]
    layer5_mapping_views: tuple[Layer5MappingView, ...]
