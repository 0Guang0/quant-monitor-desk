"""M-DATA-03 S-R2-EVIDENCE — tier_a_live_acceptance --report tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from backend.app.datasources.live_tier_router import TIER_A_SOURCES
from backend.app.ops.tier_a_live_acceptance import (
    MANIFEST_FILENAME,
    _acceptance_report_exit_code,
    classify_source_report_failure,
    fail_external_adr_ref,
    run_acceptance_report,
)
from backend.app.ops.tier_a_live_incremental_dispatch import LiveIncrementalOutcome
from tests.contract_gate_support import PROJECT_ROOT

EVIDENCE_CONTRACT = PROJECT_ROOT / "specs/contracts/live_tier_a_evidence_v1.yaml"


def _load_contract() -> dict[str, Any]:
    return yaml.safe_load(EVIDENCE_CONTRACT.read_text(encoding="utf-8")) or {}


def _mock_outcome(source_id: str) -> LiveIncrementalOutcome:
    bindings = _load_contract()["source_bindings"]
    binding = bindings[source_id]
    return LiveIncrementalOutcome(
        source_id=source_id,
        sync_status="COMPLETED",
        inspect_status="PASS",
        clean_table=binding["clean_table"],
        clean_row_count=2,
        detail="mock report run",
    )


def _mock_f0_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    """Report tests target manifest shape; isolate from S-R2-F0 evidence requirements."""
    monkeypatch.setattr(
        "backend.app.ops.tier_a_live_acceptance._run_f0_data_health",
        lambda *_a, **_k: ("PASS", "mock f0 for report test"),
    )


def test_reportRun_writesElevenManifests(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """覆盖范围：一次 --report run 落盘 11 份 manifest
    测试对象：run_acceptance_report
    目的/目标：全量 report 为每 Tier A 源写出 live_tier_a_evidence_manifest.json
    验证点：11 个 manifest 文件；每行 evidence_manifest_path 指向存在文件
    失败含义：统一验收层缺 per-source 证据工件
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setenv("FRED_API_KEY", "a" * 32)
    monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "b" * 16)
    monkeypatch.setenv("SEC_EDGAR_USER_AGENT", "contract-test@example.com")

    def _mock_incremental(source_id: str, _data_root: Path) -> LiveIncrementalOutcome:
        return _mock_outcome(source_id)

    monkeypatch.setattr(
        "backend.app.ops.tier_a_live_acceptance.run_tier_a_live_incremental",
        _mock_incremental,
    )
    monkeypatch.setattr(
        "backend.app.ops.tier_a_live_incremental_dispatch.run_tier_a_live_incremental",
        _mock_incremental,
    )
    _mock_f0_pass(monkeypatch)

    report_path = tmp_path / "tier-a-report.json"
    exit_code = run_acceptance_report(
        report_path,
        data_root=isolated_live_data_root,
    )
    assert exit_code == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert len(report["sources"]) == 11
    manifest_paths: list[Path] = []
    for row in report["sources"]:
        rel = row["evidence_manifest_path"]
        manifest_path = isolated_live_data_root / rel
        assert manifest_path.is_file(), f"missing manifest for {row['source_id']}"
        assert manifest_path.name == MANIFEST_FILENAME
        manifest_paths.append(manifest_path)
    assert len(manifest_paths) == 11
    assert frozenset(p.parent.name for p in manifest_paths) == TIER_A_SOURCES


def test_acceptanceReport_hasContractTopLevelFields(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """覆盖范围：acceptance_report.required_top_level_fields
    测试对象：run_acceptance_report JSON 输出
    目的/目标：report 工件符合 live_tier_a_evidence_v1 acceptance_report 段
    验证点：顶层字段齐全；summary 含 total/passed/failed_* 计数
    失败含义：CI/人工无法消费结构化验收报告
    """
    contract = _load_contract()
    required_top = contract["acceptance_report"]["required_top_level_fields"]
    per_source_fields = contract["acceptance_report"]["per_source_row_fields"]
    summary_fields = contract["acceptance_report"]["summary_fields"]

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setenv("FRED_API_KEY", "a" * 32)
    monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "b" * 16)
    monkeypatch.setenv("SEC_EDGAR_USER_AGENT", "contract-test@example.com")

    def _mock_incremental(source_id: str, _data_root: Path) -> LiveIncrementalOutcome:
        return _mock_outcome(source_id)

    monkeypatch.setattr(
        "backend.app.ops.tier_a_live_acceptance.run_tier_a_live_incremental",
        _mock_incremental,
    )
    _mock_f0_pass(monkeypatch)

    report_path = tmp_path / "tier-a-shape.json"
    run_acceptance_report(report_path, data_root=isolated_live_data_root)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    for field in required_top:
        assert field in report
    for field in summary_fields:
        assert field in report["summary"]
    assert report["summary"]["total"] == 11
    for row in report["sources"]:
        for field in per_source_fields:
            assert field in row


