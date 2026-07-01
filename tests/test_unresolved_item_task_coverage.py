"""未闭合项任务覆盖索引门禁测试。

覆盖范围：UNRESOLVED_ITEM_TASK_COVERAGE 是否为 Plan 必读、是否列出全部当前 OPEN/DEFERRED ID、
各任务卡是否交叉引用映射的未闭合项，防止只读单卡而遗漏开放债。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.contract_gate_support import PROJECT_ROOT

COVERAGE = PROJECT_ROOT / "docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md"
UNRESOLVED = PROJECT_ROOT / "docs/UNRESOLVED_ISSUES_REGISTRY.md"
RESOLVED = PROJECT_ROOT / "docs/RESOLVED_ISSUES_REGISTRY.md"
TASK_INDEX = PROJECT_ROOT / "docs/implementation_tasks/TASK_INPUT_CONTEXT_INDEX.md"
TASK_README = PROJECT_ROOT / "docs/implementation_tasks/README.md"

EXPECTED_UNRESOLVED_IDS = {
    "R2.6-IMPL-6",
    "R2.6-IMPL-8",
    "R3-AUDIT-DEF-02",
    "R3-B2.75-01",
    "R3-PARTIAL-1",
    "R3-PARTIAL-3",
    "R3-PARTIAL-4",
    "D2-P1-1",
    "D2-P1-3",
    "D2-P2-1",
    "D2-P2-2",
    "D2-P3-1",
    "D7-P1-1",
    "D7-P2-2",
    "A9-P3-01",
    "R2-RISK-1",
    "R2-RISK-2",
    "R2-HYG-4",
    "R2-HYG-5",
    "B2.5-O-05",
    "R3-B25-HYG-01",
    "R3-B25-HYG-02",
    "R2-GAP-2",
    "R4-API-SEC-3",
    "R4-API-SEC-4",
    "R4-API-SEC-5",
    "R4-API-SEC-6",
    "R4-API-SEC-7",
    "R4-API-SEC-8",
    "R4-API-SEC-9",
    "R4-API-SEC-10",
    "R4-API-SEC-11",
    "R4-API-SEC-12",
    "R4-API-SEC-13",
    "R4-NOTIF-1",
    "R4-NOTIF-2",
    "R4-NOTIF-3",
    "R4-FE-2",
    "R4-FE-3",
    "R3-PROMPT14-AKSHARE-VAL-01",
    "ADV-R3X-LINEAGE-001",
    "R3Y-LINEAGE-VR-001",
    "R2-RISK-5",
}

TASK_CARD_EXPECTATIONS = {
    "ROUND_1_DATA_FOUNDATION/005_create_schema_sql.md": {
        "A9-P2-01",
        "A9-P3-01",
        "R2-GAP-1",
        "D2-P3-1",
        "R2-RISK-4",
    },
    "ROUND_1_DATA_FOUNDATION/008_implement_write_manager.md": {"R2-RISK-3", "D3-P1-2"},
    "ROUND_2_DATA_INGESTION_VALIDATION/013_implement_core_adapter_skeletons.md": {"R2-HYG-5"},
    "ROUND_2_DATA_INGESTION_VALIDATION/014_implement_data_sync_orchestrator.md": {
        "R3-PARTIAL-1",
        "R3-PARTIAL-3",
        "D2-P1-1",
        "D2-P1-3",
        "D2-P2-1",
        "D2-P2-2",
        "D2-P3-1",
        "D7-P1-1",
        "R2-RISK-1",
        "D3-P1-2",
        "R2-HYG-4",
    },
    "ROUND_2_DATA_INGESTION_VALIDATION/015_implement_data_quality_validator.md": {
        "D2-P1-1",
        "R2-HYG-5",
    },
    "ROUND_2_DATA_INGESTION_VALIDATION/016_implement_source_conflict_validator.md": {
        "R3-PARTIAL-3",
        "D2-P2-2",
        "R3-PARTIAL-4",
        "A9-P2-01",
        "R2-RISK-2",
    },
    (
        "ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/"
        "016D_define_data_sync_quick_reference_and_error_guides.md"
    ): {
        "R2.6-IMPL-6",
        "D2-P1-3",
        "R2-GAP-1",
        "D7-P2-2",
    },
    "ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016F_define_prod_equivalent_scale_benchmark.md": {
        "R2.6-IMPL-8",
        "R3-AUDIT-DEF-02",
        "R3-B25-HYG-03",
    },
    "ROUND3_EARLY_CLOSE_PLAN.md": {
        "R2.6-IMPL-8",
        "R3-AUDIT-DEF-01",
        "R3-AUDIT-DEF-02",
        "R3-AUDIT-DEF-03",
        "R3-B25-HYG-03",
    },
    "ROUND_3_MODELING_LAYERS/018A_layer1_observation_ingestion_bridge.md": {
        "R3-B25-HYG-01",
        "R2.6-IMPL-6",
        "D2-P1-3",
        "D2-P2-1",
    },
    "ROUND_3_MODELING_LAYERS/018B_production_live_pilot_gate.md": {
        "R3-B2.75-01",
        "B2.5-O-05",
        "R3-B25-HYG-01",
        "R3-B25-HYG-03",
        "qmd data",
        "layer1_ingestion_refactor_rollback_plan.md",
        "同 sprint 混做",
    },
    "ROUND_3_MODELING_LAYERS/023_implement_layer5_evidence_chain.md": {"R3-PARTIAL-4", "R2-RISK-2"},
    "ROUND_4_API_FRONTEND_AGENT_BACKTEST/024_implement_fastapi_routes.md": {
        "R2-GAP-2",
        "R4-API-SEC-3",
        "R4-API-SEC-4",
        "R4-API-SEC-5",
        "R4-API-SEC-6",
        "R4-API-SEC-7",
        "R4-API-SEC-8",
        "R4-API-SEC-9",
        "R4-API-SEC-10",
        "R4-API-SEC-11",
        "R4-API-SEC-12",
        "R4-API-SEC-13",
    },
    "ROUND_4_API_FRONTEND_AGENT_BACKTEST/026_implement_frontend_shell.md": {"R4-FE-2"},
    "ROUND_4_API_FRONTEND_AGENT_BACKTEST/027_implement_frontend_layer_pages.md": {
        "R3-B25-HYG-02",
        "R4-API-SEC-5",
        "R4-FE-3",
    },
    "ROUND_4_API_FRONTEND_AGENT_BACKTEST/028_implement_reports_and_notifications.md": {
        "R4-NOTIF-1",
        "R4-NOTIF-2",
        "R4-NOTIF-3",
        "R4-FE-2",
    },
    "ROUND_4_API_FRONTEND_AGENT_BACKTEST/029_implement_backtest_and_review.md": {"R3-PARTIAL-4"},
    "ROUND_5_INTEGRATION_RELEASE/033_implement_security_and_boundary_tests.md": {"R2-RISK-5"},
    "ROUND_5_INTEGRATION_RELEASE/034_implement_docs_consistency_check.md": {
        "R3-AUDIT-DEF-01",
        "R3-AUDIT-DEF-03",
        "R2-RISK-3",
        "R2-RISK-4",
    },
    "ROUND_5_INTEGRATION_RELEASE/035_implement_final_package_cleanup.md": {
        "R2.6-IMPL-6",
        "D2-P1-3",
        "R2-GAP-1",
        "D7-P2-2",
        "R2-RISK-5",
    },
}


def _read(path: Path) -> str:
    assert path.is_file(), f"missing expected file: {path}"
    return path.read_text(encoding="utf-8")


def test_coverageIndex_isMandatoryPlanInput() -> None:
    """覆盖范围：Plan 阶段是否把未闭合项覆盖索引列为必读输入
    测试对象：docs/implementation_tasks/README.md 与 TASK_INPUT_CONTEXT_INDEX.md
    目的/目标：做复杂任务 Plan 时不能只读单张任务卡而漏掉开放项
    验证点：两份文档都提到 UNRESOLVED_ITEM_TASK_COVERAGE.md 且含 Plan 字样
    失败含义：覆盖索引未入 Plan 必读，未闭合项可能在规划阶段被遗漏
    """
    readme = _read(TASK_README)
    index = _read(TASK_INDEX)

    assert "UNRESOLVED_ITEM_TASK_COVERAGE.md" in readme
    assert "UNRESOLVED_ITEM_TASK_COVERAGE.md" in index
    assert "Plan" in readme and "Plan" in index


def test_coverageIndex_mentionsEveryCurrentUnresolvedId() -> None:
    """覆盖范围：覆盖索引是否列出当前全部未闭合项 ID
    测试对象：UNRESOLVED_ITEM_TASK_COVERAGE.md 与 EXPECTED_UNRESOLVED_IDS 集合
    目的/目标：每个已知 OPEN/DEFERRED 项在覆盖表里有对应行
    验证点：EXPECTED_UNRESOLVED_IDS 中每个 item_id 都出现在 COVERAGE 正文
    失败含义：有开放项未进覆盖索引，Plan 阶段无法追溯到责任任务卡
    """
    text = _read(COVERAGE)
    missing = sorted(item_id for item_id in EXPECTED_UNRESOLVED_IDS if item_id not in text)
    assert not missing, f"unresolved IDs missing from coverage index: {missing}"


def test_r3ySync001_closedInResolvedNotOpen() -> None:
    """覆盖范围：R3Y-SYNC-001 adapter bypass 项的 registry 闭合状态
    测试对象：RESOLVED_ISSUES_REGISTRY、UNRESOLVED_ISSUES_REGISTRY、COVERAGE §4.5
    目的/目标：已闭合的 SYNC-001 不得仍出现在 UNRESOLVED 的 OPEN 行
    验证点：R3Y-SYNC-001 在 RESOLVED 与 COVERAGE；UNRESOLVED 无 | R3Y-SYNC-001 | OPEN；COVERAGE 邻近文本含 CLOSED
    失败含义：已修复项仍标 OPEN，会误导并行 slice 重复抢同一修复
    """
    resolved = _read(RESOLVED)
    unresolved = _read(UNRESOLVED)
    coverage = _read(PROJECT_ROOT / "docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md")

    assert "R3Y-SYNC-001" in resolved
    assert "test_r3ySync001" in resolved
    assert f"| R3Y-SYNC-001 | OPEN" not in unresolved
    assert "R3Y-SYNC-001" in coverage
    assert "CLOSED" in coverage.split("R3Y-SYNC-001", maxsplit=1)[1][:200]


def test_r3yMutProof001_closedInResolvedNotOpen() -> None:
    """覆盖范围：R3Y-MUT-PROOF-001 在 PROMPT_19 合并后应已闭合
    测试对象：RESOLVED、UNRESOLVED、COVERAGE registries
    目的/目标：mutation_proof 语义债不得仍标 OPEN，避免重复开 PROMPT_19
    验证点：R3Y-MUT-PROOF-001 在 RESOLVED 与 COVERAGE CLOSED；UNRESOLVED 无 OPEN 行
    失败含义：已修复项仍标 OPEN，会误导并行 slice 重复抢同一修复
    """
    resolved = _read(RESOLVED)
    unresolved = _read(UNRESOLVED)
    coverage = _read(COVERAGE)

    assert "R3Y-MUT-PROOF-001" in resolved
    assert "R3Y-MUT-PROOF-001" in coverage
    assert "CLOSED" in coverage.split("R3Y-MUT-PROOF-001", maxsplit=1)[1][:200]
    assert f"| R3Y-MUT-PROOF-001 | OPEN" not in unresolved


def test_r3yStagedReg001_closedInResolvedNotOpen() -> None:
    """覆盖范围：R3Y-STAGED-REG-001 在 fix β-2 合并后应已闭合
    测试对象：RESOLVED、UNRESOLVED、COVERAGE registries
    目的/目标：staged registry 旁路债不得仍标 OPEN，避免重复开 β-2
    验证点：R3Y-STAGED-REG-001 在 RESOLVED 与 COVERAGE CLOSED；UNRESOLVED 无 OPEN 行
    失败含义：已修复项仍标 OPEN，会误导并行 slice 重复抢同一修复
    """
    resolved = _read(RESOLVED)
    unresolved = _read(UNRESOLVED)
    coverage = _read(COVERAGE)

    assert "R3Y-STAGED-REG-001" in resolved
    assert "R3Y-STAGED-REG-001" in coverage
    assert "CLOSED" in coverage.split("R3Y-STAGED-REG-001", maxsplit=1)[1][:200]
    assert f"| R3Y-STAGED-REG-001 | OPEN" not in unresolved


def test_r3yPrompt15Evid001_closedInResolvedNotOpen() -> None:
    """覆盖范围：R3Y-PROMPT15-EVID-001 在 fix α-3 合并后应已闭合
    测试对象：RESOLVED、UNRESOLVED、COVERAGE registries
    目的/目标：PROMPT_15 证据链债不得仍标 OPEN，避免重复开 α-3
    验证点：R3Y-PROMPT15-EVID-001 在 RESOLVED 与 COVERAGE CLOSED；UNRESOLVED 无 OPEN 行
    失败含义：已修复项仍标 OPEN，会误导并行 slice 重复抢同一修复
    """
    resolved = _read(RESOLVED)
    unresolved = _read(UNRESOLVED)
    coverage = _read(COVERAGE)

    assert "R3Y-PROMPT15-EVID-001" in resolved
    assert "R3Y-PROMPT15-EVID-001" in coverage
    assert "CLOSED" in coverage.split("R3Y-PROMPT15-EVID-001", maxsplit=1)[1][:200]
    assert f"| R3Y-PROMPT15-EVID-001 | OPEN" not in unresolved


def test_batch3fR3AuditDef03_closedInCoverageVerifyOnly() -> None:
    """覆盖范围：R3-AUDIT-DEF-03 在 post-14 已 RESOLVED 后的 COVERAGE 对齐
    测试对象：RESOLVED、UNRESOLVED、UNRESOLVED_ITEM_TASK_COVERAGE.md
    目的/目标：per-subdir scan cap 已闭合，COVERAGE 须标 CLOSED 而非仍要求补齐测试
    验证点：DEF-03 在 RESOLVED 与 COVERAGE CLOSED；UNRESOLVED 无 DEFERRED 行；邻近文本含 test_ops_db_inspector
    失败含义：Plan 索引仍把已闭合项当开放债，会重开 inspector 实现
    """
    resolved = _read(RESOLVED)
    unresolved = _read(UNRESOLVED)
    coverage = _read(COVERAGE)

    assert "R3-AUDIT-DEF-03" in resolved
    assert "R3-AUDIT-DEF-03" in coverage
    assert "CLOSED" in coverage.split("R3-AUDIT-DEF-03", maxsplit=1)[1][:220]
    assert f"| R3-AUDIT-DEF-03 | DEFERRED" not in unresolved
    assert "test_ops_db_inspector" in coverage.split("R3-AUDIT-DEF-03", maxsplit=1)[1][:220]


def test_batch3fR2Risk3_closedInCoverageVerifyOnly() -> None:
    """覆盖范围：R2-RISK-3 在 post-14 B-008 已 RESOLVED 后的 COVERAGE 对齐
    测试对象：RESOLVED、UNRESOLVED、UNRESOLVED_ITEM_TASK_COVERAGE.md
    目的/目标：UNSUPPORTED_MODES fail-closed 已闭合，COVERAGE 须标 CLOSED 而非 matrix doc 开放债
    验证点：R2-RISK-3 在 RESOLVED 与 COVERAGE CLOSED；UNRESOLVED 无 DEFERRED 行；邻近文本含 UNSUPPORTED_MODES
    失败含义：Plan 索引仍把 write_mode 拒绝当开放实现项，会重开 WriteManager 改动
    """
    resolved = _read(RESOLVED)
    unresolved = _read(UNRESOLVED)
    coverage = _read(COVERAGE)

    assert "R2-RISK-3" in resolved
    assert "R2-RISK-3" in coverage
    assert "CLOSED" in coverage.split("R2-RISK-3", maxsplit=1)[1][:220]
    assert f"| R2-RISK-3 | DEFERRED" not in unresolved
    assert "UNSUPPORTED_MODES" in coverage.split("R2-RISK-3", maxsplit=1)[1][:220]


def test_batch3vR3Partial5_closedInResolvedNotOpen() -> None:
    """覆盖范围：R3-PARTIAL-5 在 B3V-C04 合并后应已闭合
    测试对象：RESOLVED、UNRESOLVED、COVERAGE registries
    目的/目标：crash recovery path A 已交付，不得仍标 DEFERRED OPEN
    验证点：R3-PARTIAL-5 在 RESOLVED 与 COVERAGE CLOSED；UNRESOLVED 无 DEFERRED 行
    失败含义：已修复项仍标 OPEN，会误导并行 slice 重复抢同一修复
    """
    resolved = _read(RESOLVED)
    unresolved = _read(UNRESOLVED)
    coverage = _read(COVERAGE)

    assert "R3-PARTIAL-5" in resolved
    assert "R3-PARTIAL-5" in coverage
    assert "CLOSED" in coverage.split("R3-PARTIAL-5", maxsplit=1)[1][:200]
    assert "| R3-PARTIAL-5          | DEFERRED" not in unresolved


def test_batch3vMigration009Check_closedInResolvedNotOpen() -> None:
    """覆盖范围：A9-P1-01 / A9-P2-02 / B2.5-O-06 在 B3V-C05 migration 009 后应已闭合
    测试对象：RESOLVED、UNRESOLVED registries
    目的/目标：009 CHECK 已落地，不得仍出现在 UNRESOLVED DEFERRED 表
    验证点：三 ID 均在 RESOLVED；UNRESOLVED 无对应 DEFERRED 行
    失败含义：migration 009 闭合未同步 registry，Plan 会重复开 migration 008 债
    """
    resolved = _read(RESOLVED)
    unresolved = _read(UNRESOLVED)

    for item_id in ("A9-P1-01", "A9-P2-02", "B2.5-O-06"):
        assert item_id in resolved
        assert f"| {item_id}" not in unresolved or f"| {item_id}              | DEFERRED" not in unresolved


def test_wave4PrepR2Gap1_closedInResolvedNotOpen() -> None:
    """覆盖范围：R2-GAP-1 init_db --sync-registry 在 Wave 4 prep 后应已闭合
    测试对象：RESOLVED、UNRESOLVED、COVERAGE registries
    目的/目标：CI one-liner 已文档化+测试，不得仍标 DEFERRED
    验证点：R2-GAP-1 在 RESOLVED 与 COVERAGE CLOSED；UNRESOLVED 无 DEFERRED 行
    失败含义：init 卫生债仍标开放，Wave 4 会重复开 R3F-CLI-03
    """
    resolved = _read(RESOLVED)
    unresolved = _read(UNRESOLVED)
    coverage = _read(COVERAGE)

    assert "R2-GAP-1" in resolved
    assert "R2-GAP-1" in coverage
    assert "CLOSED" in coverage.split("R2-GAP-1", maxsplit=1)[1][:220]
    assert "| R2-GAP-1              | DEFERRED" not in unresolved


def test_wave4PrepR3AuditDef01_closedInResolvedNotOpen() -> None:
    """覆盖范围：R3-AUDIT-DEF-01 contract SSOT 在 Wave 4 prep 后应已闭合
    测试对象：RESOLVED、UNRESOLVED、COVERAGE registries
    目的/目标：db_inspector YAML loader + drift test 已交付
    验证点：R3-AUDIT-DEF-01 在 RESOLVED 与 COVERAGE CLOSED；UNRESOLVED 无 DEFERRED 行
    失败含义：inspect 契约漂移债仍标开放，会重开 B3V-C01
    """
    resolved = _read(RESOLVED)
    unresolved = _read(UNRESOLVED)
    coverage = _read(COVERAGE)

    assert "R3-AUDIT-DEF-01" in resolved
    assert "R3-AUDIT-DEF-01" in coverage
    assert "CLOSED" in coverage.split("R3-AUDIT-DEF-01", maxsplit=1)[1][:220]
    assert "| R3-AUDIT-DEF-01       | DEFERRED" not in unresolved


@pytest.mark.parametrize(
    "item_id",
    (
        "D3-P1-2",
        "A9-P2-01",
        "R2-RISK-4",
        "R3-B25-PERF-BUDGET-01",
        "R3-B25-HYG-03",
        "R3Y-TEST-DEPTH-001",
    ),
)
def test_wave4PrepClosed_inResolvedNotDeferred(item_id: str) -> None:
    """覆盖范围：Wave 4 prep 其余闭合项 registry 交叉一致性
    测试对象：RESOLVED、UNRESOLVED、COVERAGE registries
    目的/目标：REQ-004 — COVERAGE §3/§4 与 RESOLVED 同步，无 DEFERRED 漂移
    验证点：item_id 在 RESOLVED 与 COVERAGE 含 CLOSED；UNRESOLVED 无 DEFERRED 行
    失败含义：Plan 索引仍标 Batch6 hygiene 开放，会重复开债
    """
    resolved = _read(RESOLVED)
    unresolved = _read(UNRESOLVED)
    coverage = _read(COVERAGE)

    assert item_id in resolved
    assert item_id in coverage
    assert "CLOSED" in coverage.split(item_id, maxsplit=1)[1][:240]
    assert f"| {item_id} | DEFERRED" not in unresolved
    assert f"| {item_id} | OPEN" not in unresolved


def test_wave4PrepSection10_lineageOnlyStillDeferred() -> None:
    """覆盖范围：COVERAGE §10 仅保留 P3 lineage 大项为 DEFERRED 叙事
    测试对象：UNRESOLVED_ITEM_TASK_COVERAGE.md §10
    目的/目标：CR-003 — 已关 R3-B6-021 / R3Y-TEST-DEPTH 不得与 lineage 混标 registry DEFERRED
    验证点：§10 含 ADV-R3X / R3Y-LINEAGE；含 CLOSED Wave 4 prep 说明；不含「registry DEFERRED」旧句
    失败含义：§10 与 §7 矛盾，Wave 4 前卫生结论不可信
    """
    text = _read(COVERAGE)
    section = text.split("## 10. Round 3D", 1)[1].split("## 9.", 1)[0]
    assert "ADV-R3X-LINEAGE-001" in section
    assert "R3Y-LINEAGE-VR-001" in section
    assert "CLOSED" in section and "Wave 4 prep" in section
    assert "registry DEFERRED" not in section


def test_r3yOpenItems_ownerBranchesInCoverageSection45() -> None:
    """覆盖范围：§4.5 中 R3Y 开放项的 owner 分支映射
    测试对象：UNRESOLVED_ITEM_TASK_COVERAGE.md §4.5（Round 3 PROMPT_18 段）
    目的/目标：并行 slice 能看清每项该由哪条分支负责
    验证点：R3Y-STAGED-REG-001→β-2；R3Y-PROMPT15-EVID-001→fix α-3，均在 §4.5 出现
    失败含义：owner 分支未登记，多 agent 可能同时改同一开放项
    """
    text = _read(COVERAGE)
    section = text.split("## 4.5 Round 3 PROMPT_18", maxsplit=1)[1].split("## 5.", maxsplit=1)[0]

    expectations = {
        "R3Y-STAGED-REG-001": "β-2",
        "R3Y-PROMPT15-EVID-001": "fix α-3",
    }
    for item_id, owner_token in expectations.items():
        assert item_id in section, f"{item_id} missing from §4.5"
        assert owner_token in section, f"{owner_token} owner missing for {item_id} in §4.5"


def test_taskCardsMentionMappedUnresolvedIds() -> None:
    """覆盖范围：各任务卡是否提及映射表要求的未闭合项 ID
    测试对象：TASK_CARD_EXPECTATIONS 中列出的 implementation_tasks/*.md
    目的/目标：读单张任务卡时仍能看到相关开放项，不会以为范围已干净
    验证点：每张卡正文包含其映射集合里全部 expected_ids；缺失则 assert not missing
    失败含义：任务卡与开放项脱节，执行者可能 unaware 地踩到已知缺口
    """
    missing: dict[str, list[str]] = {}
    for relative_path, expected_ids in TASK_CARD_EXPECTATIONS.items():
        path = PROJECT_ROOT / "docs/implementation_tasks" / relative_path
        text = _read(path)
        not_found = sorted(item_id for item_id in expected_ids if item_id not in text)
        if not_found:
            missing[relative_path] = not_found

    assert not missing, f"mapped unresolved IDs missing from task cards: {missing}"
