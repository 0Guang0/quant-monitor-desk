"""R3-DCP-10 S01 — fetch bundle → Layer5 SourceProvenance 映射桥。"""

from __future__ import annotations

from datetime import date

import pytest

from backend.app.config import PROJECT_ROOT
from backend.app.datasources.normalizers.cn_market import read_cn_market_evidence_bundle
from backend.app.datasources.normalizers.cn_market import CN_MARKET_EVIDENCE_SCHEMA_VERSION
from backend.app.datasources.normalizers.evidence_bundle import bundle_layer5_provenance, finalize_bundle
from backend.app.layer5_evidence.foundation import EvidenceFoundationValidator
from backend.app.layer5_evidence.models import (
    EvidenceFoundationRecord,
    EvidenceKind,
    InstrumentEvidenceRef,
    ManualReviewState,
    SourceProvenance,
)
from backend.app.layer5_evidence.provenance import build_source_provenance_from_bundle

MOOTDX_REPLAY = PROJECT_ROOT / "tests/fixtures/replay/cn_market/tdx/mootdx_daily_replay.json"

INSTRUMENT_REF = InstrumentEvidenceRef(
    instrument_id="sh.600519",
    symbol="600519",
    asset_type="equity",
    market_id="CN",
    exchange="SSE",
    currency="CNY",
    is_active=True,
)


def test_layer5Provenance_finalizeBundle_mapsAdr031Fields() -> None:
    """覆盖范围：ADR-031 P0 bundle → SourceProvenance 字段映射
    测试对象：build_source_provenance_from_bundle
    目的/目标：replay finalize bundle 的三件套与 dataset ids 可按 ADR-031 表断言
    验证点：fetch_id、content_hash、schema/domain/clean dataset id 与 bundle 一致
    失败含义：Layer5 无法绑真源 fetch bundle，G5 子集无法关账
    """
    bundle = read_cn_market_evidence_bundle(MOOTDX_REPLAY)
    bundle = finalize_bundle(bundle)
    provenance = build_source_provenance_from_bundle(bundle)

    assert provenance.source_fetch_ids == (bundle["source_fetch_id"],)
    assert provenance.source_content_hashes == (bundle["content_hash"],)
    schema_version = bundle["schema_version"]
    schema_hash = bundle["schema_hash"]
    assert f"schema:{schema_hash}@{schema_version}" in provenance.source_dataset_ids
    assert f"version:{schema_version}" in provenance.source_dataset_ids
    assert f"clean:security_bar_1d@{bundle['source_id']}" in provenance.source_dataset_ids
    assert f"domain:{bundle['data_domain']}" in provenance.source_dataset_ids


def test_layer5Provenance_finalizeBundle_passesFoundationValidator() -> None:
    """覆盖范围：映射后的 provenance 可通过 foundation 校验
    测试对象：build_source_provenance_from_bundle + EvidenceFoundationValidator
    目的/目标：真实 bundle 映射不得使用 staged 占位符且满足事实类追溯要求
    验证点：fetch_id ≠ fetch-staged-001；validate_record 无异常
    失败含义：映射结果不能作为 factual_source 入库
    """
    bundle = finalize_bundle(read_cn_market_evidence_bundle(MOOTDX_REPLAY))
    provenance = build_source_provenance_from_bundle(bundle)
    assert provenance.source_fetch_ids[0] != "fetch-staged-001"

    record = EvidenceFoundationRecord(
        evidence_id="EV-DCP10-PROV-001",
        target_id="sh.600519",
        target_type="instrument",
        trade_date=date(2024, 6, 25),
        evidence_kind=EvidenceKind.FACTUAL_SOURCE,
        evidence_summary="mootdx bar replay provenance bridge",
        need_human_review=False,
        manual_review_state=ManualReviewState.NOT_REQUIRED,
        created_by="layer5_provenance_bridge",
        instrument_ref=INSTRUMENT_REF,
        provenance=provenance,
    )
    EvidenceFoundationValidator().validate_record(record)


def test_layer5Provenance_missingContentHash_raises() -> None:
    """覆盖范围：缺 content_hash 的 bundle fail-closed
    测试对象：build_source_provenance_from_bundle
    目的/目标：无 content_hash 不得构造可追溯 provenance（对齐 reference-adoption §2.2）
    验证点：空 content_hash → ValueError
    失败含义：无内容指纹的 bundle 可冒充 Layer5 事实证据
    """
    bundle = finalize_bundle(
        {
            "schema_version": CN_MARKET_EVIDENCE_SCHEMA_VERSION,
            "source_id": "mootdx",
            "data_domain": "cn_equity_daily_bar",
            "source_fetch_id": "fetch-test-001",
            "content_hash": "",
        }
    )
    bundle["content_hash"] = ""
    with pytest.raises(ValueError, match="content_hash"):
        build_source_provenance_from_bundle(bundle)


def test_layer5Provenance_missingSchemaVersion_skipsMacroSchemaId() -> None:
    """覆盖范围：未 finalize 的 bundle 缺 schema_version 时不误标 macro schema
    测试对象：bundle_layer5_provenance
    目的/目标：缺 schema_version 不得默认 official_macro_evidence_v1 写入 source_dataset_ids
    验证点：无 schema:/version: 条目；clean/domain 仍可用
    失败含义：跨域 bundle 被误标为 macro schema，Layer5 追溯错位
    """
    fields = bundle_layer5_provenance(
        {
            "source_fetch_id": "fetch-test-002",
            "content_hash": "deadbeef",
            "source_id": "mootdx",
            "data_domain": "cn_equity_daily_bar",
        }
    )
    assert not any(item.startswith("schema:") for item in fields["source_dataset_ids"])
    assert not any(item.startswith("version:") for item in fields["source_dataset_ids"])
    assert "clean:security_bar_1d@mootdx" in fields["source_dataset_ids"]
    assert "domain:cn_equity_daily_bar" in fields["source_dataset_ids"]


def test_layer5Provenance_missingFetchId_raises() -> None:
    """覆盖范围：缺 source_fetch_id 的 bundle fail-closed
    测试对象：build_source_provenance_from_bundle
    目的/目标：无 fetch_id 不得构造可追溯 provenance（对齐 digital-oracle hash 纪律）
    验证点：空 fetch_id → ValueError
    失败含义：无来源指纹的 bundle 可冒充 Layer5 事实证据
    """
    bundle = finalize_bundle(
        {
            "schema_version": CN_MARKET_EVIDENCE_SCHEMA_VERSION,
            "source_id": "mootdx",
            "data_domain": "cn_equity_daily_bar",
            "source_fetch_id": "",
            "content_hash": "deadbeef",
        }
    )
    with pytest.raises(ValueError, match="source_fetch_id"):
        build_source_provenance_from_bundle(bundle)
