"""第三层产业链快照构建器测试（Round 3 任务 021）。

覆盖范围：用测试用的产业链配置和第五层股价，生成行业链日快照、
股价对照视图和来源追溯（血缘）记录。
"""

from __future__ import annotations

import shutil
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
import yaml
from backend.app.config import PROJECT_ROOT
from backend.app.core.snapshot_lineage import LINEAGE_REQUIRED_FIELDS
from backend.app.layer3_chains.loader import STAGED_LAYER3_BUNDLE_DIR, IndustryChainLoader
from backend.app.layer3_chains.models import (
    IndustryChainLoadResult,
    IndustryChainSnapshotBuildResult,
)
from backend.app.layer3_chains.snapshot_builder import (
    IndustryChainSnapshotBuilder,
    Layer3SnapshotError,
    _parse_ts,
)

_FIXTURE_L5 = Path(__file__).resolve().parent / "fixtures" / "layer3_l5_staged_bars"
_MUTATION_ROOT = PROJECT_ROOT / ".audit-sandbox" / "layer3_l5_mutations"
AS_OF = datetime(2026, 6, 15, 16, 0, tzinfo=UTC)
TRADE_DATE = date(2026, 6, 14)


def _build(
    *,
    l5_bundle_dir: Path = _FIXTURE_L5,
    as_of: datetime = AS_OF,
) -> IndustryChainSnapshotBuildResult:
    """ponytail: shared build() for AC tests; copytree only when mutating manifest."""
    load_result = IndustryChainLoader().load(bundle_dir=STAGED_LAYER3_BUNDLE_DIR)
    return IndustryChainSnapshotBuilder().build(
        load_result=load_result,
        as_of=as_of,
        trade_date=TRADE_DATE,
        l5_bundle_dir=l5_bundle_dir,
    )


def _copy_l5_bundle(tmp_path: Path) -> Path:
    """Copy fixture under PROJECT_ROOT so UF-1 path guard allows mutation tests."""
    dest = _MUTATION_ROOT / tmp_path.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(_FIXTURE_L5, dest)
    return dest


def _mutate_l5_manifest(tmp_path: Path, mutator) -> Path:
    """ponytail: copy L5 bundle then apply in-place manifest mutation."""
    bundle = _copy_l5_bundle(tmp_path)
    manifest_path = bundle / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    mutator(manifest)
    manifest_path.write_text(yaml.safe_dump(manifest, allow_unicode=True), encoding="utf-8")
    return bundle


def test_layer3Snapshot_buildsFromStagedLoaderAndL5_success() -> None:
    """覆盖范围：用测试用的产业链数据和股价文件，在数据齐全时走正常建快照路径
    测试对象：IndustryChainSnapshotBuilder.build
    目的/目标：证明在合规测试数据下能生成至少一条带价格的行业链日快照，并正确记录 as_of 时间
    验证点：至少一条快照有 latest_price；全部 as_of_timestamp 等于入参；含 MSFT 锚点
    失败含义：正常 staged 路径建不出有价快照，说明 loader+L5 拼接主路径坏了
    """
    result = _build()
    priced = [s for s in result.snapshots if s.latest_price is not None]
    assert len(priced) >= 1
    assert all(s.as_of_timestamp == AS_OF for s in result.snapshots)
    assert any(s.anchor_id == "MSFT" for s in result.snapshots)


def test_layer3Snapshot_nonStagedL5Source_rejects(tmp_path: Path) -> None:
    """覆盖范围：股价数据来源不是「仅测试数据」时的拒绝逻辑
    测试对象：IndustryChainSnapshotBuilder.build 对 manifest 的校验
    目的/目标：防止把线上真实行情误当成测试快照来生成
    验证点：source_mode=production_live → Layer3SnapshotError 且含 staged_fixture_only
    失败含义：非 staged 行情仍能建快照，Batch3 gate 双闸失效
    """
    bundle = _mutate_l5_manifest(
        tmp_path, lambda m: m.update({"source_mode": "production_live"})
    )
    with pytest.raises(Layer3SnapshotError, match="staged_fixture_only"):
        _build(l5_bundle_dir=bundle)


