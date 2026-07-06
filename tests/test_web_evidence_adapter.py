"""R3H-04 网页证据适配器测试（Batch 3H）。

覆盖范围：web_search 的 fetch port、manual_review staging、证据契约与 Layer smoke。
测试对象：backend/app/evidence/manual_review_staging.py 及 web_search_evidence_port 模块。
目的/目标：证明 web_search 仅走 manual-review staging，need_human_review=true 且不得写 clean 表。
验证点：test_web_evidence_adapter 全量及 -k layer 子集通过当前 pytest 验收。
失败含义：Batch 3H R3H-04 无法在 Round4 前闭合网页证据源生产入口决策。
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from backend.app.config import PROJECT_ROOT
from tests.service_path_support import enable_source_route

_WEB_REPLAY = PROJECT_ROOT / "tests/fixtures/replay/web_evidence/supplemental_query_replay.json"
_WEB_ADVERSARIAL = (
    PROJECT_ROOT / "tests/fixtures/replay/web_evidence/adversarial_no_manual_review.json"
)


def test_bootSkeleton_testModuleLoads() -> None:
    """覆盖范围：Execute 9.0 网页证据测试模块骨架是否可加载
    测试对象：tests/test_web_evidence_adapter.py 模块本身
    目的/目标：确认 R3H-04 web 测试文件已登记且 pytest 可收集
    验证点：模块 docstring 声明 web_search 覆盖范围
    失败含义：Execute 无法在本模块追加网页证据适配器回归用例
    """
    import tests.test_web_evidence_adapter as mod

    assert "web_search" in (mod.__doc__ or "")


def test_bootSkeleton_manualReviewStagingModuleExists() -> None:
    """覆盖范围：Execute 9.0 manual_review_staging 模块可导入
    测试对象：backend.app.evidence.manual_review_staging
    目的/目标：确认 R3H-04 web evidence staging SSOT 已落地
    验证点：WEB_EVIDENCE_STAGING_SCHEMA_VERSION 非空
    失败含义：manual_review_staging 缺失，web_search 无 staging 路径
    """
    from backend.app.evidence import manual_review_staging as mod

    assert mod.WEB_EVIDENCE_STAGING_SCHEMA_VERSION == "web_evidence_staging_v1"


def test_web_search_port_mockFetch_emitsStagingBundleWithManualReview() -> None:
    """覆盖范围：mock web_search port 默认 stub 抓取
    测试对象：create_web_search_evidence_fetch_port + fetch_payload
    目的/目标：port 产出 web_evidence_staging_v1 且 need_human_review=true
    验证点：schema_version、need_human_review、manual_review_state=queued
    失败含义：web_search 无 mock stub 或缺 manual-review 标记
    """
    from backend.app.datasources.fetch_ports.web_search_evidence_port import (
        create_web_search_evidence_fetch_port,
    )
    from backend.app.datasources.fetch_result import FetchRequest
    from backend.app.evidence.manual_review_staging import WEB_EVIDENCE_STAGING_SCHEMA_VERSION

    port = create_web_search_evidence_fetch_port(
        queries=("fed rate cut outlook 2024",), max_results=1
    )
    req = FetchRequest(
        run_id="r3h04-web",
        source_id="web_search",
        data_domain="supplemental_web_evidence",
        instrument_id="fed rate cut outlook 2024",
    )
    payload = port.fetch_payload(req)
    body = json.loads(payload.content.decode("utf-8"))
    assert body["schema_version"] == WEB_EVIDENCE_STAGING_SCHEMA_VERSION
    assert body["need_human_review"] is True
    assert body["manual_review_state"] == "queued"
    assert body["results"]
    assert body["source_fetch_id"]
    assert body["content_hash"]


def test_web_search_staging_roundTrip_fixturePreservesManualReviewFields(tmp_path: Path) -> None:
    """覆盖范围：web evidence staging read/write 往返
    测试对象：write_web_evidence_staging_bundle + read_web_evidence_staging_bundle
    目的/目标：replay fixture 经 staging normalizer 无损读写
    验证点：need_human_review、manual_review_state、query、results 保留
    失败含义：web_evidence_staging_v1 无法贯通 replay 链
    """
    from backend.app.evidence.manual_review_staging import (
        WEB_EVIDENCE_STAGING_SCHEMA_VERSION,
        read_web_evidence_staging_bundle,
        write_web_evidence_staging_bundle,
    )

    legacy = json.loads(_WEB_REPLAY.read_text(encoding="utf-8"))
    out = tmp_path / "roundtrip"
    write_web_evidence_staging_bundle(out, legacy)
    bundle = read_web_evidence_staging_bundle(out)
    assert bundle["schema_version"] == WEB_EVIDENCE_STAGING_SCHEMA_VERSION
    assert bundle["need_human_review"] is True
    assert bundle["manual_review_state"] == "queued"
    assert bundle["query"] == "fed rate cut outlook 2024"


def test_web_search_staging_stageForManualReview_neverPermitsCleanWrite() -> None:
    """覆盖范围：stage_for_manual_review 输出 staging 元数据
    测试对象：stage_for_manual_review + reject_clean_table_promotion
    目的/目标：staging 路径 clean_write_permitted=false；promote 硬拒绝
    验证点：staging.clean_write_permitted is False；reject_clean_table_promotion raises
    失败含义：web 证据可 silent promote 到 clean 表
    """
    from backend.app.evidence.manual_review_staging import (
        ManualReviewStagingError,
        read_web_evidence_staging_bundle,
        reject_clean_table_promotion,
        stage_for_manual_review,
    )

    bundle = read_web_evidence_staging_bundle(_WEB_REPLAY)
    staging = stage_for_manual_review(bundle)
    assert staging["clean_write_permitted"] is False
    assert staging["need_human_review"] is True
    with pytest.raises(ManualReviewStagingError, match="cannot promote"):
        reject_clean_table_promotion(target_table="security_bar_daily")


def test_web_search_staging_openbbWidgetArtifactShape_boundedTableFields() -> None:
    """覆盖范围：manual_review_staging OpenBB widget artifact 字段形状
    测试对象：build_web_evidence_staging_bundle.evidence_artifact
    目的/目标：architecture_only 对齐 agents-for-openbb item.content + bounded table 元数据
    验证点：artifact_kind、items[].content、columns、rows、widget_metadata.name/widget_id
    失败含义：证据摘要未与 OpenBB widget JSON 形状对齐，采纳 guardrails 不合规
    """
    from backend.app.evidence.manual_review_staging import (
        OPENBB_WIDGET_ARTIFACT_KIND,
        build_web_evidence_staging_bundle,
    )

    bundle = build_web_evidence_staging_bundle(
        query="fed rate cut outlook 2024",
        results=[
            {
                "title": "Fed outlook",
                "url": "https://example.com/1",
                "snippet": "Supplemental context for manual review.",
            }
        ],
        data_domain="supplemental_web_evidence",
        source_fetch_id="web-shape-test",
        content_hash="web-shape-hash",
        as_of_timestamp="2024-06-25T00:00:00Z",
    )
    artifact = bundle["evidence_artifact"]
    assert artifact["artifact_kind"] == OPENBB_WIDGET_ARTIFACT_KIND
    assert artifact["source_data_separated"] is True
    assert artifact["items"][0]["content"]
    assert artifact["columns"] == ["title", "url", "snippet"]
    assert len(artifact["rows"]) == 1
    meta = artifact["widget_metadata"]
    assert meta["name"]
    assert meta["widget_id"].startswith("web-evidence-")


def test_web_search_port_capOverflow_blocksOverMaxResults() -> None:
    """覆盖范围：web_search port 结果数 cap 溢出
    测试对象：WebSearchEvidenceMockFetchPort max_results 超上限
    目的/目标：max_results 超 MAX_RESULTS 时构造即 PortError
    验证点：max_results 超 cap 时 PortError
    失败含义：web 搜索可无界拉取结果
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.web_search_evidence_port import (
        MAX_RESULTS,
        create_web_search_evidence_fetch_port,
    )

    with pytest.raises(PortError, match="cap"):
        create_web_search_evidence_fetch_port(
            queries=("fed rate cut outlook 2024",), max_results=MAX_RESULTS + 1
        )


