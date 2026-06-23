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


# --- PROMPT_19 staged pilot v2 (R3Y-SP2-01..09) --------------------------------

TASK_EVIDENCE_V2 = (
    PROJECT_ROOT
    / ".trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence"
)


def _approved_baostock_v2_request():
    from backend.app.ops.staged_pilot import StagedPilotRequest, V2_BAOSTOCK_SYMBOLS

    return StagedPilotRequest(
        source_id="baostock",
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        symbols_or_indicators=V2_BAOSTOCK_SYMBOLS,
        date_window="recent 30 trading days",
        max_rows=100,
        authorization_evidence=AUTH_PATH,
    )


def _mock_v2_fetch_item(request, *, sandbox_root: Path) -> dict:
    from backend.app.ops.staged_pilot import PILOT_ID_V2

    symbol = request.symbols_or_indicators[0]
    raw_rel = f".audit-sandbox/mock/{request.source_id}_{symbol}.json"
    return {
        "pilot_id": PILOT_ID_V2,
        "pilot_request_id": f"v2-{request.source_id}",
        "request": {
            "source_id": request.source_id,
            "data_domain": request.data_domain,
            "operation": request.operation,
        },
        "fetch_result": {
            "status": "SUCCESS",
            "row_count": 3,
            "run_id": f"fetch-{request.source_id}-v2",
            "content_hash": "abc123deadbeef",
            "raw_file_paths": [raw_rel],
        },
        "taxonomy_status": "SUCCESS",
        "staged_file_ids": ["file-v2-1"],
        "sandbox_root": str(sandbox_root),
    }


def test_stagedPilotV2_capsJson_matchesApprovedEnvelope(tmp_path: Path) -> None:
    """覆盖范围：v2 caps JSON 与批准 envelope 一致。

    测试对象：write_pilot_v2_caps / pilot_v2_caps_payload。
    目的/目标：AC-SP2-01 — 冻结 pilot_id、caps、sandbox 路径。
    """
    from backend.app.ops.staged_pilot import (
        PILOT_ID_V2,
        PILOT_V2_CAPS_JSON,
        MAX_NETWORK_CALLS_V2,
        MAX_ROWS_V2,
        MAX_SYMBOLS_V2,
        MAX_TRADE_DAYS_V2,
        write_pilot_v2_caps,
    )

    payload = write_pilot_v2_caps(tmp_path)
    assert payload["pilot_id"] == PILOT_ID_V2
    assert payload["max_symbols"] == MAX_SYMBOLS_V2
    assert payload["max_trade_days"] == MAX_TRADE_DAYS_V2
    assert payload["max_rows_per_source_domain"] == MAX_ROWS_V2
    assert payload["max_network_calls_per_run"] == MAX_NETWORK_CALLS_V2
    assert payload["production_clean_write"] is False
    assert (tmp_path / PILOT_V2_CAPS_JSON).is_file()


def test_stagedPilotV2_capsExceedingMaxSymbols_rejects() -> None:
    """覆盖范围：v2 超 max_symbols 拒绝。

    测试对象：validate_pilot_v2_authorization。
    目的/目标：AC-SP2-01 — 未经批准的 caps 扩样 fail-closed。
    """
    from backend.app.ops.staged_pilot import (
        StagedPilotAuthorizationError,
        validate_pilot_v2_authorization,
    )

    too_many = replace(
        _approved_baostock_v2_request(),
        symbols_or_indicators=tuple(f"sh.60000{i}" for i in range(6)),
    )
    with pytest.raises(StagedPilotAuthorizationError, match="max_symbols"):
        validate_pilot_v2_authorization(too_many)


