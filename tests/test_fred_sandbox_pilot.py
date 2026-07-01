"""FRED sandbox pilot tests (B01-FRED FRED-02..07)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from backend.app.ops.fred_evidence_validator import validate_fred_evidence_health
from backend.app.ops.fred_sandbox_pilot import (
    DEFAULT_AUTHORIZATION_REL,
    FredPilotRequest,
    FredPilotSeriesRejectedError,
    FredPilotStatus,
    build_pilot_closeout,
    build_route_preview,
    run_failure_scenario,
    run_live_fetch,
    run_mock_fetch,
    validate_series_whitelist,
)
from tests.contract_gate_support import PROJECT_ROOT

_FRED_PILOT_TASK_ROOT = (
    PROJECT_ROOT / ".trellis/tasks/archive/2026-07/round3-fred-authorized-sandbox-pilot"
)


def test_fredRoutePreview_whitelistedSeries_sandboxOnly() -> None:
    """覆盖范围：P0 FRED series 路由预览
    测试对象：fred_sandbox_pilot.build_route_preview
    目的/目标：白名单 series 产生 sandbox/raw-only 计划；fred 默认禁用
    验证点：sandbox_only、production_clean_write=False；未列 series 拒绝
    失败含义：未授权 series 可路由或计划声称 production 写
    """
    preview = build_route_preview(
        FredPilotRequest(series_ids=("DGS10", "VIXCLS"), dry_run=True)
    )
    assert preview["sandbox_only"] is True
    assert preview["production_clean_write"] is False
    assert preview["data_domain"] == "macro_series"
    assert set(preview["series_ids"]) == {"DGS10", "VIXCLS"}
    fred = preview.get("fred_candidate") or {}
    assert fred.get("source_id") == "fred"
    assert fred.get("enabled") is False

    with pytest.raises(FredPilotSeriesRejectedError, match="not in P0 whitelist"):
        validate_series_whitelist(("UNKNOWN_SERIES",))


def test_fredMockFetch_writesManifestWithHashAndFetchId(tmp_path: Path) -> None:
    """覆盖范围：mocked FRED fetch manifest
    测试对象：fred_sandbox_pilot.run_mock_fetch
    目的/目标：manifest 含 series_id/date/value/fetch_id/hash/as_of
    验证点：status PASS_RAW_ONLY；每 series 有 source_fetch_id 与 content_hash
    失败含义：无 hash/fetch_id 无法做 lineage 与 B2.5-O-05 证据
    """
    manifest = run_mock_fetch(
        FredPilotRequest(
            series_ids=("DGS10", "T10Y3M"),
            sandbox_root=tmp_path,
            dry_run=True,
            use_mock_port=True,
        )
    )
    assert manifest["status"] == FredPilotStatus.FRED_PILOT_PASS_RAW_ONLY
    assert manifest["production_clean_write"] is False
    for entry in manifest["series"]:
        assert entry.get("series_id")
        assert entry.get("source_fetch_id")
        assert entry.get("content_hash")
        assert entry.get("as_of_timestamp")
        assert entry["rows"]
        for row in entry["rows"]:
            assert row.get("observation_date")
            assert row.get("value") is not None


def test_fredPilot_missingAuth_returnsFailAuth() -> None:
    """覆盖范围：live fetch 缺授权
    测试对象：fred_sandbox_pilot.run_live_fetch / run_failure_scenario
    目的/目标：无 authorization 须 FRED_PILOT_FAIL_AUTH
    验证点：status FAIL_AUTH；不得静默 PASS
    失败含义：缺 key/授权仍 live 成功会违反 hardening §3
    """
    result = run_failure_scenario("missing_auth")
    assert result["status"] == FredPilotStatus.FRED_PILOT_FAIL_AUTH


@pytest.mark.parametrize(
    "scenario,expected",
    [
        ("network", FredPilotStatus.FRED_PILOT_FAIL_NETWORK),
        ("schema", FredPilotStatus.FRED_PILOT_FAIL_SCHEMA),
        ("validation", FredPilotStatus.FRED_PILOT_FAIL_VALIDATION),
    ],
)
def test_fredPilot_failureTaxonomy_explicitStatus(scenario: str, expected: FredPilotStatus) -> None:
    """覆盖范围：FRED pilot 失败分类
    测试对象：fred_sandbox_pilot.run_failure_scenario
    目的/目标：network/schema/validation 失败有显式状态
    验证点：各场景 status 匹配枚举
    失败含义：静默 PASS 会掩盖 pilot 风险
    """
    result = run_failure_scenario(scenario)
    assert result["status"] == expected


def test_fredEvidenceHealth_staleObservation_warnsOrFails() -> None:
    """覆盖范围：pilot-local evidence health
    测试对象：fred_evidence_validator.validate_fred_evidence_health
    目的/目标：坏 evidence 检出 stale/missing/malformed/missing hash
    验证点：缺 hash → FAIL；极旧日期 → WARN 或 FAIL
    失败含义：坏 evidence 通过会污染 B2.5-O-05 闭合判断
    """
    missing_hash = {
        "series": [
            {
                "series_id": "DGS10",
                "source_fetch_id": "fetch-1",
                "rows": [{"observation_date": "2020-01-01", "value": "1.5"}],
            }
        ]
    }
    health_missing = validate_fred_evidence_health(missing_hash)
    assert health_missing["status"] == "FAIL"
    assert any(i["code"] == "MISSING_HASH" for i in health_missing["issues"])

    stale = {
        "series": [
            {
                "series_id": "DGS10",
                "source_fetch_id": "fetch-2",
                "content_hash": "abc",
                "rows": [{"observation_date": "2010-01-01", "value": "2.0"}],
            }
        ]
    }
    health_stale = validate_fred_evidence_health(stale, stale_after_days=30)
    assert health_stale["status"] in {"WARN", "FAIL"}
    assert any(i["code"] == "STALE_OBSERVATION" for i in health_stale["issues"])


@pytest.mark.parametrize(
    "manifest,expected_codes",
    [
        (
            {
                "series": [
                    {
                        "series_id": "DGS10",
                        "source_fetch_id": "fetch-1",
                        "content_hash": "abc",
                        "rows": [],
                    }
                ]
            },
            {"MISSING_ROWS"},
        ),
        (
            {
                "series": [
                    {
                        "series_id": "DGS10",
                        "source_fetch_id": "fetch-2",
                        "content_hash": "abc",
                        "rows": [{"value": "1.5"}],
                    }
                ]
            },
            {"MALFORMED_ROW"},
        ),
        (
            {
                "series": [
                    {
                        "series_id": "DGS10",
                        "source_fetch_id": "fetch-3",
                        "content_hash": "abc",
                        "rows": [{"observation_date": "2020-01-01"}],
                    }
                ]
            },
            {"MALFORMED_VALUE"},
        ),
        (
            {
                "series": [
                    {
                        "series_id": "DGS10",
                        "source_fetch_id": "fetch-4",
                        "content_hash": "abc",
                        "rows": [{"observation_date": "not-a-date", "value": "1.5"}],
                    }
                ]
            },
            {"MALFORMED_DATE"},
        ),
    ],
)
def test_fredEvidenceHealth_malformedBranches_failExplicitly(
    manifest: dict,
    expected_codes: set[str],
) -> None:
    """覆盖范围：AA-FRED-A8-01 evidence health MALFORMED_* / MISSING_ROWS
    测试对象：fred_evidence_validator.validate_fred_evidence_health
    目的/目标：各畸形分支产出显式 issue code 而非静默 PASS
    验证点：status FAIL；issues 含 expected_codes 全集
    失败含义：坏 manifest 漏检会污染 B2.5-O-05 闭合判断
    """
    health = validate_fred_evidence_health(manifest)
    assert health["status"] == "FAIL"
    codes = {issue["code"] for issue in health["issues"]}
    assert expected_codes <= codes


def test_fredCloseout_macroCannotClose_withoutFredOnlyEvidence() -> None:
    """覆盖范围：B2.5-O-05 closeout 决策
    测试对象：fred_sandbox_pilot.build_pilot_closeout
    目的/目标：无 FRED-only 证据不得关闭 B2.5-O-05
    验证点：b2_5_o_05_closed=False；macro_supplementary_cannot_close=True
    失败含义：macro 证据误关 FRED 主源延期项
    """
    closeout = build_pilot_closeout(
        manifest={"source_id": "akshare", "series": []},
        health={"status": "PASS"},
    )
    assert closeout["b2_5_o_05_closed"] is False
    assert closeout["macro_supplementary_cannot_close"] is True

    sandbox = PROJECT_ROOT / ".audit-sandbox/test-fred-closeout"
    manifest = run_mock_fetch(
        FredPilotRequest(series_ids=("DGS10",), sandbox_root=sandbox)
    )
    health = validate_fred_evidence_health(manifest)
    fred_closeout = build_pilot_closeout(manifest=manifest, health=health)
    assert fred_closeout["fred_only_evidence"] is True
    assert fred_closeout["production_live_claim"] is False


def test_fred07_liveFetch_closureClosedSkipOptIn_withoutApiKey() -> None:
    """覆盖范围：FRED-07 无 API key 时的 Audit 闭合
    测试对象：b01-fred-audit-closures.md · run_live_fetch · authorization.yaml
    目的/目标：无 FRED_API_KEY 时 slice 标 CLOSED-SKIP-OPT-IN 而非 OPEN
    验证点：closure 文档含 CLOSED-SKIP-OPT-IN；authorization 存在；无 key 时 live 须 FAIL_AUTH
    失败含义：可选 live 切片被标 OPEN 会阻塞 Audit 零遗留
    """
    closure_doc = _FRED_PILOT_TASK_ROOT / "research" / "b01-fred-audit-closures.md"
    assert closure_doc.is_file()
    closure_text = closure_doc.read_text(encoding="utf-8")
    assert "FRED-07" in closure_text
    assert "CLOSED-SKIP-OPT-IN" in closure_text
    assert "| OPEN |" not in closure_text

    auth_path = PROJECT_ROOT / DEFAULT_AUTHORIZATION_REL
    assert auth_path.is_file()

    if os.environ.get("FRED_API_KEY"):
        pytest.skip("FRED_API_KEY present — CLOSED-SKIP-OPT-IN applies only without key")

    result = run_live_fetch(
        FredPilotRequest(
            series_ids=("DGS10",),
            authorization_evidence=str(auth_path.relative_to(PROJECT_ROOT)),
            skip_live_fetch=False,
            use_mock_port=False,
        )
    )
    assert result["status"] == FredPilotStatus.FRED_PILOT_FAIL_AUTH


def test_b250o05_reDeferred_closureRowClosed() -> None:
    """覆盖范围：B2.5-O-05 RE-DEFERRED 书面闭合行
    测试对象：b01-fred-audit-closures.md · fred_pilot_closeout.json
    目的/目标：re-defer 含 owner/phase/closure test；Audit 标 CLOSED 非 OPEN
    验证点：closure 行含 Batch 6、RE-DEFERRED、closure test 锚点；b2_5_o_05_closed=false
    失败含义：缺书面 re-defer 会导致 registry 与 pilot 证据脱节
    """
    closure_doc = _FRED_PILOT_TASK_ROOT / "research" / "b01-fred-audit-closures.md"
    text = closure_doc.read_text(encoding="utf-8")
    for token in (
        "B2.5-O-05",
        "RE-DEFERRED",
        "Batch 6",
        "test_b250o05_reDeferred_closureRowClosed",
        "test_fred_staged_semantics.py",
        "**CLOSED**",
    ):
        assert token in text
    assert "| OPEN |" not in text

    task_root = _FRED_PILOT_TASK_ROOT
    closeout_path = task_root / "execute-evidence/fred_pilot_closeout.json"

    closeout = json.loads(closeout_path.read_text(encoding="utf-8"))
    assert closeout["b2_5_o_05_closed"] is False
    assert closeout["fred_only_evidence"] is True
    assert closeout["macro_supplementary_cannot_close"] is True
    assert closeout["b2_5_o_05_decision"] == "FRED_SANDBOX_EVIDENCE_RECORDED"


@pytest.mark.skipif(
    not os.environ.get("FRED_API_KEY"),
    reason="FRED_API_KEY absent — live fetch opt-in skipped",
)
def test_fredLiveFetch_authorized_respectsCaps(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：授权 live FRED fetch（FRED-07 opt-in）
    测试对象：fred_sandbox_pilot.run_live_fetch
    目的/目标：有 authorization.yaml + FRED_API_KEY 时 cap 内 sandbox 写
    验证点：PASS_SANDBOX_STAGING；production_clean_write=False
    失败含义：live 越权或写 production clean
    """
    auth_path = PROJECT_ROOT / DEFAULT_AUTHORIZATION_REL
    if not auth_path.is_file():
        pytest.skip("authorization.yaml not present in execute-evidence")

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    result = run_live_fetch(
        FredPilotRequest(
            series_ids=("DGS10",),
            authorization_evidence=str(auth_path.relative_to(PROJECT_ROOT)),
            skip_live_fetch=False,
            use_mock_port=False,
            max_rows_per_series=10,
            sandbox_root=tmp_path,
        )
    )
    assert result["status"] == FredPilotStatus.FRED_PILOT_PASS_SANDBOX_STAGING
    assert result.get("production_clean_write") is False
    assert result.get("series")
