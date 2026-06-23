"""Load layer3 industry chain registry from staged fixture bundle (Batch 4 / 020)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from backend.app.config import PROJECT_ROOT
from backend.app.layer3_chains.models import (
    AnchorEntry,
    ChainEntry,
    CrossChainEdgeEntry,
    EdgeEntry,
    IndustryChainLoadResult,
    NodeEntry,
)

STAGED_LAYER3_BUNDLE_DIR = PROJECT_ROOT / "tests" / "fixtures" / "layer3_staged_bundle"

_P0_PRIORITIES = frozenset({"P0_CORE", "P0_EVENT"})
_SOURCE_VALIDATION_STATUSES = frozenset({
    "verified",
    "needs_source",
    "event_only_verified",
    "price_proxy_needs_feed",
})

# ponytail: five _load_* functions kept separate (no factory); ceiling is
# _safe_yaml_load + _edge_id_from + _validate_edge_node_refs + _assert_non_empty


class IndustryChainLoadError(ValueError):
    """Layer 3 staged bundle failed validation."""


class IndustryChainLoader:
    """Parse staged layer3 registry bundle into typed entries."""

    def load(self, *, bundle_dir: Path | None = None) -> IndustryChainLoadResult:
        root = (bundle_dir or STAGED_LAYER3_BUNDLE_DIR).resolve()
        manifest_path = root / "bundle_manifest.yaml"
        if not manifest_path.is_file():
            raise IndustryChainLoadError(f"missing bundle manifest: {manifest_path}")

        manifest = _safe_yaml_load(
            manifest_path.read_text(encoding="utf-8"), "bundle manifest"
        )
        if not isinstance(manifest, dict):
            raise IndustryChainLoadError("bundle manifest root must be a mapping")

        mode = str(manifest.get("loader_mode", ""))
        if mode != "staged_fixture_only":
            raise IndustryChainLoadError(
                f"loader_mode {mode!r} is not staged_fixture_only; "
                "production-live registry load is forbidden on 020"
            )

        chains = _load_chains(root, manifest)
        nodes = _load_nodes(root, manifest)
        anchors = _load_anchors(root, manifest)
        edges = _load_edges(root, manifest)
        cross_chain_edges = _load_cross_chain_edges(root, manifest)

        _assert_non_empty(chains, "chain registry")
        _assert_non_empty(nodes, "node registry")
        _assert_non_empty(anchors, "anchor registry")
        _assert_non_empty(edges, "edge registry")
        _assert_non_empty(cross_chain_edges, "cross-chain edge registry")

        node_ids = {node.node_id for node in nodes}

        _assert_unique([chain.chain_id for chain in chains], "chain_id")
        _assert_unique([node.node_id for node in nodes], "node_id")
        _assert_unique([anchor.anchor_id for anchor in anchors], "anchor_id")

        _validate_edge_node_refs(edges, node_ids, edge_kind="")
        _validate_edge_node_refs(cross_chain_edges, node_ids, edge_kind="cross-chain")

        for anchor in anchors:
            if anchor.node_id not in node_ids:
                raise IndustryChainLoadError(
                    f"anchor {anchor.anchor_id!r} references missing node_id {anchor.node_id!r}"
                )
            _validate_anchor_rules(anchor)

        return IndustryChainLoadResult(
            chains=tuple(chains),
            anchors=tuple(anchors),
            nodes=tuple(nodes),
            edges=tuple(edges),
            cross_chain_edges=tuple(cross_chain_edges),
            loader_mode=mode,
        )


def _safe_yaml_load(text: str, label: str) -> Any:
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise IndustryChainLoadError(f"invalid yaml in {label}") from exc


def _assert_non_empty(items: list[Any], label: str) -> None:
    if not items:
        raise IndustryChainLoadError(f"{label} must be a non-empty list")


def _resolve_manifest_file(root: Path, manifest: dict[str, Any], key: str) -> Path:
    rel = manifest.get(key)
    if not rel:
        raise IndustryChainLoadError(f"manifest missing path for {key!r}")
    path = root / str(rel)
    if not path.is_file():
        raise IndustryChainLoadError(f"missing {key}: {path}")
    return path


def _load_json_list(root: Path, manifest: dict[str, Any], key: str) -> list[dict[str, Any]]:
    path = _resolve_manifest_file(root, manifest, key)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise IndustryChainLoadError(f"invalid json in {key}: {path}") from exc
    if not isinstance(raw, list):
        raise IndustryChainLoadError(f"{key} root must be a list")
    items: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            raise IndustryChainLoadError(f"each entry in {key} must be a mapping")
        items.append(item)
    return items


def _load_chains(root: Path, manifest: dict[str, Any]) -> list[ChainEntry]:
    path = _resolve_manifest_file(root, manifest, "layer3_global_industry_chain_registry.yaml")
    raw = _safe_yaml_load(path.read_text(encoding="utf-8"), "chain registry")
    if not isinstance(raw, dict):
        raise IndustryChainLoadError("chain registry root must be a mapping")
    chains_raw = raw.get("chains")
    if not isinstance(chains_raw, list):
        raise IndustryChainLoadError("chain registry must contain a chains list")

    chains: list[ChainEntry] = []
    for item in chains_raw:
        if not isinstance(item, dict):
            raise IndustryChainLoadError("each chain entry must be a mapping")
        chain_id = str(item.get("chain_id", "")).strip()
        if not chain_id:
            raise IndustryChainLoadError("chain entry missing chain_id")
        chains.append(
            ChainEntry(
                chain_id=chain_id,
                chain_name_cn=str(item.get("chain_name_cn", chain_id)),
                chain_name_en=str(item.get("chain_name_en", "")),
                chain_type=str(item.get("chain_type", "")),
            )
        )
    return chains


def _load_nodes(root: Path, manifest: dict[str, Any]) -> list[NodeEntry]:
    items = _load_json_list(root, manifest, "layer3_node_registry.json")
    nodes: list[NodeEntry] = []
    for item in items:
        node_id = str(item.get("node_id", "")).strip()
        if not node_id:
            raise IndustryChainLoadError("node entry missing node_id")
        nodes.append(
            NodeEntry(
                node_id=node_id,
                chain_id=str(item.get("chain_id", "")),
                node_name_cn=str(item.get("node_name_cn", "")),
                node_role=str(item.get("node_role", "")),
            )
        )
    return nodes


def _load_anchors(root: Path, manifest: dict[str, Any]) -> list[AnchorEntry]:
    items = _load_json_list(root, manifest, "layer3_anchor_registry.json")
    anchors: list[AnchorEntry] = []
    for item in items:
        anchor_id = str(item.get("anchor_id", "")).strip()
        if not anchor_id:
            raise IndustryChainLoadError("anchor entry missing anchor_id")
        source_raw = item.get("source_keys", [])
        if source_raw is None:
            source_raw = []
        if not isinstance(source_raw, list):
            raise IndustryChainLoadError(f"anchor {anchor_id!r} source_keys must be a list")
        status = str(item.get("source_validation_status", "")).strip()
        if status not in _SOURCE_VALIDATION_STATUSES:
            raise IndustryChainLoadError(
                f"anchor {anchor_id!r} has invalid source_validation_status {status!r}"
            )
        anchors.append(
            AnchorEntry(
                anchor_id=anchor_id,
                node_id=str(item.get("node_id", "")),
                chain_id=str(item.get("chain_id", "")),
                instrument_type=str(item.get("instrument_type", "")),
                event_only=bool(item.get("event_only", False)),
                anchor_priority=str(item.get("anchor_priority", "")),
                source_keys=tuple(str(k) for k in source_raw),
                source_validation_status=status,
                display_name_cn=str(item.get("display_name_cn", anchor_id)),
                ticker=str(item.get("ticker", "")),
            )
        )
    return anchors


def _edge_id_from(item: dict[str, Any], missing_msg: str) -> str:
    edge_id = str(item.get("edge_id", "")).strip()
    if not edge_id:
        raise IndustryChainLoadError(missing_msg)
    return edge_id


def _load_edges(root: Path, manifest: dict[str, Any]) -> list[EdgeEntry]:
    items = _load_json_list(root, manifest, "layer3_edge_registry.json")
    edges: list[EdgeEntry] = []
    for item in items:
        edge_id = _edge_id_from(item, "edge entry missing edge_id")
        edges.append(
            EdgeEntry(
                edge_id=edge_id,
                chain_id=str(item.get("chain_id", "")),
                from_node_id=str(item.get("from_node_id", "")),
                to_node_id=str(item.get("to_node_id", "")),
                relation_type=str(item.get("relation_type", "")),
            )
        )
    return edges


def _load_cross_chain_edges(root: Path, manifest: dict[str, Any]) -> list[CrossChainEdgeEntry]:
    items = _load_json_list(root, manifest, "layer3_cross_chain_edge_registry.json")
    edges: list[CrossChainEdgeEntry] = []
    for item in items:
        edge_id = _edge_id_from(item, "cross-chain edge entry missing edge_id")
        edges.append(
            CrossChainEdgeEntry(
                edge_id=edge_id,
                from_chain_id=str(item.get("from_chain_id", "")),
                from_node_id=str(item.get("from_node_id", "")),
                to_chain_id=str(item.get("to_chain_id", "")),
                to_node_id=str(item.get("to_node_id", "")),
                relation_type=str(item.get("relation_type", "")),
            )
        )
    return edges


def _assert_unique(values: list[str], field_name: str) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise IndustryChainLoadError(f"duplicate {field_name} {value!r}")
        seen.add(value)


def _validate_edge_node_refs(
    edges: list[EdgeEntry] | list[CrossChainEdgeEntry],
    node_ids: set[str],
    *,
    edge_kind: str,
) -> None:
    prefix = f"{edge_kind} " if edge_kind else ""
    for edge in edges:
        if edge.from_node_id not in node_ids:
            raise IndustryChainLoadError(
                f"{prefix}edge {edge.edge_id!r} references missing "
                f"from_node_id {edge.from_node_id!r}"
            )
        if edge.to_node_id not in node_ids:
            raise IndustryChainLoadError(
                f"{prefix}edge {edge.edge_id!r} references missing "
                f"to_node_id {edge.to_node_id!r}"
            )


def _validate_anchor_rules(anchor: AnchorEntry) -> None:
    if anchor.instrument_type == "private_company" and not anchor.event_only:
        raise IndustryChainLoadError(
            f"anchor {anchor.anchor_id!r} private_company with event_only=false "
            "must not be treated as ordinary daily price anchor"
        )
    if anchor.anchor_priority in _P0_PRIORITIES and not anchor.source_keys:
        raise IndustryChainLoadError(
            f"anchor {anchor.anchor_id!r} with priority {anchor.anchor_priority!r} "
            "missing source_keys"
        )
    if (
        anchor.anchor_priority in _P0_PRIORITIES
        and anchor.source_validation_status == "needs_source"
    ):
        raise IndustryChainLoadError(
            f"anchor {anchor.anchor_id!r} with priority {anchor.anchor_priority!r} "
            "cannot have source_validation_status needs_source"
        )
