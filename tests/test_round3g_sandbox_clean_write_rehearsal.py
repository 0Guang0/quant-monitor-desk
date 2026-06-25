"""Round 3G R3G-01 sandbox clean-write rehearsal 契约门禁。"""

from __future__ import annotations

from tests.contract_gate_support import PROJECT_ROOT, load_yaml

CONTRACT = PROJECT_ROOT / "specs/contracts/sandbox_clean_write_contract.yaml"


def _contract() -> dict:
    return load_yaml(CONTRACT)


def test_r3g01Contract_sandboxOnlyBlocksProductionMutation() -> None:
    """覆盖范围：R3G-01 rehearsal 契约 fail-closed 语义
    测试对象：sandbox_clean_write_contract.yaml r3g01_rehearsal
    目的/目标：排练阶段必须 sandbox-only 且禁止 production mutation
    验证点：production_mutation_allowed 为 false；sandbox_only 为 true
    失败含义：契约允许生产写路径，Batch 3G 安全边界被突破
    """
    gate = _contract()["r3g01_rehearsal"]
    assert gate["production_mutation_allowed"] is False
    assert gate["sandbox_only"] is True


def test_r3g01Contract_requiresRehearsalReportFields() -> None:
    """覆盖范围：R3G-01 排练报告必填字段
    测试对象：r3g01_rehearsal.required_report_fields
    目的/目标：排练证据须可审计 lineage 与 write_manager 操作
    验证点：必填字段含 rollback_artifact_path 与 write_manager_operation_id
    失败含义：排练报告缺关键字段会导致 3G 证据链不可追溯
    """
    fields = set(_contract()["r3g01_rehearsal"]["required_report_fields"])
    assert "rollback_artifact_path" in fields
    assert "write_manager_operation_id" in fields
    assert "source_fetch_id_coverage" in fields


def test_r3g01TaskCard_linkedFromContract() -> None:
    """覆盖范围：契约与 R3G-01 任务卡交叉引用
    测试对象：canonical_task_cards.R3G-01
    目的/目标：契约 SSOT 须指向可读的冻结任务卡路径
    验证点：任务卡文件存在且正文引用本契约
    失败含义：Execute 无法从契约路由到 R3G-01 实施说明
    """
    rel = _contract()["canonical_task_cards"]["R3G-01"]
    card = PROJECT_ROOT / rel
    assert card.is_file(), f"missing task card: {rel}"
    assert "sandbox_clean_write_contract.yaml" in card.read_text(encoding="utf-8")
