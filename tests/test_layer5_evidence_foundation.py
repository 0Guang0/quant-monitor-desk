"""第五层证据基础校验与血缘测试（Round 3 Batch 5A / 023A）。"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from backend.app.layer5_evidence.foundation import (
    EvidenceFoundationError,
    EvidenceFoundationValidator,
)
from backend.app.layer5_evidence.lineage import (
    LINEAGE_REQUIRED_FIELDS,
    Layer5LineageBuilder,
    Layer5LineageError,
)
from backend.app.layer5_evidence.models import (
    EvidenceFoundationRecord,
    EvidenceKind,
    InstrumentEvidenceRef,
    ManualReviewState,
    SourceProvenance,
)

TRADE_DATE = date(2026, 6, 15)
AS_OF = datetime(2026, 6, 15, 16, 0, tzinfo=UTC)
WINDOW_START = datetime(2026, 6, 15, 0, 0, tzinfo=UTC)
WINDOW_END = datetime(2026, 6, 15, 16, 0, tzinfo=UTC)

INSTRUMENT_REF = InstrumentEvidenceRef(
    instrument_id="L5-000001.SZ",
    symbol="000001.SZ",
    asset_type="equity",
    market_id="CN_A",
    exchange="SZSE",
    currency="CNY",
    is_active=True,
)

STAGED_PROVENANCE = SourceProvenance(
    source_fetch_ids=("fetch-staged-001",),
    source_content_hashes=("sha256:abc123",),
    source_dataset_ids=("staged_fixture:security_bar_daily",),
)


def _factual_record(**overrides) -> EvidenceFoundationRecord:
    base = dict(
        evidence_id="EV-023A-001",
        target_id="L5-000001.SZ",
        target_type="instrument",
        trade_date=TRADE_DATE,
        evidence_kind=EvidenceKind.FACTUAL_SOURCE,
        evidence_summary="close=12.34 volume=1.2e6 source=staged_fixture",
        need_human_review=False,
        manual_review_state=ManualReviewState.NOT_REQUIRED,
        created_by="layer5_foundation_validator",
        instrument_ref=INSTRUMENT_REF,
        provenance=STAGED_PROVENANCE,
    )
    base.update(overrides)
    return EvidenceFoundationRecord(**base)


def test_evidenceFoundation_factualRecord_requiresProvenance() -> None:
    """覆盖范围：事实类证据的来源追溯必填
    测试对象：EvidenceFoundationValidator.validate_record（FACTUAL_SOURCE）
    目的/目标：事实记录必须能追溯到至少一次抓取或内容指纹，空来源应拒收
    验证点：空 provenance → EvidenceFoundationError 且匹配 source_fetch_ids or source_content_hashes
    失败含义：无来源指纹的事实证据可入库，审计无法回溯原始抓取
    """
    validator = EvidenceFoundationValidator()
    empty_provenance = SourceProvenance(
        source_fetch_ids=(),
        source_content_hashes=(),
    )
    record = _factual_record(provenance=empty_provenance)
    with pytest.raises(EvidenceFoundationError, match="source_fetch_ids or source_content_hashes"):
        validator.validate_record(record)


def test_evidenceFoundation_recordKinds_areDistinct() -> None:
    """覆盖范围：证据种类与来源追溯的互斥规则
    测试对象：EvidenceFoundationValidator.validate_record（各 EvidenceKind）
    目的/目标：派生与校验类可无来源；代理解释类不得夹带事实来源指纹
    验证点：DERIVED/AGENT 合法路径通过；AGENT 携带事实 provenance → must not carry factual source provenance
    失败含义：证据种类边界模糊，代理解释可伪装成行情事实
    """
    validator = EvidenceFoundationValidator()
    derived = _factual_record(
        evidence_kind=EvidenceKind.DERIVED_VALIDATION,
        evidence_summary="validation_status=passed",
        created_by="data_quality_validator",
    )
    validator.validate_record(derived)

    agent = EvidenceFoundationRecord(
        evidence_id="EV-023A-AGENT-001",
        target_id="L5-000001.SZ",
        target_type="instrument",
        trade_date=TRADE_DATE,
        evidence_kind=EvidenceKind.AGENT_INTERPRETATION,
        evidence_summary="Agent narrative: macro backdrop is supportive (not a fact source).",
        need_human_review=False,
        manual_review_state=ManualReviewState.NOT_REQUIRED,
        created_by="agent_interpreter",
        instrument_ref=INSTRUMENT_REF,
        provenance=None,
    )
    validator.validate_record(agent)

    with pytest.raises(EvidenceFoundationError, match="must not carry factual source provenance"):
        validator.validate_record(
            _factual_record(
                evidence_kind=EvidenceKind.AGENT_INTERPRETATION,
                provenance=STAGED_PROVENANCE,
            )
        )


def test_evidenceFoundation_agentTextNotFactSource_rejectsFactualKind() -> None:
    """覆盖范围：代理生成文本不得标记为事实来源
    测试对象：EvidenceFoundationValidator.validate_record（代理痕迹检测）
    目的/目标：创建者、摘要或数据集标识中的代理痕迹不得进入事实类证据
    验证点：agent_summarizer / agent_summary 文案 / agent_summary 数据集均 → EvidenceFoundationError
    失败含义：大模型生成内容可冒充行情事实，下游模型误用
    """
    validator = EvidenceFoundationValidator()
    with pytest.raises(EvidenceFoundationError, match="agent-created prose"):
        validator.validate_record(_factual_record(created_by="agent_summarizer"))

    with pytest.raises(EvidenceFoundationError, match="agent-generated text markers"):
        validator.validate_record(
            _factual_record(evidence_summary="agent_summary: strong buy signal on volume")
        )

    with pytest.raises(EvidenceFoundationError, match="agent outputs must not appear"):
        validator.validate_record(
            _factual_record(
                provenance=SourceProvenance(
                    source_fetch_ids=("fetch-staged-001",),
                    source_content_hashes=("sha256:abc123",),
                    source_dataset_ids=("agent_summary:layer5",),
                )
            )
        )


def test_evidenceFoundation_manualReviewFlag_requiresQueuedState() -> None:
    """覆盖范围：人工复核标记与队列状态一致性
    测试对象：EvidenceFoundationValidator.validate_record（need_human_review）
    目的/目标：标记需人工复核时，队列状态必须同步为已入队，否则运维无法发现待审项
    验证点：需复核但状态为未要求 → 报错；需复核且状态为已入队的派生记录可通过
    失败含义：需人工处理的数据无队列状态，待审项会被静默忽略
    """
    validator = EvidenceFoundationValidator()
    with pytest.raises(EvidenceFoundationError, match="manual_review_state=queued"):
        validator.validate_record(
            _factual_record(
                need_human_review=True,
                manual_review_state=ManualReviewState.NOT_REQUIRED,
            )
        )

    queued = _factual_record(
        need_human_review=True,
        manual_review_state=ManualReviewState.QUEUED,
        evidence_kind=EvidenceKind.DERIVED_VALIDATION,
        evidence_summary="reconcile_failed: source conflict",
        created_by="source_conflict_validator",
    )
    validator.validate_record(queued)


def test_evidenceFoundation_identityHash_isDeterministic() -> None:
    """覆盖范围：证据记录身份哈希稳定性
    测试对象：EvidenceFoundationValidator.build_identity_hash
    目的/目标：同一记录多次哈希应完全一致，用于去重与幂等写入
    验证点：两次 build_identity_hash 结果相等
    失败含义：身份哈希漂移导致重复证据或更新误判
    """
    validator = EvidenceFoundationValidator()
    record = _factual_record()
    assert validator.build_identity_hash(record) == validator.build_identity_hash(record)


def test_layer5Lineage_envelopeMatchesSnapshotContractFields() -> None:
    """覆盖范围：第五层血缘信封与快照契约字段
    测试对象：Layer5LineageBuilder.build
    目的/目标：产出血缘须含全部必填字段且标明第五层；代理数据集标识应拒收
    验证点：envelope.layer_id=layer5；必填字段非空；agent_summary 数据集 → Layer5LineageError
    失败含义：第五层血缘不合规仍可构建，持久化与跨层追溯失败
    """
    builder = Layer5LineageBuilder()
    envelope = builder.build(
        snapshot_id="L5-SNAP-001",
        snapshot_type="evidence_foundation_snapshot",
        as_of=AS_OF,
        input_window_start=WINDOW_START,
        input_window_end=WINDOW_END,
        provenance=STAGED_PROVENANCE,
        rule_version="layer5-foundation-v1",
        parameter_hash=builder.parameter_hash_for(
            rule_version="layer5-foundation-v1",
            inputs=("L5-000001.SZ", TRADE_DATE.isoformat()),
        ),
        upstream_snapshot_ids=("L2-SNAP-001",),
    )
    assert envelope.layer_id == "layer5"
    for field in LINEAGE_REQUIRED_FIELDS:
        if field == "rebuild_reason":
            continue
        assert getattr(envelope, field) is not None

    with pytest.raises(Layer5LineageError, match="agent outputs must not appear"):
        builder.build(
            snapshot_id="L5-SNAP-BAD",
            snapshot_type="evidence_foundation_snapshot",
            as_of=AS_OF,
            input_window_start=WINDOW_START,
            input_window_end=WINDOW_END,
            provenance=SourceProvenance(
                source_fetch_ids=("fetch-staged-001",),
                source_content_hashes=("sha256:abc123",),
                source_dataset_ids=("agent_summary:bad",),
            ),
            rule_version="layer5-foundation-v1",
            parameter_hash="deadbeef",
        )