def test_stagedPilotV2_baostockExpanded_writesManifestV2(tmp_path: Path) -> None:
    """覆盖范围：baostock 扩样 manifest v2 必需字段。

    测试对象：capture_baostock_evidence_v2。
    目的/目标：AC-SP2-02 — manifest 含 hash/fetch_id/relative path。
    """
    from backend.app.ops.staged_pilot import (
        RAW_MANIFEST_V2_JSON,
        STAGING_MANIFEST_V2_JSON,
        capture_baostock_evidence_v2,
    )

    payload = capture_baostock_evidence_v2(
        evidence_dir=tmp_path,
        fetch_runner=_mock_v2_fetch_item,
    )
    assert (tmp_path / RAW_MANIFEST_V2_JSON).is_file()
    assert (tmp_path / STAGING_MANIFEST_V2_JSON).is_file()
    entry = payload["manifest_entries"][0]
    assert entry["content_hash"] == "abc123deadbeef"
    assert entry["source_fetch_id"] == "fetch-baostock-v2"
    assert entry["relative_paths"]
    assert payload["required_fields_present"] is True


def test_stagedPilotV2_cninfoExpanded_schemaFieldsPresent(tmp_path: Path) -> None:
    """覆盖范围：cninfo 扩样 metadata 字段结构。

    测试对象：capture_cninfo_evidence_v2。
    目的/目标：AC-SP2-03 — schema notes 与 metadata 字段可追溯。
    """
    from backend.app.ops.staged_pilot import (
        CNINFO_SCHEMA_NOTES_V2_MD,
        capture_cninfo_evidence_v2,
    )

    def _cninfo_fetch(request, *, sandbox_root: Path) -> dict:
        item = _mock_v2_fetch_item(request, sandbox_root=sandbox_root)
        item["fetch_result"]["raw_file_paths"] = [".audit-sandbox/mock/cninfo.json"]
        return item

    with patch(
        "backend.app.ops.staged_pilot._load_raw_json_payload",
        return_value={
            "rows": [{"公告标题": "年报", "公告时间": "2026-06-01"}],
            "vendor_api": "stock_zh_a_disclosure_report_cninfo",
        },
    ):
        payload = capture_cninfo_evidence_v2(
            evidence_dir=tmp_path,
            fetch_runner=_cninfo_fetch,
        )
    assert "公告标题" in payload["schema_fields"]
    assert (tmp_path / CNINFO_SCHEMA_NOTES_V2_MD).is_file()


def test_stagedPilotV2_akshareValidation_recordsTaxonomy(tmp_path: Path) -> None:
    """覆盖范围：akshare validation taxonomy 枚举。

    测试对象：capture_akshare_validation_taxonomy_v2。
    目的/目标：AC-SP2-04 — taxonomy 含 SUCCESS/ERROR 等稳定 status。
    """
    from backend.app.ops.staged_pilot import (
        AKSHARE_TAXONOMY_V2_JSON,
        FetchTaxonomyStatus,
        capture_akshare_validation_taxonomy_v2,
    )

    payload = capture_akshare_validation_taxonomy_v2(evidence_dir=tmp_path)
    statuses = {record["status"] for record in payload["records"]}
    assert FetchTaxonomyStatus.SUCCESS.value in statuses
    assert FetchTaxonomyStatus.SOURCE_FAILURE.value in statuses
    assert payload["validation_only"] is True
    assert payload["primary_forbidden"] is True
    assert (tmp_path / AKSHARE_TAXONOMY_V2_JSON).is_file()


def test_stagedPilotV2_routePreviewMatrixV2_allStatuses(tmp_path: Path) -> None:
    """覆盖范围：route preview matrix v2 全 route status。

    测试对象：capture_route_preview_matrix_v2。
    目的/目标：AC-SP2-05 — selected/skipped/disabled/validation-only 均可见。
    """
    from backend.app.ops.staged_pilot import (
        ROUTE_MATRIX_V2_JSON,
        capture_route_preview_matrix_v2,
    )

    payload = capture_route_preview_matrix_v2(evidence_dir=tmp_path)
    coverage = set(payload["route_status_coverage"])
    assert {"selected", "disabled", "validation_only"}.issubset(coverage)
    assert "user_auth_required" in coverage
    explicit_statuses = {
        ex["explicit_source_route_status"]
        for ex in payload["route_status_examples"]
    }
    assert "USER_AUTH_REQUIRED" in explicit_statuses
    assert any(
        ex.get("route_kind") == "user_auth_required"
        for ex in payload["route_status_examples"]
    )
    assert "skipped" in coverage or "user_auth_required" in coverage
    assert (tmp_path / ROUTE_MATRIX_V2_JSON).is_file()