def test_layer3Snapshot_lineageRequiredFieldsComplete() -> None:
    """覆盖范围：生成快照时附带的血缘（来源追溯）信息是否齐全
    测试对象：IndustryChainSnapshotBuilder.build 产出的 lineage_envelopes
    目的/目标：每条快照都能说清楚「数据从哪来、何时算的」，缺关键字段就视为不合格
    验证点：LINEAGE_REQUIRED_FIELDS 逐字段非空（rebuild_reason 可空）；layer_id=layer3；hashes 非空
    失败含义：血缘缺字段仍绿，contract AC-021-2 与增量重建审计会失真
    """
    result = _build()
    assert len(result.lineage_envelopes) >= 1
    envelope = result.lineage_envelopes[0]
    for field in LINEAGE_REQUIRED_FIELDS:
        if field == "rebuild_reason":
            continue
        assert getattr(envelope, field) is not None, field
    assert envelope.layer_id == "layer3"
    assert envelope.source_content_hashes


def test_snapshotLineageContainsSourceHashes() -> None:
    """覆盖范围：单独组装血缘记录时必填项是否齐全
    测试对象：Layer3LineageBuilder.build
    目的/目标：血缘里要带上数据来源的校验指纹，并标明属于第三层（layer3）
    验证点：LINEAGE_REQUIRED_FIELDS 全填；layer_id=layer3
    失败含义：Layer3LineageBuilder 单独调用时契约字段不全，下游持久化会拒收
    """
    from backend.app.layer3_chains.lineage import Layer3LineageBuilder

    lineage = Layer3LineageBuilder().build(
        snapshot_id="l3-test-lineage",
        snapshot_type="industry_chain_daily_snapshot",
        as_of=AS_OF,
        input_window_start=AS_OF - timedelta(days=5),
        input_window_end=AS_OF - timedelta(days=1),
        source_dataset_ids=("staged:layer5_bar:MSFT",),
        source_fetch_ids=("fetch-l3-1",),
        source_content_hashes=("sha256-deadbeef",),
        rule_version="layer3_chain_staged_v1",
        parameter_hash="param-hash-l3",
    )
    for field in LINEAGE_REQUIRED_FIELDS:
        if field == "rebuild_reason":
            continue
        assert getattr(lineage, field) is not None
    assert lineage.layer_id == "layer3"


def test_snapshotRejectsFutureInput(tmp_path: Path) -> None:
    """覆盖范围：观测时间晚于「截至日」时的拒绝逻辑
    测试对象：IndustryChainSnapshotBuilder.build 对 as_of 边界的检查
    目的/目标：不允许用「未来」的行情数据回填历史快照
    验证点：bar as_of_timestamp 晚于 build as_of → Layer3SnapshotError 含 future
    失败含义：未来可见数据混入快照，no_future_data 契约被绕过
    """
    bundle = _mutate_l5_manifest(
        tmp_path,
        lambda m: m["anchors"]["MSFT"]["bars"][0].update(
            {"as_of_timestamp": (AS_OF + timedelta(days=1)).isoformat()}
        ),
    )
    with pytest.raises(Layer3SnapshotError, match="future"):
        _build(l5_bundle_dir=bundle)


def test_layer3Snapshot_eventOnly_skipsPriceFields() -> None:
    """覆盖范围：只有事件、没有上市股票代码的锚点
    测试对象：IndustryChainSnapshotBuilder.build 对 event_only 的处理
    目的/目标：这类锚点不应硬填股价和涨跌幅（例如 OPENAI 没有公开 ticker）
    验证点：OPENAI 快照 latest_price、pct_change_1d 均为 None
    失败含义：event_only 被误填行情，§8.12.6 staged 子集语义错误
    """
    result = _build()
    openai = next(s for s in result.snapshots if s.anchor_id == "OPENAI")
    assert openai.latest_price is None
    assert openai.pct_change_1d is None