def test_web_search_port_capOverflow_blocksOverMaxQueries() -> None:
    """覆盖范围：web_search port 查询数 cap 溢出
    测试对象：create_web_search_evidence_fetch_port queries 超上限
    目的/目标：max_queries 超 MAX_QUERIES 时构造即 PortError
    验证点：4 条 query 触发 PortError 且消息含上限数字
    失败含义：web 搜索可无界多查询
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.fetch_ports.web_search_evidence_port import (
        MAX_QUERIES,
        create_web_search_evidence_fetch_port,
    )

    with pytest.raises(PortError, match=str(MAX_QUERIES)):
        create_web_search_evidence_fetch_port(
            queries=tuple(f"query-{i}" for i in range(MAX_QUERIES + 1)),
            max_results=1,
        )


def test_web_search_port_route_validationOnlyPrimaryBlockedWhenEnabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：启用 web_search 后 yaml Primary 仍被 validation_only 阻断
    测试对象：SourceRoutePlanner + supplemental_web_evidence 域
    目的/目标：validation_only 源不得作 Primary；evidence 路径靠 port/staging 非 clean route
    验证点：route_status=VALIDATION_ONLY_BLOCKED；skip_reason=validation_only_cannot_be_primary
    失败含义：web_search 可 silent 升格 primary 并绕过 manual-review 语义
    """
    planner = enable_source_route(monkeypatch, source_id="web_search", data_domain="supplemental_web_evidence")
    plan = planner.plan(
        data_domain="supplemental_web_evidence",
        operation="fetch_supplemental_web_evidence",
        run_id="r3h04-web-route-valonly",
        job_id="web-route-valonly",
    )
    assert plan.route_status == "VALIDATION_ONLY_BLOCKED"
    candidate = next(c for c in plan.candidates if c.source_id == "web_search")
    assert candidate.skip_reason == "validation_only_cannot_be_primary"


