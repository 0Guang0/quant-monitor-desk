"""Round 3H Layer1-5 binding audit planning gate tests."""

from __future__ import annotations

from tests.contract_gate_support import PROJECT_ROOT

AUDIT_TEMPLATE = PROJECT_ROOT / "docs/quality/round3h_real_data_production_entry_audit.md"
R3H05_CARD = (
    PROJECT_ROOT
    / "docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY"
    / "BATCH_3H_REAL_DATA_PRODUCTION_ENTRY"
    / "R3H_05_LAYER_BINDING_AND_PRODUCTION_ENTRY_AUDIT.md"
)
BATCH05_ROOT = (
    PROJECT_ROOT
    / "docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE"
)

REQUIRED_LAYER_FIELDS = {
    "layer1_binding",
    "layer2_binding",
    "layer3_binding",
    "layer4_binding",
    "layer5_binding",
}

REQUIRED_RELEASE_TERMS = {
    "READY_WITH_EVIDENCE",
    "ADR_DISABLED_OUT_OF_SCOPE",
    "DISABLED_SOURCE",
    "source limitation",
    "route/evidence status",
}


def test_r3h05DefinesAllRound4AdmissionOutcomes() -> None:
    """覆盖范围：R3H-05 Round4 admission gate
    测试对象：R3H_05_LAYER_BINDING_AND_PRODUCTION_ENTRY_AUDIT.md
    目的/目标：Round4 只能在 PASS 或 WARN_WITH_ADR 后启动
    验证点：PASS/WARN/BLOCK 三种输出都被任务卡定义
    失败含义：Round4 admission 语义可能被执行者自由解释
    """
    text = R3H05_CARD.read_text(encoding="utf-8")
    assert "PASS_ROUND4_REAL_DATA_READY" in text
    assert "WARN_ROUND4_ALLOWED_WITH_NARROWED_SCOPE_ADR" in text
    assert "BLOCK_ROUND4_DATA_ENTRY_INCOMPLETE" in text


def test_r3hAuditTemplate_requiresLayerOneThroughFiveBindings() -> None:
    """覆盖范围：五层 Layer real-data binding 审计字段
    测试对象：round3h_real_data_production_entry_audit.md
    目的/目标：R3H 不止 source adapter，还必须绑定 Layer1-5 真实数据/evidence
    验证点：模板含 Layer1/2/3/4/5 binding 字段和 summary 行
    失败含义：Round4 可能消费只有 source readiness、没有 Layer evidence 的数据面
    """
    text = AUDIT_TEMPLATE.read_text(encoding="utf-8")
    missing = sorted(field for field in REQUIRED_LAYER_FIELDS if field not in text)
    assert not missing, f"audit template missing layer fields: {missing}"
    for layer in ("Layer1", "Layer2", "Layer3", "Layer4", "Layer5"):
        assert layer in text


def test_batch05ReleaseManifestCarriesR3hSourcePosture() -> None:
    """覆盖范围：Batch05 release manifest 对 R3H source 状态的继承
    测试对象：Batch05 manifest 与 B05_03 release card
    目的/目标：发布门禁不能隐藏 READY/ADR-disabled/DISABLED_SOURCE 状态
    验证点：Batch05 文件要求 source limitation 与 route/evidence status
    失败含义：Release manifest 可能把未完成 source 包装成已发布能力
    """
    combined = "\n".join(
        [
            (BATCH05_ROOT / "BATCH_05_TASK_CARD_MANIFEST.md").read_text(
                encoding="utf-8"
            ),
            (BATCH05_ROOT / "B05_03_release_manifest_and_package_cleanup.md").read_text(
                encoding="utf-8"
            ),
        ]
    )
    missing = sorted(term for term in REQUIRED_RELEASE_TERMS if term not in combined)
    assert not missing, f"Batch05 source posture terms missing: {missing}"