def test_layer3Snapshot_eventOnly_lineageUsesAnchorDatasetId() -> None:
    """覆盖范围：event_only 锚点血缘的 source_dataset_ids 语义
    测试对象：IndustryChainSnapshotBuilder.build 对 event_only 的 lineage 分支
    目的/目标：event_only 不消费 L5 bar，dataset_id 应指向 layer3 anchor 而非 layer5 bar
    验证点：OPENAI envelope 的 source_dataset_ids 含 staged:layer3_anchor:OPENAI
    失败含义：event_only 血缘标成 L5 bar 来源，溯源指纹与实际输入错位（D-1 锁定）
    """
    result = _build()
    openai_lineage = next(
        e for e in result.lineage_envelopes if e.snapshot_id.startswith("l3-lineage-OPENAI")
    )
    assert openai_lineage.source_dataset_ids == ("staged:layer3_anchor:OPENAI",)


def test_layer3Snapshot_layer5MappingView_nonEventOnly() -> None:
    """覆盖范围：快照与第五层股价之间的对照视图
    测试对象：IndustryChainSnapshotBuilder.build 产出的 layer5_mapping_views
    目的/目标：有股票的锚点（如 MSFT）能在视图里看到对应的 instrument 和收盘价
    验证点：MSFT 视图 instrument_id、close、trade_date、as_of_timestamp 与 fixture 一致
    失败含义：mapping view 缺字段或错价，AC-021-5 与 Layer5 对照链断裂
    """
    result = _build()
    msft_view = next(v for v in result.layer5_mapping_views if v.instrument_id == "L5-MSFT-US")
    assert msft_view.close == 420.5
    assert msft_view.trade_date == TRADE_DATE
    assert msft_view.as_of_timestamp <= AS_OF


def test_layer3Snapshot_missingL5Bar_rejects(tmp_path: Path) -> None:
    """覆盖范围：某只股票应有行情文件却找不到时
    测试对象：IndustryChainSnapshotBuilder.build 查找 bar 的逻辑
    目的/目标：缺行情就整体失败，不能悄悄跳过只生成一半快照
    验证点：manifest 删 MSFT 锚点 → Layer3SnapshotError 且提及 MSFT
    失败含义：缺 bar 仍部分成功，fail-fast 与 L2 对称行为失效
    """
    bundle = _mutate_l5_manifest(tmp_path, lambda m: m["anchors"].pop("MSFT"))
    with pytest.raises(Layer3SnapshotError, match="MSFT"):
        _build(l5_bundle_dir=bundle)


def test_layer3Snapshot_tradeDateMismatch_rejects(tmp_path: Path) -> None:
    """覆盖范围：请求 trade_date 与 manifest bar 交易日不一致
    测试对象：IndustryChainSnapshotBuilder.build 的 _bar_for_trade_date
    目的/目标：对齐 L2 test_snapshotBuilder_rejectsTradeDateMismatch，fail-closed 拒绝错日行情
    验证点：bar 仅含 2026-06-13、build 要 2026-06-14 → Layer3SnapshotError 含 trade_date
    失败含义：错日 bar 被误用或静默跳过，日快照键与行情日不一致
    """
    bundle = _mutate_l5_manifest(
        tmp_path,
        lambda m: m["anchors"]["MSFT"]["bars"][0].update({"trade_date": "2026-06-13"}),
    )
    with pytest.raises(Layer3SnapshotError, match="trade_date"):
        _build(l5_bundle_dir=bundle)


def test_layer3Snapshot_missingManifestHashes_rejects(tmp_path: Path) -> None:
    """覆盖范围：L5 manifest 缺 source_content_hashes
    测试对象：IndustryChainSnapshotBuilder.build 的 _manifest_provenance
    目的/目标：§5.2 S2 失败语义 — 无溯源指纹不得建 lineage
    验证点：删除 source_content_hashes → Layer3SnapshotError 含 source_content_hashes
    失败含义：缺 hash 仍建快照，血缘不可审计
    """
    bundle = _mutate_l5_manifest(tmp_path, lambda m: m.pop("source_content_hashes"))
    with pytest.raises(Layer3SnapshotError, match="source_content_hashes"):
        _build(l5_bundle_dir=bundle)