def test_web_search_staging_adversarialFixture_canonicalizesManualReview() -> None:
    """覆盖范围：对抗 fixture 篡改 need_human_review 不可持久化
    测试对象：read_web_evidence_staging_bundle 读路径 canonicalize
    目的/目标：fixture 设 need_human_review=false 仍输出 true/queued
    验证点：read 后 need_human_review=true；manual_review_state=queued
    失败含义：staging 读路径可绕过 manual-review 语义
    """
    from backend.app.evidence.manual_review_staging import read_web_evidence_staging_bundle

    bundle = read_web_evidence_staging_bundle(_WEB_ADVERSARIAL)
    assert bundle["need_human_review"] is True
    assert bundle["manual_review_state"] == "queued"


def test_layer_smoke_webReplay_manualReviewFoundationBinding() -> None:
    """覆盖范围：web evidence replay → Layer5 manual_review 绑定
    测试对象：read_web_evidence_staging_bundle + EvidenceFoundationValidator
    目的/目标：need_human_review=true 须 paired manual_review_state=queued
    验证点：EvidenceFoundationRecord 校验通过；evidence_kind=DERIVED_VALIDATION
    失败含义：web 证据无法绑定 Layer5 manual-review 语义
    """
    from backend.app.evidence.manual_review_staging import read_web_evidence_staging_bundle
    from backend.app.layer5_evidence.foundation import EvidenceFoundationValidator
    from backend.app.layer5_evidence.models import (
        EvidenceFoundationRecord,
        EvidenceKind,
        ManualReviewState,
        SourceProvenance,
    )

    bundle = read_web_evidence_staging_bundle(_WEB_REPLAY)
    assert bundle["source_fetch_id"] == "web-search-replay-fed-outlook"
    assert bundle["content_hash"] == "web-search-replay-hash-fed-outlook"
    record = EvidenceFoundationRecord(
        evidence_id="r3h04-web-layer",
        target_id="fed-outlook",
        target_type="supplemental_web_evidence",
        trade_date=date(2024, 6, 25),
        evidence_kind=EvidenceKind.DERIVED_VALIDATION,
        evidence_summary=f"Web supplemental query: {bundle['query']}",
        need_human_review=True,
        manual_review_state=ManualReviewState.QUEUED,
        created_by="r3h04_layer_smoke",
        provenance=SourceProvenance(
            source_fetch_ids=(bundle["source_fetch_id"],),
            source_content_hashes=(bundle["content_hash"],),
        ),
    )
    EvidenceFoundationValidator().validate_record(record)
