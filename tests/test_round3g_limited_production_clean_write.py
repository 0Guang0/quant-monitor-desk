"""Round 3G R3G-03 limited production clean-write 入口契约门禁。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.contract_gate_support import PROJECT_ROOT, load_yaml

CONTRACT = PROJECT_ROOT / "specs/contracts/sandbox_clean_write_contract.yaml"
R3G03_FIXTURES = PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g03"
APPROVAL_FIXTURE = R3G03_FIXTURES / "approval_minimal.yaml"
AUDIT_FIXTURE = R3G03_FIXTURES / "audit_decision_allow.json"
BEFORE_PROOF_FIXTURE = R3G03_FIXTURES / "before_proof_minimal.json"
ROLLBACK_FIXTURE = R3G03_FIXTURES / "rollback_plan_minimal.json"


def _contract() -> dict:
    return load_yaml(CONTRACT)


def _write_aligned_approval_audit(
    tmp_path: Path,
    *,
    audit_overrides: dict | None = None,
    approval_overrides: dict | None = None,
) -> tuple[Path, Path]:
    """Write approval+audit pair with matching audit_decision_file path."""
    import yaml

    audit = json.loads(AUDIT_FIXTURE.read_text(encoding="utf-8"))
    if audit_overrides:
        audit.update(audit_overrides)
    audit_path = tmp_path / "audit.json"
    audit_path.write_text(json.dumps(audit), encoding="utf-8")
    raw = yaml.safe_load(APPROVAL_FIXTURE.read_text(encoding="utf-8"))
    if approval_overrides:
        raw.update(approval_overrides)
    raw["audit_decision_file"] = audit_path.as_posix()
    approval_path = tmp_path / "approval.yaml"
    approval_path.write_text(yaml.dump(raw), encoding="utf-8")
    return approval_path, audit_path


def _audit_sandbox_promote_db(tmp_path: Path) -> Path:
    """Place promote test DB under .audit-sandbox (allowed by _assert_within_data_root)."""
    db_dir = PROJECT_ROOT / ".audit-sandbox" / "round3g" / "pytest" / tmp_path.name
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / "r3g03_promote_fixture.duckdb"
    if db_path.is_file():
        db_path.unlink()
    return db_path


@pytest.fixture
def r3g03_artifact_paths(tmp_path: Path) -> dict[str, Path]:
    """复制 r3g03 fixture 到 audit-sandbox 路径，after_proof 为可写输出路径。"""
    prod_db = _audit_sandbox_promote_db(tmp_path)
    before = json.loads(BEFORE_PROOF_FIXTURE.read_text(encoding="utf-8"))
    before["production_db_path"] = str(prod_db)
    before_path = tmp_path / "before_proof.json"
    before_path.write_text(json.dumps(before, indent=2), encoding="utf-8")
    rollback = json.loads(ROLLBACK_FIXTURE.read_text(encoding="utf-8"))
    rollback["production_db_path"] = str(prod_db)
    rollback_path = tmp_path / "rollback_plan.json"
    rollback_path.write_text(json.dumps(rollback, indent=2), encoding="utf-8")
    audit = json.loads(AUDIT_FIXTURE.read_text(encoding="utf-8"))
    audit["production_db_path"] = str(prod_db)
    audit_path = tmp_path / "audit_decision.json"
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    approval_text = APPROVAL_FIXTURE.read_text(encoding="utf-8").replace(
        ".audit-sandbox/round3g/r3g03_promote_fixture.duckdb",
        prod_db.as_posix(),
    )
    approval_text = approval_text.replace(
        "tests/fixtures/sandbox_clean_write/r3g03/audit_decision_allow.json",
        audit_path.as_posix(),
    ).replace(
        "tests/fixtures/sandbox_clean_write/r3g03/rollback_plan_minimal.json",
        rollback_path.as_posix(),
    )
    approval_path = tmp_path / "approval.yaml"
    approval_path.write_text(approval_text, encoding="utf-8")
    return {
        "approval": approval_path,
        "audit": audit_path,
        "before_proof": before_path,
        "rollback_plan": rollback_path,
        "after_proof": tmp_path / "after_proof.json",
        "prod_db": prod_db,
        "evidence_dir": tmp_path / "evidence",
    }


def test_r3g03Contract_requiresExplicitUserApproval() -> None:
    """覆盖范围：R3G-03 limited entry 人工审批门
    测试对象：r3g03_limited_entry.explicit_user_approval_required
    目的/目标：有限生产 clean-write 必须显式用户批准，禁止 agent 代签
    验证点：explicit_user_approval_required 为 true
    失败含义：无人工批准门会导致自动化路径误触发生产写
    """
    entry = _contract()["r3g03_limited_entry"]
    assert entry["explicit_user_approval_required"] is True
    assert entry["before_after_proof_required"] is True


def test_r3g03Contract_blocksAgentTriggeredWrite() -> None:
    """覆盖范围：R3G-03 block_if 对 agent 触发写路径的拒绝
    测试对象：r3g03_limited_entry.block_if
    目的/目标：limited entry 必须 fail-closed 拒绝 agent 触发的写路径
    验证点：block_if 含 agent_triggered_write_path
    失败含义：agent 可能绕过 WriteManager 与用户审批链
    """
    block_if = set(_contract()["r3g03_limited_entry"]["block_if"])
    assert "agent_triggered_write_path" in block_if
    assert "cap_expansion" in block_if


def test_r3g03CandidateCaps_boundFredAuthorization() -> None:
    """覆盖范围：R3G-03 candidate_caps 对 FRED 授权与默认禁用
    测试对象：candidate_caps.fred
    目的/目标：宏观序列候选须保持 disabled-by-default 且要求用户授权
    验证点：requires_user_authorization 与 enabled_by_default 符合 registry 语义
    失败含义：FRED 可能在未授权时被 3G 路径误选为默认源
    """
    fred = _contract()["candidate_caps"]["fred"]
    assert fred["requires_user_authorization"] is True
    assert fred["enabled_by_default"] is False
    assert "macro_series" in fred["allowed_domains"]


# --- PromoteEntry (9.0) ------------------------------------------------------


def test_PromoteEntry_moduleExportsRunner() -> None:
    """覆盖范围：R3G-03 limited_production_entry 模块可导入
    测试对象：limited_production_entry.run_limited_production_entry
    目的/目标：Boot 确认 promote runner 模块存在且可加载
    验证点：run_limited_production_entry 可调用
    失败含义：Execute 9.0 无法挂载 limited production entry
    """
    from backend.app.ops.sandbox_clean_write.limited_production_entry import (
        run_limited_production_entry,
    )

    assert callable(run_limited_production_entry)


# --- ApprovalContract (9.1) --------------------------------------------------


def test_ApprovalContract_validatesAlignedFixture() -> None:
    """覆盖范围：approval 与 audit_decision 字段对齐
    测试对象：validate_approval_contract
    目的/目标：AC-02 四门之一 — approval/audit 逐字段一致才放行
    验证点：fixture 对齐时不抛错
    失败含义：合法 promote 被误拒或非法 promote 被放行
    """
    from backend.app.ops.sandbox_clean_write.approval_contract import (
        validate_approval_contract,
    )

    contract, audit, candidate = validate_approval_contract(APPROVAL_FIXTURE, AUDIT_FIXTURE)
    assert contract.approval_id.startswith("r3g03")
    assert candidate.source_id == "baostock"


def test_ApprovalContract_missingApprovalFile_blocks() -> None:
    """覆盖范围：block_if missing_approval_file
    测试对象：load_approval_contract
    目的/目标：缺 approval YAML 时 fail-closed
    验证点：不存在路径抛 ApprovalContractError
    失败含义：无 approval 仍可 promote
    """
    from backend.app.ops.sandbox_clean_write.approval_contract import (
        ApprovalContractError,
        load_approval_contract,
    )

    with pytest.raises(ApprovalContractError, match="missing_approval_file"):
        load_approval_contract(PROJECT_ROOT / "nonexistent_approval.yaml")


def test_ApprovalContract_auditDecisionNotAllowing_blocks(tmp_path: Path) -> None:
    """覆盖范围：block_if audit_decision_not_allowing_entry
    测试对象：validate_approval_contract decision enum
    目的/目标：BLOCK_PRODUCTION_WRITE 决策不得放行 promote
    验证点：decision=BLOCK 时抛错
    失败含义：审计拒绝后仍可进入 limited production
    """
    from backend.app.ops.sandbox_clean_write.approval_contract import (
        ApprovalContractError,
        validate_approval_contract,
    )

    audit = json.loads(AUDIT_FIXTURE.read_text(encoding="utf-8"))
    audit["decision"] = "BLOCK_PRODUCTION_WRITE"
    approval_path, audit_path = _write_aligned_approval_audit(
        tmp_path,
        audit_overrides={"decision": "BLOCK_PRODUCTION_WRITE"},
    )
    with pytest.raises(ApprovalContractError, match="audit_decision_not_allowing_entry"):
        validate_approval_contract(approval_path, audit_path)


def test_ApprovalContract_approvalAuditMismatch_blocks(tmp_path: Path) -> None:
    """覆盖范围：block_if approval_audit_mismatch
    测试对象：validate_approval_contract 字段 equality
    目的/目标：approval 与 audit 的 symbol/window 不一致时拒绝
    验证点：篡改 audit symbols 后抛错
    失败含义：approval 与 audit 可不对齐仍 promote
    """
    from backend.app.ops.sandbox_clean_write.approval_contract import (
        ApprovalContractError,
        validate_approval_contract,
    )

    approval_path, audit_path = _write_aligned_approval_audit(tmp_path)
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["symbols"] = ["sz.000001"]
    audit_path.write_text(json.dumps(audit), encoding="utf-8")
    with pytest.raises(ApprovalContractError, match="approval_audit_mismatch"):
        validate_approval_contract(approval_path, audit_path)


def test_ApprovalContract_capExpansion_blocks(tmp_path: Path) -> None:
    """覆盖范围：block_if cap_expansion
    测试对象：validate_r3g03_source_caps
    目的/目标：超 r3g03_max_symbols 时拒绝
    验证点：11 个 symbol 抛 cap 错误
    失败含义：cap 可被 approval 静默扩大
    """
    from backend.app.ops.sandbox_clean_write.approval_contract import (
        ApprovalCandidate,
        ApprovalContractError,
        validate_r3g03_source_caps,
    )

    symbols = tuple(f"sh.60000{i}" for i in range(11))
    candidate = ApprovalCandidate(
        source_id="baostock",
        domain="cn_equity_daily_bar",
        symbols=symbols,
        start_date="2026-05-01",
        end_date="2026-05-30",
        max_rows=100,
        target_table="market_bar_clean",
    )
    with pytest.raises(ApprovalContractError, match="max 10 symbols"):
        validate_r3g03_source_caps(candidate)


def test_ApprovalContract_agentTriggeredWrite_blocks(tmp_path: Path) -> None:
    """覆盖范围：block_if agent_triggered_write_path
    测试对象：validate_approval_contract no_agent_triggered_write
    目的/目标：no_agent_triggered_write=false 时拒绝
    验证点：篡改 approval YAML 后抛错
    失败含义：agent 路径可触发生产写
    """
    import yaml

    from backend.app.ops.sandbox_clean_write.approval_contract import (
        ApprovalContractError,
        validate_approval_contract,
    )

    raw = yaml.safe_load(APPROVAL_FIXTURE.read_text(encoding="utf-8"))
    raw["no_agent_triggered_write"] = False
    approval_path = tmp_path / "approval_agent.yaml"
    audit_path = tmp_path / "audit.json"
    audit_path.write_text(AUDIT_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    raw["audit_decision_file"] = audit_path.as_posix()
    approval_path.write_text(yaml.dump(raw), encoding="utf-8")
    with pytest.raises(ApprovalContractError, match="agent_triggered_write_path"):
        validate_approval_contract(approval_path, audit_path)


# --- BeforeProof (9.2) -------------------------------------------------------


def test_BeforeProof_buildsRequiredFields(tmp_path: Path) -> None:
    """覆盖范围：活卡 §7 before proof 字段
    测试对象：build_before_proof
    目的/目标：AC-05 before proof 机器可读且字段齐全
    验证点：必填字段均存在
    失败含义：before proof 缺字段导致 promote 证据链断裂
    """
    from backend.app.ops.sandbox_clean_write.approval_contract import ApprovalCandidate
    from backend.app.ops.sandbox_clean_write.limited_production_entry import build_before_proof

    candidate = ApprovalCandidate(
        source_id="baostock",
        domain="cn_equity_daily_bar",
        symbols=("sh.600000",),
        start_date="2026-05-01",
        end_date="2026-05-30",
        max_rows=100,
        target_table="market_bar_clean",
    )
    db_path = PROJECT_ROOT / ".audit-sandbox/round3g/pytest/before_proof_prod.duckdb"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    proof = build_before_proof(db_path, candidate)
    for field in (
        "target_table_row_count",
        "affected_key_range_count",
        "target_schema_hash",
        "resource_guard_decision",
    ):
        assert field in proof


def test_BeforeProof_missingFile_blocks() -> None:
    """覆盖范围：block_if missing_before_proof
    测试对象：load_before_proof
    目的/目标：缺 before proof 文件时 fail-closed
    验证点：不存在路径抛 LimitedProductionEntryError
    失败含义：无 before proof 仍可 promote
    """
    from backend.app.ops.sandbox_clean_write.limited_production_entry import (
        LimitedProductionEntryError,
        load_before_proof,
    )

    with pytest.raises(LimitedProductionEntryError, match="missing_before_proof"):
        load_before_proof(PROJECT_ROOT / "nonexistent_before.json")


# --- PromoteRunner (9.4) -----------------------------------------------------


def test_PromoteRunner_dryRunProducesReport(r3g03_artifact_paths: dict[str, Path]) -> None:
    """覆盖范围：limited entry dry_run 默认路径
    测试对象：run_limited_production_entry
    目的/目标：AC-07 默认 dry_run 产出 promote_report 且 production_mutation_allowed=false
    验证点：报告含 required_gates 与 write_manager_operation_id 字段位
    失败含义：dry_run 默认仍触发生产 mutation
    """
    from backend.app.ops.sandbox_clean_write.limited_production_entry import (
        PromoteRequest,
        run_limited_production_entry,
    )

    paths = r3g03_artifact_paths
    report = run_limited_production_entry(
        PromoteRequest(
            approval_file=paths["approval"],
            audit_decision=paths["audit"],
            before_proof=paths["before_proof"],
            after_proof=paths["after_proof"],
            rollback_plan=paths["rollback_plan"],
            evidence_dir=paths["evidence_dir"],
            dry_run=True,
        )
    )
    assert report["dry_run"] is True
    assert report["production_mutation_allowed"] is False
    assert report["write_manager_operation_id"] is None
    assert report["validation_status"]
    assert "WriteManager" in report["required_gates"]
    after = json.loads(paths["after_proof"].read_text(encoding="utf-8"))
    assert after["production_mutation_allowed"] is False
    assert paths["after_proof"].is_file()


def test_PromoteRunner_forbiddenSource_blocks(tmp_path: Path) -> None:
    """覆盖范围：forbidden source/domain
    测试对象：validate_r3g03_source_caps
    目的/目标：未在 contract caps 中的源不得 promote
    验证点：yahoo 源抛 forbidden 错误
    失败含义：禁止源可进入 limited production
    """
    from backend.app.ops.sandbox_clean_write.approval_contract import (
        ApprovalCandidate,
        ApprovalContractError,
        validate_r3g03_source_caps,
    )

    candidate = ApprovalCandidate(
        source_id="yahoo",
        domain="us_equity_daily_bar",
        symbols=("AAPL",),
        start_date="2026-05-01",
        end_date="2026-05-30",
        max_rows=10,
        target_table="market_bar_clean",
    )
    with pytest.raises(ApprovalContractError, match="forbidden or unknown source"):
        validate_r3g03_source_caps(candidate)


def test_PromoteRunner_writeManagerBypassRequiresExplicitGate() -> None:
    """覆盖范围：WriteManager/DbValidationGate bypass 对抗
    测试对象：WriteManager 构造
    目的/目标：WriteManager 无 gate 时必须抛 ValueError
    验证点：gate=None 拒绝实例化
    失败含义：可绕过 DbValidationGate 直接写生产库
    """
    from backend.app.db.write_manager import WriteManager

    with pytest.raises(ValueError, match="explicit ValidationGate"):
        WriteManager(object(), None)


# --- AfterProof (9.5) --------------------------------------------------------


def test_AfterProof_buildsRequiredFields() -> None:
    """覆盖范围：活卡 §7 after proof 字段
    测试对象：build_after_proof
    目的/目标：AC-05 写后 proof 含 WM op id 与 rollback plan id
    验证点：必填字段齐全且 dry_run inserted=0
    失败含义：after proof 不可机器校验
    """
    from backend.app.ops.sandbox_clean_write.approval_contract import ApprovalCandidate
    from backend.app.ops.sandbox_clean_write.limited_production_entry import build_after_proof

    candidate = ApprovalCandidate(
        source_id="baostock",
        domain="cn_equity_daily_bar",
        symbols=("sh.600000",),
        start_date="2026-05-01",
        end_date="2026-05-30",
        max_rows=100,
        target_table="market_bar_clean",
    )
    before = {"target_table_row_count": 0, "production_db_path": "/tmp/x.duckdb"}
    after = build_after_proof(
        before_proof=before,
        candidate=candidate,
        write_manager_operation_id=None,
        rollback_plan_id="r3g03-rollback-test",
        validation_status="PASSED",
        data_health_status="PASS",
        bundle_metrics={},
        dry_run=True,
    )
    assert after["inserted_updated_row_count"] == 0
    assert after["rollback_plan_id"] == "r3g03-rollback-test"
    assert after["write_manager_operation_id"] is None


def test_AfterProof_missingPath_blocksPromote(r3g03_artifact_paths: dict[str, Path]) -> None:
    """覆盖范围：block_if missing_after_proof
    测试对象：run_limited_production_entry after_proof 输出路径
    目的/目标：缺 after_proof 输出路径时拒绝
    验证点：after_proof=None 抛错
    失败含义：无 after proof 路径仍可完成 promote
    """
    from backend.app.ops.sandbox_clean_write.limited_production_entry import (
        LimitedProductionEntryError,
        PromoteRequest,
        run_limited_production_entry,
    )

    paths = r3g03_artifact_paths
    with pytest.raises(LimitedProductionEntryError, match="missing_after_proof"):
        run_limited_production_entry(
            PromoteRequest(
                approval_file=paths["approval"],
                audit_decision=paths["audit"],
                before_proof=paths["before_proof"],
                after_proof=None,
                rollback_plan=paths["rollback_plan"],
                evidence_dir=paths["evidence_dir"],
            )
        )


# --- PromoteCli (9.6) --------------------------------------------------------


def test_PromoteCli_missingApprovalFile_blocks() -> None:
    """覆盖范围：CLI missing_approval_file
    测试对象：sandbox_clean_write_promote
    目的/目标：CLI 缺 approval 时非零 CliFailure
    验证点：missing approval 抛 CliFailure
    失败含义：CLI 可在无 approval 时运行
    """
    from backend.app.cli.data_commands import sandbox_clean_write_promote
    from backend.app.cli.errors import CliFailure

    with pytest.raises(CliFailure, match="missing approval"):
        sandbox_clean_write_promote(
            approval_file=PROJECT_ROOT / "missing.yaml",
            audit_decision=AUDIT_FIXTURE,
            before_proof=BEFORE_PROOF_FIXTURE,
            after_proof=PROJECT_ROOT / "after.json",
            rollback_plan=ROLLBACK_FIXTURE,
        )


def test_PromoteCli_missingRollbackPlan_blocks() -> None:
    """覆盖范围：CLI missing_rollback_plan
    测试对象：sandbox_clean_write_promote
    目的/目标：CLI 缺 rollback plan 时 fail-closed
    验证点：missing rollback 抛 CliFailure
    失败含义：无 rollback 计划仍可 CLI promote
    """
    from backend.app.cli.data_commands import sandbox_clean_write_promote
    from backend.app.cli.errors import CliFailure

    with pytest.raises(CliFailure, match="missing rollback"):
        sandbox_clean_write_promote(
            approval_file=APPROVAL_FIXTURE,
            audit_decision=AUDIT_FIXTURE,
            before_proof=BEFORE_PROOF_FIXTURE,
            after_proof=PROJECT_ROOT / "after.json",
            rollback_plan=PROJECT_ROOT / "missing_rollback.json",
        )


def test_PromoteCli_helpRegistered() -> None:
    """覆盖范围：CLI promote 子命令注册
    测试对象：qmd data sandbox-clean-write promote --help
    目的/目标：活卡 §5 CLI 形状可发现
    验证点：--help 含 promote 与 --approval-file
    失败含义：用户无法发现 promote 子命令
    """
    from backend.app.cli.main import main

    with pytest.raises(SystemExit) as exc:
        main(["data", "sandbox-clean-write", "promote", "--help"])
    assert exc.value.code == 0


def test_PromoteCli_dryRunDefault(r3g03_artifact_paths: dict[str, Path]) -> None:
    """覆盖范围：CLI 默认 dry_run
    测试对象：sandbox_clean_write_promote
    目的/目标：默认不触发生产 mutation
    验证点：dry_run 报告 production_mutation_allowed=false
    失败含义：CLI 默认真写生产库
    """
    from backend.app.cli.data_commands import sandbox_clean_write_promote

    paths = r3g03_artifact_paths
    payload = sandbox_clean_write_promote(
        approval_file=paths["approval"],
        audit_decision=paths["audit"],
        before_proof=paths["before_proof"],
        after_proof=paths["after_proof"],
        rollback_plan=paths["rollback_plan"],
        evidence_dir=paths["evidence_dir"],
    )
    assert payload["production_mutation_allowed"] is False


# --- Audit repair (R3G-03) ---------------------------------------------------


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("domain", "us_equity_daily_bar"),
        ("max_rows", 999),
        ("target_table", "other_table"),
        ("start_date", "2026-01-01"),
        ("end_date", "2026-01-31"),
    ],
)
def test_ApprovalContract_approvalAuditMismatch_perField_blocks(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    """覆盖范围：approval/audit 逐字段对抗 equality
    测试对象：validate_approval_contract _mismatched_field
    目的/目标：任一 promote 字段不一致时 fail-closed
    验证点：篡改 audit 单字段后抛 approval_audit_mismatch
    失败含义：仅 symbols 不一致才被拒绝，其他字段可漂移
    """
    from backend.app.ops.sandbox_clean_write.approval_contract import (
        ApprovalContractError,
        validate_approval_contract,
    )

    audit = json.loads(AUDIT_FIXTURE.read_text(encoding="utf-8"))
    audit[field] = value
    approval_path, audit_path = _write_aligned_approval_audit(tmp_path)
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit[field] = value
    audit_path.write_text(json.dumps(audit), encoding="utf-8")
    with pytest.raises(ApprovalContractError, match="approval_audit_mismatch"):
        validate_approval_contract(approval_path, audit_path)


def test_ApprovalContract_auditDecisionFilePathMismatch_blocks(tmp_path: Path) -> None:
    """覆盖范围：CLI audit 路径与 approval audit_decision_file 交叉校验
    测试对象：validate_approval_contract audit_decision_file equality
    目的/目标：活卡 §5 要求 approval 声明的 audit 路径与实参一致
    验证点：传入与 YAML 不同的 audit 文件时拒绝
    失败含义：可挂名 approval 却传入另一 decision 文件
    """
    from backend.app.ops.sandbox_clean_write.approval_contract import (
        ApprovalContractError,
        validate_approval_contract,
    )

    other_audit = tmp_path / "other_audit.json"
    other_audit.write_text(AUDIT_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(ApprovalContractError, match="audit_decision_file"):
        validate_approval_contract(APPROVAL_FIXTURE, other_audit)


def test_ApprovalContract_rollbackPlanPathMismatch_blocks(tmp_path: Path) -> None:
    """覆盖范围：CLI rollback 路径与 approval rollback_plan_path 交叉校验
    测试对象：validate_approval_contract rollback_plan_path equality
    目的/目标：活卡 §5 rollback plan path 必须与 approval 声明一致
    验证点：传入不同 rollback plan 时拒绝
    失败含义：approval 与 rollback plan 路径可不对齐
    """
    from backend.app.ops.sandbox_clean_write.approval_contract import (
        ApprovalContractError,
        validate_approval_contract,
    )

    other_rollback = tmp_path / "other_rollback.json"
    other_rollback.write_text(ROLLBACK_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(ApprovalContractError, match="rollback_plan_path"):
        validate_approval_contract(
            APPROVAL_FIXTURE,
            AUDIT_FIXTURE,
            rollback_plan_path=other_rollback,
        )


def test_ApprovalContract_windowCapExpansion_blocks() -> None:
    """覆盖范围：block_if cap_expansion — window 天数
    测试对象：validate_r3g03_source_caps r3g03_max_window_days
    目的/目标：超过 120 天窗口时拒绝
    验证点：121 天窗口抛 cap 错误
    失败含义：window cap 可被静默扩大
    """
    from backend.app.ops.sandbox_clean_write.approval_contract import (
        ApprovalCandidate,
        ApprovalContractError,
        validate_r3g03_source_caps,
    )

    candidate = ApprovalCandidate(
        source_id="baostock",
        domain="cn_equity_daily_bar",
        symbols=("sh.600000",),
        start_date="2026-01-01",
        end_date="2026-05-01",
        max_rows=100,
        target_table="market_bar_clean",
    )
    with pytest.raises(ApprovalContractError, match="max window"):
        validate_r3g03_source_caps(candidate)


def test_ApprovalContract_noCapExpansionFlag_blocks(tmp_path: Path) -> None:
    """覆盖范围：block_if cap_expansion — no_cap_expansion 标志
    测试对象：validate_approval_contract no_cap_expansion
    目的/目标：no_cap_expansion=false 时拒绝 promote
    验证点：篡改 approval YAML 后抛 cap_expansion
    失败含义：cap expansion 标志可被绕过
    """
    import yaml

    from backend.app.ops.sandbox_clean_write.approval_contract import (
        ApprovalContractError,
        validate_approval_contract,
    )

    raw = yaml.safe_load(APPROVAL_FIXTURE.read_text(encoding="utf-8"))
    raw["no_cap_expansion"] = False
    approval_path = tmp_path / "approval_cap.yaml"
    audit_path = tmp_path / "audit.json"
    audit_path.write_text(AUDIT_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    raw["audit_decision_file"] = audit_path.as_posix()
    approval_path.write_text(yaml.dump(raw), encoding="utf-8")
    with pytest.raises(ApprovalContractError, match="cap_expansion"):
        validate_approval_contract(approval_path, audit_path)


def test_ApprovalContract_warnDecision_allowsAlignedFixture(tmp_path: Path) -> None:
    """覆盖范围：WARN_ALLOW_WITH_MANUAL_APPROVAL 放行路径
    测试对象：validate_approval_contract ALLOWING_DECISIONS
    目的/目标：WARN 决策在对齐字段时允许 limited entry
    验证点：decision=WARN 时不抛错
    失败含义：合法 WARN 决策被误拒
    """
    from backend.app.ops.sandbox_clean_write.approval_contract import validate_approval_contract

    approval_path, audit_path = _write_aligned_approval_audit(
        tmp_path,
        audit_overrides={"decision": "WARN_ALLOW_WITH_MANUAL_APPROVAL"},
    )
    validate_approval_contract(approval_path, audit_path)


def test_ApprovalContract_invalidTargetTableSql_blocks() -> None:
    """覆盖范围：target_table SQL 注入面
    测试对象：ApprovalCandidate.from_dict quote_ident 校验
    目的/目标：非法表名在契约层 fail-closed
    验证点：含引号的 target_table 抛 invalid target_table
    失败含义：恶意 YAML 可在读路径拼接 SQL
    """
    from backend.app.ops.sandbox_clean_write.approval_contract import (
        ApprovalContractError,
        ApprovalCandidate,
    )

    with pytest.raises(ApprovalContractError, match="invalid target_table"):
        ApprovalCandidate.from_dict(
            {
                "source_id": "baostock",
                "domain": "cn_equity_daily_bar",
                "symbols": ["sh.600000"],
                "start_date": "2026-05-01",
                "end_date": "2026-05-30",
                "max_rows": 100,
                "target_table": 'evil"; SELECT 1; --',
            }
        )


def test_PromoteRunner_productionDbOutsideDataRoot_blocks(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：production_db_path DATA_ROOT 边界
    测试对象：_assert_within_data_root
    目的/目标：DATA_ROOT 外路径不得 promote
    验证点：系统盘根级路径抛 PRODUCTION_DB_PATH_REJECTED
    失败含义：任意路径可成为 promote 目标库
    """
    from backend.app import config as app_config
    from backend.app.ops.sandbox_clean_write.limited_production_entry import (
        LimitedProductionEntryError,
        _assert_within_data_root,
    )

    monkeypatch.setattr(app_config, "DATA_ROOT", PROJECT_ROOT / "data")
    outside_db = Path("C:/r3g03_forbidden_promote_outside_data_root.duckdb")
    with pytest.raises(LimitedProductionEntryError, match="outside DATA_ROOT"):
        _assert_within_data_root(outside_db)


