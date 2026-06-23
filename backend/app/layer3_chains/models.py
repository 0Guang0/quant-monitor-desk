"""Layer 3 industry chain domain models (staged-only Round 3 Batch 4)."""

from __future__ import annotations

from dataclasses import dataclass


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
