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
    proof = payload["mutation_proof"]
    if proof["proof_status"] == "VERIFIED":
        assert proof["row_counts_unchanged"] is True
    else:
        assert proof["proof_status"] == "INCONCLUSIVE"
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
    budget = mod._active_network_budget()
    for _ in range(MAX_NETWORK_CALLS_PER_RUN):
        budget.consume()
    with pytest.raises(StagedPilotNetworkCapExceededError):
        budget.consume()
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


def test_stagedPilot_mutationProof_inconclusiveWhenProductionDbMissing(tmp_path: Path) -> None:
    """覆盖范围：生产库缺失时 no-mutation proof fail-closed。

    测试对象：build_production_mutation_proof。
    目的/目标：ADV-POST14-A-001 — proof_status=INCONCLUSIVE，不得空 pass。
    """
    from backend.app.ops.mutation_proof import build_production_mutation_proof

    missing = tmp_path / "missing-production.duckdb"
    proof = build_production_mutation_proof(missing)
    assert proof["proof_status"] == "INCONCLUSIVE"
    assert proof["db_hash_unchanged"] is None
    assert proof["row_counts_unchanged"] is None
    assert proof["reason"] == "production_db_file_missing"


def test_stagedPilot_validationReport_emitsConflictDeferArtifact(tmp_path: Path) -> None:
    """覆盖范围：冲突检查显式 defer 证据。

    测试对象：capture_validation_report。
    目的/目标：ADV-POST14-A-002 — NO_CONFLICT_CHECK_DEFERRED 落盘。
    """
    from backend.app.ops.staged_pilot import CONFLICT_CHECK_JSON, capture_validation_report

    payload = capture_validation_report(evidence_dir=tmp_path, raw_manifest={"fetches": []})
    assert payload["conflict_check"]["status"] == "NO_CONFLICT_CHECK_DEFERRED"
    assert (tmp_path / CONFLICT_CHECK_JSON).is_file()


def test_stagedPilot_validationReport_declaresSandboxValidators(tmp_path: Path) -> None:
    """覆盖范围：validation report 声明 DbValidationGate / DQV 契约。

    测试对象：capture_validation_report。
    目的/目标：ADV-POST14-A-006 — 不得仅 shallow JSON，需声明 validator 路径。
    """
    from backend.app.ops.staged_pilot import capture_validation_report

    payload = capture_validation_report(evidence_dir=tmp_path, raw_manifest={"fetches": []})
    refs = payload["declared_validators"]
    assert "DataQualityValidator" in refs["data_quality_validator"]
    assert "DbValidationGate" in refs["clean_write_gate"]
    assert "SourceConflictValidator" in refs["source_conflict_validator"]


def test_stagedPilot_dateWindowBoundToFetchPort() -> None:
    """覆盖范围：授权 date_window 绑定 fetch 窗口。

    测试对象：parse_pilot_date_window / create_staged_fetch_port。
    目的/目标：ADV-POST14-A-005 — cninfo 14 calendar days 不得硬编码忽略。
    """
    from backend.app.ops.live_pilot_fetch_ports import parse_pilot_date_window
    from backend.app.ops.staged_pilot_fetch_ports import CninfoMetadataStagedFetchPort

    assert parse_pilot_date_window("recent 14 calendar days") == 14
    assert parse_pilot_date_window("recent 10 trading days") == 17
    port = CninfoMetadataStagedFetchPort(
        symbols=("sh.600519",),
        max_rows=10,
        date_window="recent 14 calendar days",
    )
    assert port.date_window == "recent 14 calendar days"


def test_stagedPilot_cninfoFetchPayloadAttributesVendorApi() -> None:
    """覆盖范围：cninfo metadata 源归因与 vendor_api。

    测试对象：CninfoMetadataStagedFetchPort（mock akshare）。
    目的/目标：ADV-POST14-A-003 — source=cninfo 且 vendor_api 可追溯。
    """
    import json
    from datetime import UTC, datetime

    from backend.app.datasources.adapters.fetch_port import FetchPayload
    from backend.app.datasources.fetch_result import FetchRequest
    from backend.app.ops.staged_pilot_fetch_ports import CninfoMetadataStagedFetchPort

    class _FakeFrame:
        def __init__(self, rows):
            self._rows = rows

        @property
        def empty(self):
            return not self._rows

        def tail(self, _n):
            return self

        def to_dict(self, orient):
            assert orient == "records"
            return self._rows

    port = CninfoMetadataStagedFetchPort(
        symbols=("sh.600519",),
        max_rows=10,
        date_window="recent 14 calendar days",
    )
    req = FetchRequest(
        run_id="r1",
        source_id="cninfo",
        data_domain="cn_announcements",
        instrument_id="sh.600519",
    )

    with patch(
        "backend.app.ops.staged_pilot_fetch_ports._run_akshare_call",
        return_value=_FakeFrame([{"公告标题": "test", "公告时间": "2026-06-01"}]),
    ), patch.dict("sys.modules", {"akshare": object()}):
        payload = port.fetch_payload(req)

    body = json.loads(payload.content.decode("utf-8"))
    assert body["source"] == "cninfo"
    assert body["vendor_api"] == "stock_zh_a_disclosure_report_cninfo"


