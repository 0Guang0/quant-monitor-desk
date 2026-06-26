"""Round 3H adapter evidence-matrix planning gate tests."""

from __future__ import annotations

from tests.contract_gate_support import PROJECT_ROOT

AUDIT_TEMPLATE = PROJECT_ROOT / "docs/quality/round3h_real_data_production_entry_audit.md"
TASK_ROOT = (
    PROJECT_ROOT
    / "docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY"
    / "BATCH_3H_REAL_DATA_PRODUCTION_ENTRY"
)

REQUIRED_AUDIT_FIELDS = {
    "source_id",
    "final_decision",
    "allowed_domains",
    "adapter_fetch_port_path",
    "auth_license_decision",
    "resource_guard_cap",
    "route_ready_or_disabled_evidence",
    "replay_fixture_or_sandbox_sample",
    "fetch_log_content_hash_schema_hash_evidence",
    "data_health_result",
    "source_conflict_result",
    "layer1_binding",
    "layer2_binding",
    "layer3_binding",
    "layer4_binding",
    "layer5_binding",
    "production_entry_status",
    "release_limitation",
}

REQUIRED_EVIDENCE_TERMS = {
    "adapter",
    "auth",
    "license",
    "ResourceGuard",
    "route",
    "replay",
    "evidence",
    "fetch_log",
    "content_hash",
    "schema_hash",
    "source_fetch_id",
    "data health",
    "source conflict",
}


def test_r3hAuditTemplate_containsRequiredEvidenceColumns() -> None:
    """覆盖范围：R3H-05 审计产物字段完整性
    测试对象：docs/quality/round3h_real_data_production_entry_audit.md
    目的/目标：source READY 不能只靠 registry note，必须有证据矩阵字段
    验证点：模板包含 adapter/auth/license/guard/route/replay/hash/health/conflict/layer 字段
    失败含义：R3H 审计无法证明完整有限生产接入闭环
    """
    text = AUDIT_TEMPLATE.read_text(encoding="utf-8")
    missing = sorted(field for field in REQUIRED_AUDIT_FIELDS if field not in text)
    assert not missing, f"audit template missing fields: {missing}"


def test_r3hTaskCards_requireEvidenceNotRegistryOnly() -> None:
    """覆盖范围：R3H adapter evidence 要求
    测试对象：R3H-01 至 R3H-05 任务卡正文
    目的/目标：防止以 registry/capability declaration 伪装 adapter 完成
    验证点：任务卡整体包含 adapter、auth/license、ResourceGuard、route、replay、hash、health、conflict 证据要求
    失败含义：执行者可能只补 YAML，而不闭合真实数据接入
    """
    combined = "\n".join(
        path.read_text(encoding="utf-8") for path in TASK_ROOT.glob("R3H_*.md")
    )
    missing = sorted(term for term in REQUIRED_EVIDENCE_TERMS if term not in combined)
    assert not missing, f"R3H task cards missing evidence terms: {missing}"


def test_r3hAuditTemplate_marksPendingRowsAsRound4Blockers() -> None:
    """覆盖范围：R3H audit template 未完成状态语义
    测试对象：PENDING_R3H_EXECUTION 与 BLOCK_ROUND4_DATA_ENTRY_INCOMPLETE
    目的/目标：模板可以暂存计划，但完成审计不得保留 pending source
    验证点：PENDING_R3H_EXECUTION 明确触发 Round4 BLOCK
    失败含义：pending source 可能被 release manifest 误读为可产品化
    """
    text = AUDIT_TEMPLATE.read_text(encoding="utf-8")
    assert "PENDING_R3H_EXECUTION" in text
    assert "not a valid completed state" in text
    assert "BLOCK_ROUND4_DATA_ENTRY_INCOMPLETE" in text