def test_cliReportFlag_writesReportViaMain(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """覆盖范围：scripts/tier_a_live_acceptance.py --report
    测试对象：tier_a_live_acceptance.main --report
    目的/目标：CLI 入口可触发 report 写出并 exit 0（mock 增量）
    验证点：main 返回 0；report 文件存在且 sources 长度 11
    失败含义：运维/CI 无法通过 CLI 产出验收 JSON
    """
    from scripts.tier_a_live_acceptance import main

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setenv("FRED_API_KEY", "a" * 32)
    monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "b" * 16)
    monkeypatch.setenv("SEC_EDGAR_USER_AGENT", "contract-test@example.com")

    def _mock_incremental(source_id: str, _data_root: Path) -> LiveIncrementalOutcome:
        return _mock_outcome(source_id)

    monkeypatch.setattr(
        "backend.app.ops.tier_a_live_acceptance.run_tier_a_live_incremental",
        _mock_incremental,
    )
    _mock_f0_pass(monkeypatch)

    report_path = tmp_path / "cli-report.json"
    exit_code = main(
        [
            "--report",
            str(report_path),
            "--data-root",
            str(isolated_live_data_root),
        ]
    )
    assert exit_code == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert len(report["sources"]) == 11


def test_reportRun_e2InspectNonFailForElevenSources(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """覆盖范围：--report 全量 11 源 E2 inspect
    测试对象：run_acceptance_report per-source e2_inspect_status
    目的/目标：S-R2-ACCEPT — 每源 DbInspector.inspect 非 FAIL
    验证点：11 行 e2_inspect_status != FAIL；manifest acceptance 同步
    失败含义：统一验收层仍放行 E2 FAIL
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setenv("FRED_API_KEY", "a" * 32)
    monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "b" * 16)
    monkeypatch.setenv("SEC_EDGAR_USER_AGENT", "contract-test@example.com")

    def _mock_incremental(source_id: str, _data_root: Path) -> LiveIncrementalOutcome:
        return _mock_outcome(source_id)

    monkeypatch.setattr(
        "backend.app.ops.tier_a_live_acceptance.run_tier_a_live_incremental",
        _mock_incremental,
    )
    _mock_f0_pass(monkeypatch)

    report_path = tmp_path / "tier-a-e2-report.json"
    exit_code = run_acceptance_report(
        report_path,
        data_root=isolated_live_data_root,
    )
    assert exit_code == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    for row in report["sources"]:
        assert row["e2_inspect_status"] != "FAIL", row["source_id"]
        manifest_path = isolated_live_data_root / row["evidence_manifest_path"]
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["acceptance"]["e2_inspect_status"] != "FAIL"


def test_reportRun_writesFailureArtifactOnFixableFail(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """覆盖范围：contract failure_artifact
    测试对象：run_acceptance_report exit 1
    目的/目标：FAIL_FIXABLE 时写出 tier_a_live_acceptance_failure_{run_id}.json
    验证点：exit 1；artifact 含 exit_code/first_failure_source_id/failure_detail
    失败含义：CI 无法在 workflow failure 时上传诊断工件
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setenv("FRED_API_KEY", "a" * 32)
    monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "b" * 16)
    monkeypatch.setenv("SEC_EDGAR_USER_AGENT", "contract-test@example.com")

    def _fail_incremental(source_id: str, _data_root: Path) -> LiveIncrementalOutcome:
        outcome = _mock_outcome(source_id)
        return LiveIncrementalOutcome(
            source_id=source_id,
            sync_status="FAILED",
            inspect_status=outcome.inspect_status,
            clean_table=outcome.clean_table,
            clean_row_count=0,
            detail="simulated sync failure",
        )

    monkeypatch.setattr(
        "backend.app.ops.tier_a_live_acceptance.run_tier_a_live_incremental",
        _fail_incremental,
    )
    _mock_f0_pass(monkeypatch)

    report_path = tmp_path / "tier-a-fail-report.json"
    exit_code = run_acceptance_report(
        report_path,
        data_root=isolated_live_data_root,
    )
    assert exit_code == 1
    artifacts = list(tmp_path.glob("tier_a_live_acceptance_failure_*.json"))
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