def test_PromoteRunner_dryRunSyntheticBypassReport_rejectsMutationClaim(
    r3g03_artifact_paths: dict[str, Path],
) -> None:
    """覆盖范围：PromoteRunner synthetic bypass 对抗
    测试对象：run_limited_production_entry 报告与 after_proof
    目的/目标：dry_run 报告不得声称 production_mutation_allowed=true
    验证点：报告与 after_proof 均为 false mutation
    失败含义：可伪造 promote 报告绕过 WM 门禁
    """
    from backend.app.ops.sandbox_clean_write.limited_production_entry import (
        PromoteRequest,
        run_limited_production_entry,
    )

    paths = r3g03_artifact_paths
    report = run_limited_production_entry(
        PromoteRequest(
            approval_file=paths["approval"],
            audit_decision=paths["audit"],
            before_proof=paths["before_proof"],
            after_proof=paths["after_proof"],
            rollback_plan=paths["rollback_plan"],
            evidence_dir=paths["evidence_dir"],
            dry_run=True,
        )
    )
    assert report["production_mutation_allowed"] is False
    after = json.loads(paths["after_proof"].read_text(encoding="utf-8"))
    assert after.get("production_mutation_allowed") is False
    assert after.get("write_manager_operation_id") is None


def test_PromoteRunner_forbiddenSourceE2E_blocks(r3g03_artifact_paths: dict[str, Path]) -> None:
    """覆盖范围：forbidden source E2E runner 拒绝
    测试对象：run_limited_production_entry
    目的/目标：yahoo 源不得进入 promote runner
    验证点：篡改 approval 为 yahoo 后 runner 抛错
    失败含义：仅 cap 层拒绝，runner 未 fail-closed
    """
    import yaml

    from backend.app.ops.sandbox_clean_write.limited_production_entry import (
        LimitedProductionEntryError,
        PromoteRequest,
        run_limited_production_entry,
    )

    paths = r3g03_artifact_paths
    raw = yaml.safe_load(paths["approval"].read_text(encoding="utf-8"))
    raw["source_candidates"][0]["source_id"] = "yahoo"
    raw["source_candidates"][0]["domain"] = "us_equity_daily_bar"
    raw["source_candidates"][0]["symbols"] = ["AAPL"]
    bad_approval = paths["approval"].parent / "approval_yahoo.yaml"
    bad_approval.write_text(yaml.dump(raw), encoding="utf-8")
    with pytest.raises(LimitedProductionEntryError, match="forbidden or unknown source"):
        run_limited_production_entry(
            PromoteRequest(
                approval_file=bad_approval,
                audit_decision=paths["audit"],
                before_proof=paths["before_proof"],
                after_proof=paths["after_proof"],
                rollback_plan=paths["rollback_plan"],
                evidence_dir=paths["evidence_dir"],
            )
        )


