"""Batch 2.75 live pilot gate tests — fail-closed orchestration evidence."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.contract_gate_support import PROJECT_ROOT, trellis_task_dir

BATCH275_TASK_SLUG = "06-21-round3-batch2-75-live-pilot"
TASK_DIR = trellis_task_dir(BATCH275_TASK_SLUG)
EVIDENCE_DIR = TASK_DIR / "execute-evidence"

TRACKED_IDS = (
    "R3-B2.75-01",
    "GLOBAL-P2-01",
    "B2.5-O-05",
    "R3-B25-PERF-BUDGET-01",
    "R3-B25-HYG-03",
)

REGISTRY_PATHS = (
    PROJECT_ROOT / "docs/AUDIT_DEFERRED_REGISTRY.md",
    PROJECT_ROOT / "docs/UNRESOLVED_ISSUES_REGISTRY.md",
    PROJECT_ROOT / "docs/RESOLVED_ISSUES_REGISTRY.md",
    PROJECT_ROOT / "docs/quality/ROUND3_BATCH25_PENDING_FIX_REGISTRY.md",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing expected artifact: {path}"
    return path.read_text(encoding="utf-8")


def test_livePilot_phaseMinus1_registryReconciliationRequired() -> None:
    """Phase -1 must reconcile five tracked IDs against registries before pilot work."""
    reconciliation = EVIDENCE_DIR / "phase_minus1_reconciliation.md"
    registry_read = EVIDENCE_DIR / "phase-1-registry-read.txt"
    assert reconciliation.is_file(), "phase_minus1_reconciliation.md required"
    assert registry_read.is_file(), "phase-1-registry-read.txt required"

    text = _read(reconciliation)
    for item_id in TRACKED_IDS:
        assert item_id in text, f"reconciliation must map tracked ID {item_id}"

    assert "not-in-scope" in text.lower() or "out of scope" in text.lower()
    assert "R2b" in text or "ingestion split" in text.lower()

    read_log = _read(registry_read)
    for registry_path in REGISTRY_PATHS:
        rel = registry_path.relative_to(PROJECT_ROOT).as_posix()
        assert rel in read_log, f"registry read log must include {rel}"

    round3_map = _read(PROJECT_ROOT / "ROUND3_BATCH_IMPLEMENTATION_MAP.md")
    assert "R3-B2.75-PROD-LIVE-PILOT" in round3_map
    assert "Batch 2.75" in round3_map

    # AC-PM2: must not reopen resolved planning-only rows as live PASS
    resolved = _read(PROJECT_ROOT / "docs/RESOLVED_ISSUES_REGISTRY.md")
    assert "R3-B2.75-PLAN-01" in resolved
    assert "Does not close `R3-B2.75-01`" in resolved

    pending = _read(PROJECT_ROOT / "docs/quality/ROUND3_BATCH25_PENDING_FIX_REGISTRY.md")
    for item_id in ("R3-B2.75-01", "GLOBAL-P2-01", "B2.5-O-05"):
        assert item_id in pending, f"pending fix registry must reference {item_id}"


def test_livePilot_missingAuthorization_blocksBeforeFetch() -> None:
    """Missing authorization evidence must block before any adapter fetch."""
    from backend.app.ops.live_pilot import (
        LivePilotAuthorizationError,
        LivePilotRequest,
        run_live_pilot_raw_only,
    )

    request = LivePilotRequest(
        source_id="baostock",
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        symbols_or_indicators=("sh.600519",),
        date_window="recent 5 trading days",
        max_rows=10,
        authorization_evidence="docs/quality/nonexistent_batch275_authorization.md",
    )
    fetch_called = {"value": False}

    def _track_fetch(*_args, **_kwargs):
        fetch_called["value"] = True
        raise AssertionError("fetch must not be called without authorization")

    with patch(
        "backend.app.datasources.service.DataSourceService.fetch",
        side_effect=_track_fetch,
    ):
        with pytest.raises(LivePilotAuthorizationError):
            run_live_pilot_raw_only(
                request,
                sandbox_root=PROJECT_ROOT / ".audit-sandbox/batch275-live-pilot",
            )
    assert fetch_called["value"] is False


def test_livePilot_disabledSource_blocksBeforeFetch() -> None:
    """Disabled sources (e.g. qmt_xtdata) must block before fetch even with auth file present."""
    from backend.app.ops.live_pilot import (
        LivePilotDisabledSourceError,
        LivePilotRequest,
        run_live_pilot_raw_only,
    )

    request = LivePilotRequest(
        source_id="qmt_xtdata",
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        symbols_or_indicators=("sh.600519",),
        date_window="recent 5 trading days",
        max_rows=10,
        authorization_evidence="docs/quality/batch275_user_authorization_2026-06-21.md",
    )
    fetch_called = {"value": False}

    def _track_fetch(*_args, **_kwargs):
        fetch_called["value"] = True
        raise AssertionError("fetch must not be called for disabled source")

    with patch(
        "backend.app.datasources.service.DataSourceService.fetch",
        side_effect=_track_fetch,
    ):
        with pytest.raises(LivePilotDisabledSourceError):
            run_live_pilot_raw_only(
                request,
                sandbox_root=PROJECT_ROOT / ".audit-sandbox/batch275-live-pilot",
            )
    assert fetch_called["value"] is False


def test_livePilot_authorization_approvedRequestPassesGate() -> None:
    """Approved baostock request with valid authorization evidence passes Phase 0 gate."""
    from backend.app.ops.live_pilot import LivePilotRequest, validate_authorization

    request = LivePilotRequest(
        source_id="baostock",
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        symbols_or_indicators=("sh.600519",),
        date_window="recent 5 trading days",
        max_rows=10,
        authorization_evidence="docs/quality/batch275_user_authorization_2026-06-21.md",
    )
    validate_authorization(request)


def test_livePilot_authorization_recordDocumentsSourceRiskRationale() -> None:
    """Phase 0 evidence must document why baostock/akshare are lower risk than QMT/FRED."""
    record = EVIDENCE_DIR / "phase0_authorization_record.md"
    assert record.is_file(), "phase0_authorization_record.md required"
    text = _read(record)
    assert "baostock" in text.lower()
    assert "akshare" in text.lower()
    for riskier in ("qmt", "fred", "yahoo"):
        assert riskier in text.lower(), f"source risk rationale must mention {riskier}"
    auth_rel = "docs/quality/batch275_user_authorization_2026-06-21.md"
    assert auth_rel in text


def test_livePilot_phase1Baseline_readOnly(tmp_path: Path) -> None:
    """Phase 1 must capture read-only baseline inventory with zero DB mutation."""
    import duckdb

    from backend.app.db.migrate import apply_migrations
    from backend.app.ops.db_inspector import REQUIRED_TOP_LEVEL_FIELDS
    from backend.app.ops.live_pilot import capture_phase1_baseline

    db = tmp_path / "quant_monitor.duckdb"
    data_root = tmp_path / "data"
    data_root.mkdir()
    con = duckdb.connect(str(db))
    apply_migrations(con)
    con.close()
    before_hash = db.read_bytes()

    out = tmp_path / "phase1-out"
    result = capture_phase1_baseline(
        db_path=db,
        data_root=data_root,
        evidence_dir=out,
    )

    assert db.read_bytes() == before_hash
    assert result["mutation_proof"]["db_hash_unchanged"] is True
    assert result["mutation_proof"]["phase1_zero_mutation"] is True

    inventory = result["inspect"]
    for field in REQUIRED_TOP_LEVEL_FIELDS:
        assert field in inventory
    assert inventory["mode"] == "read_only"
    assert inventory["db"]["read_only_open"] is True

    capability = result["capability_snapshot"]
    assert len(capability["pilot_requests"]) == 3
    request_keys = {
        (item["source_id"], item["data_domain"], item["operation"])
        for item in capability["pilot_requests"]
    }
    assert ("baostock", "cn_equity_daily_bar", "fetch_daily_bar") in request_keys
    assert ("akshare", "cn_equity_daily_bar", "fetch_daily_bar_validation") in request_keys
    assert ("akshare", "macro_supplementary", "fetch_macro_series") in request_keys

    for name in (
        "phase1_baseline_inventory.json",
        "phase1_baseline_inventory.md",
        "phase1_no_mutation_proof.md",
        "phase1_capability_snapshot.json",
    ):
        assert (out / name).is_file(), f"missing artifact {name}"

    task_inventory = EVIDENCE_DIR / "phase1_baseline_inventory.json"
    task_capability = EVIDENCE_DIR / "phase1_capability_snapshot.json"
    task_proof = EVIDENCE_DIR / "phase1_no_mutation_proof.md"
    assert task_inventory.is_file(), "execute-evidence phase1_baseline_inventory.json required"
    assert task_capability.is_file(), "execute-evidence phase1_capability_snapshot.json required"
    assert task_proof.is_file(), "execute-evidence phase1_no_mutation_proof.md required"


AUTH_EVIDENCE = "docs/quality/batch275_user_authorization_2026-06-21.md"


def test_livePilot_phase2RouteMatrix_threeRequests(tmp_path: Path) -> None:
    """Phase 2 dry-run route matrix for three authorized requests — no fetch."""
    from backend.app.ops.live_pilot import (
        approved_pilot_requests,
        capture_phase2_route_matrix,
    )

    fetch_called = {"value": False}

    def _track_fetch(*_args, **_kwargs):
        fetch_called["value"] = True
        raise AssertionError("Phase 2 must not invoke fetch")

    with patch(
        "backend.app.datasources.service.DataSourceService.fetch",
        side_effect=_track_fetch,
    ):
        result = capture_phase2_route_matrix(
            requests=approved_pilot_requests(),
            evidence_dir=tmp_path / "phase2-out",
            db_path=tmp_path / "unused.duckdb",
        )

    assert fetch_called["value"] is False
    assert result["dry_run"] is True
    assert len(result["previews"]) == 3
    for preview in result["previews"]:
        assert preview["explicit_source_route_status"] == "READY"
        assert preview["resource_guard_decision"] in {"OK", "PAUSE"}
        assert preview["route_plan"]["data_domain"]
        assert preview["route_plan"]["operation"]
        assert preview["request"]["authorization_evidence"] == AUTH_EVIDENCE

    matrix_path = EVIDENCE_DIR / "phase2_route_preview_matrix.json"
    assert matrix_path.is_file(), "execute-evidence phase2_route_preview_matrix.json required"
    payload = json.loads(matrix_path.read_text(encoding="utf-8"))
    assert payload["dry_run"] is True
    assert len(payload["previews"]) == 3
    assert payload.get("fred_primary_deferred") is True


def test_livePilot_phase2_previewIncludesResourceGuardDecision(tmp_path: Path) -> None:
    """Each route preview must include ResourceGuard decision snapshot."""
    from backend.app.ops.live_pilot import approved_pilot_requests, preview_live_pilot

    request = approved_pilot_requests()[0]
    preview = preview_live_pilot(request)
    assert "resource_guard_decision" in preview
    assert "resource_guard_reason" in preview
    assert preview["dry_run"] is True
    assert preview["explicit_source_route_status"] == "READY"


def test_livePilot_phase3_requiresHitlBeforeFetch(tmp_path: Path) -> None:
    """Phase 3 live fetch must fail without HITL confirmation file."""
    from backend.app.ops.live_pilot import (
        LivePilotAuthorizationError,
        approved_pilot_requests,
        run_live_pilot_raw_only,
    )

    out = tmp_path / "no-hitl"
    out.mkdir()
    request = approved_pilot_requests()[0]
    with pytest.raises(LivePilotAuthorizationError, match="HITL"):
        run_live_pilot_raw_only(
            replace(request, dry_run=False),
            sandbox_root=tmp_path / "sandbox",
            evidence_dir=out,
        )


def test_livePilot_phase3_rejectsFixtureFetchPort(tmp_path: Path) -> None:
    """StubFetchPort must not satisfy live pilot evidence requirements."""
    from backend.app.datasources.adapters.fetch_port import StubFetchPort
    from backend.app.ops.live_pilot import (
        LivePilotFixtureForbiddenError,
        _assert_live_fetch_port,
    )

    with pytest.raises(LivePilotFixtureForbiddenError):
        _assert_live_fetch_port(StubFetchPort(payload=b"{}"))


@pytest.mark.network
@pytest.mark.slow
def test_livePilot_phase3RawOnly_threeRequestsLive(tmp_path: Path) -> None:
    """Live sandbox raw-only fetch for three authorized requests (network)."""
    from backend.app.ops.live_pilot import (
        approved_pilot_requests,
        capture_phase3_raw_evidence,
    )

    sandbox = tmp_path / "live-sandbox"
    out = tmp_path / "phase3-out"
    out.mkdir()
    hitl_src = EVIDENCE_DIR / "phase3_hitl_user_confirmation.md"
    assert hitl_src.is_file()
    (out / "phase3_hitl_user_confirmation.md").write_text(
        hitl_src.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    result = capture_phase3_raw_evidence(
        requests=approved_pilot_requests(),
        sandbox_root=sandbox,
        evidence_dir=out,
    )
    assert len(result["fetches"]) == 3
    for item in result["fetches"]:
        assert item["fetch_result"]["status"] == "SUCCESS"
        assert item["fetch_result"]["row_count"] > 0
        assert item["fetch_result"]["content_hash"]
        proof = item["production_mutation_proof"]
        assert proof["db_hash_unchanged"] is True
        assert proof["row_counts_unchanged"] is True
        for path in item["fetch_result"]["raw_file_paths"]:
            assert str(sandbox.resolve()) in str(Path(path).resolve())


def test_livePilot_phase4Validation_noCleanWriteByDefault() -> None:
    """Phase 4 validation must default to allow_clean_write=false and perform no clean write."""
    from backend.app.ops.live_pilot import capture_task_phase4_validation_evidence

    result = capture_task_phase4_validation_evidence(EVIDENCE_DIR)
    assert result["allow_clean_write"] is False
    assert result["clean_write_performed"] is False

    report_path = EVIDENCE_DIR / "phase4_validation_report.json"
    proof_path = EVIDENCE_DIR / "phase4_no_production_mutation_proof.md"
    assert report_path.is_file()
    assert proof_path.is_file()

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["allow_clean_write"] is False
    for item in payload["validations"]:
        assert item.get("allow_clean_write") is False

    proof = proof_path.read_text(encoding="utf-8")
    assert "allow_clean_write" in proof
    assert "false" in proof.lower()


def test_livePilot_phase4Conflict_inspectOrNoConflict() -> None:
    """Phase 4 must emit conflict inspect text with explicit Request 2 sidecar boundary."""
    from backend.app.ops.live_pilot import capture_task_phase4_validation_evidence

    capture_task_phase4_validation_evidence(EVIDENCE_DIR)
    conflict_path = EVIDENCE_DIR / "phase4_conflict_inspect.txt"
    reconciliation_path = EVIDENCE_DIR / "phase3_request2_evidence_reconciliation.md"
    assert conflict_path.is_file()
    assert reconciliation_path.is_file()

    text = _read(conflict_path)
    assert "Request 2" in text
    assert "sidecar" in text.lower() or "informational" in text.lower()
    assert "NO_CONFLICT_INSPECT_REQUIRED_FOR_CLOSEOUT" in text or "Informational sidecar" in text

    report = json.loads(_read(EVIDENCE_DIR / "phase4_validation_report.json"))
    req2 = next(v for v in report["validations"] if v["pilot_request_id"] == "pilot-req-2")
    assert req2["status"] == "SOURCE_ENDPOINT_FAILURE"
    classification = req2["request2_endpoint_classification"]
    assert classification["closes_original_request2"] is False
    assert classification["supports_pilot_pass_raw_only"] is False


def test_livePilot_request2Reconciliation_requiredBeforePhase4() -> None:
    """Request 2 reconciliation artifact must exist and reference eastmoney verdict."""
    reconciliation = EVIDENCE_DIR / "phase3_request2_evidence_reconciliation.md"
    verdict = EVIDENCE_DIR / "eastmoney_stock_zh_a_hist_verdict.md"
    assert reconciliation.is_file()
    assert verdict.is_file()
    text = _read(reconciliation)
    assert "stock_zh_a_hist" in text
    assert "push2his.eastmoney.com" in text
    assert "stock_zh_a_daily" in text
    assert "sidecar" in text.lower()
    assert "PILOT_PASS_RAW_ONLY" in text
    assert "018C_tdx_pytdx_low_cost_probe.md" in text
