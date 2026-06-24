"""第五层完整证据链 staged 测试（Round 3 Batch 5B / 023b Execute）。"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
from backend.app.layer5_evidence.evidence_chain import (
    EvidenceChainBuilder,
    EvidenceChainError,
    reject_agent_text_as_fact,
)
from backend.app.layer5_evidence.evidence_validator import (
    EvidenceValidationError,
    StagedEvidenceValidator,
)
from backend.app.layer5_evidence.foundation import EvidenceFoundationError
from backend.app.layer5_evidence.instrument_registry import (
    InstrumentRegistryError,
    InstrumentRegistryValidator,
)
from backend.app.layer5_evidence.models import (
    EvidenceFoundationRecord,
    EvidenceKind,
    InstrumentEvidenceRef,
    LayerContextBundle,
    ManualReviewState,
    SecurityBarDaily,
    SourceProvenance,
)
from backend.app.layer5_evidence.ports import EvidenceReadPort

_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "layer5_staged_evidence"
_MINIMAL_BUNDLE = json.loads((_FIXTURES / "minimal_bundle.json").read_text(encoding="utf-8"))

_REGISTRY_ROW = InstrumentEvidenceRef(
    instrument_id="L5-000001.SZ",
    symbol="000001.SZ",
    asset_type="equity",
    market_id="CN_A",
    exchange="SZSE",
    currency="CNY",
    is_active=True,
)

_STAGED_PROVENANCE = SourceProvenance(
    source_fetch_ids=("fetch-staged-001",),
    source_content_hashes=("sha256:abc123",),
    source_dataset_ids=("staged_fixture:security_bar_daily",),
)

_LAYER_CONTEXT = LayerContextBundle(
    layer3_context='{"anchor_id":"ANCHOR-CU"}',
    layer4_context='{"market_id":"CN_A"}',
    upstream_snapshot_ids=("L3-SNAPSHOT-001", "L4-SNAPSHOT-001"),
)


def _factual_record(**overrides) -> EvidenceFoundationRecord:
    base = dict(
        evidence_id="EV-023B-001",
        target_id="L5-000001.SZ",
        target_type="instrument",
        trade_date=date(2026, 6, 15),
        evidence_kind=EvidenceKind.FACTUAL_SOURCE,
        evidence_summary="close=12.34 volume=1.2e6 source=staged_fixture",
        need_human_review=False,
        manual_review_state=ManualReviewState.NOT_REQUIRED,
        created_by="layer5_evidence_chain",
        provenance=_STAGED_PROVENANCE,
    )
    base.update(overrides)
    return EvidenceFoundationRecord(**base)


def test_instrumentRegistry_uniqueIds() -> None:
    """覆盖范围：instrument_registry staged 行唯一性
    测试对象：InstrumentRegistryValidator.validate_bundle
    目的/目标：instrument_id 在 staged bundle 内唯一；重复 id 应拒收
    验证点：两笔相同 instrument_id → InstrumentRegistryError 且匹配 duplicate instrument_id
    失败含义：重复标的可进入证据链，下游 snapshot 关联歧义
    """
    validator = InstrumentRegistryValidator()
    duplicate = InstrumentEvidenceRef(
        instrument_id="L5-000001.SZ",
        symbol="000001.SZ",
        asset_type="equity",
        market_id="CN_A",
        exchange="SZSE",
        currency="CNY",
        is_active=False,
    )
    validator.validate_bundle([_REGISTRY_ROW])
    with pytest.raises(InstrumentRegistryError, match="duplicate instrument_id"):
        validator.validate_bundle([_REGISTRY_ROW, duplicate])


def test_securityBar_rejectsFutureTradeDate() -> None:
    """覆盖范围：security_bar_daily no-future-data 边界
    测试对象：StagedEvidenceValidator.validate_bar
    目的/目标：trade_date 不得晚于 as_of 窗口上界
    验证点：未来 trade_date 行 → 校验拒绝
    失败含义：未来行情可进入 staged 证据，破坏 as_of 语义
    """
    validator = StagedEvidenceValidator()
    bar = SecurityBarDaily(
        instrument_id="L5-000001.SZ",
        trade_date=date(2026, 6, 20),
        open=1.0,
        high=2.0,
        low=1.0,
        close=2.0,
        volume=100.0,
        amount=200.0,
        source="staged_fixture",
        quality_flag="STAGED",
    )
    with pytest.raises(EvidenceValidationError, match="future trade_date"):
        validator.validate_bar(bar, as_of_end=date(2026, 6, 15))


def test_evidenceChain_rejectsEmptyUpstreamContext() -> None:
    """覆盖范围：空 upstream / 空 layer context 边界
    测试对象：EvidenceChainBuilder.build
    目的/目标：证据链须绑定非空 L3/L4 upstream 与 context 槽
    验证点：空 upstream_snapshot_ids 或空 layer3/4 context → EvidenceChainError
    失败含义：无上游快照的链可构建，审计追溯断链
    """
    builder = EvidenceChainBuilder()
    record = _factual_record()
    with pytest.raises(EvidenceChainError, match="upstream_snapshot_ids required"):
        builder.build(
            record=record,
            layer_context=LayerContextBundle(
                layer3_context='{"anchor_id":"ANCHOR-CU"}',
                layer4_context='{"market_id":"CN_A"}',
                upstream_snapshot_ids=(),
            ),
        )
    with pytest.raises(EvidenceChainError, match="layer3_context and layer4_context are required"):
        builder.build(
            record=record,
            layer_context=LayerContextBundle(
                layer3_context="",
                layer4_context='{"market_id":"CN_A"}',
                upstream_snapshot_ids=("L3-SNAPSHOT-001",),
            ),
        )


def test_evidenceChain_traceUpstreamSnapshots() -> None:
    """覆盖范围：EvidenceChainBuilder 上游 snapshot 追溯
    测试对象：EvidenceChainBuilder.build
    目的/目标：chain 须保留 L3/L4 upstream_snapshot_ids 与 layer context 槽
    验证点：构建结果含非空 upstream ids 与 layer3/layer4 context
    失败含义：证据链无法关联 Layer3/4 快照，审计断链
    """
    builder = EvidenceChainBuilder()
    chain = builder.build(record=_factual_record(), layer_context=_LAYER_CONTEXT)
    assert chain.upstream_snapshot_ids == ("L3-SNAPSHOT-001", "L4-SNAPSHOT-001")
    assert "ANCHOR-CU" in chain.layer3_context
    assert "CN_A" in chain.layer4_context


def test_evidenceChain_rejectsAgentTextAsFact() -> None:
    """覆盖范围：Agent 文本不得作事实证据源
    测试对象：EvidenceChainBuilder + EvidenceFoundationValidator 复用
    目的/目标：Agent 生成摘要不能进入事实证据链
    验证点：agent 标记文本作事实源 → 构建/校验拒绝
    失败含义：代理解释可伪装为行情事实，违反 AC-023-3
    """
    builder = EvidenceChainBuilder()
    agent_record = _factual_record(
        evidence_summary="Agent summary: 建议买入",
        created_by="agent_interpreter",
    )
    with pytest.raises(EvidenceFoundationError, match="agent"):
        builder.build(record=agent_record, layer_context=_LAYER_CONTEXT)

    with pytest.raises(EvidenceFoundationError, match="agent"):
        reject_agent_text_as_fact(text="agent_summary bullish", created_by="layer5_evidence_chain")


def test_evidenceChain_severeConflictQueuesManualReview() -> None:
    """覆盖范围：severe reconcile failed → manual review queued
    测试对象：冲突策略与 EvidenceChainBuilder
    目的/目标：severe 冲突标记须将 manual_review_state 置为 queued
    验证点：severe conflict 输入 → queued；无 flag 的 queued → 拒绝
    失败含义：严重冲突不进入人工复核队列，数据质量风险外泄
    """
    builder = EvidenceChainBuilder()
    chain = builder.build(
        record=_factual_record(),
        layer_context=_LAYER_CONTEXT,
        conflict_severity="severe",
    )
    assert chain.need_human_review is True
    assert chain.manual_review_state == ManualReviewState.QUEUED

    with pytest.raises(EvidenceFoundationError, match="manual_review_state=queued requires"):
        builder.build(
            record=_factual_record(
                need_human_review=False,
                manual_review_state=ManualReviewState.QUEUED,
            ),
            layer_context=_LAYER_CONTEXT,
        )


class _FakeEvidenceReadPort:
    """ponytail: minimal in-test fake; no storage import."""

    def __init__(self, bundle: dict) -> None:
        self._bundle = bundle

    def load_staged_bundle(self, instrument_id: str) -> dict:
        if instrument_id != self._bundle["instrument_id"]:
            raise KeyError(instrument_id)
        return self._bundle


def test_evidenceReadPort_boundary() -> None:
    """覆盖范围：EvidenceReadPort 注入边界
    测试对象：EvidenceReadPort fake 实现
    目的/目标：builder 通过 port 读 staged bundle，不直接 import storage
    验证点：fake port 返回 staged dict 可驱动构建；无 port 硬依赖 storage 类
    失败含义：证据链与具体存储实现耦合，无法 staged 单测
    """
    port: EvidenceReadPort = _FakeEvidenceReadPort(_MINIMAL_BUNDLE)
    builder = EvidenceChainBuilder(read_port=port)
    chain = builder.build_from_port("L5-000001.SZ")
    assert chain.evidence_id == "EV-023B-001"
    assert chain.upstream_snapshot_ids

    with pytest.raises(EvidenceChainError, match="EvidenceReadPort required"):
        EvidenceChainBuilder().build_from_port("L5-000001.SZ")
