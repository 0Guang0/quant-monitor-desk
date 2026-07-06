"""R3H-04 三源 clean-write 与事实 resolve 负例测试（Batch 3H）。

覆盖范围：kalshi、polymarket、web_search 不得写 clean 表、不得 resolve 事实结果。
测试对象：三源 route/bundle/staging 负例路径。
目的/目标：证明预测价格与网页证据无法升格为 factual clean table 或事件结果判定。
验证点：test_no_clean_write_for_web_evidence 及 -k resolve 子集通过当前 pytest 验收。
失败含义：非事实源可 silent 写入 clean 表或将概率当事实，Round4 入口不安全。
"""

from __future__ import annotations

import json

import pytest
import yaml

from backend.app.config import PROJECT_ROOT
from backend.app.datasources.normalizers.probability_signal import FORBIDDEN_RESOLUTION_FIELDS

_KALSHI_REPLAY = (
    PROJECT_ROOT / "tests/fixtures/replay/prediction_market/kalshi/probability_replay.json"
)
_POLYMARKET_REPLAY = (
    PROJECT_ROOT
    / "tests/fixtures/replay/prediction_market/polymarket/probability_replay.json"
)
_WEB_REPLAY = PROJECT_ROOT / "tests/fixtures/replay/web_evidence/supplemental_query_replay.json"

_FORBIDDEN_FIELDS = FORBIDDEN_RESOLUTION_FIELDS


def test_bootSkeleton_testModuleLoads() -> None:
    """覆盖范围：Execute 9.0 clean-write 负例测试模块骨架
    测试对象：tests/test_no_clean_write_for_web_evidence.py 模块本身
    目的/目标：确认 R3H-04 负例测试文件已登记
    验证点：模块 docstring 声明三源负例覆盖
    失败含义：Execute 无法登记 clean-write/resolve 负例
    """
    import tests.test_no_clean_write_for_web_evidence as mod

    assert "kalshi" in (mod.__doc__ or "")
    assert "web_search" in (mod.__doc__ or "")


def _load_registry() -> dict:
    path = PROJECT_ROOT / "specs/datasource_registry/source_registry.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


@pytest.mark.parametrize(
    ("domain", "expected_fallback"),
    [
        ("supplemental_web_evidence", "manual_review_required"),
        ("vix_cds_supplement", "manual_review_required"),
        ("event_resolution_evidence", "manual_review_required"),
        ("prediction_market_probability", "mark_missing"),
        ("regulated_event_contract", "mark_missing"),
    ],
)
def test_webAndPredictionDomains_fallbackPolicyNotCleanWriter(
    domain: str, expected_fallback: str
) -> None:
    """覆盖范围：三源关联网页/预测域的 fallback_policy 不得指向 clean writer
    测试对象：source_registry.yaml domain_roles fallback_policy
    目的/目标：web 域须 manual_review_required；预测域不得 silent clean promote
    验证点：fallback_policy 等于预期值，非 use_last_good_cache 类 clean 路径
    失败含义：registry 将非事实源路由到可写 clean 表的 fallback
    """
    roles = (_load_registry().get("domain_roles") or {}).get(domain) or {}
    assert roles.get("fallback_policy") == expected_fallback
    notes = str(roles.get("notes") or "")
    if domain.startswith("supplemental") or domain.startswith("vix") or domain.startswith("event_resolution"):
        assert "clean" not in notes.lower() or "never clean" in notes.lower() or "manual_review" in notes.lower()


@pytest.mark.parametrize(
    ("fixture_path", "source_id"),
    [
        (_KALSHI_REPLAY, "kalshi"),
        (_POLYMARKET_REPLAY, "polymarket"),
    ],
)
def test_resolve_predictionReplayBundles_haveNoForbiddenResolutionFields(
    fixture_path, source_id: str
) -> None:
    """覆盖范围：预测市场 replay bundle 禁止事实 resolve 字段
    测试对象：probability_signal replay fixtures
    目的/目标：概率证据不得含 resolved_outcome/factual_resolution 等
    验证点：bundle 与 signals[] 均无 FORBIDDEN_FIELDS
    失败含义：预测价格被编码为事实结果，违反 hardening §4
    """
    from backend.app.datasources.normalizers.probability_signal import (
        read_probability_signal_evidence_bundle,
    )

    bundle = read_probability_signal_evidence_bundle(fixture_path)
    assert bundle["source_id"] == source_id
    for field in _FORBIDDEN_FIELDS:
        assert field not in bundle
        for sig in bundle.get("signals") or []:
            assert field not in sig