def test_layer3Snapshot_malformedBarElement_rejects(tmp_path: Path) -> None:
    """覆盖范围：bars[] 含非 dict 元素时的 schema 边界拒绝
    测试对象：IndustryChainSnapshotBuilder.build 的 _bar_for_trade_date
    目的/目标：R3-B6-021-O-01 — 畸形 bar 须 fail-closed，禁止 continue 静默跳过
    验证点：bars 插入字符串元素 → Layer3SnapshotError 含 mapping
    失败含义：非 dict bar 被跳过或误用，manifest 畸形数据可渗入快照
    """
    bundle = _mutate_l5_manifest(
        tmp_path,
        lambda m: m["anchors"]["MSFT"]["bars"].insert(0, "not-a-dict-bar"),
    )
    with pytest.raises(Layer3SnapshotError, match="mapping"):
        _build(l5_bundle_dir=bundle)


def test_layer3Snapshot_missingBarField_rejects(tmp_path: Path) -> None:
    """覆盖范围：匹配到的 bar 缺必填字段 close
    测试对象：_bar_for_trade_date 返回前的字段校验（D-2）
    目的/目标：畸形 YAML 抛 Layer3SnapshotError，不泄漏 KeyError
    验证点：删 MSFT bar 的 close → Layer3SnapshotError 含 close
    失败含义：KeyError 逃出信任边界，调用方无法统一 fail-closed
    """
    bundle = _mutate_l5_manifest(
        tmp_path, lambda m: m["anchors"]["MSFT"]["bars"][0].pop("close")
    )
    with pytest.raises(Layer3SnapshotError, match="close"):
        _build(l5_bundle_dir=bundle)


def test_snapshotParseTs_rejectsNaiveTimestamp() -> None:
    """覆盖范围：_parse_ts 对无时区时间戳的拒绝（D-3）
    测试对象：snapshot_builder._parse_ts
    目的/目标：naive datetime 不得与 aware as_of 比较，须 fail-closed
    验证点：传入 naive ISO 字符串 → Layer3SnapshotError 含 timezone-aware
    失败含义：naive/aware 混比导致 TypeError 或静默错误比较
    """
    with pytest.raises(Layer3SnapshotError, match="timezone-aware"):
        _parse_ts("2026-06-14T20:00:00")


def test_layer3Snapshot_naiveBarTimestamp_rejects(tmp_path: Path) -> None:
    """覆盖范围：bar as_of_timestamp 为 naive 时的 build 路径拒绝
    测试对象：IndustryChainSnapshotBuilder.build 经 _parse_ts 的集成路径
    目的/目标：D-3 不仅在单元级，畸形 fixture 也须在 build 边界拒绝
    验证点：MSFT bar as_of_timestamp 去掉时区 → Layer3SnapshotError
    失败含义：集成路径仍接受 naive，生产化 as_of 边界不可靠
    """
    bundle = _mutate_l5_manifest(
        tmp_path,
        lambda m: m["anchors"]["MSFT"]["bars"][0].update(
            {"as_of_timestamp": "2026-06-14T20:00:00"}
        ),
    )
    with pytest.raises(Layer3SnapshotError, match="timezone-aware"):
        _build(l5_bundle_dir=bundle)


