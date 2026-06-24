"""Staged pilot v3 tests — WL-driven model input expansion (B01-SP3)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from tests.contract_gate_support import PROJECT_ROOT

AUTH_PATH = "docs/quality/prompt14_user_authorization_2026-06-22.md"
SANDBOX_ROOT = PROJECT_ROOT / ".audit-sandbox/r3e-staged-pilot-v3-test"


def _mock_v3_fetch_item(request, *, sandbox_root: Path) -> dict:
    return {
        "pilot_request_id": f"v3-{request.source_id}",
        "request": {
            "source_id": request.source_id,
            "data_domain": request.data_domain,
            "operation": request.operation,
        },
        "fetch_result": {
            "run_id": f"fetch-{request.source_id}-v3",
            "content_hash": "abc123",
            "raw_file_paths": [],
            "row_count": 3,
            "status": "SUCCESS",
        },
        "staged_file_ids": ["file-v3-1"],
        "generated_at": "2026-06-25T00:00:00Z",
        "taxonomy_status": "SUCCESS",
    }


def test_v3_refuses_missing_whitelist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    覆盖范围：无 model input 白名单时 pilot v3 必须拒绝启动。
    测试对象：backend.app.ops.staged_pilot（v3 WL gate）。
    目的/目标：防止 hand-picked symbol 绕过 B01-WL。
    验证点：缺 specs/model_inputs 时 fail-closed。
    失败含义：无 WL 仍能跑 pilot，破坏 model-driven 边界。
    """
    from backend.app.ops import staged_pilot
    from backend.app.ops.staged_pilot import (
        StagedPilotAuthorizationError,
        assert_model_inputs_whitelist_present,
        write_pilot_v3_caps,
    )

    missing_dir = tmp_path / "no_model_inputs"
    monkeypatch.setattr(staged_pilot, "MODEL_INPUTS_DIR", missing_dir)

    with pytest.raises(StagedPilotAuthorizationError, match="whitelist"):
        assert_model_inputs_whitelist_present()

    with pytest.raises(StagedPilotAuthorizationError, match="whitelist"):
        write_pilot_v3_caps(tmp_path)


def test_v3_whitelist_caps_enforced() -> None:
    """
    覆盖范围：白名单 symbol/row 超 cap 时拒绝。
    测试对象：v3 caps + WL loader。
    目的/目标：防止全市场/超量拉取。
    验证点：超 cap 抛 StagedPilotAuthorizationError 或等价 FAIL。
    失败含义：资源护栏失效。
    """
    from backend.app.ops.staged_pilot import (
        StagedPilotAuthorizationError,
        approved_pilot_v3_requests,
        validate_pilot_v3_authorization,
    )

    approved = approved_pilot_v3_requests()[0]
    over_symbols = replace(
        approved,
        symbols_or_indicators=approved.symbols_or_indicators + ("sh.999999",),
    )
    with pytest.raises(StagedPilotAuthorizationError, match="whitelist"):
        validate_pilot_v3_authorization(over_symbols)

    over_rows = replace(approved, max_rows=5000)
    with pytest.raises(StagedPilotAuthorizationError, match="max_rows"):
        validate_pilot_v3_authorization(over_rows)


def test_v3_baostock_manifest_fields(tmp_path: Path) -> None:
    """
    覆盖范围：baostock v3 mock fetch 产出 manifest 必填字段。
    测试对象：baostock raw/staging manifest v3。
    目的/目标：证据链可供 DH2/L5 下游引用。
    验证点：source_fetch_id、content_hash、as_of 存在。
    失败含义：证据不可审计。
    """
    from backend.app.ops.staged_pilot import (
        RAW_MANIFEST_V3_BAOSTOCK_JSON,
        capture_baostock_evidence_v3,
        pilot_v3_caps_payload,
    )

    payload = capture_baostock_evidence_v3(
        evidence_dir=tmp_path,
        fetch_runner=_mock_v3_fetch_item,
    )
    entry = payload["manifest_entries"][0]
    assert entry["source_fetch_id"] == "fetch-baostock-v3"
    assert entry["content_hash"] == "abc123"
    assert entry["as_of_timestamp"]
    assert payload["whitelist_ref"]["aggregate_sha256"]
    assert payload["required_fields_present"] is True
    assert (tmp_path / RAW_MANIFEST_V3_BAOSTOCK_JSON).is_file()
    caps = pilot_v3_caps_payload()
    assert caps["model_driven"] is True
    assert caps["whitelist_ref"]["files"]