def test_PromoteCli_missingAuditDecision_blocks() -> None:
    """覆盖范围：CLI missing audit_decision
    测试对象：sandbox_clean_write_promote
    目的/目标：CLI 缺 audit decision 时 fail-closed
    验证点：missing audit 抛 CliFailure
    失败含义：无 audit 仍可 CLI promote
    """
    from backend.app.cli.data_commands import sandbox_clean_write_promote
    from backend.app.cli.errors import CliFailure

    with pytest.raises(CliFailure, match="missing audit"):
        sandbox_clean_write_promote(
            approval_file=APPROVAL_FIXTURE,
            audit_decision=PROJECT_ROOT / "missing_audit.json",
            before_proof=BEFORE_PROOF_FIXTURE,
            after_proof=PROJECT_ROOT / "after.json",
            rollback_plan=ROLLBACK_FIXTURE,
        )


def test_PromoteCli_missingBeforeProof_blocks() -> None:
    """覆盖范围：CLI missing_before_proof
    测试对象：sandbox_clean_write_promote
    目的/目标：CLI 缺 before proof 时 fail-closed
    验证点：missing before 抛 CliFailure
    失败含义：无 before proof 仍可 CLI promote
    """
    from backend.app.cli.data_commands import sandbox_clean_write_promote
    from backend.app.cli.errors import CliFailure

    with pytest.raises(CliFailure, match="missing before"):
        sandbox_clean_write_promote(
            approval_file=APPROVAL_FIXTURE,
            audit_decision=AUDIT_FIXTURE,
            before_proof=PROJECT_ROOT / "missing_before.json",
            after_proof=PROJECT_ROOT / "after.json",
            rollback_plan=ROLLBACK_FIXTURE,
        )


