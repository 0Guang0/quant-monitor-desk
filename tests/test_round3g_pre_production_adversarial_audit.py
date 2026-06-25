"""Round 3G R3G-02 预生产对抗审计契约门禁。"""

from __future__ import annotations

from tests.contract_gate_support import PROJECT_ROOT, load_yaml

CONTRACT = PROJECT_ROOT / "specs/contracts/sandbox_clean_write_contract.yaml"


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
