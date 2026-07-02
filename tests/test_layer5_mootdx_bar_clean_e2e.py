"""R3-DCP-10 S02 — mootdx incremental → security_bar_1d → Layer5 provenance e2e。"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from backend.app.layer5_evidence.foundation import EvidenceFoundationValidator
from backend.app.layer5_evidence.lineage import Layer5LineageBuilder
from backend.app.layer5_evidence.models import (
    EvidenceFoundationRecord,
    EvidenceKind,
    InstrumentEvidenceRef,
    ManualReviewState,
)
from backend.app.layer5_evidence.provenance import build_source_provenance_from_bundle

from tests.incremental_mootdx_support import (
    FIXTURE_DATE,
    SYMBOL,
    fetch_security_bar_row,
    load_mootdx_raw_bundle_from_fetch_log,
    run_mootdx_replay_incremental,
)


def _assert_adr031_dataset_ids(provenance, bundle: dict) -> None:
    schema_version = bundle["schema_version"]
    schema_hash = bundle["schema_hash"]
    assert f"schema:{schema_hash}@{schema_version}" in provenance.source_dataset_ids
    assert f"version:{schema_version}" in provenance.source_dataset_ids
    assert f"clean:security_bar_1d@{bundle['source_id']}" in provenance.source_dataset_ids
    assert f"domain:{bundle['data_domain']}" in provenance.source_dataset_ids


def test_mootdxBarClean_layer5Provenance_matchesSameRunBundle(
    tmp_path: Path, monkeypatch
) -> None:
    """覆盖范围：mootdx replay 增量写 clean 后 Layer5 provenance 与同 run raw bundle 一致
    测试对象：run_incremental + build_source_provenance_from_bundle + Layer5LineageBuilder
    目的/目标：P0 竖切 sh.600519 事实证据绑真源，非 staged 占位
    验证点：clean 行存在；provenance 三字段与 bundle 映射一致；lineage 对齐
    失败含义：Wave 4 G5 无法证明 fetch→clean→Layer5 绑真源
    """
    job_id = "job-dcp10-layer5-e2e"
    cm, _data_root, result = run_mootdx_replay_incremental(
        tmp_path, monkeypatch, job_id=job_id
    )
    assert result.status == "COMPLETED"

    as_of = FIXTURE_DATE.isoformat()
    with cm.reader() as con:
        row = fetch_security_bar_row(con, as_of)
        bundle = load_mootdx_raw_bundle_from_fetch_log(con, job_id)
    assert row is not None
    assert row[2] == "mootdx"

    provenance = build_source_provenance_from_bundle(bundle)
    assert provenance.source_fetch_ids[0] != "fetch-staged-001"
    assert provenance.source_fetch_ids == (bundle["source_fetch_id"],)
    assert provenance.source_content_hashes == (bundle["content_hash"],)
    _assert_adr031_dataset_ids(provenance, bundle)

    instrument_ref = InstrumentEvidenceRef(
        instrument_id=SYMBOL,
        symbol="600519",
        asset_type="equity",
        market_id="CN",
        exchange="SSE",
        currency="CNY",
        is_active=True,
    )
    record = EvidenceFoundationRecord(
        evidence_id="EV-DCP10-MOOTDX-E2E",
        target_id=SYMBOL,
        target_type="instrument",
        trade_date=FIXTURE_DATE,
        evidence_kind=EvidenceKind.FACTUAL_SOURCE,
        evidence_summary=f"close={row[1]} source=mootdx security_bar_1d",
        need_human_review=False,
        manual_review_state=ManualReviewState.NOT_REQUIRED,
        created_by="layer5_mootdx_bar_clean_e2e",
        instrument_ref=instrument_ref,
        provenance=provenance,
    )
    EvidenceFoundationValidator().validate_record(record)

    as_of_dt = datetime(2024, 6, 25, 15, 0, tzinfo=UTC)
    window_start = datetime(2024, 6, 25, 0, 0, tzinfo=UTC)
    envelope = Layer5LineageBuilder().build(
        snapshot_id="snap-dcp10-mootdx-bar",
        snapshot_type="layer5_foundation",
        as_of=as_of_dt,
        input_window_start=window_start,
        input_window_end=as_of_dt,
        provenance=provenance,
        rule_version="layer5-foundation-v1",
        parameter_hash=Layer5LineageBuilder.parameter_hash_for(
            rule_version="layer5-foundation-v1",
            inputs=(SYMBOL, FIXTURE_DATE.isoformat()),
        ),
        is_incremental=True,
    )
    assert envelope.source_fetch_ids == provenance.source_fetch_ids
    assert envelope.source_content_hashes == provenance.source_content_hashes
    assert envelope.source_dataset_ids == provenance.source_dataset_ids
