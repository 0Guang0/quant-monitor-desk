"""Round 3G R3G-02 预生产对抗审计契约门禁。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.contract_gate_support import PROJECT_ROOT, load_yaml

# ponytail: ResourceGuard autouse — tests/conftest.py::_resourceGuardOkUnlessTestOverrides

CONTRACT = PROJECT_ROOT / "specs/contracts/sandbox_clean_write_contract.yaml"
FRED_AUTH = PROJECT_ROOT / ".audit-sandbox/round3g/fred_user_authorization.yaml"

def _contract() -> dict:
    return load_yaml(CONTRACT)


def test_r3g02Contract_decisionEnumFrozen() -> None:
    """覆盖范围：R3G-02 审计决策枚举
    测试对象：r3g02_audit.decision_enum
    目的/目标：对抗审计只允许契约列明的三种决策，不得静默扩展
    验证点：枚举集合与 Batch 3G 设计一致
    失败含义：决策枚举漂移会导致审批流与 rollback 语义不一致
    """
    expected = {
        "PASS_ALLOW_LIMITED_PROD_WRITE",
        "WARN_ALLOW_WITH_MANUAL_APPROVAL",
        "BLOCK_PRODUCTION_WRITE",
    }
    assert set(_contract()["r3g02_audit"]["decision_enum"]) == expected


def test_r3g02Contract_blocksReferenceRuntimeImport() -> None:
    """覆盖范围：R3G-02 block_if 对参考项目 runtime import 的 fail-closed
    测试对象：r3g02_audit.block_if
    目的/目标：对抗审计必须拒绝从参考项目直接 runtime import
    验证点：block_if 含 runtime_import_from_reference_project
    失败含义：参考项目代码可能被误当作生产 runtime 依赖
    """
    block_if = set(_contract()["r3g02_audit"]["block_if"])
    assert "runtime_import_from_reference_project" in block_if
    assert "agent_triggered_write_path" in block_if


def test_r3g02Contract_rejectsProductionMutation() -> None:
    """覆盖范围：R3G-02 审计阶段 production mutation 禁止
    测试对象：r3g02_audit.production_mutation_allowed
    目的/目标：审计阶段不得声称或执行生产库写入
    验证点：production_mutation_allowed 为 false
    失败含义：审计与 limited entry 边界混淆，可能提前触发生产写
    """
    assert _contract()["r3g02_audit"]["production_mutation_allowed"] is False


def test_r3g02AuditDecision_enumMatchesContract() -> None:
    """覆盖范围：R3G-02 AuditDecision 枚举与契约对齐
    测试对象：audit_decision.AuditDecision
    目的/目标：运行时决策枚举不得扩展契约 decision_enum 之外
    验证点：成员值集合与 r3g02_audit.decision_enum 一致
    失败含义：审批流与 R3G-03 gate 会因枚举漂移而误判
    """
    from backend.app.ops.sandbox_clean_write.audit_decision import AuditDecision

    contract_values = set(_contract()["r3g02_audit"]["decision_enum"])
    assert {member.value for member in AuditDecision} == contract_values


def test_r3g02AuditResult_serializesBlockingAndWarningReasons() -> None:
    """覆盖范围：R3G-02 AuditResult 结构化序列化
    测试对象：audit_decision.AuditResult.serialize
    目的/目标：每条决策必须携带 blocking/warning reasons 与 evidence_paths
    验证点：JSON 形态含 decision、reasons、evidence_paths、production_mutation_allowed=false
    失败含义：审计结论无法被 R3G-03 机器消费或缺少 fail-closed 依据
    """
    from backend.app.ops.sandbox_clean_write.audit_decision import (
        AuditDecision,
        AuditFinding,
        AuditResult,
    )

    result = AuditResult(
        decision=AuditDecision.BLOCK_PRODUCTION_WRITE,
        blocking_reasons=(
            AuditFinding(
                code="missing_rehearsal_report",
                message="rehearsal report path missing",
                evidence_paths=("/tmp/missing.json",),
            ),
        ),
        warning_reasons=(),
        evidence_paths=("/tmp/missing.json",),
    )
    payload = result.serialize()
    assert payload["decision"] == "BLOCK_PRODUCTION_WRITE"
    assert payload["production_mutation_allowed"] is False
    assert payload["blocking_reasons"][0]["code"] == "missing_rehearsal_report"
    assert payload["blocking_reasons"][0]["evidence_paths"] == ["/tmp/missing.json"]
    assert payload["evidence_paths"] == ["/tmp/missing.json"]
    assert payload["warning_reasons"] == []


def test_r3g02AuditResult_rejectsUnknownDecisionOnDeserialize() -> None:
    """覆盖范围：R3G-02 未知决策值反序列化 fail-closed
    测试对象：audit_decision.AuditResult.from_dict
    目的/目标：禁止静默接受契约外 decision 字符串
    验证点：未知 decision 触发 ValueError
    失败含义：审批 gate 可能被伪造决策绕过
    """
    from backend.app.ops.sandbox_clean_write.audit_decision import AuditResult

    with pytest.raises(ValueError, match="decision"):
        AuditResult.from_dict(
            {
                "decision": "ALLOW_ANYTHING",
                "blocking_reasons": [],
                "warning_reasons": [],
                "evidence_paths": [],
                "production_mutation_allowed": False,
            }
        )


# --- §1.2 adversarial_audit core ---


def test_r3g02AdversarialAudit_missingReportBlocks() -> None:
    """覆盖范围：缺 rehearsal report 时 fail-closed
    测试对象：run_adversarial_audit
    目的/目标：无 R3G-01 报告必须 BLOCK_PRODUCTION_WRITE
    验证点：decision=BLOCK；blocking_reasons 含 missing_rehearsal_report
    失败含义：无证据审计可能误放行 R3G-03
    """
    from backend.app.ops.sandbox_clean_write.adversarial_audit import (
        AdversarialAuditRequest,
        run_adversarial_audit,
    )
    from backend.app.ops.sandbox_clean_write.audit_decision import AuditDecision

    result = run_adversarial_audit(
        AdversarialAuditRequest(
            rehearsal_report=PROJECT_ROOT / ".audit-sandbox/round3g/does_not_exist.json",
            sandbox_db=PROJECT_ROOT / ".audit-sandbox/round3g/rehearsal.duckdb",
            evidence_dir=PROJECT_ROOT / ".audit-sandbox/round3g/evidence",
        )
    )
    assert result.decision == AuditDecision.BLOCK_PRODUCTION_WRITE
    codes = {f.code for f in result.blocking_reasons}
    assert "missing_rehearsal_report" in codes


def _run_rehearsal(tmp_path: Path) -> dict[str, Path]:
    from backend.app.ops.sandbox_clean_write.rehearsal_runner import (
        RehearsalRequest,
        run_sandbox_clean_write_rehearsal,
    )

    paths = {
        "sandbox_db": tmp_path / "sandbox.duckdb",
        "evidence_dir": tmp_path / "evidence",
        "report_path": tmp_path / "rehearsal_report.json",
    }
    run_sandbox_clean_write_rehearsal(
        RehearsalRequest(
            candidate_set="r3g_p0",
            sandbox_db=paths["sandbox_db"],
            evidence_dir=paths["evidence_dir"],
            report_path=paths["report_path"],
            no_production_mutation=True,
            dry_run=True,
            fred_authorization=FRED_AUTH,
        )
    )
    return paths


def _patch_gate_ready_report(report: dict) -> None:
    """Gate-ready rehearsal shape for PASS path (full lineage, no synthetic bypass)."""
    for src in report.get("per_source_reports", []):
        if src.get("domain") == "cn_equity_daily_bar":
            src["source_fetch_id_coverage"] = 1.0
            src["content_hash_coverage"] = 1.0
            src["schema_hash_coverage"] = 1.0
        src["synthetic_admission"] = False


def _patch_gate_ready_evidence(evidence_dir: Path) -> None:
    """Copy FRED authorization artifact into evidence for provider auth audit."""
    import shutil

    fred_dir = evidence_dir / "fred"
    fred_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(FRED_AUTH, fred_dir / "fred_user_authorization.yaml")


def test_r3g02AdversarialAudit_zeroLineageCoverageBlocks(tmp_path: Path) -> None:
    """覆盖范围：P0-01 bar 源零 lineage coverage fail-closed
    测试对象：run_adversarial_audit §3.3 lineage coverage
    目的/目标：source_fetch_id/content_hash coverage=0.0 不得 PASS
    验证点：decision=BLOCK；blocking 含 missing_rehearsal_report（零 coverage）
    失败含义：无 lineage 证据仍放行 limited prod write
    """
    from backend.app.ops.sandbox_clean_write.adversarial_audit import (
        AdversarialAuditRequest,
        run_adversarial_audit,
    )
    from backend.app.ops.sandbox_clean_write.audit_decision import AuditDecision

    paths = _run_rehearsal(tmp_path)
    result = run_adversarial_audit(
        AdversarialAuditRequest(
            rehearsal_report=paths["report_path"],
            sandbox_db=paths["sandbox_db"],
            evidence_dir=paths["evidence_dir"],
        )
    )
    assert result.decision == AuditDecision.BLOCK_PRODUCTION_WRITE
    codes = {f.code for f in result.blocking_reasons}
    assert "missing_rehearsal_report" in codes
    assert any("zero lineage coverage" in f.message for f in result.blocking_reasons)


def test_r3g02AdversarialAudit_syntheticAdmissionPassedBlocks(tmp_path: Path) -> None:
    """覆盖范围：P0-02 synthetic_admission + validation_status=PASSED
    测试对象：run_adversarial_audit §3.3 synthetic admission
    目的/目标：合成准入与 PASSED 并存须触发 gate_bypass BLOCK
    验证点：blocking_reasons 含 write_manager_or_db_validation_gate_bypass
    失败含义：合成 validation 绕过 DbValidationGate 未被审计捕获
    """
    from backend.app.ops.sandbox_clean_write.adversarial_audit import (
        AdversarialAuditRequest,
        run_adversarial_audit,
    )
    from backend.app.ops.sandbox_clean_write.audit_decision import AuditDecision

    paths = _run_rehearsal(tmp_path)
    report = json.loads(paths["report_path"].read_text(encoding="utf-8"))
    for src in report["per_source_reports"]:
        src["synthetic_admission"] = True
        src["validation_status"] = "PASSED"
        if src.get("domain") == "cn_equity_daily_bar":
            src["source_fetch_id_coverage"] = 1.0
            src["content_hash_coverage"] = 1.0
    paths["report_path"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    result = run_adversarial_audit(
        AdversarialAuditRequest(
            rehearsal_report=paths["report_path"],
            sandbox_db=paths["sandbox_db"],
            evidence_dir=paths["evidence_dir"],
        )
    )
    assert result.decision == AuditDecision.BLOCK_PRODUCTION_WRITE
    assert "write_manager_or_db_validation_gate_bypass" in {f.code for f in result.blocking_reasons}


def test_r3g02AdversarialAudit_partialLineageCoverageWarns(tmp_path: Path) -> None:
    """覆盖范围：P0-01 bar 源 partial lineage coverage 上限 WARN
    测试对象：run_adversarial_audit §3.3 lineage coverage
    目的/目标：coverage 在 (0,1) 区间不得 PASS，须 WARN+manual
    验证点：decision=WARN；warning_reasons 含 incomplete_lineage_coverage
    失败含义：不完整 lineage 被当作可自动放行的 limited prod write
    """
    from backend.app.ops.sandbox_clean_write.adversarial_audit import (
        AdversarialAuditRequest,
        run_adversarial_audit,
    )
    from backend.app.ops.sandbox_clean_write.audit_decision import AuditDecision

    paths = _run_rehearsal(tmp_path)
    report = json.loads(paths["report_path"].read_text(encoding="utf-8"))
    _patch_gate_ready_report(report)
    for src in report["per_source_reports"]:
        if src.get("domain") == "cn_equity_daily_bar":
            src["source_fetch_id_coverage"] = 0.5
            src["content_hash_coverage"] = 0.5
    paths["report_path"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    result = run_adversarial_audit(
        AdversarialAuditRequest(
            rehearsal_report=paths["report_path"],
            sandbox_db=paths["sandbox_db"],
            evidence_dir=paths["evidence_dir"],
        )
    )
    assert result.decision == AuditDecision.WARN_ALLOW_WITH_MANUAL_APPROVAL
    assert "incomplete_lineage_coverage" in {f.code for f in result.warning_reasons}


def test_r3g02AdversarialAudit_missingRollbackFileBlocks(tmp_path: Path) -> None:
    """覆盖范围：P0-03 rollback_artifact_path 必须指向真实文件
    测试对象：run_adversarial_audit §3.3 rollback 证据
    目的/目标：报告含 rollback 路径但磁盘无文件时 fail-closed BLOCK
    验证点：decision=BLOCK；blocking 含 missing_rehearsal_report 且 message 提及 rollback
    失败含义：伪造 rollback 路径可绕过 write/rollback 可追溯性审计
    """
    from backend.app.ops.sandbox_clean_write.adversarial_audit import (
        AdversarialAuditRequest,
        run_adversarial_audit,
    )
    from backend.app.ops.sandbox_clean_write.audit_decision import AuditDecision

    paths = _run_rehearsal(tmp_path)
    report = json.loads(paths["report_path"].read_text(encoding="utf-8"))
    _patch_gate_ready_report(report)
    for src in report["per_source_reports"]:
        src["rollback_artifact_path"] = str(
            paths["evidence_dir"] / src["source_id"] / "rollback_artifact_MISSING.json"
        )
    paths["report_path"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    result = run_adversarial_audit(
        AdversarialAuditRequest(
            rehearsal_report=paths["report_path"],
            sandbox_db=paths["sandbox_db"],
            evidence_dir=paths["evidence_dir"],
        )
    )
    assert result.decision == AuditDecision.BLOCK_PRODUCTION_WRITE
    codes = {f.code for f in result.blocking_reasons}
    assert "missing_rehearsal_report" in codes
    assert any("rollback" in f.message.lower() for f in result.blocking_reasons)


def test_r3g02AdversarialAudit_missingDhProfileBlocks(tmp_path: Path) -> None:
    """覆盖范围：cn_equity_daily_bar 缺 DH profile 证据
    测试对象：run_adversarial_audit §3.1
    目的/目标：无结构化 data_health_summary 且无磁盘证据时 BLOCK
    验证点：blocking_reasons 含 missing_data_health_profile_evidence
    失败含义：缺 OHLCV profile 仍可能讨论生产写
    """
    from backend.app.ops.sandbox_clean_write.adversarial_audit import (
        AdversarialAuditRequest,
        run_adversarial_audit,
    )
    from backend.app.ops.sandbox_clean_write.audit_decision import AuditDecision

    paths = _run_rehearsal(tmp_path)
    report = json.loads(paths["report_path"].read_text(encoding="utf-8"))
    for src in report["per_source_reports"]:
        if src.get("domain") == "cn_equity_daily_bar":
            src.pop("data_health_summary", None)
    paths["report_path"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    result = run_adversarial_audit(
        AdversarialAuditRequest(
            rehearsal_report=paths["report_path"],
            sandbox_db=paths["sandbox_db"],
            evidence_dir=paths["evidence_dir"],
        )
    )
    assert result.decision == AuditDecision.BLOCK_PRODUCTION_WRITE
    assert "missing_data_health_profile_evidence" in {f.code for f in result.blocking_reasons}


def test_r3g02AdversarialAudit_approximateCalendarAtMostWarns(tmp_path: Path) -> None:
    """覆盖范围：近似 calendar 证据上限 WARN
    测试对象：run_adversarial_audit §3.1 calendar 行为
    目的/目标：近似 calendar 不得 PASS，至多 WARN+manual
    验证点：decision=WARN_ALLOW_WITH_MANUAL_APPROVAL
    失败含义：不精确 calendar 被当作可自动放行
    """
    from backend.app.ops.sandbox_clean_write.adversarial_audit import (
        AdversarialAuditRequest,
        run_adversarial_audit,
    )
    from backend.app.ops.sandbox_clean_write.audit_decision import AuditDecision

    paths = _run_rehearsal(tmp_path)
    report = json.loads(paths["report_path"].read_text(encoding="utf-8"))
    _patch_gate_ready_report(report)
    for src in report["per_source_reports"]:
        if src.get("source_id") == "baostock":
            src["data_health_summary"] = {
                **src["data_health_summary"],
                "overall_status": "WARN",
                "calendar_gap_violation_count": 2,
                "gate_rationale": "approximate calendar — official exchange calendar not available",
            }
    paths["report_path"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    result = run_adversarial_audit(
        AdversarialAuditRequest(
            rehearsal_report=paths["report_path"],
            sandbox_db=paths["sandbox_db"],
            evidence_dir=paths["evidence_dir"],
        )
    )
    assert result.decision == AuditDecision.WARN_ALLOW_WITH_MANUAL_APPROVAL
    assert any(f.code == "approximate_calendar_evidence" for f in result.warning_reasons)


def test_r3g02AdversarialAudit_uncappedCandidateBlocks(tmp_path: Path) -> None:
    """覆盖范围：超 cap 候选集 fail-closed
    测试对象：run_adversarial_audit validate_source_caps
    目的/目标：uncapped candidate set 必须 BLOCK
    验证点：blocking_reasons 含 uncapped_candidate_set
    失败含义：审计未守住 R3G-01 bounded rehearsal 边界
    """
    from backend.app.ops.sandbox_clean_write.adversarial_audit import (
        AdversarialAuditRequest,
        run_adversarial_audit,
    )
    from backend.app.ops.sandbox_clean_write.audit_decision import AuditDecision

    paths = _run_rehearsal(tmp_path)
    report = json.loads(paths["report_path"].read_text(encoding="utf-8"))
    for src in report["per_source_reports"]:
        if src.get("source_id") == "baostock":
            src["symbol_or_series_count"] = 999
    paths["report_path"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    result = run_adversarial_audit(
        AdversarialAuditRequest(
            rehearsal_report=paths["report_path"],
            sandbox_db=paths["sandbox_db"],
            evidence_dir=paths["evidence_dir"],
        )
    )
    assert result.decision == AuditDecision.BLOCK_PRODUCTION_WRITE
    assert "uncapped_candidate_set" in {f.code for f in result.blocking_reasons}


def test_r3g02AdversarialAudit_runtimeImportScanBlocks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """覆盖范围：runtime 参考项目 import 扫描（mock 扫描注入边界）
    测试对象：run_adversarial_audit 对 _scan_runtime_guardrails 结果的决策
    目的/目标：发现 reference runtime import finding 时 BLOCK
    验证点：blocking_reasons 含 runtime_import_from_reference_project
    失败含义：参考项目代码渗入 QMD runtime 未被审计决策层捕获
    """
    from backend.app.ops.sandbox_clean_write.adversarial_audit import (
        AdversarialAuditRequest,
        AuditFinding,
        run_adversarial_audit,
    )
    from backend.app.ops.sandbox_clean_write.audit_decision import AuditDecision

    paths = _run_rehearsal(tmp_path)
    monkeypatch.setattr(
        "backend.app.ops.sandbox_clean_write.adversarial_audit._scan_runtime_guardrails",
        lambda: [
            AuditFinding(
                code="runtime_import_from_reference_project",
                message="synthetic scan hit",
                evidence_paths=("backend/app/example.py",),
            )
        ],
    )
    result = run_adversarial_audit(
        AdversarialAuditRequest(
            rehearsal_report=paths["report_path"],
            sandbox_db=paths["sandbox_db"],
            evidence_dir=paths["evidence_dir"],
        )
    )
    assert result.decision == AuditDecision.BLOCK_PRODUCTION_WRITE
    assert "runtime_import_from_reference_project" in {f.code for f in result.blocking_reasons}


def test_r3g02AdversarialAudit_forbiddenTradingApiBlocks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """覆盖范围：JQ2PTrade 禁止交易 API 名（mock 扫描注入边界）
    测试对象：run_adversarial_audit 对 guardrail finding 的决策
    目的/目标：forbidden trading/order API finding 命中时 BLOCK
    验证点：blocking_reasons 含 jq2ptrade_disallowed_api_surface
    失败含义：执行面 API finding 未升级为 BLOCK 决策
    """
    from backend.app.ops.sandbox_clean_write.adversarial_audit import (
        AdversarialAuditRequest,
        AuditFinding,
        run_adversarial_audit,
    )
    from backend.app.ops.sandbox_clean_write.audit_decision import AuditDecision

    paths = _run_rehearsal(tmp_path)
    monkeypatch.setattr(
        "backend.app.ops.sandbox_clean_write.adversarial_audit._scan_runtime_guardrails",
        lambda: [
            AuditFinding(
                code="jq2ptrade_disallowed_api_surface",
                message="synthetic order() def",
                evidence_paths=("backend/app/example.py",),
            )
        ],
    )
    result = run_adversarial_audit(
        AdversarialAuditRequest(
            rehearsal_report=paths["report_path"],
            sandbox_db=paths["sandbox_db"],
            evidence_dir=paths["evidence_dir"],
        )
    )
    assert result.decision == AuditDecision.BLOCK_PRODUCTION_WRITE
    assert "jq2ptrade_disallowed_api_surface" in {f.code for f in result.blocking_reasons}


def test_r3g02AdversarialAudit_copiedOpenbbBlocks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """覆盖范围：OpenBB runtime 拷贝（mock 扫描注入边界）
    测试对象：run_adversarial_audit 对 OpenBB finding 的决策
    目的/目标：copied OpenBB runtime finding 命中时 BLOCK
    验证点：blocking_reasons 含 copied_openbb_runtime_source
    失败含义：OpenBB provider 拷贝 finding 未升级为 BLOCK
    """
    from backend.app.ops.sandbox_clean_write.adversarial_audit import (
        AdversarialAuditRequest,
        AuditFinding,
        run_adversarial_audit,
    )
    from backend.app.ops.sandbox_clean_write.audit_decision import AuditDecision

    paths = _run_rehearsal(tmp_path)
    monkeypatch.setattr(
        "backend.app.ops.sandbox_clean_write.adversarial_audit._scan_runtime_guardrails",
        lambda: [
            AuditFinding(
                code="copied_openbb_runtime_source",
                message="synthetic openbb import",
                evidence_paths=("backend/app/example.py",),
            )
        ],
    )
    result = run_adversarial_audit(
        AdversarialAuditRequest(
            rehearsal_report=paths["report_path"],
            sandbox_db=paths["sandbox_db"],
            evidence_dir=paths["evidence_dir"],
        )
    )
    assert result.decision == AuditDecision.BLOCK_PRODUCTION_WRITE
    assert "copied_openbb_runtime_source" in {f.code for f in result.blocking_reasons}


def test_r3g02AdversarialAudit_boundedRehearsalPasses(tmp_path: Path) -> None:
    """覆盖范围：合法有界 R3G-01 证据 PASS 路径
    测试对象：run_adversarial_audit 端到端
    目的/目标：gate-ready dry_run 排练应 PASS_ALLOW_LIMITED_PROD_WRITE
    验证点：decision=PASS；production_mutation_allowed=false
    失败含义：正常排练证据被误 BLOCK，阻塞 R3G-03 讨论
    """
    from backend.app.ops.sandbox_clean_write.adversarial_audit import (
        AdversarialAuditRequest,
        run_adversarial_audit,
    )
    from backend.app.ops.sandbox_clean_write.audit_decision import AuditDecision

    paths = _run_rehearsal(tmp_path)
    report = json.loads(paths["report_path"].read_text(encoding="utf-8"))
    _patch_gate_ready_report(report)
    paths["report_path"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    _patch_gate_ready_evidence(paths["evidence_dir"])
    result = run_adversarial_audit(
        AdversarialAuditRequest(
            rehearsal_report=paths["report_path"],
            sandbox_db=paths["sandbox_db"],
            evidence_dir=paths["evidence_dir"],
        )
    )
    assert result.decision == AuditDecision.PASS_ALLOW_LIMITED_PROD_WRITE
    assert result.production_mutation_allowed is False


# --- §1.3 CLI ---


def test_r3g02AuditCli_productionDbPathRejected(tmp_path: Path) -> None:
    """覆盖范围：audit CLI 拒绝生产 DB 路径
    测试对象：sandbox_clean_write_audit
    目的/目标：--sandbox-db 不得指向生产 duckdb
    验证点：CliFailure 含 production DB path refused
    失败含义：审计 CLI 可绑定生产写路径
    """
    from backend.app.cli.data_commands import sandbox_clean_write_audit
    from backend.app.cli.errors import CliFailure
    from backend.app.ops.staged_pilot import DEFAULT_PRODUCTION_DB

    with pytest.raises(CliFailure, match="production DB path refused"):
        sandbox_clean_write_audit(
            rehearsal_report=tmp_path / "report.json",
            sandbox_db=DEFAULT_PRODUCTION_DB,
            evidence_dir=tmp_path / "evidence",
            decision_report=tmp_path / "audit_decision.json",
        )


def test_r3g02AuditCli_writesDecisionReport(tmp_path: Path) -> None:
    """覆盖范围：audit CLI 写出 audit_decision.json
    测试对象：sandbox_clean_write_audit
    目的/目标：CLI 形状与任务卡 §5 一致并落盘决策
    验证点：decision_report 存在且含契约 decision 字段
    失败含义：操作员无法留存机器可读的 go/no-go 证据
    """
    from backend.app.cli.data_commands import sandbox_clean_write_audit

    paths = _run_rehearsal(tmp_path)
    decision_path = tmp_path / "audit_decision.json"
    payload = sandbox_clean_write_audit(
        rehearsal_report=paths["report_path"],
        sandbox_db=paths["sandbox_db"],
        evidence_dir=paths["evidence_dir"],
        decision_report=decision_path,
    )
    assert decision_path.is_file()
    on_disk = json.loads(decision_path.read_text(encoding="utf-8"))
    assert on_disk["decision"] == payload["decision"]
    assert on_disk["production_mutation_allowed"] is False


def test_r3g02AuditCli_helpDocumentsAuditSubcommand() -> None:
    """覆盖范围：CLI help 暴露 audit 子命令
    测试对象：qmd data sandbox-clean-write audit --help
    目的/目标：任务卡 §5 CLI 形状可发现
    验证点：help 含 audit、rehearsal-report、decision-report
    失败含义：操作员无法发现对抗审计 CLI
    """
    import subprocess
    import sys

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "backend.app.cli.main",
            "data",
            "sandbox-clean-write",
            "audit",
            "--help",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    help_text = proc.stdout + proc.stderr
    assert "audit" in help_text
    assert "rehearsal-report" in help_text
    assert "decision-report" in help_text


# --- P1–P3 audit repair ---


def test_r3g02AdversarialAudit_readsBarEvidenceSubstance(tmp_path: Path) -> None:
    """覆盖范围：P1-01 §3.1 EasyXT 证据内容实质读取
    测试对象：run_adversarial_audit bars.json OHLCV 检查
    目的/目标：磁盘 bars 证据 OHLC 关系违规时 fail-closed BLOCK
    验证点：blocking_reasons 含 missing_data_health_profile_evidence
    失败含义：仅查 data_health_summary 结构而不读证据内容
    """
    from backend.app.ops.sandbox_clean_write.adversarial_audit import (
        AdversarialAuditRequest,
        run_adversarial_audit,
    )
    from backend.app.ops.sandbox_clean_write.audit_decision import AuditDecision

    paths = _run_rehearsal(tmp_path)
    report = json.loads(paths["report_path"].read_text(encoding="utf-8"))
    _patch_gate_ready_report(report)
    paths["report_path"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    bars_path = paths["evidence_dir"] / "baostock" / "bars.json"
    bars_path.parent.mkdir(parents=True, exist_ok=True)
    bars_path.write_text(
        json.dumps({"rows": [{"open": 5, "high": 1, "low": 4, "close": 3, "volume": 1}]})
        + "\n",
        encoding="utf-8",
    )

    result = run_adversarial_audit(
        AdversarialAuditRequest(
            rehearsal_report=paths["report_path"],
            sandbox_db=paths["sandbox_db"],
            evidence_dir=paths["evidence_dir"],
        )
    )
    assert result.decision == AuditDecision.BLOCK_PRODUCTION_WRITE
    assert "missing_data_health_profile_evidence" in {f.code for f in result.blocking_reasons}


def test_r3g02AdversarialAudit_realGuardrailScanDetectsFixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """覆盖范围：P1-02 真实 guardrail 扫描集成（非 monkeypatch 扫描函数）
    测试对象：_scan_runtime_guardrails 对临时坏文件
    目的/目标：真实扫描器须捕获 agent_triggered_write 模式
    验证点：findings 含 agent_triggered_write_path
    失败含义：guardrail 扫描仅 mock 边界、未验证真实 AST/模式逻辑
    """
    from backend.app.ops.sandbox_clean_write.adversarial_audit import _scan_runtime_guardrails

    bad_py = tmp_path / "agent_hook.py"
    bad_py.write_text("def agent_expanded_candidate_set():\n    pass\n", encoding="utf-8")
    monkeypatch.setattr(
        "backend.app.ops.sandbox_clean_write.adversarial_audit.GUARDRAIL_SCAN_ROOTS",
        (tmp_path,),
    )
    findings = _scan_runtime_guardrails()
    assert any(f.code == "agent_triggered_write_path" for f in findings)


def test_r3g02AdversarialAudit_providerMetadataChecksAuthAndCaps(tmp_path: Path) -> None:
    """覆盖范围：P1-03 §3.4 provider 元数据完整校验
    测试对象：_audit_provider_metadata production_default_enabled
    目的/目标：production_default_enabled=true 须 BLOCK
    验证点：blocking_reasons 含 uncapped_candidate_set
    失败含义：仅查 catalog 存在性而忽略 auth/default cap posture
    """
    from backend.app.ops.sandbox_clean_write.adversarial_audit import (
        AdversarialAuditRequest,
        run_adversarial_audit,
    )
    from backend.app.ops.sandbox_clean_write.audit_decision import AuditDecision

    paths = _run_rehearsal(tmp_path)
    report = json.loads(paths["report_path"].read_text(encoding="utf-8"))
    _patch_gate_ready_report(report)
    for src in report["per_source_reports"]:
        if src.get("source_id") == "baostock":
            src["symbol_or_series_count"] = 999
    paths["report_path"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    result = run_adversarial_audit(
        AdversarialAuditRequest(
            rehearsal_report=paths["report_path"],
            sandbox_db=paths["sandbox_db"],
            evidence_dir=paths["evidence_dir"],
        )
    )
    assert result.decision == AuditDecision.BLOCK_PRODUCTION_WRITE
    assert "uncapped_candidate_set" in {f.code for f in result.blocking_reasons}


def test_r3g02AdversarialAudit_forbiddenGetTradingApiBlocks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """覆盖范围：P1-06 JQ2PTrade get_* API 与护栏契约 SSOT 对齐
    测试对象：_scan_runtime_guardrails real_trading_or_order_api
    目的/目标：get_portfolio/get_orders 等禁止 API 须触发 jq2ptrade_disallowed_api_surface
    验证点：临时坏文件定义 get_portfolio() 时被扫描捕获
    失败含义：仅扫 order/buy/sell 而漏掉契约列明的 get_* 查询 API
    """
    from backend.app.ops.sandbox_clean_write.adversarial_audit import _scan_runtime_guardrails

    bad_py = tmp_path / "jq2p_get_api.py"
    bad_py.write_text("def get_portfolio():\n    return {}\n", encoding="utf-8")
    monkeypatch.setattr(
        "backend.app.ops.sandbox_clean_write.adversarial_audit.GUARDRAIL_SCAN_ROOTS",
        (tmp_path,),
    )
    findings = _scan_runtime_guardrails()
    assert any(f.code == "jq2ptrade_disallowed_api_surface" for f in findings)


def test_r3g02AdversarialAudit_evidenceDirNotDirectoryBlocks(tmp_path: Path) -> None:
    """覆盖范围：P1-05 evidence_dir 非目录 fail-closed
    测试对象：run_adversarial_audit evidence_dir 存在性
    目的/目标：report 存在但 evidence_dir 非目录须 BLOCK
    验证点：blocking_reasons 含 missing_rehearsal_report 且 message 提及 evidence_dir
    失败含义：无证据目录仍可能 PASS
    """
    from backend.app.ops.sandbox_clean_write.adversarial_audit import (
        AdversarialAuditRequest,
        run_adversarial_audit,
    )
    from backend.app.ops.sandbox_clean_write.audit_decision import AuditDecision

    paths = _run_rehearsal(tmp_path)
    not_a_dir = paths["evidence_dir"] / "file_not_dir"
    not_a_dir.write_text("{}", encoding="utf-8")
    result = run_adversarial_audit(
        AdversarialAuditRequest(
            rehearsal_report=paths["report_path"],
            sandbox_db=paths["sandbox_db"],
            evidence_dir=not_a_dir,
        )
    )
    assert result.decision == AuditDecision.BLOCK_PRODUCTION_WRITE
    assert "missing_rehearsal_report" in {f.code for f in result.blocking_reasons}
    assert any("evidence_dir" in f.message for f in result.blocking_reasons)


def test_r3g02AdversarialAudit_metadataZeroStagedBlocks(tmp_path: Path) -> None:
    """覆盖范围：P1-04 §3.3 metadata 源 staged 行数实质校验
    测试对象：run_adversarial_audit row count audit
    目的/目标：metadata 源 staged_row_count=0 须 BLOCK
    验证点：blocking_reasons 含 missing_rehearsal_report 且提及 staged
    失败含义：仅检查字段存在而不校验计数合理性
    """
    from backend.app.ops.sandbox_clean_write.adversarial_audit import (
        AdversarialAuditRequest,
        run_adversarial_audit,
    )
    from backend.app.ops.sandbox_clean_write.audit_decision import AuditDecision

    paths = _run_rehearsal(tmp_path)
    report = json.loads(paths["report_path"].read_text(encoding="utf-8"))
    _patch_gate_ready_report(report)
    for src in report["per_source_reports"]:
        if src.get("domain") == "cn_announcements":
            src["staged_row_count"] = 0
    paths["report_path"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    result = run_adversarial_audit(
        AdversarialAuditRequest(
            rehearsal_report=paths["report_path"],
            sandbox_db=paths["sandbox_db"],
            evidence_dir=paths["evidence_dir"],
        )
    )
    assert result.decision == AuditDecision.BLOCK_PRODUCTION_WRITE
    assert any("staged_row_count" in f.message for f in result.blocking_reasons)


def test_r3g02AdversarialAudit_agentTriggeredWriteBlocks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """覆盖范围：P2-01 agent_triggered_write 对抗测
    测试对象：run_adversarial_audit 端到端 guardrail 集成
    目的/目标：agent 写路径模式须 BLOCK
    验证点：blocking_reasons 含 agent_triggered_write_path
    失败含义：§7 矩阵缺 agent 写路径对抗覆盖
    """
    from backend.app.ops.sandbox_clean_write.adversarial_audit import (
        AdversarialAuditRequest,
        run_adversarial_audit,
    )
    from backend.app.ops.sandbox_clean_write.audit_decision import AuditDecision

    paths = _run_rehearsal(tmp_path)
    report = json.loads(paths["report_path"].read_text(encoding="utf-8"))
    _patch_gate_ready_report(report)
    paths["report_path"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    bad_py = tmp_path / "scan_root" / "agent_write.py"
    bad_py.parent.mkdir(parents=True, exist_ok=True)
    bad_py.write_text("agent_triggered_write = True\n", encoding="utf-8")
    monkeypatch.setattr(
        "backend.app.ops.sandbox_clean_write.adversarial_audit.GUARDRAIL_SCAN_ROOTS",
        (bad_py.parent,),
    )

    result = run_adversarial_audit(
        AdversarialAuditRequest(
            rehearsal_report=paths["report_path"],
            sandbox_db=paths["sandbox_db"],
            evidence_dir=paths["evidence_dir"],
        )
    )
    assert result.decision == AuditDecision.BLOCK_PRODUCTION_WRITE
    assert "agent_triggered_write_path" in {f.code for f in result.blocking_reasons}


def test_r3g02AdversarialAudit_strategyMetricsInSourceReportBlocks(tmp_path: Path) -> None:
    """覆盖范围：P2-02 gate_bypass 合成报告 strategy metrics 对抗测
    测试对象：run_adversarial_audit per-source strategy metric keys
    目的/目标：per_source_reports 含 sharpe_ratio 等须 BLOCK gate_bypass
    验证点：blocking_reasons 含 write_manager_or_db_validation_gate_bypass
    失败含义：策略回测指标渗入排练报告未被审计捕获
    """
    from backend.app.ops.sandbox_clean_write.adversarial_audit import (
        AdversarialAuditRequest,
        run_adversarial_audit,
    )
    from backend.app.ops.sandbox_clean_write.audit_decision import AuditDecision

    paths = _run_rehearsal(tmp_path)
    report = json.loads(paths["report_path"].read_text(encoding="utf-8"))
    for src in report["per_source_reports"]:
        if src.get("source_id") == "baostock":
            src["sharpe_ratio"] = 1.23
    paths["report_path"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    result = run_adversarial_audit(
        AdversarialAuditRequest(
            rehearsal_report=paths["report_path"],
            sandbox_db=paths["sandbox_db"],
            evidence_dir=paths["evidence_dir"],
        )
    )
    assert result.decision == AuditDecision.BLOCK_PRODUCTION_WRITE
    assert "write_manager_or_db_validation_gate_bypass" in {f.code for f in result.blocking_reasons}


def test_r3g02AdversarialAudit_productionMutationClaimBlocks(tmp_path: Path) -> None:
    """覆盖范围：P2-02 gate_bypass production_mutation_allowed 对抗测
    测试对象：run_adversarial_audit 顶层 production_mutation_allowed
    目的/目标：报告声称 production mutation 须 BLOCK gate_bypass
    验证点：blocking_reasons 含 write_manager_or_db_validation_gate_bypass
    失败含义：契约 block_if gate_bypass 无专门端到端测试
    """
    from backend.app.ops.sandbox_clean_write.adversarial_audit import (
        AdversarialAuditRequest,
        run_adversarial_audit,
    )
    from backend.app.ops.sandbox_clean_write.audit_decision import AuditDecision

    paths = _run_rehearsal(tmp_path)
    report = json.loads(paths["report_path"].read_text(encoding="utf-8"))
    report["production_mutation_allowed"] = True
    paths["report_path"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    result = run_adversarial_audit(
        AdversarialAuditRequest(
            rehearsal_report=paths["report_path"],
            sandbox_db=paths["sandbox_db"],
            evidence_dir=paths["evidence_dir"],
        )
    )
    assert result.decision == AuditDecision.BLOCK_PRODUCTION_WRITE
    assert "write_manager_or_db_validation_gate_bypass" in {f.code for f in result.blocking_reasons}


def test_r3g02AuditCli_dataRootProductionDbPathRejected(tmp_path: Path) -> None:
    """覆盖范围：P2-03 audit CLI DATA_ROOT 生产 duckdb 拒绝
    测试对象：sandbox_clean_write_audit + DATA_ROOT/duckdb/quant_monitor.duckdb
    目的/目标：与 R3G-01 对齐第二生产路径 fail-closed
    验证点：CliFailure 含 production DB path refused
    失败含义：audit CLI 可绑定 DATA_ROOT 生产库
    """
    from backend.app.cli.data_commands import sandbox_clean_write_audit
    from backend.app.cli.errors import CliFailure

    with pytest.raises(CliFailure, match="production DB path refused"):
        sandbox_clean_write_audit(
            rehearsal_report=tmp_path / "report.json",
            sandbox_db=PROJECT_ROOT / "data" / "duckdb" / "quant_monitor.duckdb",
            evidence_dir=tmp_path / "evidence",
            decision_report=tmp_path / "audit_decision.json",
        )


def test_r3g02AdversarialAudit_missingGateRationaleBlocks(tmp_path: Path) -> None:
    """覆盖范围：P2-04 adhoc DH 缺 gate_rationale
    测试对象：run_adversarial_audit §3.1 第三条
    目的/目标：无 R3F profile 且缺 gate_rationale 须 BLOCK
    验证点：blocking_reasons 含 missing_data_health_profile_evidence
    失败含义：adhoc 重实现 DH 未被审计识别
    """
    from backend.app.ops.sandbox_clean_write.adversarial_audit import (
        AdversarialAuditRequest,
        run_adversarial_audit,
    )
    from backend.app.ops.sandbox_clean_write.audit_decision import AuditDecision

    paths = _run_rehearsal(tmp_path)
    report = json.loads(paths["report_path"].read_text(encoding="utf-8"))
    _patch_gate_ready_report(report)
    for src in report["per_source_reports"]:
        if src.get("domain") == "cn_equity_daily_bar":
            src["data_health_summary"] = {
                k: v for k, v in src["data_health_summary"].items() if k != "gate_rationale"
            }
    paths["report_path"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    result = run_adversarial_audit(
        AdversarialAuditRequest(
            rehearsal_report=paths["report_path"],
            sandbox_db=paths["sandbox_db"],
            evidence_dir=paths["evidence_dir"],
        )
    )
    assert result.decision == AuditDecision.BLOCK_PRODUCTION_WRITE
    assert "missing_data_health_profile_evidence" in {f.code for f in result.blocking_reasons}


def test_r3g02Contract_warningIfIncludesApproximateCalendar() -> None:
    """覆盖范围：P2-07 契约 warning_if 文档化近似 calendar 上限
    测试对象：r3g02_audit.warning_if
    目的/目标：approximate_calendar_evidence 须在契约 warning_if 中机读声明
    验证点：warning_if 含 approximate_calendar_evidence
    失败含义：WARN 语义无契约 SSOT，审批流无法对齐
    """
    warning_if = set(_contract()["r3g02_audit"].get("warning_if") or [])
    assert "approximate_calendar_evidence" in warning_if


def test_r3g02RehearsalLoader_noDisallowedJq2ptradeApiSurface() -> None:
    """覆盖范围：P2-06 rehearsal_loader JQ2PTrade 模式专审
    测试对象：rehearsal_loader.py 静态面
    目的/目标：loader 仅采纳 DataBundle 形状，不得定义禁止交易/get_* API
    验证点：scan_forbidden_function_defs 对 loader 路径零命中
    失败含义：JQ2PTrade 执行 API 可能经 loader 渗入 Round3G runtime
    """
    from tests.contract_gate_support import FORBIDDEN_TRADING_DEF_NAMES, scan_forbidden_function_defs

    loader = PROJECT_ROOT / "backend/app/ops/sandbox_clean_write/rehearsal_loader.py"
    violations = scan_forbidden_function_defs(
        FORBIDDEN_TRADING_DEF_NAMES
        | frozenset(
            {
                "get_open_orders",
                "get_portfolio",
                "get_positions",
                "get_orders",
                "get_trades",
            }
        ),
        roots=(loader.parent,),
    )
    loader_hits = [v for v in violations if "rehearsal_loader.py" in v]
    assert loader_hits == [], f"rehearsal_loader forbidden API defs: {loader_hits}"


def test_r3g02AdversarialAudit_missingEvidenceDirBlocks(tmp_path: Path) -> None:
    """覆盖范围：P1-05 evidence_dir 缺失 fail-closed
    测试对象：run_adversarial_audit evidence_dir 存在性
    目的/目标：report 存在但 evidence_dir 非目录须 BLOCK
    验证点：blocking_reasons 含 missing_rehearsal_report
    失败含义：无证据目录仍可能 PASS
    """
    from backend.app.ops.sandbox_clean_write.adversarial_audit import (
        AdversarialAuditRequest,
        run_adversarial_audit,
    )
    from backend.app.ops.sandbox_clean_write.audit_decision import AuditDecision

    paths = _run_rehearsal(tmp_path)
    missing_evidence = tmp_path / "no_such_evidence_dir"
    result = run_adversarial_audit(
        AdversarialAuditRequest(
            rehearsal_report=paths["report_path"],
            sandbox_db=paths["sandbox_db"],
            evidence_dir=missing_evidence,
        )
    )
    assert result.decision == AuditDecision.BLOCK_PRODUCTION_WRITE
    assert "missing_rehearsal_report" in {f.code for f in result.blocking_reasons}


def test_r3g02AdversarialAudit_fredAuthPostureWarnsWhenNoEvidence(tmp_path: Path) -> None:
    """覆盖范围：P2-06 fred requires_user_authorization posture
    测试对象：run_adversarial_audit fred 授权证据
    目的/目标：catalog 要求用户授权但无授权证据时至少 WARN
    验证点：warning_reasons 含 fred_authorization_evidence_missing
    失败含义：fred 授权 posture 未纳入审计
    """
    from backend.app.ops.sandbox_clean_write.adversarial_audit import (
        AdversarialAuditRequest,
        run_adversarial_audit,
    )
    from backend.app.ops.sandbox_clean_write.audit_decision import AuditDecision

    paths = _run_rehearsal(tmp_path)
    report = json.loads(paths["report_path"].read_text(encoding="utf-8"))
    _patch_gate_ready_report(report)
    paths["report_path"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    result = run_adversarial_audit(
        AdversarialAuditRequest(
            rehearsal_report=paths["report_path"],
            sandbox_db=paths["sandbox_db"],
            evidence_dir=paths["evidence_dir"],
        )
    )
    assert result.decision == AuditDecision.WARN_ALLOW_WITH_MANUAL_APPROVAL
    assert "fred_authorization_evidence_missing" in {f.code for f in result.warning_reasons}


def test_r3g02Package_exportsAuditApi() -> None:
    """覆盖范围：P3-01 __init__ 导出 audit API
    测试对象：backend.app.ops.sandbox_clean_write
    目的/目标：包级可发现 run_adversarial_audit / AuditResult
    验证点：__all__ 含对抗审计公共符号
    失败含义：审计 API 仅能通过深层 import 访问
    """
    from backend.app.ops import sandbox_clean_write as scw

    assert "run_adversarial_audit" in scw.__all__
    assert "AuditResult" in scw.__all__
    assert "AdversarialAuditRequest" in scw.__all__
    assert callable(scw.run_adversarial_audit)


def test_r3g02AuditResult_serializesWithoutDeadEnumGuard() -> None:
    """覆盖范围：P3-02 AuditResult.serialize 无 StrEnum 死代码
    测试对象：audit_decision.AuditResult.serialize
    目的/目标：合法枚举序列化不触发冗余校验分支
    验证点：serialize 成功且 decision 字段正确
    失败含义：死代码掩盖真实 contract 校验缺失
    """
    from backend.app.ops.sandbox_clean_write.audit_decision import (
        AuditDecision,
        AuditResult,
    )

    result = AuditResult(
        decision=AuditDecision.PASS_ALLOW_LIMITED_PROD_WRITE,
        blocking_reasons=(),
        warning_reasons=(),
        evidence_paths=(),
    )
    payload = result.serialize()
    assert payload["decision"] == "PASS_ALLOW_LIMITED_PROD_WRITE"