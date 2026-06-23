"""Trellis 审计溯源权威门禁测试（Batch 2.75 plan freeze）。

覆盖范围：归档任务 audit.jsonl、AUDIT.plan、plan.freeze 与 018C follow-up
是否把原始任务卡、地图与未闭合项覆盖索引纳入审计溯源权威集。
"""

from __future__ import annotations

import json

from tests.contract_gate_support import PROJECT_ROOT

TASK_DIR = PROJECT_ROOT / ".trellis/tasks/archive/2026-06/06-21-round3-batch2-75-live-pilot"
AUDIT_JSONL = TASK_DIR / "audit.jsonl"
AUDIT_PLAN = TASK_DIR / "AUDIT.plan.md"
PLAN_FREEZE = TASK_DIR / "plan.freeze.md"

REQUIRED_AUDIT_PATHS = (
    "docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018B_production_live_pilot_gate.md",
    "MIGRATION_MAP.md",
    "ROUND3_BATCH_IMPLEMENTATION_MAP.md",
    "docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md",
)


def _audit_jsonl_paths() -> list[str]:
    paths: list[str] = []
    for line in AUDIT_JSONL.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        paths.append(json.loads(line)["file"].replace("\\", "/"))
    return paths


def test_auditJsonl_includesTraceAuthorityFiles() -> None:
    """覆盖范围：Batch 2.75 归档任务 audit.jsonl 是否收录溯源权威文件
    测试对象：.trellis/tasks/archive/.../audit.jsonl 与 REQUIRED_AUDIT_PATHS
    目的/目标：审计轨迹必须能倒查到原始任务卡与三份地图/覆盖文档
    验证点：jsonl 每条 file 字段含四个 required 路径；磁盘上对应文件存在
    失败含义：审计轨迹少记了权威文档，事后无法核对任务卡与地图是否一致
    """
    paths = _audit_jsonl_paths()
    for required in REQUIRED_AUDIT_PATHS:
        assert required in paths, f"audit.jsonl missing trace authority: {required}"
        assert (PROJECT_ROOT / required).is_file(), f"missing on disk: {required}"


def test_auditPlan_assignsA1A5A8SourceTraceDuties() -> None:
    """覆盖范围：AUDIT.plan.md 是否给 A1/A5/A8 分配溯源职责
    测试对象：.trellis/tasks/archive/.../AUDIT.plan.md
    目的/目标：审计阶段各维度知道要倒查原始任务卡与 AC 来源链
    验证点：含 Trace Authority Set；A1 做 original-source trace；A5 做 AC source-chain；A8 做 red-flags test-gap；并写明必须倒查原始任务卡
    失败含义：审计 plan 未分派溯源职责，Batch 2.75 冻结门禁形同虚设
    """
    text = AUDIT_PLAN.read_text(encoding="utf-8")
    assert "Trace Authority Set" in text
    assert "A1 必须执行 original-source trace" in text
    assert "A5 必须执行 AC source-chain trace" in text
    assert "A8 必须执行 original-red-flags test-gap trace" in text
    assert "A1 / A5 / A8 必须倒查原始任务卡" in text


def test_auditPlan_includesTraceAuthorityTable() -> None:
    """覆盖范围：AUDIT.plan.md 溯源权威表是否列出全部关键文件
    测试对象：AUDIT.plan.md 中的 trace authority 表行
    目的/目标：审计人一眼能看到要核对哪些 SSOT 文档
    验证点：正文含 018B、MIGRATION_MAP、ROUND3_MAP、UNRESOLVED_ITEM_TASK_COVERAGE、original-plan-trace、integration-ledger 等 marker
    失败含义：溯源表缺行，审计可能漏核对地图或覆盖索引
    """
    text = AUDIT_PLAN.read_text(encoding="utf-8")
    for marker in (
        "018B_production_live_pilot_gate.md",
        "MIGRATION_MAP.md",
        "ROUND3_BATCH_IMPLEMENTATION_MAP.md",
        "UNRESOLVED_ITEM_TASK_COVERAGE.md",
        "original-plan-trace.md",
        "integration-ledger.md",
    ):
        assert marker in text, f"AUDIT.plan missing trace row marker: {marker}"