def test_layer3Snapshot_emptyAnchors_returnsEmpty() -> None:
    """覆盖范围：产业链加载结果里没有任何锚点（anchors 为空）
    测试对象：IndustryChainSnapshotBuilder.build
    目的/目标：没有锚点时应返回空结果，而不是报错或捏造快照行
    验证点：空 anchors → snapshots、mapping_views、lineage_envelopes 均为空元组
    失败含义：空输入仍产出假数据或抛错，说明边界处理坏了
    """
    empty_load = IndustryChainLoadResult(
        chains=(),
        anchors=(),
        nodes=(),
        edges=(),
        cross_chain_edges=(),
        loader_mode="staged_fixture_only",
    )
    result = IndustryChainSnapshotBuilder().build(
        load_result=empty_load,
        as_of=AS_OF,
        trade_date=TRADE_DATE,
        l5_bundle_dir=_FIXTURE_L5,
    )
    assert result.snapshots == ()
    assert result.layer5_mapping_views == ()
    assert result.lineage_envelopes == ()


def test_layer3Snapshot_missingManifestFetchIds_rejects(tmp_path: Path) -> None:
    """覆盖范围：L5 manifest 缺 source_fetch_ids
    测试对象：IndustryChainSnapshotBuilder.build 的 _manifest_provenance
    目的/目标：§5.2 S2 失败语义 — 无 fetch id 不得建 lineage
    验证点：删除 source_fetch_ids → Layer3SnapshotError 含 source_fetch_ids
    失败含义：缺 fetch id 仍建快照，血缘不可追溯到抓取批次
    """
    bundle = _mutate_l5_manifest(tmp_path, lambda m: m.pop("source_fetch_ids"))
    with pytest.raises(Layer3SnapshotError, match="source_fetch_ids"):
        _build(l5_bundle_dir=bundle)


def test_layer3Snapshot_missingL5Manifest_rejects(tmp_path: Path) -> None:
    """覆盖范围：L5 bundle 目录无 manifest.yaml
    测试对象：IndustryChainSnapshotBuilder.build 的 _read_l5_manifest
    目的/目标：缺 manifest 须 fail-closed，不得静默空读
    验证点：空目录作 l5_bundle_dir → Layer3SnapshotError 含 missing L5 manifest
    失败含义：无 manifest 仍继续 build，staged 双闸与 provenance 链断裂
    """
    bundle = _MUTATION_ROOT / tmp_path.name / "empty"
    bundle.mkdir(parents=True, exist_ok=True)
    with pytest.raises(Layer3SnapshotError, match="missing L5 manifest"):
        _build(l5_bundle_dir=bundle)


def test_layer3Snapshot_invalidManifestYaml_rejects(tmp_path: Path) -> None:
    """覆盖范围：L5 manifest YAML 语法非法
    测试对象：IndustryChainSnapshotBuilder.build 的 _read_l5_manifest
    目的/目标：畸形 YAML 须包装为 Layer3SnapshotError，不泄漏 YAMLError
    验证点：写入坏 YAML → Layer3SnapshotError 含 invalid yaml
    失败含义：YAMLError 逃出信任边界，调用方无法统一 fail-closed
    """
    bundle = _copy_l5_bundle(tmp_path)
    (bundle / "manifest.yaml").write_text("not: valid: yaml: [", encoding="utf-8")
    with pytest.raises(Layer3SnapshotError, match="invalid yaml"):
        _build(l5_bundle_dir=bundle)


def test_layer3Lineage_rejectsEmptySourceFetchIds() -> None:
    """覆盖范围：Layer3 lineage builder 对空 source_fetch_ids 的拒绝
    测试对象：Layer3LineageBuilder.build
    目的/目标：ADV-R3X contract-scoped — 无 fetch id 不得建 lineage envelope
    验证点：source_fetch_ids=() → Layer3LineageError 含 source_fetch_ids
    失败含义：空 fetch id 仍建 lineage，血缘不可追溯到抓取批次
    """
    from backend.app.layer3_chains.lineage import Layer3LineageBuilder, Layer3LineageError

    with pytest.raises(Layer3LineageError, match="source_fetch_ids"):
        Layer3LineageBuilder().build(
            snapshot_id="l3-empty-fetch",
            snapshot_type="industry_chain_daily_snapshot",
            as_of=AS_OF,
            input_window_start=AS_OF - timedelta(days=1),
            input_window_end=AS_OF,
            source_dataset_ids=("staged:layer3_anchor:MSFT",),
            source_fetch_ids=(),
            source_content_hashes=("sha256-deadbeef",),
            rule_version="layer3_chain_staged_v1",
            parameter_hash="param-hash-l3",
        )