def test_stagedPilotV2_validationReportV2_exposesQualityFlags(tmp_path: Path) -> None:
    """覆盖范围：validation report v2 质量暴露。

    测试对象：capture_validation_report_v2。
    目的/目标：AC-SP2-06 — quality_flags 与 row_count 字段可见。
    """
    from backend.app.ops.staged_pilot import (
        VALIDATION_REPORT_V2_JSON,
        capture_validation_report_v2,
    )

    raw_manifest = {
        "fetches": [
            {
                "pilot_request_id": "v2-baostock",
                "request": {
                    "source_id": "baostock",
                    "data_domain": "cn_equity_daily_bar",
                    "operation": "fetch_daily_bar",
                },
                "fetch_result": {
                    "status": "SUCCESS",
                    "row_count": 5,
                    "raw_file_paths": [],
                },
            }
        ]
    }
    payload = capture_validation_report_v2(
        evidence_dir=tmp_path,
        raw_manifest=raw_manifest,
    )
    item = payload["validations_v2"][0]
    assert item["row_count"] == 5
    assert "quality_flags" in item
    assert (tmp_path / VALIDATION_REPORT_V2_JSON).is_file()


def test_stagedPilotV2_conflictSummaryV2_primaryOrDeferred(tmp_path: Path) -> None:
    """覆盖范围：conflict summary v2 primary 或 deferred。

    测试对象：capture_conflict_summary_v2。
    目的/目标：AC-SP2-07 — 记录 conflict 比较或 deferred reason。
    """
    from backend.app.ops.staged_pilot import (
        CONFLICT_CHECK_V2_JSON,
        capture_conflict_summary_v2,
    )

    payload = capture_conflict_summary_v2(
        evidence_dir=tmp_path,
        validation_report={
            "validations_v2": [
                {"source_id": "baostock"},
                {"source_id": "akshare"},
            ]
        },
    )
    assert payload["status"] in {
        "PRIMARY_VS_VALIDATION_COMPARE_DEFERRED",
        "NO_CONFLICT_CHECK_DEFERRED",
    }
    assert payload["reason"]
    assert (tmp_path / CONFLICT_CHECK_V2_JSON).is_file()


def test_mutationProof_verifiedOnlyWhenHashAndCountsUnchanged(tmp_path: Path) -> None:
    """覆盖范围：VERIFIED 仅当 hash 与 counts 均不变。

    测试对象：build_production_mutation_proof。
    目的/目标：AC-MUT-001 / R3Y-MUT-PROOF-001 — 收紧 proof_status 语义。
    """
    import duckdb

    from backend.app.db.migrate import apply_migrations
    from backend.app.ops.mutation_proof import build_production_mutation_proof

    db_path = tmp_path / "stable.duckdb"
    con = duckdb.connect(str(db_path))
    apply_migrations(con)
    con.close()
    before_bytes = db_path.read_bytes()
    before_counts = build_production_mutation_proof(db_path)["before_key_table_counts"]
    before_all = build_production_mutation_proof(db_path)["before_all_table_counts"]
    proof = build_production_mutation_proof(
        db_path,
        before_bytes=before_bytes,
        after_bytes=before_bytes,
        before_counts=before_counts,
        after_counts=before_counts,
        before_all_counts=before_all,
        after_all_counts=before_all,
    )
    assert proof["proof_status"] == "VERIFIED"
    assert proof["db_hash_unchanged"] is True
    assert proof["row_counts_unchanged"] is True