def test_planFreeze_includesAuditSourceTraceGate() -> None:
    """覆盖范围：plan.freeze.md 是否写入审计溯源门禁条款
    测试对象：.trellis/tasks/archive/.../plan.freeze.md
    目的/目标：计划一冻结就要把审计溯源门禁写死，不能事后补洞
    验证点：含 Audit source trace gate；audit.jsonl includes original task card；A1/A5/A8；PH-B0 includes source trace authority check
    失败含义：冻结文档未写溯源门禁，后续审计可能跳过原始任务卡核对
    """
    text = PLAN_FREEZE.read_text(encoding="utf-8")
    assert "Audit source trace gate" in text
    assert "audit.jsonl` includes original task card" in text
    assert "A1 / A5 / A8" in text
    assert "PH-B0 includes source trace authority check" in text


def test_phB0_includesB07SourceTraceCheck() -> None:
    """覆盖范围：AUDIT.plan PH-B0 是否含 B0-7 溯源权威检查项
    测试对象：AUDIT.plan.md 中 B0-7 检查点
    目的/目标：审计启动前必须确认已读齐原始来源权威文件集
    验证点：含 B0-7 与 original-source trace authority set 措辞
    失败含义：启动清单缺溯源检查，审计 bootstrap 可能漏读关键文档
    """
    text = AUDIT_PLAN.read_text(encoding="utf-8")
    assert "B0-7" in text
    assert "original-source trace authority set" in text


def test_followup018C_documentsExternalReferencesAndBoundaries() -> None:
    """覆盖范围：018C 跟进任务卡的外部参考与边界声明
    测试对象：018C_tdx_pytdx_low_cost_probe.md
    目的/目标：probe 任务写明参考仓库、数据通路与不默认启用 tdx 的约束
    验证点：含列出的 GitHub 链接；SourceRegistry→fetch port→raw evidence 链路；No default enablement of tdx_pytdx；No silent fallback；stock_zh_a_daily 不能闭合 Batch 2.75 Request 2
    失败含义：018C 边界不清，可能被误用为闭合 live pilot Request 2 的捷径
    """
    task = (
        PROJECT_ROOT
        / "docs/implementation_tasks/ROUND_3_MODELING_LAYERS"
        / "018C_tdx_pytdx_low_cost_probe.md"
    )
    text = task.read_text(encoding="utf-8")

    for marker in (
        "https://github.com/quant-king299/EasyXT",
        "https://github.com/quant-king299/JQ2PTrade",
        "https://github.com/quant-king299/ptqmt-site",
        "https://github.com/eosphoros-ai/DB-GPT",
        "https://github.com/eosphoros-ai/DB-GPT-Hub",
        "https://github.com/bebopze/tdx-quant",
        "https://github.com/afute/TdxQuantNet",
        "SourceRegistry -> CapabilityRegistry -> RoutePreview -> ResourceGuard -> fetch port "
        "-> raw evidence",
        "No default enablement of `tdx_pytdx`",
        "No silent fallback",
        "stock_zh_a_daily` candidate cannot satisfy Batch 2.75 `stock_zh_a_hist` "
        "Request 2 closeout",
    ):
        assert marker in text, f"018C missing required boundary/detail: {marker}"


def test_round3Map_tracksFollowup018C() -> None:
    """覆盖范围：ROUND3 地图是否跟踪 018C follow-up 切片
    测试对象：ROUND3_BATCH_IMPLEMENTATION_MAP.md
    目的/目标：地图读者知道 018C 是 Batch 2.75 follow-up 且不能闭合 Request 2
    验证点：含 R3-B2.75-FOLLOWUP-DATA-INTERFACE-PROBE、018C_tdx_pytdx_low_cost_probe.md、cannot close Batch 2.75 Request 2、Batch 2.75 follow-up
    失败含义：地图未登记 018C，协调人不知道 probe 与 live pilot 的边界
    """
    text = (PROJECT_ROOT / "ROUND3_BATCH_IMPLEMENTATION_MAP.md").read_text(encoding="utf-8")
    assert "R3-B2.75-FOLLOWUP-DATA-INTERFACE-PROBE" in text
    assert "018C_tdx_pytdx_low_cost_probe.md" in text
    assert "cannot close Batch 2.75 Request 2" in text
    assert "Batch 2.75 follow-up" in text
