"""Layer 3 industry chain staged loader tests (020 Execute)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import yaml
from backend.app.layer3_chains.loader import (
    STAGED_LAYER3_BUNDLE_DIR,
    IndustryChainLoader,
    IndustryChainLoadError,
)

_FIXTURE_BUNDLE = Path(__file__).resolve().parent / "fixtures" / "layer3_staged_bundle"


def _copy_bundle(tmp_path: Path) -> Path:
    """复制最小 staged bundle 到 tmp_path 供变异测试。"""
    dest = tmp_path / "bundle"
    shutil.copytree(_FIXTURE_BUNDLE, dest)
    return dest


def _write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def test_layer3Loader_loadsStagedFixture_success() -> None:
  """purpose: 验证 staged bundle 五表加载成功
  target: IndustryChainLoader.load
  verifies: AC-020-1 五类集合非空；loader_mode==staged_fixture_only
  failure_meaning: loader 未解析五表或 mode 非 staged 时本测失败
  """
  result = IndustryChainLoader().load(bundle_dir=STAGED_LAYER3_BUNDLE_DIR)
  assert result.loader_mode == "staged_fixture_only"
  assert len(result.chains) >= 1
  assert len(result.nodes) >= 1
  assert len(result.anchors) >= 1
  assert len(result.edges) >= 1
  assert len(result.cross_chain_edges) >= 1
  msft = next(a for a in result.anchors if a.anchor_id == "MSFT")
  assert msft.instrument_type == "public_equity"
  assert msft.event_only is False
  assert msft.source_validation_status == "verified"


def test_layer3Loader_nonStagedMode_rejects(tmp_path: Path) -> None:
  """purpose: 拒绝非 staged_fixture_only 模式
  target: IndustryChainLoader.load manifest loader_mode
  verifies: AC-020-5 staged-only gate
  failure_meaning: 非 staged mode 未抛 IndustryChainLoadError 则 loader 绕过 gate
  """
  bundle = _copy_bundle(tmp_path)
  manifest = yaml.safe_load((bundle / "bundle_manifest.yaml").read_text(encoding="utf-8"))
  manifest["loader_mode"] = "production_live"
  (bundle / "bundle_manifest.yaml").write_text(
    yaml.safe_dump(manifest, allow_unicode=True), encoding="utf-8"
  )
  with pytest.raises(IndustryChainLoadError, match="staged_fixture_only"):
    IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_duplicateChainId_rejects(tmp_path: Path) -> None:
  """purpose: 拒绝重复 chain_id
  target: chain registry 唯一性校验
  verifies: contract chain_id must be unique
  failure_meaning: 重复 chain_id 未拒绝则唯一性规则失效
  """
  bundle = _copy_bundle(tmp_path)
  reg_path = bundle / "layer3_global_industry_chain_registry.yaml"
  reg = yaml.safe_load(reg_path.read_text(encoding="utf-8"))
  reg["chains"].append(dict(reg["chains"][0]))
  reg_path.write_text(yaml.safe_dump(reg, allow_unicode=True), encoding="utf-8")
  with pytest.raises(IndustryChainLoadError, match="chain_id"):
    IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_duplicateNodeId_rejects(tmp_path: Path) -> None:
  """purpose: 拒绝重复 node_id
  target: node registry 唯一性校验
  verifies: contract node_id must be unique
  failure_meaning: 重复 node_id 未拒绝则图节点唯一性失效
  """
  bundle = _copy_bundle(tmp_path)
  node_path = bundle / "layer3_node_registry.json"
  nodes = json.loads(node_path.read_text(encoding="utf-8"))
  nodes.append(dict(nodes[0]))
  _write_json(node_path, nodes)
  with pytest.raises(IndustryChainLoadError, match="node_id"):
    IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_duplicateAnchorId_rejects(tmp_path: Path) -> None:
  """purpose: 拒绝重复 anchor_id
  target: anchor registry 唯一性校验
  verifies: contract anchor_id must be unique
  failure_meaning: 重复 anchor_id 未拒绝则锚点唯一性失效
  """
  bundle = _copy_bundle(tmp_path)
  anchor_path = bundle / "layer3_anchor_registry.json"
  anchors = json.loads(anchor_path.read_text(encoding="utf-8"))
  anchors.append(dict(anchors[0]))
  _write_json(anchor_path, anchors)
  with pytest.raises(IndustryChainLoadError, match="anchor_id"):
    IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_edgeMissingToNode_rejects(tmp_path: Path) -> None:
  """purpose: 拒绝悬空 to_node_id
  target: edge to_node_id 引用校验
  verifies: contract edge to_node_id must exist
  failure_meaning: 悬空 to_node_id 未拒绝则图引用完整性失效
  """
  bundle = _copy_bundle(tmp_path)
  edge_path = bundle / "layer3_edge_registry.json"
  edges = json.loads(edge_path.read_text(encoding="utf-8"))
  edges[0]["to_node_id"] = "L3_MISSING_NODE"
  _write_json(edge_path, edges)
  with pytest.raises(IndustryChainLoadError, match="to_node_id"):
    IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_edgeMissingFromNode_rejects(tmp_path: Path) -> None:
  """purpose: 拒绝悬空 from_node_id
  target: edge from_node_id 引用校验
  verifies: contract edge from_node_id must exist
  failure_meaning: 悬空 from_node_id 未拒绝则图引用完整性失效
  """
  bundle = _copy_bundle(tmp_path)
  edge_path = bundle / "layer3_edge_registry.json"
  edges = json.loads(edge_path.read_text(encoding="utf-8"))
  edges[0]["from_node_id"] = "L3_MISSING_NODE"
  _write_json(edge_path, edges)
  with pytest.raises(IndustryChainLoadError, match="from_node_id"):
    IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_missingBundleFile_rejects(tmp_path: Path) -> None:
  """purpose: 缺 manifest 或数据文件时 fail-fast
  target: bundle 文件存在性检查
  verifies: contract fail-fast 无部分结果
  failure_meaning: 缺文件仍返回部分结果则违反 fail-fast
  """
  bundle = _copy_bundle(tmp_path)
  (bundle / "layer3_node_registry.json").unlink()
  with pytest.raises(IndustryChainLoadError, match="missing|node_registry"):
    IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_invalidJson_rejects(tmp_path: Path) -> None:
  """purpose: 坏 JSON 拒绝加载
  target: JSON 解析错误处理
  verifies: contract fail-fast
  failure_meaning: 坏 JSON 未抛 IndustryChainLoadError 则解析门控失效
  """
  bundle = _copy_bundle(tmp_path)
  (bundle / "layer3_anchor_registry.json").write_text("{not-json", encoding="utf-8")
  with pytest.raises(IndustryChainLoadError, match="json|anchor"):
    IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_anchorMissingNode_rejects(tmp_path: Path) -> None:
  """purpose: 拒绝 anchor 指向不存在 node
  target: anchor.node_id 引用校验
  verifies: contract anchor.node_id must exist
  failure_meaning: 悬空 anchor.node_id 未拒绝则锚点-节点绑定失效
  """
  bundle = _copy_bundle(tmp_path)
  anchor_path = bundle / "layer3_anchor_registry.json"
  anchors = json.loads(anchor_path.read_text(encoding="utf-8"))
  anchors[0]["node_id"] = "L3_MISSING_NODE"
  _write_json(anchor_path, anchors)
  with pytest.raises(IndustryChainLoadError, match="node_id"):
    IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_eventOnlyPrivate_notDailyPriceAnchor(tmp_path: Path) -> None:
  """purpose: private_company 不得作为普通日度价锚
  target: event_only + instrument_type 语义校验
  verifies: contract event_only private companies must not be ordinary daily price anchors
  failure_meaning: private_company 且 event_only=false 未拒绝则被当作行情锚
  """
  bundle = _copy_bundle(tmp_path)
  anchor_path = bundle / "layer3_anchor_registry.json"
  anchors = json.loads(anchor_path.read_text(encoding="utf-8"))
  anchors.append(
    {
      "anchor_id": "BAD_PRIVATE",
      "display_name_cn": "坏私有锚",
      "instrument_type": "private_company",
      "anchor_priority": "P1_ACTIVE",
      "node_id": "L3_TEST_CHAIN_PRIVATE_EVENTS",
      "chain_id": "L3_TEST_CHAIN",
      "event_only": False,
      "source_keys": [],
      "source_validation_status": "needs_source",
    }
  )
  _write_json(anchor_path, anchors)
  with pytest.raises(IndustryChainLoadError, match="event_only|private_company|daily price"):
    IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_p0Anchor_missingSourceKeys_rejects(tmp_path: Path) -> None:
  """purpose: P0 锚点须有 source_keys
  target: P0_CORE/P0_EVENT source_keys 校验
  verifies: contract P0_CORE and P0_EVENT anchors must have source_keys
  failure_meaning: P0 缺 source_keys 未拒绝则来源审计链断裂
  """
  bundle = _copy_bundle(tmp_path)
  anchor_path = bundle / "layer3_anchor_registry.json"
  anchors = json.loads(anchor_path.read_text(encoding="utf-8"))
  anchors[0]["source_keys"] = []
  _write_json(anchor_path, anchors)
  with pytest.raises(IndustryChainLoadError, match="source_keys"):
    IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_crossChainMissingNode_rejects(tmp_path: Path) -> None:
  """purpose: 拒绝 cross-chain 悬空节点引用
  target: cross-chain from/to node 引用校验
  verifies: contract cross-chain refs must exist
  failure_meaning: cross-chain 端点悬空未拒绝则跨链图完整性失效
  """
  bundle = _copy_bundle(tmp_path)
  cc_path = bundle / "layer3_cross_chain_edge_registry.json"
  edges = json.loads(cc_path.read_text(encoding="utf-8"))
  edges[0]["to_node_id"] = "L3_MISSING_NODE"
  _write_json(cc_path, edges)
  with pytest.raises(IndustryChainLoadError, match="to_node_id|cross"):
    IndustryChainLoader().load(bundle_dir=bundle)


def _write_empty_bundle(tmp_path: Path) -> Path:
  """构造五表均为空的 staged bundle（AUDIT A8 边界）。"""
  bundle = tmp_path / "empty_bundle"
  bundle.mkdir()
  manifest = {
    "loader_mode": "staged_fixture_only",
    "layer3_global_industry_chain_registry.yaml": "layer3_global_industry_chain_registry.yaml",
    "layer3_anchor_registry.json": "layer3_anchor_registry.json",
    "layer3_node_registry.json": "layer3_node_registry.json",
    "layer3_edge_registry.json": "layer3_edge_registry.json",
    "layer3_cross_chain_edge_registry.json": "layer3_cross_chain_edge_registry.json",
  }
  (bundle / "bundle_manifest.yaml").write_text(
    yaml.safe_dump(manifest, allow_unicode=True), encoding="utf-8"
  )
  (bundle / "layer3_global_industry_chain_registry.yaml").write_text(
    yaml.safe_dump({"chains": []}, allow_unicode=True), encoding="utf-8"
  )
  for name in (
    "layer3_anchor_registry.json",
    "layer3_node_registry.json",
    "layer3_edge_registry.json",
    "layer3_cross_chain_edge_registry.json",
  ):
    _write_json(bundle / name, [])
  return bundle


def test_layer3Loader_invalidYaml_rejects(tmp_path: Path) -> None:
  """purpose: 坏 YAML 拒绝加载
  target: manifest / chain registry YAML 解析
  verifies: O-020-02 yaml.YAMLError → IndustryChainLoadError
  failure_meaning: 坏 YAML 未统一 wrap 则调用方收到 ParserError
  """
  bundle = _copy_bundle(tmp_path)
  (bundle / "bundle_manifest.yaml").write_text("loader_mode: [\n", encoding="utf-8")
  with pytest.raises(IndustryChainLoadError, match="yaml|manifest"):
    IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_partialEmptyTables_rejects(tmp_path: Path) -> None:
  """purpose: 拒绝 chains 非空但余表为空的 bundle
  target: 五表全非空 loader 强制
  verifies: O-020-03 五表 len>=1
  failure_meaning: 仅 chains 非空时余表可全空则 AC-020-1 语义缝未闭合
  """
  bundle = _copy_bundle(tmp_path)
  for name in (
    "layer3_anchor_registry.json",
    "layer3_node_registry.json",
    "layer3_edge_registry.json",
    "layer3_cross_chain_edge_registry.json",
  ):
    _write_json(bundle / name, [])
  with pytest.raises(IndustryChainLoadError, match="non-empty|empty"):
    IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_invalidSourceValidationStatus_rejects(tmp_path: Path) -> None:
  """purpose: 拒绝非法 source_validation_status 枚举
  target: anchor source_validation_status 校验
  verifies: O-020-01 contract 枚举 gate
  failure_meaning: 非法 status 未拒绝则来源审计状态不可信
  """
  bundle = _copy_bundle(tmp_path)
  anchor_path = bundle / "layer3_anchor_registry.json"
  anchors = json.loads(anchor_path.read_text(encoding="utf-8"))
  anchors[0]["source_validation_status"] = "bogus_status"
  _write_json(anchor_path, anchors)
  with pytest.raises(IndustryChainLoadError, match="source_validation_status"):
    IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_p0Anchor_needsSourceStatus_rejects(tmp_path: Path) -> None:
  """purpose: P0 锚点不得为 needs_source
  target: P0_CORE/P0_EVENT + source_validation_status
  verifies: O-020-01 对齐 data dictionary
  failure_meaning: P0 标 needs_source 未拒绝则强证据锚点门控失效
  """
  bundle = _copy_bundle(tmp_path)
  anchor_path = bundle / "layer3_anchor_registry.json"
  anchors = json.loads(anchor_path.read_text(encoding="utf-8"))
  anchors[0]["source_validation_status"] = "needs_source"
  _write_json(anchor_path, anchors)
  with pytest.raises(IndustryChainLoadError, match="needs_source|P0"):
    IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_emptyBundle_rejects(tmp_path: Path) -> None:
  """purpose: 拒绝五表均为空的 staged bundle（AUDIT A8 边界）
  target: IndustryChainLoader.load 空 registry 集合
  verifies: fail-fast 无部分结果；空 chains 不得返回 IndustryChainLoadResult
  failure_meaning: 空 bundle 仍返回空 result 则违反 fail-fast 与 AC-020-1 非空语义
  """
  bundle = _write_empty_bundle(tmp_path)
  with pytest.raises(IndustryChainLoadError, match="non-empty|chains"):
    IndustryChainLoader().load(bundle_dir=bundle)