def test_mutationProof_mutationDetectedWhenKeyTableRowsChange(tmp_path: Path) -> None:
    """覆盖范围：KEY 表行数变异检测。

    测试对象：build_production_mutation_proof。
    目的/目标：AC-MUT-001 — KEY 表变异 → MUTATION_DETECTED。
    """
    import duckdb

    from backend.app.db.migrate import apply_migrations
    from backend.app.ops.mutation_proof import (
        all_table_row_counts,
        build_production_mutation_proof,
        key_table_row_counts,
    )

    db_path = tmp_path / "mutated-key.duckdb"
    con = duckdb.connect(str(db_path))
    apply_migrations(con)
    con.close()
    before_bytes = db_path.read_bytes()
    before_counts = key_table_row_counts(db_path)
    before_all = all_table_row_counts(db_path)
    con = duckdb.connect(str(db_path))
    con.execute(
        """
        INSERT INTO file_registry (
            file_id, file_type, source, local_path, content_hash,
            fetch_time, as_of_timestamp, parse_status, quality_flag
        ) VALUES (
            'mut-proof-test-file', 'json', 'test', '/tmp/x.json', 'hash',
            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'PARSED', 'STAGED'
        )
        """
    )
    con.close()
    proof = build_production_mutation_proof(
        db_path,
        before_bytes=before_bytes,
        before_counts=before_counts,
        before_all_counts=before_all,
    )
    assert proof["proof_status"] == "MUTATION_DETECTED"
    assert proof["row_counts_unchanged"] is False


def test_mutationProof_mutationDetectedWhenNonKeyTableRowCountChanges(
    tmp_path: Path,
) -> None:
    """覆盖范围：非 KEY 表行数变异检测。

    测试对象：build_production_mutation_proof。
    目的/目标：AC-MUT-001 — 非 KEY 表行数变 → MUTATION_DETECTED。
    """
    import duckdb

    from backend.app.db.migrate import apply_migrations
    from backend.app.ops.mutation_proof import (
        all_table_row_counts,
        build_production_mutation_proof,
        key_table_row_counts,
    )

    db_path = tmp_path / "mutated-nonkey.duckdb"
    con = duckdb.connect(str(db_path))
    apply_migrations(con)
    con.close()
    before_bytes = db_path.read_bytes()
    before_counts = key_table_row_counts(db_path)
    before_all = all_table_row_counts(db_path)
    con = duckdb.connect(str(db_path))
    con.execute(
        """
        INSERT INTO stg_foundation_smoke (
            instrument_id, trade_date, close, source_used, batch_id
        ) VALUES ('sh.600519', DATE '2026-06-01', 1.0, 'test', 'batch-1')
        """
    )
    con.close()
    proof = build_production_mutation_proof(
        db_path,
        before_bytes=before_bytes,
        before_counts=before_counts,
        before_all_counts=before_all,
    )
    assert proof["proof_status"] == "MUTATION_DETECTED"
    assert proof["db_hash_unchanged"] is False


def test_mutationProof_inconclusiveWhenHashChangesKeyCountUnchanged(
    tmp_path: Path,
) -> None:
    """覆盖范围：hash 变、KEY count 不变 → INCONCLUSIVE。

    测试对象：build_production_mutation_proof。
    目的/目标：AC-MUT-001 — 不得将 hash-only 漂移标为 VERIFIED。
    """
    import duckdb

    from backend.app.db.migrate import apply_migrations
    from backend.app.ops.mutation_proof import (
        all_table_row_counts,
        build_production_mutation_proof,
        key_table_row_counts,
    )

    db_path = tmp_path / "hash-only.duckdb"
    con = duckdb.connect(str(db_path))
    apply_migrations(con)
    con.close()
    before_bytes = db_path.read_bytes()
    before_counts = key_table_row_counts(db_path)
    before_all = all_table_row_counts(db_path)
    mutated = bytearray(before_bytes)
    mutated[-1] ^= 0x01
    proof = build_production_mutation_proof(
        db_path,
        before_bytes=bytes(before_bytes),
        after_bytes=bytes(mutated),
        before_counts=before_counts,
        after_counts=before_counts,
        before_all_counts=before_all,
        after_all_counts=before_all,
    )
    assert proof["proof_status"] == "INCONCLUSIVE"
    assert proof["db_hash_unchanged"] is False
    assert proof["row_counts_unchanged"] is True