def test_layer3Lineage_rejectsEmptySourceContentHashes() -> None:
    """覆盖范围：Layer3 lineage builder 对空 source_content_hashes 的拒绝
    测试对象：Layer3LineageBuilder.build
    目的/目标：ADV-R3X contract-scoped — 无内容指纹不得建 lineage envelope
    验证点：source_content_hashes=() → Layer3LineageError 含 source_content_hashes
    失败含义：空 hash 仍建 lineage，增量重建无法校验输入完整性
    """
    from backend.app.layer3_chains.lineage import Layer3LineageBuilder, Layer3LineageError

    with pytest.raises(Layer3LineageError, match="source_content_hashes"):
        Layer3LineageBuilder().build(
            snapshot_id="l3-empty-hash",
            snapshot_type="industry_chain_daily_snapshot",
            as_of=AS_OF,
            input_window_start=AS_OF - timedelta(days=1),
            input_window_end=AS_OF,
            source_dataset_ids=("staged:layer3_anchor:MSFT",),
            source_fetch_ids=("fetch-l3-1",),
            source_content_hashes=(),
            rule_version="layer3_chain_staged_v1",
            parameter_hash="param-hash-l3",
        )


def test_snapshotLineage_agentOutputsNotSource_rejectsAgentProse() -> None:
    """覆盖范围：agent 文案不得进入 source_dataset_ids（contract 约束）
    测试对象：Layer3LineageBuilder.build 经 validate_source_dataset_ids
    目的/目标：对齐 L1 负向测，Layer3 lineage 须拒绝 agent_summary 类 dataset id
    验证点：source_dataset_ids 含 agent_summary → Layer3LineageError 含 agent outputs
    失败含义：agent 输出混入血缘来源，agent_outputs_not_source 契约失效
    """
    from backend.app.layer3_chains.lineage import Layer3LineageBuilder, Layer3LineageError

    with pytest.raises(Layer3LineageError, match="agent outputs"):
        Layer3LineageBuilder().build(
            snapshot_id="l3-agent-bad",
            snapshot_type="industry_chain_daily_snapshot",
            as_of=AS_OF,
            input_window_start=AS_OF - timedelta(days=1),
            input_window_end=AS_OF,
            source_dataset_ids=("agent_summary:建议买入",),
            source_fetch_ids=("fetch-l3-1",),
            source_content_hashes=("sha256-deadbeef",),
            rule_version="layer3_chain_staged_v1",
            parameter_hash="param-hash-l3",
        )


def test_layer3Snapshot_deterministicRebuild_sameInputsSameHash() -> None:
    """覆盖范围：同输入重复 build 的全 row tuple 与 lineage 稳定性
    测试对象：IndustryChainSnapshotBuilder.build 产出的 snapshots 与 lineage_envelopes
    目的/目标：R3-B6-021-O-02 — 同输入两次 build 全字段一致（lineage 除 generated_at）
    验证点：两次 _build() 的 IndustryChainDailySnapshotRow 全等；lineage 约定字段全等
    失败含义：同输入 row/lineage 漂移，增量重建与审计对账不可复现
    """
    result1 = _build()
    result2 = _build()

    snaps1 = sorted(result1.snapshots, key=lambda s: s.anchor_id)
    snaps2 = sorted(result2.snapshots, key=lambda s: s.anchor_id)
    assert snaps1 == snaps2

    lin1 = sorted(result1.lineage_envelopes, key=lambda e: e.snapshot_id)
    lin2 = sorted(result2.lineage_envelopes, key=lambda e: e.snapshot_id)
    assert len(lin1) == len(lin2)
    lineage_compare_fields = (
        "snapshot_id",
        "snapshot_type",
        "layer_id",
        "as_of_timestamp",
        "input_data_window_start",
        "input_data_window_end",
        "source_dataset_ids",
        "source_fetch_ids",
        "source_content_hashes",
        "rule_version",
        "code_version",
        "parameter_hash",
        "resource_profile",
        "upstream_snapshot_ids",
        "is_incremental",
        "rebuild_reason",
    )
    for env1, env2 in zip(lin1, lin2, strict=True):
        for field in lineage_compare_fields:
            assert getattr(env1, field) == getattr(env2, field), field