def test_PromoteCli_helpDocumentsPromoteFlags() -> None:
    """覆盖范围：CLI promote help 文本
    测试对象：qmd-data data sandbox-clean-write promote --help
    目的/目标：操作员可发现四门链与 dry-run 默认
    验证点：help 含 --approval-file 与 --dry-run
    失败含义：promote CLI 形状不可发现
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
            "promote",
            "--help",
        ],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        check=False,
    )
    assert proc.returncode == 0
    assert "--approval-file" in proc.stdout
    assert "--dry-run" in proc.stdout


def test_BeforeProof_invalidBackupPointer_blocks() -> None:
    """覆盖范围：backup_or_snapshot_pointer 校验
    测试对象：build_before_proof _validate_backup_pointer
    目的/目标：非法 backup 指针在 before proof 构建时拒绝
    验证点：空字符串指针抛 MISSING_BACKUP_POINTER
    失败含义：execute 前可无有效备份指针证据
    """
    from backend.app.ops.sandbox_clean_write.approval_contract import ApprovalCandidate
    from backend.app.ops.sandbox_clean_write.limited_production_entry import (
        LimitedProductionEntryError,
        build_before_proof,
    )

    candidate = ApprovalCandidate(
        source_id="baostock",
        domain="cn_equity_daily_bar",
        symbols=("sh.600000",),
        start_date="2026-05-01",
        end_date="2026-05-30",
        max_rows=100,
        target_table="market_bar_clean",
    )
    db_path = PROJECT_ROOT / ".audit-sandbox/round3g/pytest/backup_ptr.duckdb"
    with pytest.raises(LimitedProductionEntryError, match="backup_or_snapshot_pointer"):
        build_before_proof(db_path, candidate, backup_or_snapshot_pointer="")


def test_StagingRowsFromBundle_baostock_matchesEvidenceRowCount() -> None:
    """覆盖范围：rehearsal_loader bundle → staging 行映射
    测试对象：staging_rows_from_bundle（baostock bars.json）
    目的/目标：evidence 多行应全部映射为 staging 行，而非 smoke 单行
    验证点：行数=2；close 来自 evidence（2.0/3.0）非占位 10.0
    失败含义：promote 仍只写 smoke 占位，mass rehearsal 无真实灌数
    """
    from backend.app.ops.sandbox_clean_write.rehearsal_loader import (
        load_rehearsal_bundle,
        staging_rows_from_bundle,
    )
    from backend.app.ops.sandbox_clean_write.rehearsal_plan import RehearsalCandidate

    evidence = PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g01/baostock"
    candidate = RehearsalCandidate(
        source_id="baostock",
        domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        symbols_or_series=("sh.600519",),
        window_days=30,
    )
    bundle = load_rehearsal_bundle(
        candidate,
        evidence_dir=evidence,
        dry_run=False,
        cap_profile="r3g03",
    )
    rows = staging_rows_from_bundle(
        bundle,
        batch_id="test-batch",
        max_rows=100,
        start_date="2024-01-01",
        end_date="2024-12-31",
    )
    assert len(rows) == 2
    closes = sorted(r.close for r in rows)
    assert closes == [2.0, 3.0]
    assert all(r.source_used == "baostock" for r in rows)
    assert all(r.instrument_id == "sh.600519" for r in rows)


def test_PromoteRunner_execute_writesEvidenceRows_notSmokePlaceholder(
    r3g03_artifact_paths: dict[str, Path],
) -> None:
    """覆盖范围：promote execute 多行 staging → clean
    测试对象：run_limited_production_entry execute 路径
    目的/目标：execute 写入行数/字段与 bundle evidence 一致
    验证点：market_bar_clean 2 行；close 含 2.0/3.0；source_used=baostock
    失败含义：execute 仍只插 1 行 close=10.0 占位
    """
    import yaml

    from backend.app.db.connection import ConnectionManager
    from backend.app.ops.sandbox_clean_write.limited_production_entry import (
        PromoteRequest,
        run_limited_production_entry,
    )

    paths = r3g03_artifact_paths
    evidence_root = PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g01"
    backup = ".audit-sandbox/round3g/pytest/pre_execute_baostock.duckdb"

    raw = yaml.safe_load(paths["approval"].read_text(encoding="utf-8"))
    raw["source_candidates"][0]["symbols"] = ["sh.600519"]
    paths["approval"].write_text(yaml.dump(raw), encoding="utf-8")
    audit = json.loads(paths["audit"].read_text(encoding="utf-8"))
    audit["symbols"] = ["sh.600519"]
    paths["audit"].write_text(json.dumps(audit, indent=2), encoding="utf-8")

    before = json.loads(paths["before_proof"].read_text(encoding="utf-8"))
    before["backup_or_snapshot_pointer"] = backup
    before["symbols"] = ["sh.600519"]
    paths["before_proof"].write_text(json.dumps(before, indent=2), encoding="utf-8")

    from backend.app.ops.sandbox_clean_write.approval_contract import (
        load_approval_contract,
        validate_approval_contract,
    )
    from backend.app.ops.sandbox_clean_write.rollback_plan import (
        build_rollback_plan,
        write_rollback_plan,
    )

    contract = load_approval_contract(paths["approval"])
    _contract, _audit, candidate = validate_approval_contract(
        paths["approval"], paths["audit"]
    )
    rollback = build_rollback_plan(contract, candidate, before_proof=before)
    write_rollback_plan(paths["rollback_plan"], rollback)

    report = run_limited_production_entry(
        PromoteRequest(
            approval_file=paths["approval"],
            audit_decision=paths["audit"],
            before_proof=paths["before_proof"],
            after_proof=paths["after_proof"],
            rollback_plan=paths["rollback_plan"],
            evidence_dir=evidence_root,
            dry_run=False,
            execute=True,
            fred_authorization=None,
        )
    )
    assert report["production_mutation_allowed"] is True
    inserted = int(report["after_proof"]["inserted_updated_row_count"])
    assert inserted == 2

    cm = ConnectionManager(paths["prod_db"])
    with cm.reader() as con:
        rows = con.execute(
            "SELECT instrument_id, trade_date, close, source_used "
            "FROM market_bar_clean ORDER BY trade_date"
        ).fetchall()
    assert len(rows) == 2
    closes = {float(r[2]) for r in rows}
    assert closes == {2.0, 3.0}
    assert all(r[3] == "baostock" for r in rows)


def test_PromoteRunner_refusesCanonicalProductionDbPath(tmp_path: Path) -> None:
    """覆盖范围：R3G-03 promote 主库路径硬拒（对齐 R3G-01 rehearsal）
    测试对象：_assert_production_db_allowed
    目的/目标：四件套齐全也不得写 quant_monitor.duckdb 主库
    验证点：canonical 主库路径抛 PRODUCTION_DB_PATH_REJECTED
    失败含义：promote 可穿透写主库
    """
    from backend.app.ops.sandbox_clean_write.limited_production_entry import (
        LimitedProductionEntryError,
        _assert_production_db_allowed,
    )

    main_db = PROJECT_ROOT / "data" / "duckdb" / "quant_monitor.duckdb"
    with pytest.raises(LimitedProductionEntryError, match="canonical production DB"):
        _assert_production_db_allowed(main_db, mkdir_if_missing=False)


def test_StagingRowsFromBundle_akshare_matchesEvidenceRowCount() -> None:
    """覆盖范围：akshare bundle → staging 行映射
    测试对象：staging_rows_from_bundle（akshare bars.json）
    目的/目标：用户授权 validation 源在 cap 内可映射多行 evidence
    验证点：行数=2（sh.600000 两日 bar）
    失败含义：akshare 纳入 mass rehearsal 后灌数失败
    """
    from backend.app.ops.sandbox_clean_write.rehearsal_loader import (
        load_rehearsal_bundle,
        staging_rows_from_bundle,
    )
    from backend.app.ops.sandbox_clean_write.rehearsal_plan import RehearsalCandidate

    evidence = PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g01/akshare"
    candidate = RehearsalCandidate(
        source_id="akshare",
        domain="cn_equity_daily_bar",
        operation="fetch_daily_bar_validation",
        symbols_or_series=("sh.600000",),
        window_days=120,
    )
    bundle = load_rehearsal_bundle(
        candidate,
        evidence_dir=evidence,
        dry_run=False,
        cap_profile="r3g03",
    )
    rows = staging_rows_from_bundle(
        bundle,
        batch_id="test-ak",
        max_rows=100,
        allow_window_fallback=True,
    )
    assert len(rows) == 2
    assert all(r.source_used == "akshare" for r in rows)


def test_r3g03TierA_documentsRehearseAuditProdPathRegression() -> None:
    """覆盖范围：§8.1 #3 rehearse/audit 生产路径不回退
    测试对象：R3G-01/R3G-02 productionDbPathRejected 回归测
    目的/目标：promote 合并后 rehearse/audit 仍拒生产 DB 路径
    验证点：子集 pytest -k productionDbPathRejected 全绿
    失败含义：R3G-03 改动导致 sandbox 路径门禁回退
    """
    import subprocess
    import sys

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_round3g_sandbox_clean_write_rehearsal.py",
            "tests/test_round3g_pre_production_adversarial_audit.py",
            "-q",
            "-k",
            "productionDbPathRejected",
            f"--basetemp={PROJECT_ROOT / '.audit-sandbox' / 'pytest'}",
        ],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_LiveEvidenceBridge_baostock_materializesBarsFromStagedV2(tmp_path: Path) -> None:
    """覆盖范围：腿 B staged pilot v2 → promote 证据桥接
    测试对象：materialize_baostock_promote_evidence
    目的/目标：真网 raw 数组行应落成 bars.json 供 load_rehearsal_bundle 消费
    验证点：bars.json 2 行；close=1212.1/1168.63；含 raw_evidence_manifest.json
    失败含义：腿 B 证据无法接入腿 A promote，ABC 接线失败
    """
    from backend.app.ops.sandbox_clean_write.live_evidence_bridge import (
        materialize_baostock_promote_evidence,
    )

    staged = PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g01/live_wire"
    out = tmp_path / "baostock"
    materialize_baostock_promote_evidence(staged, out)
    bars = json.loads((out / "bars.json").read_text(encoding="utf-8"))["rows"]
    assert len(bars) == 2
    closes = sorted(float(r["close"]) for r in bars)
    assert closes == [1168.63, 1212.1]
    assert (out / "raw_evidence_manifest.json").is_file()
    assert (out / "pilot_v2_closeout.json").is_file()
    closeout = json.loads((out / "pilot_v2_closeout.json").read_text(encoding="utf-8"))
    assert closeout.get("sandbox_clean_write_rehearsal") is True


def test_LiveEvidenceBridge_fred_materializesMultiSeriesObservations(tmp_path: Path) -> None:
    """覆盖范围：腿 C FRED live → promote 证据桥接
    测试对象：materialize_fred_promote_evidence + staging_rows_from_bundle
    目的/目标：多 series live 证据应映射为多 instrument staging 行
    验证点：fred_evidence 3 观测；staging 含 DGS10×2 + VIXCLS×1
    失败含义：FRED 真网数据无法经同一 promote 链写入练习库
    """
    from backend.app.ops.sandbox_clean_write.live_evidence_bridge import (
        materialize_fred_promote_evidence,
    )
    from backend.app.ops.sandbox_clean_write.rehearsal_loader import (
        load_rehearsal_bundle,
        staging_rows_from_bundle,
    )
    from backend.app.ops.sandbox_clean_write.rehearsal_plan import RehearsalCandidate

    live = PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g01/live_wire/fred_live_fetch_evidence.json"
    out = tmp_path / "fred"
    materialize_fred_promote_evidence(live, out)
    candidate = RehearsalCandidate(
        source_id="fred",
        domain="macro_series",
        operation="fetch_macro_series",
        symbols_or_series=("DGS10", "VIXCLS"),
        window_days=120,
    )
    bundle = load_rehearsal_bundle(candidate, evidence_dir=out, dry_run=False, cap_profile="r3g03")
    rows = staging_rows_from_bundle(
        bundle,
        batch_id="live-wire",
        max_rows=400,
        start_date="2026-01-01",
        end_date="2026-12-31",
    )
    assert len(rows) == 3
    dgs10 = [r for r in rows if r.instrument_id == "DGS10"]
    vix = [r for r in rows if r.instrument_id == "VIXCLS"]
    assert len(dgs10) == 2
    assert len(vix) == 1
    assert dgs10[0].close == 4.4
    fred_payload = json.loads((out / "fred_evidence.json").read_text(encoding="utf-8"))
    assert fred_payload.get("retrieved_at")
    assert (out / "pilot_v2_closeout.json").is_file()