def test_stagedPilot_routePreview_exposesOrganicRouteAndOverrideFlag() -> None:
    """覆盖范围：显式 source 路由 override 证据字段。

    测试对象：preview_staged_pilot。
    目的/目标：ADV-POST14-A-008 — organic_route_status 与 override 标记可见。
    """
    from backend.app.ops.staged_pilot import preview_staged_pilot

    preview = preview_staged_pilot(_approved_baostock_request())
    assert "organic_route_status" in preview
    assert "pilot_route_override_applied" in preview


def test_stagedPilot_mockFetchSuccess_usesWriteManagerStagedQualityFlag(
    tmp_path: Path,
) -> None:
    """覆盖范围：mock fetch 成功路径与 file_registry 单一路径。

    测试对象：run_staged_pilot_raw_only / _StagedPilotFileRegistry。
    目的/目标：ADV-POST14-A-004 / B-002 — quality_flag=STAGED via WriteManager。
    """
    from backend.app.datasources.adapters.fetch_port import FetchPayload
    from backend.app.datasources.fetch_result import FetchRequest
    from backend.app.ops.staged_pilot import reset_network_call_budget, run_staged_pilot_raw_only

    sandbox = tmp_path / "sandbox"
    reset_network_call_budget()

    class _StubPort:
        def fetch_payload(self, req: FetchRequest) -> FetchPayload:
            content = json.dumps(
                {
                    "symbol": req.instrument_id,
                    "source": "baostock",
                    "rows": [["2026-06-20", "sh.600519", "1", "2", "3", "4", "5"]],
                }
            ).encode("utf-8")
            return FetchPayload(content=content, file_type="json", row_count=1)

    with patch(
        "backend.app.ops.staged_pilot_fetch_ports.create_staged_fetch_port",
        return_value=_StubPort(),
    ):
        result = run_staged_pilot_raw_only(
            _approved_baostock_request(),
            sandbox_root=sandbox,
            pilot_request_id="staged-req-mock",
        )

    assert result["file_registry_write_path"] == "WriteManager"
    assert result["file_registry_quality_flag"] == "STAGED"
    assert result["staged_file_ids"]


def test_stagedPilot_sandboxValidationReport_canWriteCleanFalse(tmp_path: Path) -> None:
    """覆盖范围：sandbox validation_report stub can_write_clean 门禁。

    测试对象：_ensure_raw_validation_report。
    目的/目标：ADV-POST14-A-007 — stub 不得 can_write_clean=True。
    """
    import duckdb
    from backend.app.db.migrate import apply_migrations
    from backend.app.ops.staged_pilot import (
        STAGED_RAW_VALIDATION_REPORT_ID,
        StagedPilotRequest,
        _ensure_raw_validation_report,
    )

    con = duckdb.connect(":memory:")
    apply_migrations(con)
    request = _approved_baostock_request()
    _ensure_raw_validation_report(con, request, "run-1")
    row = con.execute(
        "SELECT can_write_clean, needs_manual_review FROM validation_report WHERE validation_report_id = ?",
        [STAGED_RAW_VALIDATION_REPORT_ID],
    ).fetchone()
    assert row[0] is False
    assert row[1] is False


def test_stagedPilot_cninfoMetadataValidation_requiresAnnouncementFields() -> None:
    """覆盖范围：cninfo metadata 结构校验增强。

    测试对象：_validate_cninfo_metadata_structure。
    目的/目标：ADV-POST14-A-018 — 弱校验升级为公告字段检查。
    """
    from backend.app.ops.staged_pilot import _validate_cninfo_metadata_structure

    weak = _validate_cninfo_metadata_structure([{"foo": "bar"}])
    assert weak["status"] == "FAILED"
    strong = _validate_cninfo_metadata_structure([{"公告标题": "年报"}])
    assert strong["status"] == "PASSED"