def test_reportRun_plannedWithZeroCleanFails(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """覆盖范围：--report 路径 zero-clean/raw 守卫
    测试对象：run_acceptance_report per-source disposition
    目的/目标：PLANNED + 零 clean 行且无 raw 不得 pass（与 CLI 路径一致）
    验证点：fred 行 disposition==fail；failure_class==FAIL_FIXABLE
    失败含义：report 路径误标 pass，AC#8 假绿
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setenv("FRED_API_KEY", "a" * 32)

    def _planned_empty(_source_id: str, _data_root: Path) -> LiveIncrementalOutcome:
        return LiveIncrementalOutcome(
            source_id="fred",
            sync_status="PLANNED",
            inspect_status="PASS",
            clean_table="axis_observation",
            clean_row_count=0,
            detail="mock planned with no rows",
        )

    monkeypatch.setattr(
        "backend.app.ops.tier_a_live_acceptance.run_tier_a_live_incremental",
        _planned_empty,
    )
    monkeypatch.setattr(
        "backend.app.ops.tier_a_live_acceptance._run_f0_data_health",
        lambda *_a, **_k: ("PASS", "mock f0 for planned-empty-clean test"),
    )

    report_path = tmp_path / "planned-empty-report.json"
    exit_code = run_acceptance_report(
        report_path,
        source_id="fred",
        data_root=isolated_live_data_root,
    )
    assert exit_code == 1
    report = json.loads(report_path.read_text(encoding="utf-8"))
    row = report["sources"][0]
    assert row["disposition"] == "fail"
    assert row["failure_class"] == "FAIL_FIXABLE"
    assert "PLANNED" in row["failure_detail"] or "empty" in row["failure_detail"].lower()


def test_classifySourceReportFailure_emptyResponseZeroCleanFails() -> None:
    """覆盖范围：EMPTY_RESPONSE + 0 clean 不得 PASS
    测试对象：classify_source_report_failure
    目的/目标：G-01 守卫 — 空响应无行须 FAIL_FIXABLE
    验证点：disposition fail；failure_class FAIL_FIXABLE
    失败含义：0 行静默 PASS 回归
    """
    outcome = LiveIncrementalOutcome(
        source_id="bis",
        sync_status="EMPTY_RESPONSE",
        inspect_status="PASS",
        clean_table="axis_observation",
        clean_row_count=0,
        detail="sync=EMPTY_RESPONSE",
    )
    disposition, failure_class, adr_ref = classify_source_report_failure(outcome)
    assert disposition == "fail"
    assert failure_class == "FAIL_FIXABLE"
    assert adr_ref is None


def test_classifySourceReportFailure_emptyResponseWithCleanRowsPasses() -> None:
    """覆盖范围：幂等二次跑 caught-up 语义
    测试对象：classify_source_report_failure
    目的/目标：EMPTY_RESPONSE 但库内已有 clean 行可 PASS（AC-3）
    验证点：disposition pass；failure_class PASS
    失败含义：二次幂等跑被误标失败
    """
    outcome = LiveIncrementalOutcome(
        source_id="fred",
        sync_status="EMPTY_RESPONSE",
        inspect_status="PASS",
        clean_table="axis_observation",
        clean_row_count=3,
        detail="caught up",
    )
    disposition, failure_class, adr_ref = classify_source_report_failure(outcome)
    assert disposition == "pass"
    assert failure_class == "PASS"
    assert adr_ref is None


def test_classifySourceReportFailure_mapsAllExternalSyncStatuses() -> None:
    """覆盖范围：FAIL_EXTERNAL 分类与契约 ADR
    测试对象：classify_source_report_failure
    目的/目标：各外部 sync 状态映射 FAIL_EXTERNAL + 契约 adr_ref（非 report mock）
    验证点：RATE_LIMITED/NETWORK_ERROR/NOT_PUBLISHED_YET/DISABLED_SOURCE 均带 adr
    失败含义：外部失败分类或 ADR SSOT 不完整，属隐形技术债
    """
    adr = fail_external_adr_ref()
    for sync_status in (
        "RATE_LIMITED",
        "NETWORK_ERROR",
        "NOT_PUBLISHED_YET",
        "DISABLED_SOURCE",
    ):
        outcome = LiveIncrementalOutcome(
            source_id="fred",
            sync_status=sync_status,
            inspect_status="PASS",
            clean_table="axis_observation",
            clean_row_count=1,
            detail=f"sync={sync_status}",
        )
        disposition, failure_class, adr_ref = classify_source_report_failure(outcome)
        assert disposition == "fail"
        assert failure_class == "FAIL_EXTERNAL"
        assert adr_ref == adr


def test_acceptanceReportExitCode_externalRowsRequireContractAdr() -> None:
    """覆盖范围：contract exit_codes 行级 ADR 判定
    测试对象：_acceptance_report_exit_code
    目的/目标：FAIL_EXTERNAL 行须带契约 adr_ref 才 exit 0（无 mock sync）
    验证点：有 adr → 0；缺 adr → 1
    失败含义：exit 码逻辑与 fail_external_requires_adr 不一致
    """
    adr = fail_external_adr_ref()
    rows_ok = [
        {
            "failure_class": "FAIL_EXTERNAL",
            "adr_ref": adr,
        }
    ]
    rows_bad = [{"failure_class": "FAIL_EXTERNAL", "adr_ref": None}]
    summary_ok = {"failed_fixable": 0, "failed_external": 1}
    summary_bad = {"failed_fixable": 0, "failed_external": 1}
    assert _acceptance_report_exit_code(rows_ok, summary_ok) == 0
    assert _acceptance_report_exit_code(rows_bad, summary_bad) == 1


def test_reportRun_exit0WhenAllExternalWithAdr(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """覆盖范围：contract exit_codes FAIL_EXTERNAL + adr_ref
    测试对象：run_acceptance_report exit code
    目的/目标：全源 FAIL_EXTERNAL 且 adr_ref 有效时 exit 0
    验证点：exit 0；summary.failed_external==1；row.adr_ref==ADR-034
    失败含义：外部失败 ADR 合并路径未实现，契约与代码漂移
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setenv("FRED_API_KEY", "a" * 32)

    def _rate_limited(_source_id: str, _data_root: Path) -> LiveIncrementalOutcome:
        return LiveIncrementalOutcome(
            source_id="fred",
            sync_status="RATE_LIMITED",
            inspect_status="PASS",
            clean_table="axis_observation",
            clean_row_count=0,
            detail="vendor rate limit",
        )

    monkeypatch.setattr(
        "backend.app.ops.tier_a_live_acceptance.run_tier_a_live_incremental",
        _rate_limited,
    )

    report_path = tmp_path / "external-adr-report.json"
    exit_code = run_acceptance_report(
        report_path,
        source_id="fred",
        data_root=isolated_live_data_root,
    )
    assert exit_code == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["summary"]["failed_external"] == 1
    assert report["sources"][0]["failure_class"] == "FAIL_EXTERNAL"
    assert report["sources"][0]["adr_ref"] == fail_external_adr_ref()


def test_reportRun_exit1WhenExternalWithoutAdr(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """覆盖范围：contract exit_codes FAIL_EXTERNAL 无 ADR
    测试对象：run_acceptance_report exit code
    目的/目标：FAIL_EXTERNAL 无 adr_ref 时 fail-closed exit 1
    验证点：exit 1；failure artifact 写出
    失败含义：无 ADR 的外部失败被误标 exit 0
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setenv("FRED_API_KEY", "a" * 32)

    def _classify_external_no_adr(
        outcome: LiveIncrementalOutcome, *, data_root: Path | None = None
    ) -> tuple[str, str, str | None]:
        return "fail", "FAIL_EXTERNAL", None

    monkeypatch.setattr(
        "backend.app.ops.tier_a_live_acceptance.classify_source_report_failure",
        _classify_external_no_adr,
    )
    monkeypatch.setattr(
        "backend.app.ops.tier_a_live_acceptance.run_tier_a_live_incremental",
        lambda _sid, _root: _mock_outcome("fred"),
    )
    _mock_f0_pass(monkeypatch)

    report_path = tmp_path / "external-no-adr-report.json"
    exit_code = run_acceptance_report(
        report_path,
        source_id="fred",
        data_root=isolated_live_data_root,
    )
    assert exit_code == 1
    assert list(tmp_path.glob("tier_a_live_acceptance_failure_*.json"))
