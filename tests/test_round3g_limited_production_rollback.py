"""Round 3G R3G-03 limited production rollback 契约门禁。"""

from __future__ import annotations

from tests.contract_gate_support import PROJECT_ROOT, load_yaml

CONTRACT = PROJECT_ROOT / "specs/contracts/sandbox_clean_write_contract.yaml"


def _contract() -> dict:
    return load_yaml(CONTRACT)


def test_r3g03Contract_rollbackDryRunRequired() -> None:
    """覆盖范围：R3G-03 rollback 预演要求
    测试对象：r3g03_limited_entry.rollback_dry_run_required
    目的/目标：有限生产写前必须完成 rollback dry-run 证据
    验证点：rollback_dry_run_required 为 true
    失败含义：无 rollback 预演会导致生产写后无法证明可回滚
    """
    assert _contract()["r3g03_limited_entry"]["rollback_dry_run_required"] is True


def test_r3g03Contract_blocksMissingRollbackPlan() -> None:
    """覆盖范围：R3G-03 block_if 对缺失 rollback 计划的 fail-closed
    测试对象：r3g03_limited_entry.block_if
    目的/目标：缺 rollback 计划时必须拒绝 limited entry
    验证点：block_if 含 missing_rollback_plan 与 missing_before_proof
    失败含义：无 rollback 计划仍可能进入 limited production clean-write
    """
    block_if = set(_contract()["r3g03_limited_entry"]["block_if"])
    assert "missing_rollback_plan" in block_if
    assert "missing_before_proof" in block_if
    assert "missing_after_proof" in block_if


def test_r3g03Contract_listsRequiredQmdGates() -> None:
    """覆盖范围：R3G 全阶段 QMD 门禁清单
    测试对象：required_qmd_gates
    目的/目标：3G 路径必须经过 WriteManager 与 DbValidationGate 等 QMD 组件
    验证点：清单含 WriteManager 与 DbValidationGate
    失败含义：契约未冻结 QMD 门禁会导致 clean-write 绕过验证链
    """
    gates = set(_contract()["required_qmd_gates"])
    assert "WriteManager" in gates
    assert "DbValidationGate" in gates
    assert "SourceRoutePlanner" in gates