def test_stagedPilot_fetchTaxonomyUsesStableEnumValues() -> None:
    """覆盖范围：fetch taxonomy 稳定枚举名。

    测试对象：FetchTaxonomyStatus / _classify_fetch_taxonomy。
    目的/目标：ADV-POST14-A-017 — 不得暴露异常类名作为 taxonomy。
    """
    from backend.app.datasources.fetch_result import FetchResult
    from backend.app.ops.staged_pilot import (
        FetchTaxonomyStatus,
        StagedPilotRequest,
        _classify_fetch_taxonomy,
    )

    req = _approved_baostock_request()
    success = FetchResult(
        run_id="r1",
        source_id="baostock",
        data_domain="cn_equity_daily_bar",
        status="SUCCESS",
        row_count=1,
        fetch_time="2026-06-22T00:00:00Z",
        raw_file_paths=["x.json"],
    )
    assert _classify_fetch_taxonomy(req, success) == FetchTaxonomyStatus.SUCCESS


def test_stagedPilot_authorization_rejectsWrongFilenamePrefix(tmp_path: Path) -> None:
    """覆盖范围：授权文件名前缀 fail-closed。

    测试对象：validate_authorization。
    目的/目标：ADV-POST14-A-019 — 必须 prompt14_user_authorization_* 前缀。
    """
    from backend.app.ops.staged_pilot import StagedPilotAuthorizationError, validate_authorization

    bad_path = tmp_path / "not_prompt14_user_authorization_2026-06-22.md"
    bad_path.write_text("Approved on 2026-06-22\n", encoding="utf-8")
    bad = replace(
        _approved_baostock_request(),
        authorization_evidence=str(bad_path),
    )
    with pytest.raises(StagedPilotAuthorizationError, match="prompt14_user_authorization"):
        validate_authorization(bad)


def test_stagedPilot_runFullPilot_closeoutIncludesNarrative(tmp_path: Path) -> None:
    """覆盖范围：closeout 叙事与 mutation/conflict 状态。

    测试对象：run_full_staged_pilot closeout payload。
    目的/目标：ADV-POST14-A-016 — closeout 含 regen/review 叙事字段。
    """
    from backend.app.ops.staged_pilot import run_full_staged_pilot

    evidence = tmp_path / "closeout"
    result = run_full_staged_pilot(evidence, skip_live_fetch=True)
    closeout = result["closeout"]
    assert "closeout_narrative" in closeout
    assert "mutation_proof_status" in closeout
    assert "conflict_check_status" in closeout


def test_stagedPilot_stagedFetchPortsUseStagedClassNames() -> None:
    """覆盖范围：staged fetch port 命名与 live pilot 区分。

    测试对象：create_staged_fetch_port。
    目的/目标：ADV-POST14-A-015 — 证据不得混用 LiveFetchPort 类名。
    """
    from backend.app.ops.staged_pilot_fetch_ports import (
        AkshareEquityStagedFetchPort,
        BaostockStagedFetchPort,
        CninfoMetadataStagedFetchPort,
        create_staged_fetch_port,
    )

    assert isinstance(
        create_staged_fetch_port(
            source_id="baostock",
            operation="fetch_daily_bar",
            symbols_or_indicators=("sh.600519",),
            max_rows=10,
            date_window="recent 10 trading days",
        ),
        BaostockStagedFetchPort,
    )
    assert isinstance(
        create_staged_fetch_port(
            source_id="akshare",
            operation="fetch_daily_bar_validation",
            symbols_or_indicators=("sh.600519",),
            max_rows=10,
            date_window="recent 10 trading days",
        ),
        AkshareEquityStagedFetchPort,
    )
    assert isinstance(
        create_staged_fetch_port(
            source_id="cninfo",
            operation="fetch_announcement_index",
            symbols_or_indicators=("sh.600519",),
            max_rows=10,
            date_window="recent 14 calendar days",
        ),
        CninfoMetadataStagedFetchPort,
    )


def test_stagedPilot_evidencePathsPreferProjectRelative(tmp_path: Path) -> None:
    """覆盖范围：证据 JSON 路径相对化。

    测试对象：_evidence_relative_path。
    目的/目标：ADV-POST14-A-013 — 避免绝对路径泄漏到 evidence。
    """
    from backend.app.ops.staged_pilot import _evidence_relative_path

    rel = _evidence_relative_path(PROJECT_ROOT / "docs/quality/foo.md")
    assert not rel.startswith("/")
    assert rel.startswith("docs/")
