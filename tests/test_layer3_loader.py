"""第三层产业链 staged 配置包加载测试（Round 3 任务 020）。

覆盖范围：IndustryChainLoader 对五表 bundle 的解析、唯一性、
引用完整性与仅测试数据模式门禁。
"""

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


def _mutate_bundle_json(tmp_path: Path, rel: str, mutator) -> Path:
    bundle = _copy_bundle(tmp_path)
    path = bundle / rel
    data = json.loads(path.read_text(encoding="utf-8"))
    mutator(data)
    _write_json(path, data)
    return bundle


def _mutate_bundle_yaml(tmp_path: Path, rel: str, mutator) -> Path:
    bundle = _copy_bundle(tmp_path)
    path = bundle / rel
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    mutator(data)
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    return bundle


def test_layer3Loader_loadsStagedFixture_success() -> None:
    """覆盖范围：测试用产业链配置包五表成功加载
    测试对象：IndustryChainLoader.load
    目的/目标：标准 staged 包应读出链、节点、锚点、边与跨链边，且处于仅测试数据模式
    验证点：loader_mode=staged_fixture_only；五表均非空；MSFT 锚点类型/仅事件/来源校验状态正确
    失败含义：五表任一未解析或模式非 staged，第三层快照主路径无法建链
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
    """覆盖范围：非仅测试数据模式拒绝加载
    测试对象：IndustryChainLoader.load 对 bundle manifest 的模式校验
    目的/目标：防止把线上生产配置误当作 staged 产业链包加载
    验证点：loader_mode=production_live → IndustryChainLoadError 且含 staged_fixture_only
    失败含义：生产模式包仍可加载，Batch3 双闸失效
    """
    bundle = _mutate_bundle_yaml(
        tmp_path, "bundle_manifest.yaml", lambda m: m.update({"loader_mode": "production_live"})
    )
    with pytest.raises(IndustryChainLoadError, match="staged_fixture_only"):
        IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_duplicateChainId_rejects(tmp_path: Path) -> None:
    """覆盖范围：产业链 ID 重复拒绝
    测试对象：chain registry 唯一性校验
    目的/目标：同一配置包内不得出现两条相同产业链标识
    验证点：重复 chain_id → IndustryChainLoadError 且含 chain_id
    失败含义：重复产业链可共存，下游路由与快照归属混乱
    """
    bundle = _mutate_bundle_yaml(
        tmp_path,
        "layer3_global_industry_chain_registry.yaml",
        lambda reg: reg["chains"].append(dict(reg["chains"][0])),
    )
    with pytest.raises(IndustryChainLoadError, match="chain_id"):
        IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_duplicateNodeId_rejects(tmp_path: Path) -> None:
    """覆盖范围：节点 ID 重复拒绝
    测试对象：node registry 唯一性校验
    目的/目标：产业链图内每个节点标识必须全局唯一
    验证点：重复 node_id → IndustryChainLoadError 且含 node_id
    失败含义：重复节点可共存，边引用与快照聚合会指向错误实体
    """
    bundle = _mutate_bundle_json(
        tmp_path, "layer3_node_registry.json", lambda nodes: nodes.append(dict(nodes[0]))
    )
    with pytest.raises(IndustryChainLoadError, match="node_id"):
        IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_duplicateAnchorId_rejects(tmp_path: Path) -> None:
    """覆盖范围：锚点 ID 重复拒绝
    测试对象：anchor registry 唯一性校验
    目的/目标：每个定价锚点标识在包内不得重复，避免股价对照歧义
    验证点：重复 anchor_id → IndustryChainLoadError 且含 anchor_id
    失败含义：重复锚点可共存，第三层与第五层对齐会冲突
    """
    bundle = _mutate_bundle_json(
        tmp_path, "layer3_anchor_registry.json", lambda anchors: anchors.append(dict(anchors[0]))
    )
    with pytest.raises(IndustryChainLoadError, match="anchor_id"):
        IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_edgeMissingToNode_rejects(tmp_path: Path) -> None:
    """覆盖范围：边指向不存在的目标节点时拒绝
    测试对象：edge to_node_id 引用校验
    目的/目标：产业链边的终点必须对应已注册节点，悬空引用不得入库
    验证点：to_node_id 不存在 → IndustryChainLoadError 且含 to_node_id
    失败含义：悬空边可加载，图遍历与快照展开会读到幽灵节点
    """
    bundle = _mutate_bundle_json(
        tmp_path,
        "layer3_edge_registry.json",
        lambda edges: edges[0].update({"to_node_id": "L3_MISSING_NODE"}),
    )
    with pytest.raises(IndustryChainLoadError, match="to_node_id"):
        IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_edgeMissingFromNode_rejects(tmp_path: Path) -> None:
    """覆盖范围：边指向不存在的源节点时拒绝
    测试对象：edge from_node_id 引用校验
    目的/目标：产业链边的起点必须对应已注册节点
    验证点：from_node_id 不存在 → IndustryChainLoadError 且含 from_node_id
    失败含义：悬空源节点边可加载，上游归因链断裂
    """
    bundle = _mutate_bundle_json(
        tmp_path,
        "layer3_edge_registry.json",
        lambda edges: edges[0].update({"from_node_id": "L3_MISSING_NODE"}),
    )
    with pytest.raises(IndustryChainLoadError, match="from_node_id"):
        IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_missingBundleFile_rejects(tmp_path: Path) -> None:
    """覆盖范围：缺少清单或数据文件时立即失败
    测试对象：bundle 文件存在性检查
    目的/目标：配置包缺文件时不应返回部分解析结果，须整包拒收
    验证点：删除 node_registry → IndustryChainLoadError 且含 missing 或 node_registry
    失败含义：缺文件仍返回半成品，下游会基于残缺图建快照
    """
    bundle = _copy_bundle(tmp_path)
    (bundle / "layer3_node_registry.json").unlink()
    with pytest.raises(IndustryChainLoadError, match="missing|node_registry"):
        IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_invalidJson_rejects(tmp_path: Path) -> None:
    """覆盖范围：损坏的 JSON 拒绝加载
    测试对象：JSON 解析错误处理
    目的/目标：锚点表等 JSON 无法解析时须整包失败，不得静默跳过
    验证点：anchor_registry 写入无效 JSON → IndustryChainLoadError 且含 json 或 anchor
    失败含义：坏 JSON 未统一报错，调用方会收到底层解析异常
    """
    bundle = _copy_bundle(tmp_path)
    (bundle / "layer3_anchor_registry.json").write_text("{not-json", encoding="utf-8")
    with pytest.raises(IndustryChainLoadError, match="json|anchor"):
        IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_anchorMissingNode_rejects(tmp_path: Path) -> None:
    """覆盖范围：锚点绑定不存在节点时拒绝
    测试对象：anchor.node_id 引用校验
    目的/目标：每个定价锚点必须挂在已注册产业链节点上
    验证点：node_id 悬空 → IndustryChainLoadError 且含 node_id
    失败含义：锚点与节点脱钩可加载，股价对照视图无法定位链上位置
    """
    bundle = _mutate_bundle_json(
        tmp_path,
        "layer3_anchor_registry.json",
        lambda anchors: anchors[0].update({"node_id": "L3_MISSING_NODE"}),
    )
    with pytest.raises(IndustryChainLoadError, match="node_id"):
        IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_eventOnlyPrivate_notDailyPriceAnchor(tmp_path: Path) -> None:
    """覆盖范围：非上市公司不得作为普通日度价锚
    测试对象：event_only 与 instrument_type 语义校验
    目的/目标：私有公司若未标为仅事件锚，不得参与日度行情对照
    验证点：private_company 且 event_only=false → IndustryChainLoadError 且含 event_only/private_company/daily price
    失败含义：私有公司被当作日度行情锚，快照会展示不存在的市价
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
    """覆盖范围：核心锚点须声明数据来源键
    测试对象：P0 级锚点 source_keys 校验
    目的/目标：最高优先级锚点必须能追溯到至少一个配置的来源键
    验证点：P0 锚点 source_keys 为空 → IndustryChainLoadError 且含 source_keys
    失败含义：核心锚点无来源键仍可加载，来源审计链断裂
    """
    bundle = _mutate_bundle_json(
        tmp_path,
        "layer3_anchor_registry.json",
        lambda anchors: anchors[0].update({"source_keys": []}),
    )
    with pytest.raises(IndustryChainLoadError, match="source_keys"):
        IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_crossChainMissingNode_rejects(tmp_path: Path) -> None:
    """覆盖范围：跨链边悬空节点引用拒绝
    测试对象：cross-chain from/to node 引用校验
    目的/目标：跨产业链连线的两端节点均须已在包内注册
    验证点：to_node_id 悬空 → IndustryChainLoadError 且含 to_node_id 或 cross
    失败含义：跨链端点悬空可加载，多链归因与展开逻辑失真
    """
    bundle = _mutate_bundle_json(
        tmp_path,
        "layer3_cross_chain_edge_registry.json",
        lambda edges: edges[0].update({"to_node_id": "L3_MISSING_NODE"}),
    )
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
    """覆盖范围：损坏的 YAML 拒绝加载
    测试对象：manifest / chain registry YAML 解析
    目的/目标：清单或链表 YAML 语法错误时须包装为统一加载错误
    验证点：manifest 写入无效 YAML → IndustryChainLoadError 且含 yaml 或 manifest
    失败含义：坏 YAML 未统一包装，调用方会收到底层解析异常
    """
    bundle = _copy_bundle(tmp_path)
    (bundle / "bundle_manifest.yaml").write_text("loader_mode: [\n", encoding="utf-8")
    with pytest.raises(IndustryChainLoadError, match="yaml|manifest"):
        IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_partialEmptyTables_rejects(tmp_path: Path) -> None:
    """覆盖范围：产业链非空但其余四表为空时拒绝
    测试对象：五表全非空强制规则
    目的/目标：仅有产业链定义而无节点/锚点/边的包不完整，不得通过
    验证点：四张 JSON 表清空 → IndustryChainLoadError 且含 non-empty 或 empty
    失败含义：仅 chains 非空时余表可全空，第三层快照无法展开图结构
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
    """覆盖范围：非法来源校验状态枚举拒绝
    测试对象：anchor source_validation_status 校验
    目的/目标：锚点来源校验状态必须是数据字典允许的取值
    验证点：bogus_status → IndustryChainLoadError 且含 source_validation_status
    失败含义：非法状态可入库，来源可信度标注不可信
    """
    bundle = _mutate_bundle_json(
        tmp_path,
        "layer3_anchor_registry.json",
        lambda anchors: anchors[0].update({"source_validation_status": "bogus_status"}),
    )
    with pytest.raises(IndustryChainLoadError, match="source_validation_status"):
        IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_p0Anchor_needsSourceStatus_rejects(tmp_path: Path) -> None:
    """覆盖范围：核心锚点不得标为待补来源
    测试对象：P0 级锚点与 source_validation_status 组合校验
    目的/目标：最高优先级锚点不能仍处于「尚需来源」状态
    验证点：P0 标 needs_source → IndustryChainLoadError 且含 needs_source 或 P0
    失败含义：核心锚点标待补来源仍可加载，强证据门控失效
    """
    bundle = _mutate_bundle_json(
        tmp_path,
        "layer3_anchor_registry.json",
        lambda anchors: anchors[0].update({"source_validation_status": "needs_source"}),
    )
    with pytest.raises(IndustryChainLoadError, match="needs_source|P0"):
        IndustryChainLoader().load(bundle_dir=bundle)


def test_layer3Loader_emptyBundle_rejects(tmp_path: Path) -> None:
    """覆盖范围：五表均为空的配置包拒绝（审计边界）
    测试对象：IndustryChainLoader.load 空 registry 集合
    目的/目标：空包不得返回空成功结果，须整包拒收
    验证点：五表全空 → IndustryChainLoadError 且含 non-empty 或 chains
    失败含义：空包仍返回空结果，下游会误以为配置有效
    """
    bundle = _write_empty_bundle(tmp_path)
    with pytest.raises(IndustryChainLoadError, match="non-empty|chains"):
        IndustryChainLoader().load(bundle_dir=bundle)