def test_v3_cninfo_rejects_pdf_expansion() -> None:
    """
    覆盖范围：cninfo 拒绝 PDF/full-text 扩张。
    测试对象：cninfo metadata pilot 路径。
    目的/目标：遵守 metadata-only 边界。
    验证点：PDF op 被拒绝。
    失败含义：bulk PDF 下载风险。
    """
    from backend.app.ops.staged_pilot import (
        StagedPilotAuthorizationError,
        StagedPilotRequest,
        validate_pilot_v3_authorization,
    )

    pdf_request = StagedPilotRequest(
        source_id="cninfo",
        data_domain="cn_filings",
        operation="fetch_filing_pdf",
        symbols_or_indicators=("sh.600000",),
        date_window="recent 30 calendar days",
        max_rows=10,
        authorization_evidence=AUTH_PATH,
    )
    with pytest.raises(StagedPilotAuthorizationError, match="PDF"):
        validate_pilot_v3_authorization(pdf_request)


def test_v3_akshare_validation_only_not_primary(tmp_path: Path) -> None:
    """
    覆盖范围：akshare 不得成为 Primary。
    测试对象：route preview + v3 request envelope。
    目的/目标：enforce validation-only（hardening §5）。
    验证点：primary 选择失败或 validation op only。
    失败含义：AkShare 误升为 primary raw fact。
    """
    from backend.app.ops.staged_pilot import (
        AKSHARE_TAXONOMY_V3_JSON,
        StagedPilotAuthorizationError,
        StagedPilotRequest,
        assert_akshare_not_primary_for_daily_bar,
        capture_akshare_validation_taxonomy_v3,
        validate_pilot_v3_authorization,
    )

    primary_attempt = StagedPilotRequest(
        source_id="akshare",
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        symbols_or_indicators=("sh.600000", "sz.000001"),
        date_window="recent 60 trading days",
        max_rows=100,
        authorization_evidence=AUTH_PATH,
    )
    with pytest.raises(StagedPilotAuthorizationError, match="validation-only"):
        validate_pilot_v3_authorization(primary_attempt)

    assert_akshare_not_primary_for_daily_bar()

    payload = capture_akshare_validation_taxonomy_v3(evidence_dir=tmp_path)
    assert payload["validation_only"] is True
    assert payload["primary_forbidden"] is True
    assert (tmp_path / AKSHARE_TAXONOMY_V3_JSON).is_file()


def test_v3_conflict_dry_run_no_clean_write(tmp_path: Path) -> None:
    """
    覆盖范围：conflict dry-run 写 summary 不写 clean 表。
    测试对象：source_conflict dry-run + v3 closeout。
    目的/目标：冲突不得自动覆盖 production clean。
    验证点：summary JSON 存在；clean write 未发生。
    失败含义：冲突误写库。
    """
    from backend.app.ops.staged_pilot import (
        CONFLICT_CHECK_V3_JSON,
        capture_conflict_summary_v3,
    )

    write_called = {"value": False}

    def _track_write(*_args, **_kwargs):
        write_called["value"] = True
        raise AssertionError("clean write must not run in v3 conflict dry-run")

    with patch("backend.app.db.write_manager.WriteManager.write", side_effect=_track_write):
        payload = capture_conflict_summary_v3(evidence_dir=tmp_path)

    assert payload["dry_run"] is True
    assert payload["clean_write_attempted"] is False
    assert payload["conflict_count"] >= 0
    assert (tmp_path / CONFLICT_CHECK_V3_JSON).is_file()
    assert write_called["value"] is False


def test_v3_closeout_readiness_matrix(tmp_path: Path) -> None:
    """
    覆盖范围：closeout 含 readiness matrix 与 no-mutation 字段。
    测试对象：build_pilot_v3_closeout（待实现）。
    目的/目标：Batch 01 可读的 source readiness 输出。
    验证点：closeout 必填字段；无 production-live 声称。
    失败含义：无法判断下一 gate。
    """
    from backend.app.ops.staged_pilot import (
        AKSHARE_TAXONOMY_V3_JSON,
        CLOSEOUT_V3_JSON,
        REGISTRY_PROPOSED_DELTA_V3_YAML,
        SOURCE_READINESS_MATRIX_V3_MD,
        build_pilot_v3_closeout,
        capture_akshare_validation_taxonomy_v3,
        write_no_mutation_proof_v3,
    )

    capture_akshare_validation_taxonomy_v3(evidence_dir=tmp_path)
    mutation_proof = write_no_mutation_proof_v3(evidence_dir=tmp_path)
    closeout = build_pilot_v3_closeout(
        evidence_dir=tmp_path,
        mutation_proof=mutation_proof,
    )

    assert closeout["production_live_readiness_claim"] is False
    assert closeout["model_driven"] is True
    assert closeout["whitelist_ref"]["aggregate_sha256"]
    assert set(closeout["per_source"]) == {"baostock", "cninfo", "akshare"}
    assert (tmp_path / CLOSEOUT_V3_JSON).is_file()
    assert (tmp_path / SOURCE_READINESS_MATRIX_V3_MD).is_file()
    assert (tmp_path / REGISTRY_PROPOSED_DELTA_V3_YAML).is_file()
    assert (tmp_path / AKSHARE_TAXONOMY_V3_JSON).is_file()
