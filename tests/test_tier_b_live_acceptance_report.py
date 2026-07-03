"""M-DATA-03 AC-7 — tier_b_live_acceptance --report tests."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import pytest
import yaml

from backend.app.config import PROJECT_ROOT
from backend.app.datasources.live_tier_router import TIER_B_SOURCES
from backend.app.ops.tier_b_live_acceptance import (
    MANIFEST_FILENAME,
    _acceptance_report_exit_code,
    assert_isolated_live_data_root,
    classify_source_report_failure,
    fail_external_adr_ref,
    run_acceptance_report,
    source_bindings,
)
from backend.app.ops.tier_b_live_validation_dispatch import LiveValidationOutcome
from tests.contract_gate_support import PROJECT_ROOT as TEST_PROJECT_ROOT

EVIDENCE_CONTRACT = TEST_PROJECT_ROOT / "specs/contracts/live_tier_b_evidence_v1.yaml"


@pytest.fixture
def isolated_tier_b_data_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolated Tier B sandbox under .audit-sandbox/m-data-03/tier-b."""
    root = (
        PROJECT_ROOT
        / ".audit-sandbox"
        / "m-data-03"
        / "tier-b"
        / f"pytest-{tmp_path.name}-{uuid.uuid4().hex[:8]}"
    )
    root.mkdir(parents=True, exist_ok=True)
    resolved = assert_isolated_live_data_root(root)
    monkeypatch.setenv("QMD_DATA_ROOT", str(resolved))
    monkeypatch.delenv("DATA_ROOT", raising=False)
    return resolved


def _load_contract() -> dict[str, Any]:
    return yaml.safe_load(EVIDENCE_CONTRACT.read_text(encoding="utf-8")) or {}


def _mock_outcome(source_id: str) -> LiveValidationOutcome:
    binding = source_bindings()[source_id]
    return LiveValidationOutcome(
        source_id=source_id,
        fetch_status="SUCCESS",
        row_count=2,
        detail="mock report run",
        inspect_status="NOT_APPLICABLE",
        clean_table=binding["clean_table"],
        fetch_provenance=str(binding.get("fetch_provenance", "mock_replay")),
    )


def _mock_f0_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "backend.app.ops.tier_b_live_acceptance._run_f0_data_health",
        lambda *_a, **_k: ("PASS", "mock f0 for report test"),
    )


def _set_tier_b_gated_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Dummy env for product_live_gated sources in full 10/10 report tests."""
    monkeypatch.setenv("THS_IFIND_LICENSE_ARTIFACT", "/tmp/ths-license-fixture")
    monkeypatch.setenv("QMT_XTDATA_AUTHORIZED", "1")
    monkeypatch.setenv("QMT_XQSHARE_AUTHORIZED", "1")
    monkeypatch.setenv("XQSHARE_REMOTE_HOST", "127.0.0.1")
    monkeypatch.setenv("XQSHARE_REMOTE_PORT", "18888")


def _patch_mock_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    def _mock_validation(source_id: str, _data_root: Path) -> LiveValidationOutcome:
        return _mock_outcome(source_id)

    monkeypatch.setattr(
        "backend.app.ops.tier_b_live_acceptance.run_tier_b_live_validation",
        _mock_validation,
    )
    monkeypatch.setattr(
        "backend.app.ops.tier_b_live_validation_dispatch.run_tier_b_live_validation",
        _mock_validation,
    )


def test_reportRun_writesTenManifests(
    isolated_tier_b_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """覆盖范围：一次 --report run 落盘 10 份 manifest
    测试对象：run_acceptance_report
    目的/目标：全量 report 为每 Tier B 源写出 live_tier_b_evidence_manifest.json
    验证点：10 个 manifest 文件；每行 evidence_manifest_path 指向存在文件
    失败含义：统一验收层缺 per-source 证据工件
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    _set_tier_b_gated_env(monkeypatch)
    _patch_mock_validation(monkeypatch)
    _mock_f0_pass(monkeypatch)

    report_path = tmp_path / "tier-b-report.json"
    exit_code = run_acceptance_report(
        report_path,
        data_root=isolated_tier_b_data_root,
    )
    assert exit_code == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert len(report["sources"]) == 10
    manifest_paths: list[Path] = []
    for row in report["sources"]:
        rel = row["evidence_manifest_path"]
        manifest_path = isolated_tier_b_data_root / rel
        assert manifest_path.is_file(), f"missing manifest for {row['source_id']}"
        assert manifest_path.name == MANIFEST_FILENAME
        manifest_paths.append(manifest_path)
    assert len(manifest_paths) == 10
    assert frozenset(p.parent.name for p in manifest_paths) == TIER_B_SOURCES