def test_stagedPilotV2_closeoutRequiresHashAndRowCountsUnchanged(tmp_path: Path) -> None:
    """覆盖范围：closeout AUD-08 hash∧counts gate。

    测试对象：build_pilot_v2_closeout。
    目的/目标：AC-MUT-001 / AUD-08 — closeout 须 db_hash_unchanged∧row_counts_unchanged。
    """
    from backend.app.ops.staged_pilot import build_pilot_v2_closeout

    closeout = build_pilot_v2_closeout(
        evidence_dir=tmp_path,
        mutation_proof={
            "proof_status": "VERIFIED",
            "db_hash_unchanged": True,
            "row_counts_unchanged": True,
        },
    )
    assert closeout["db_hash_unchanged"] is True
    assert closeout["row_counts_unchanged"] is True
    assert closeout["closeout_pass"] is True

    blocked = build_pilot_v2_closeout(
        evidence_dir=tmp_path,
        mutation_proof={
            "proof_status": "MUTATION_DETECTED",
            "db_hash_unchanged": False,
            "row_counts_unchanged": False,
        },
    )
    assert blocked["closeout_pass"] is False


def test_stagedPilotV2_closeoutMatrix_allSourcesClassified(tmp_path: Path) -> None:
    """覆盖范围：closeout per-source expand/re-defer 矩阵。

    测试对象：build_pilot_v2_closeout。
    目的/目标：AC-SP2-09 — 每源 expand/retry/re-defer/block 分类完整。
    """
    from backend.app.ops.staged_pilot import (
        CLOSEOUT_V2_JSON,
        V2_SOURCE_CLOSEOUT_IDS,
        build_pilot_v2_closeout,
        capture_akshare_validation_taxonomy_v2,
        capture_validation_report_v2,
    )

    capture_akshare_validation_taxonomy_v2(evidence_dir=tmp_path)
    capture_validation_report_v2(
        evidence_dir=tmp_path,
        raw_manifest={
            "fetches": [
                {
                    "pilot_request_id": "v2-baostock",
                    "request": {"source_id": "baostock"},
                    "fetch_result": {"status": "SUCCESS", "row_count": 1, "raw_file_paths": []},
                }
            ]
        },
    )
    closeout = build_pilot_v2_closeout(
        evidence_dir=tmp_path,
        mutation_proof={
            "proof_status": "INCONCLUSIVE",
            "db_hash_unchanged": None,
            "row_counts_unchanged": None,
            "reason": "production_db_file_missing",
        },
    )
    assert set(closeout["per_source"]) == set(V2_SOURCE_CLOSEOUT_IDS)
    for decision in closeout["per_source"].values():
        assert decision in {"expand", "retry", "re-defer", "block"}
    assert closeout["production_live_readiness_claim"] is False
    assert closeout["sandbox_clean_write_rehearsal"] is False
    assert closeout["closeout_pass"] is False
    assert closeout["db_hash_unchanged"] is None
    assert closeout["row_counts_unchanged"] is None
    assert closeout["mutation_proof_reason"] == "production_db_file_missing"
    written = json.loads((tmp_path / CLOSEOUT_V2_JSON).read_text(encoding="utf-8"))
    assert written["db_hash_unchanged"] is None
    assert written["row_counts_unchanged"] is None
    assert (tmp_path / CLOSEOUT_V2_JSON).is_file()


def test_stagedPilotV2_closeoutThreeStateSemantics(tmp_path: Path) -> None:
    """覆盖范围：closeout hash/count 三态序列化。

    测试对象：build_pilot_v2_closeout。
    目的/目标：OOB-1 — None 不得 coerce 为 false；gate 仍要求 is True。
    验证点：INCONCLUSIVE+None→null；MUTATION_DETECTED+False→false。
    失败含义：closeout 与 mutation_proof markdown 语义再次分叉。
    """
    from backend.app.ops.staged_pilot import build_pilot_v2_closeout

    inconclusive = build_pilot_v2_closeout(
        evidence_dir=tmp_path,
        mutation_proof={
            "proof_status": "INCONCLUSIVE",
            "db_hash_unchanged": None,
            "row_counts_unchanged": None,
        },
    )
    assert inconclusive["closeout_pass"] is False
    assert inconclusive["db_hash_unchanged"] is None

    detected = build_pilot_v2_closeout(
        evidence_dir=tmp_path,
        mutation_proof={
            "proof_status": "MUTATION_DETECTED",
            "db_hash_unchanged": False,
            "row_counts_unchanged": False,
        },
    )
    assert detected["db_hash_unchanged"] is False
    assert detected["row_counts_unchanged"] is False