def test_layer3Snapshot_nonNumericVolume_rejects(tmp_path: Path) -> None:
    """覆盖范围：bar volume 非数值时的拒绝（主会话对抗复核 / OOF-7 对称）
    测试对象：_parse_bar_numeric 经 build 集成路径
    目的/目标：非数值 volume 须抛 Layer3SnapshotError，不泄漏 ValueError
    验证点：volume=not-a-number → Layer3SnapshotError 含 numeric
    失败含义：close 已 fail-closed 而 volume 仍 ValueError，信任边界不一致
    """
    bundle = _mutate_l5_manifest(
        tmp_path,
        lambda m: m["anchors"]["MSFT"]["bars"][0].update({"volume": "not-a-number"}),
    )
    with pytest.raises(Layer3SnapshotError, match="numeric"):
        _build(l5_bundle_dir=bundle)


def test_layer3Snapshot_missingInstrumentId_rejects(tmp_path: Path) -> None:
    """覆盖范围：L5 anchor 配置缺 instrument_id（主会话对抗复核）
    测试对象：IndustryChainSnapshotBuilder.build 的 mapping view 路径
    目的/目标：缺 instrument_id 须抛 Layer3SnapshotError，不泄漏 KeyError
    验证点：删 MSFT instrument_id → Layer3SnapshotError 含 instrument_id
    失败含义：KeyError 逃出信任边界，CLI 无法统一捕获畸形 manifest
    """
    bundle = _mutate_l5_manifest(
        tmp_path, lambda m: m["anchors"]["MSFT"].pop("instrument_id")
    )
    with pytest.raises(Layer3SnapshotError, match="instrument_id"):
        _build(l5_bundle_dir=bundle)


def test_layer3Snapshot_nonNumericClose_rejects(tmp_path: Path) -> None:
    """覆盖范围：bar close 非数值时的拒绝（OOF-7）
    测试对象：_parse_bar_numeric 经 build 集成路径
    目的/目标：非数值 close 须抛 Layer3SnapshotError，不泄漏 ValueError
    验证点：close=not-a-number → Layer3SnapshotError 含 numeric
    失败含义：ValueError 逃出信任边界，ops 侧无法统一捕获
    """
    bundle = _mutate_l5_manifest(
        tmp_path,
        lambda m: m["anchors"]["MSFT"]["bars"][0].update({"close": "not-a-number"}),
    )
    with pytest.raises(Layer3SnapshotError, match="numeric"):
        _build(l5_bundle_dir=bundle)


def test_layer3Snapshot_l5BundleOutsideProjectRoot_rejects(tmp_path: Path) -> None:
    """覆盖范围：l5_bundle_dir 须在 PROJECT_ROOT 下（UF-1）
    测试对象：IndustryChainSnapshotBuilder.build 的 _resolve_l5_bundle_root
    目的/目标：阻止任意路径读 manifest，对齐 staged 本地信任边界
    验证点：tmp_path（项目外）作 l5_bundle_dir → Layer3SnapshotError 含 project root
    失败含义：任意可读目录可作 L5 来源，未来 CLI 切片无路径白名单
    """
    outside = tmp_path / "outside_l5"
    shutil.copytree(_FIXTURE_L5, outside)
    with pytest.raises(Layer3SnapshotError, match="project root"):
        _build(l5_bundle_dir=outside)