def test_acceptanceReport_hasContractTopLevelFields(
    isolated_tier_b_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """覆盖范围：acceptance_report.required_top_level_fields
    测试对象：run_acceptance_report JSON 输出
    目的/目标：report 工件符合 live_tier_b_evidence_v1 acceptance_report 段
    验证点：顶层字段齐全；summary 含 total/passed/failed_* 计数；每行含 fetch_provenance
    失败含义：CI/人工无法消费结构化验收报告
    """
    contract = _load_contract()
    required_top = contract["acceptance_report"]["required_top_level_fields"]
    per_source_fields = contract["acceptance_report"]["per_source_row_fields"]
    summary_fields = contract["acceptance_report"]["summary_fields"]

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    _set_tier_b_gated_env(monkeypatch)
    _patch_mock_validation(monkeypatch)
    _mock_f0_pass(monkeypatch)

    report_path = tmp_path / "tier-b-shape.json"
    run_acceptance_report(report_path, data_root=isolated_tier_b_data_root)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    for field in required_top:
        assert field in report
    for field in summary_fields:
        assert field in report["summary"]
    assert report["summary"]["total"] == 10
    for row in report["sources"]:
        for field in per_source_fields:
            assert field in row
        assert row["fetch_provenance"] in {"mock_replay", "product_live_gated"}


def test_cliReportFlag_writesReportViaMain(
    isolated_tier_b_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """覆盖范围：scripts/tier_b_live_acceptance.py --report
    测试对象：tier_b_live_acceptance.main --report
    目的/目标：CLI 入口可触发 report 写出并 exit 0（mock validation）
    验证点：main 返回 0；report 文件存在且 sources 长度 10
    失败含义：运维/CI 无法通过 CLI 产出验收 JSON
    """
    from scripts.tier_b_live_acceptance import main

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    _set_tier_b_gated_env(monkeypatch)
    _patch_mock_validation(monkeypatch)
    _mock_f0_pass(monkeypatch)

    report_path = tmp_path / "cli-report.json"
    exit_code = main(
        [
            "--report",
            str(report_path),
            "--data-root",
            str(isolated_tier_b_data_root),
        ]
    )
    assert exit_code == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert len(report["sources"]) == 10


def test_reportRun_e2InspectNotApplicableForTenSources(
    isolated_tier_b_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """覆盖范围：--report 全量 10 源 E2 inspect 不变量
    测试对象：run_acceptance_report per-source e2_inspect_status
    目的/目标：Tier B validation_fetch 轨 E2 恒为 NOT_APPLICABLE
    验证点：10 行 e2_inspect_status == NOT_APPLICABLE；manifest acceptance 同步
    失败含义：Tier B 误跑 incremental E2 inspect
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    _set_tier_b_gated_env(monkeypatch)
    _patch_mock_validation(monkeypatch)
    _mock_f0_pass(monkeypatch)

    report_path = tmp_path / "tier-b-e2-report.json"
    exit_code = run_acceptance_report(
        report_path,
        data_root=isolated_tier_b_data_root,
    )
    assert exit_code == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    for row in report["sources"]:
        assert row["e2_inspect_status"] == "NOT_APPLICABLE", row["source_id"]
        manifest_path = isolated_tier_b_data_root / row["evidence_manifest_path"]
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["acceptance"]["e2_inspect_status"] == "NOT_APPLICABLE"


def test_reportRun_writesFailureArtifactOnFixableFail(
    isolated_tier_b_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """覆盖范围：contract failure_artifact
    测试对象：run_acceptance_report exit 1
    目的/目标：FAIL_FIXABLE 时写出 tier_b_live_acceptance_failure_{run_id}.json
    验证点：exit 1；artifact 含 exit_code/first_failure_source_id/failure_detail
    失败含义：CI 无法在 workflow failure 时上传诊断工件
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    _set_tier_b_gated_env(monkeypatch)

    def _fail_validation(source_id: str, _data_root: Path) -> LiveValidationOutcome:
        outcome = _mock_outcome(source_id)
        return LiveValidationOutcome(
            source_id=source_id,
            fetch_status="FAILED",
            row_count=0,
            detail="simulated validation failure",
            inspect_status=outcome.inspect_status,
            clean_table=outcome.clean_table,
            fetch_provenance=outcome.fetch_provenance,
        )

    monkeypatch.setattr(
        "backend.app.ops.tier_b_live_acceptance.run_tier_b_live_validation",
        _fail_validation,
    )
    _mock_f0_pass(monkeypatch)

    report_path = tmp_path / "tier-b-fail-report.json"
    exit_code = run_acceptance_report(
        report_path,
        data_root=isolated_tier_b_data_root,
    )
    assert exit_code == 1
    artifacts = list(tmp_path.glob("tier_b_live_acceptance_failure_*.json"))
    assert len(artifacts) == 1
    artifact = json.loads(artifacts[0].read_text(encoding="utf-8"))
    assert artifact["exit_code"] == 1
    assert artifact["first_failure_source_id"] is not None
    assert artifact["failure_detail"]
    for field in (
        "command",
        "schema_version",
        "data_root",
        "generated_at",
        "sources",
        "summary",
    ):
        assert field in artifact


def test_reportRun_zeroRowsFails(
    isolated_tier_b_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """覆盖范围：--report 路径 zero-row 守卫
    测试对象：run_acceptance_report per-source disposition
    目的/目标：SUCCESS + 0 row 不得 pass
    验证点：yahoo_finance 行 disposition==fail；failure_class==FAIL_FIXABLE
    失败含义：report 路径误标 pass，validation_fetch 假绿
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")

    def _empty_success(_source_id: str, _data_root: Path) -> LiveValidationOutcome:
        return LiveValidationOutcome(
            source_id="yahoo_finance",
            fetch_status="SUCCESS",
            row_count=0,
            detail="mock success with no rows",
            inspect_status="NOT_APPLICABLE",
            clean_table="security_bar_1d",
            fetch_provenance="mock_replay",
        )

    monkeypatch.setattr(
        "backend.app.ops.tier_b_live_acceptance.run_tier_b_live_validation",
        _empty_success,
    )
    _mock_f0_pass(monkeypatch)

    report_path = tmp_path / "zero-row-report.json"
    exit_code = run_acceptance_report(
        report_path,
        source_id="yahoo_finance",
        data_root=isolated_tier_b_data_root,
    )
    assert exit_code == 1
    report = json.loads(report_path.read_text(encoding="utf-8"))
    row = report["sources"][0]
    assert row["disposition"] == "fail"
    assert row["failure_class"] == "FAIL_FIXABLE"


def test_reportRun_f0BlockedFailsFixable(
    isolated_tier_b_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """覆盖范围：F0 BLOCKED 须 FAIL_FIXABLE
    测试对象：run_acceptance_report per-source disposition
    目的/目标：fetch 成功但 data-health BLOCKED 不得 pass
    验证点：disposition fail；failure_detail 含 BLOCKED
    失败含义：F0 BLOCKED 被静默放行
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    _set_tier_b_gated_env(monkeypatch)
    _patch_mock_validation(monkeypatch)
    monkeypatch.setattr(
        "backend.app.ops.tier_b_live_acceptance._run_f0_data_health",
        lambda *_a, **_k: ("BLOCKED", "staged-only gate"),
    )

    report_path = tmp_path / "f0-blocked-report.json"
    exit_code = run_acceptance_report(
        report_path,
        source_id="yahoo_finance",
        data_root=isolated_tier_b_data_root,
    )
    assert exit_code == 1
    report = json.loads(report_path.read_text(encoding="utf-8"))
    row = report["sources"][0]
    assert row["disposition"] == "fail"
    assert row["failure_class"] == "FAIL_FIXABLE"
    assert "BLOCKED" in row["failure_detail"]


def test_classifySourceReportFailure_zeroRowsFails() -> None:
    """覆盖范围：SUCCESS + 0 row 不得 PASS
    测试对象：classify_source_report_failure
    目的/目标：validation_fetch 零行须 FAIL_FIXABLE
    验证点：disposition fail；failure_class FAIL_FIXABLE
    失败含义：0 行静默 PASS 回归
    """
    outcome = LiveValidationOutcome(
        source_id="yahoo_finance",
        fetch_status="SUCCESS",
        row_count=0,
        detail="zero rows",
        inspect_status="NOT_APPLICABLE",
        clean_table="security_bar_1d",
    )
    disposition, failure_class, adr_ref = classify_source_report_failure(outcome)
    assert disposition == "fail"
    assert failure_class == "FAIL_FIXABLE"
    assert adr_ref is None


def test_classifySourceReportFailure_mapsAllExternalFetchStatuses() -> None:
    """覆盖范围：FAIL_EXTERNAL 分类与契约 ADR
    测试对象：classify_source_report_failure
    目的/目标：各外部 fetch 状态映射 FAIL_EXTERNAL + 契约 adr_ref
    验证点：RATE_LIMITED/NETWORK_ERROR/NOT_PUBLISHED_YET/DISABLED_SOURCE/AUTH_FAILED 均带 adr
    失败含义：外部失败分类或 ADR SSOT 不完整
    """
    adr = fail_external_adr_ref()
    for fetch_status in (
        "RATE_LIMITED",
        "NETWORK_ERROR",
        "NOT_PUBLISHED_YET",
        "DISABLED_SOURCE",
        "AUTH_FAILED",
    ):
        outcome = LiveValidationOutcome(
            source_id="yahoo_finance",
            fetch_status=fetch_status,
            row_count=0,
            detail=f"fetch={fetch_status}",
            inspect_status="NOT_APPLICABLE",
            clean_table="security_bar_1d",
        )
        disposition, failure_class, adr_ref = classify_source_report_failure(outcome)
        assert disposition == "fail"
        assert failure_class == "FAIL_EXTERNAL"
        assert adr_ref == adr


def test_acceptanceReportExitCode_externalRowsRequireContractAdr() -> None:
    """覆盖范围：contract exit_codes 行级 ADR 判定
    测试对象：_acceptance_report_exit_code
    目的/目标：FAIL_EXTERNAL 行须带契约 adr_ref 才 exit 0
    验证点：有 adr → 0；缺 adr → 1
    失败含义：exit 码逻辑与 fail_external_requires_adr 不一致
    """
    adr = fail_external_adr_ref()
    rows_ok = [{"failure_class": "FAIL_EXTERNAL", "adr_ref": adr}]
    rows_bad = [{"failure_class": "FAIL_EXTERNAL", "adr_ref": None}]
    summary_ok = {"failed_fixable": 0, "failed_external": 1}
    summary_bad = {"failed_fixable": 0, "failed_external": 1}
    assert _acceptance_report_exit_code(rows_ok, summary_ok) == 0
    assert _acceptance_report_exit_code(rows_bad, summary_bad) == 1


def test_reportRun_exit0WhenExternalWithAdr(
    isolated_tier_b_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """覆盖范围：contract exit_codes FAIL_EXTERNAL + adr_ref
    测试对象：run_acceptance_report exit code
    目的/目标：FAIL_EXTERNAL 且 adr_ref 有效时 exit 0
    验证点：exit 0；summary.failed_external==1；row.adr_ref==ADR-034
    失败含义：外部失败 ADR 合并路径未实现
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")

    def _rate_limited(_source_id: str, _data_root: Path) -> LiveValidationOutcome:
        return LiveValidationOutcome(
            source_id="yahoo_finance",
            fetch_status="RATE_LIMITED",
            row_count=0,
            detail="vendor rate limit",
            inspect_status="NOT_APPLICABLE",
            clean_table="security_bar_1d",
            fetch_provenance="mock_replay",
        )

    monkeypatch.setattr(
        "backend.app.ops.tier_b_live_acceptance.run_tier_b_live_validation",
        _rate_limited,
    )

    report_path = tmp_path / "external-adr-report.json"
    exit_code = run_acceptance_report(
        report_path,
        source_id="yahoo_finance",
        data_root=isolated_tier_b_data_root,
    )
    assert exit_code == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["summary"]["failed_external"] == 1
    assert report["sources"][0]["failure_class"] == "FAIL_EXTERNAL"
    assert report["sources"][0]["adr_ref"] == fail_external_adr_ref()
