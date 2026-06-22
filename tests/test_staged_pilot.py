"""PROMPT_14 staged real-data pilot gate tests — fail-closed orchestration."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from tests.contract_gate_support import PROJECT_ROOT

AUTH_PATH = "docs/quality/prompt14_user_authorization_2026-06-22.md"
SANDBOX_ROOT = PROJECT_ROOT / ".audit-sandbox/r3x-staged-pilot-test"
TASK_EVIDENCE = (
    PROJECT_ROOT / ".trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence"
)


def _approved_baostock_request():
    from backend.app.ops.staged_pilot import StagedPilotRequest

    return StagedPilotRequest(
        source_id="baostock",
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        symbols_or_indicators=("sh.600519",),
        date_window="recent 10 trading days",
        max_rows=10,
        authorization_evidence=AUTH_PATH,
    )


def test_stagedPilot_missingAuthorization_blocksBeforeFetch() -> None:
    """覆盖范围：授权门禁在 fetch 之前 fail-closed。

    测试对象：run_staged_pilot_raw_only。
    目的/目标：缺失授权证据时必须阻止任何网络 fetch。
    """
    from backend.app.ops.staged_pilot import (
        StagedPilotAuthorizationError,
        StagedPilotRequest,
        run_staged_pilot_raw_only,
    )

    request = StagedPilotRequest(
        source_id="baostock",
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        symbols_or_indicators=("sh.600519",),
        date_window="recent 10 trading days",
        max_rows=10,
        authorization_evidence="docs/quality/nonexistent_prompt14_authorization.md",
    )
    fetch_called = {"value": False}

    def _track_fetch(*_args, **_kwargs):
        fetch_called["value"] = True
        raise AssertionError("fetch must not be called without authorization")

    with patch(
        "backend.app.datasources.service.DataSourceService.fetch",
        side_effect=_track_fetch,
    ):
        with pytest.raises(StagedPilotAuthorizationError):
            run_staged_pilot_raw_only(request, sandbox_root=SANDBOX_ROOT)
    assert fetch_called["value"] is False


def test_stagedPilot_disabledSource_blocksBeforeFetch() -> None:
    """覆盖范围：禁用源在 fetch 前被拦截。

    测试对象：validate_authorization / run_staged_pilot_raw_only。
    目的/目标：tdx_pytdx 等禁用源不得发起 fetch。
    """
    from backend.app.ops.staged_pilot import (
        StagedPilotDisabledSourceError,
        StagedPilotRequest,
        run_staged_pilot_raw_only,
    )

    request = StagedPilotRequest(
        source_id="tdx_pytdx",
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        symbols_or_indicators=("sh.600519",),
        date_window="recent 10 trading days",
        max_rows=10,
        authorization_evidence=AUTH_PATH,
    )
    with pytest.raises(StagedPilotDisabledSourceError):
        run_staged_pilot_raw_only(request, sandbox_root=SANDBOX_ROOT)


def test_stagedPilot_approvedRequestPassesAuthorizationGate() -> None:
    """覆盖范围：三请求授权信封与 prompt14 授权文件一致。

    测试对象：validate_authorization。
    目的/目标：已批准 baostock 请求通过 Phase 0 授权门禁。
    """
    from backend.app.ops.staged_pilot import validate_authorization

    validate_authorization(_approved_baostock_request())


def test_stagedPilot_authorization_rejectsExpandedEnvelope() -> None:
    """覆盖范围：授权绑定精确符号/窗口/行数上限。

    测试对象：validate_authorization。
    目的/目标：扩大样本必须 fail-closed。
    """
    from backend.app.ops.staged_pilot import (
        StagedPilotAuthorizationError,
        approved_pilot_requests,
        validate_authorization,
    )

    approved = approved_pilot_requests()[0]
    for bad in (
        replace(approved, symbols_or_indicators=("sh.600000",)),
        replace(approved, date_window="recent 30 trading days"),
        replace(approved, max_rows=approved.max_rows + 1),
        replace(approved, allow_clean_write=True),
    ):
        with pytest.raises(StagedPilotAuthorizationError):
            validate_authorization(bad)


def test_stagedPilot_cninfoInApprovedSet() -> None:
    """覆盖范围：PROMPT_14 授权包含 cninfo metadata 请求。

    测试对象：approved_pilot_requests。
    目的/目标：cninfo / cn_announcements 在批准集合内（区别于 Batch 2.75 三请求集）。
    """
    from backend.app.ops.staged_pilot import approved_pilot_requests

    triples = {
        (r.source_id, r.data_domain, r.operation) for r in approved_pilot_requests()
    }
    assert ("cninfo", "cn_announcements", "fetch_announcement_index") in triples
    assert len(triples) == 3


def test_stagedPilot_routePreview_dryRunNoFetch() -> None:
    """覆盖范围：route preview 阶段零 fetch。

    测试对象：preview_staged_pilot。
    目的/目标：dry_run=true 时产出 route 矩阵字段且不调用 fetch。
    """
    from backend.app.ops.staged_pilot import preview_staged_pilot

    fetch_called = {"value": False}

    def _track_fetch(*_args, **_kwargs):
        fetch_called["value"] = True
        raise AssertionError("route preview must not fetch")

    with patch(
        "backend.app.datasources.service.DataSourceService.fetch",
        side_effect=_track_fetch,
    ):
        preview = preview_staged_pilot(_approved_baostock_request())
    assert preview["dry_run"] is True
    assert "explicit_source_route_status" in preview
    assert fetch_called["value"] is False


def test_stagedPilot_captureRouteMatrix_writesEvidenceAndNoMutation(tmp_path: Path) -> None:
    """覆盖范围：route preview 矩阵与 DB no-mutation proof。

    测试对象：capture_route_preview_matrix。
    目的/目标：写出 route_preview_matrix.json 且 key table counts 不变。
    """
    from backend.app.ops.staged_pilot import (
        ROUTE_MATRIX_JSON,
        approved_pilot_requests,
        capture_route_preview_matrix,
    )

    evidence = tmp_path / "evidence"
    payload = capture_route_preview_matrix(
        requests=approved_pilot_requests(),
        evidence_dir=evidence,
    )
    assert (evidence / ROUTE_MATRIX_JSON).is_file()
    assert payload["run_mode"] == "staged_only"
    assert payload["mutation_proof"]["row_counts_unchanged"] is True
    assert len(payload["previews"]) == 3


def test_stagedPilot_networkCallCapEnforced() -> None:
    """覆盖范围：单次运行网络调用上限。

    测试对象：_NetworkCallBudget。
    目的/目标：超过 max_network_calls_per_run 时 fail-closed。
    """
    from backend.app.ops import staged_pilot as mod
    from backend.app.ops.staged_pilot import (
        MAX_NETWORK_CALLS_PER_RUN,
        StagedPilotNetworkCapExceededError,
        reset_network_call_budget,
    )

    reset_network_call_budget()
    for _ in range(MAX_NETWORK_CALLS_PER_RUN):
        mod._NETWORK_BUDGET.consume()
    with pytest.raises(StagedPilotNetworkCapExceededError):
        mod._NETWORK_BUDGET.consume()
    snapshot = mod.network_call_budget_snapshot()
    assert snapshot["network_calls_consumed"] == MAX_NETWORK_CALLS_PER_RUN
    assert snapshot["within_cap"] is True


def test_stagedPilot_validationReport_blocksCleanWrite(tmp_path: Path) -> None:
    """覆盖范围：validation report 默认禁止 clean write。

    测试对象：capture_validation_report。
    目的/目标：allow_clean_write=false 且 can_write_clean=false。
    """
    from backend.app.ops.staged_pilot import capture_validation_report

    raw_manifest = {
        "fetches": [
            {
                "pilot_request_id": "staged-req-1",
                "request": {
                    "source_id": "baostock",
                    "data_domain": "cn_equity_daily_bar",
                    "operation": "fetch_daily_bar",
                },
                "fetch_result": {
                    "status": "SUCCESS",
                    "raw_file_paths": [],
                },
            }
        ]
    }
    payload = capture_validation_report(evidence_dir=tmp_path, raw_manifest=raw_manifest)
    assert payload["allow_clean_write"] is False
    assert payload["can_write_clean"] is False
    assert payload["clean_write_performed"] is False


def test_stagedPilot_runFullPilot_skipLiveFetch_writesEvidence(tmp_path: Path) -> None:
    """覆盖范围：skip_live_fetch 路径写出完整证据集。

    测试对象：run_full_staged_pilot。
    目的/目标：route + resource guard + validation + closeout 文件落盘。
    """
    from backend.app.ops.staged_pilot import (
        CLOSEOUT_JSON,
        RESOURCE_GUARD_JSON,
        ROUTE_MATRIX_JSON,
        VALIDATION_REPORT_JSON,
        run_full_staged_pilot,
    )

    evidence = tmp_path / "full"
    result = run_full_staged_pilot(evidence, skip_live_fetch=True)
    assert (evidence / ROUTE_MATRIX_JSON).is_file()
    assert (evidence / RESOURCE_GUARD_JSON).is_file()
    assert (evidence / VALIDATION_REPORT_JSON).is_file()
    assert (evidence / CLOSEOUT_JSON).is_file()
    assert result["closeout"]["production_live_readiness_claim"] is False


def test_stagedPilot_partialSuccess_closeoutPassStagedRaw() -> None:
    """覆盖范围：部分 source 成功时的 closeout 判定。

    测试对象：derive_pilot_closeout_outcome。
    目的/目标：至少一个 PASSED 即 PILOT_PASS_STAGED_RAW（非 production-live）。
    """
    from backend.app.ops.staged_pilot import (
        StagedPilotOutcome,
        derive_pilot_closeout_outcome,
    )

    payload = {
        "validations": [
            {"status": "PASSED"},
            {"status": "SOURCE_FAILURE"},
        ]
    }
    assert derive_pilot_closeout_outcome(payload) == StagedPilotOutcome.PILOT_PASS_STAGED_RAW


def test_stagedPilot_authorizationFile_exists() -> None:
    """覆盖范围：prompt14 用户授权证据文件存在且含批准标记。

    测试对象：docs/quality/prompt14_user_authorization_2026-06-22.md。
    目的/目标：Execute 门禁要求的授权证据在仓库内可追溯。
    """
    path = PROJECT_ROOT / AUTH_PATH
    assert path.is_file(), f"missing authorization evidence: {path}"
    text = path.read_text(encoding="utf-8")
    assert "Approved on" in text
    assert "r3x-staged-pilot-20260622" in text
    assert "production_clean_write" in text