def test_resolve_probabilityNormalizer_rejectsForbiddenResolutionField() -> None:
    """覆盖范围：probability_signal normalizer 拒绝禁止字段
    测试对象：build_probability_signal_evidence_bundle + reject_forbidden_resolution_fields
    目的/目标：构造含 resolved_outcome 的 signal 须 fail-closed
    验证点：ProbabilitySignalEvidenceError 抛出
    失败含义：normalizer 可接受事实 resolve 字段
    """
    from backend.app.datasources.normalizers.probability_signal import (
        ProbabilitySignalEvidenceError,
        build_probability_signal_evidence_bundle,
    )

    with pytest.raises(ProbabilitySignalEvidenceError, match="forbidden"):
        build_probability_signal_evidence_bundle(
            signals=[{"market_ticker": "X", "resolved_outcome": "yes", "probability": 0.9}],
            data_domain="prediction_market_probability",
            source_id="kalshi",
            source_fetch_id="bad",
            content_hash="bad",
            as_of_timestamp="2024-01-01T00:00:00Z",
        )


def test_no_clean_write_webStaging_rejectsCleanTablePromotion() -> None:
    """覆盖范围：web_search staging 不得 promote 到 clean 表
    测试对象：reject_clean_table_promotion
    目的/目标：任何 clean 表名均须拒绝
    验证点：ManualReviewStagingError on promote
    失败含义：web 证据可写入 security_bar_daily 等 clean 表
    """
    from backend.app.evidence.manual_review_staging import (
        ManualReviewStagingError,
        reject_clean_table_promotion,
    )

    with pytest.raises(ManualReviewStagingError, match="cannot promote"):
        reject_clean_table_promotion(target_table="instrument_registry")


def test_no_clean_write_webBundle_alwaysRequiresManualReview() -> None:
    """覆盖范围：web evidence bundle 恒须 manual review
    测试对象：read_web_evidence_staging_bundle replay fixture
    目的/目标：need_human_review=true 且 manual_review_state=queued
    验证点：两字段固定为 true/queued
    失败含义：web 证据可绕过人工审核直接进入下游
    """
    from backend.app.evidence.manual_review_staging import read_web_evidence_staging_bundle

    bundle = read_web_evidence_staging_bundle(_WEB_REPLAY)
    assert bundle["need_human_review"] is True
    assert bundle["manual_review_state"] == "queued"


@pytest.mark.parametrize("source_id", ["kalshi", "polymarket", "web_search"])
def test_no_clean_write_sources_defaultDisabledInRegistry(source_id: str) -> None:
    """覆盖范围：三源默认禁用，防止未配置即 clean 路径
    测试对象：source_registry.yaml 三源 enabled_by_default
    目的/目标：enabled_by_default=false 直到显式启用
    验证点：三源 registry 行 enabled_by_default is False
    失败含义：三源默认可用，绕过 mock-first / user gate
    """
    sources = {s["source_id"]: s for s in (_load_registry().get("sources") or [])}
    entry = sources.get(source_id)
    assert entry is not None, source_id
    assert entry.get("enabled_by_default") is False


def test_no_clean_write_kalshiPortOutput_hasNoCleanWriteTarget() -> None:
    """覆盖范围：Kalshi port 输出无 clean_write_target
    测试对象：KalshiMockFetchPort.fetch_payload JSON body
    目的/目标：port 层不携带 clean 写目标字段
    验证点：clean_write_target 不在 body
    失败含义：port 暗示可写 clean 表
    """
    from backend.app.datasources.fetch_ports.kalshi_port import create_kalshi_fetch_port
    from backend.app.datasources.fetch_result import FetchRequest

    port = create_kalshi_fetch_port(market_tickers=("KXHIGHNY-24",), max_markets=1)
    req = FetchRequest(
        run_id="r3h04-neg",
        source_id="kalshi",
        data_domain="prediction_market_probability",
        instrument_id="KXHIGHNY-24",
    )
    body = json.loads(port.fetch_payload(req).content.decode("utf-8"))
    assert "clean_write_target" not in body
    assert "factual_resolution" not in body


def test_no_clean_write_polymarketPortOutput_hasNoCleanWriteTarget() -> None:
    """覆盖范围：Polymarket port 输出无 clean_write_target
    测试对象：PolymarketMockFetchPort.fetch_payload JSON body
    目的/目标：port 层不携带 clean 写目标字段（对称 kalshi）
    验证点：clean_write_target 不在 body
    失败含义：polymarket port 暗示可写 clean 表
    """
    from backend.app.datasources.fetch_ports.polymarket_port import create_polymarket_fetch_port
    from backend.app.datasources.fetch_result import FetchRequest

    port = create_polymarket_fetch_port(
        market_slugs=("will-fed-cut-rates-2024",), max_markets=1
    )
    req = FetchRequest(
        run_id="r3h04-neg-poly",
        source_id="polymarket",
        data_domain="prediction_market_probability",
        instrument_id="will-fed-cut-rates-2024",
    )
    body = json.loads(port.fetch_payload(req).content.decode("utf-8"))
    assert "clean_write_target" not in body
    assert "factual_resolution" not in body
