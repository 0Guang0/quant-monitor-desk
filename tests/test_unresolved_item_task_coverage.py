"""未闭合项任务覆盖索引门禁测试。

覆盖范围：UNRESOLVED_ITEM_TASK_COVERAGE 是否为 Plan 必读、是否列出全部当前 OPEN/DEFERRED ID、
各任务卡是否交叉引用映射的未闭合项，防止只读单卡而遗漏开放债。
"""

from __future__ import annotations

from pathlib import Path

from tests.contract_gate_support import PROJECT_ROOT

COVERAGE = PROJECT_ROOT / "docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md"
UNRESOLVED = PROJECT_ROOT / "docs/UNRESOLVED_ISSUES_REGISTRY.md"
RESOLVED = PROJECT_ROOT / "docs/RESOLVED_ISSUES_REGISTRY.md"
TASK_INDEX = PROJECT_ROOT / "docs/implementation_tasks/TASK_INPUT_CONTEXT_INDEX.md"
TASK_README = PROJECT_ROOT / "docs/implementation_tasks/README.md"

EXPECTED_UNRESOLVED_IDS = {
    "R2.6-IMPL-6",
    "R2.6-IMPL-8",
    "R3-AUDIT-DEF-01",
    "R3-AUDIT-DEF-02",
    "R3-AUDIT-DEF-03",
    "R3-B2.75-01",
    "R3-PARTIAL-1",
    "R3-PARTIAL-3",
    "R3-PARTIAL-4",
    "R3-PARTIAL-5",
    "D2-P1-1",
    "D2-P1-3",
    "D2-P2-1",
    "D2-P2-2",
    "R2-GAP-1",
    "D2-P3-1",
    "D7-P1-1",
    "D7-P2-2",
    "D3-P1-2",
    "A9-P1-01",
    "A9-P2-01",
    "A9-P2-02",
    "A9-P3-01",
    "R2-RISK-1",
    "R2-RISK-2",
    "R2-RISK-3",
    "R2-RISK-4",
    "R2-HYG-4",
    "R2-HYG-5",
    "B2.5-O-05",
    "B2.5-O-06",
    "R3-B25-HYG-01",
    "R3-B25-HYG-02",
    "R3-B25-HYG-03",
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
    "R3Y-MUT-PROOF-001",
    "R3Y-STAGED-REG-001",
    "R3Y-PROMPT15-EVID-001",
    "R3Y-TEST-DEPTH-001",
    "ADV-R3X-LINEAGE-001",
    "R3Y-LINEAGE-VR-001",
    "R2-RISK-5",
}

TASK_CARD_EXPECTATIONS = {
    "ROUND_1_DATA_FOUNDATION/005_create_schema_sql.md": {
        "B2.5-O-06",
        "A9-P1-01",
        "A9-P2-01",
        "A9-P2-02",
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
        "R3-PARTIAL-5",
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
        "A9-P2-02",
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


def test_r3yOpenItems_ownerBranchesInCoverageSection45() -> None:
    """覆盖范围：§4.5 中 R3Y 开放项的 owner 分支映射
    测试对象：UNRESOLVED_ITEM_TASK_COVERAGE.md §4.5（Round 3 PROMPT_18 段）
    目的/目标：并行 slice 能看清每项该由哪条分支负责
    验证点：R3Y-MUT-PROOF-001→PROMPT_19；R3Y-STAGED-REG-001→β-2；R3Y-PROMPT15-EVID-001→fix/r3y-prompt15-evidence，均在 §4.5 出现
    失败含义：owner 分支未登记，多 agent 可能同时改同一开放项
    """
    text = _read(COVERAGE)
    section = text.split("## 4.5 Round 3 PROMPT_18", maxsplit=1)[1].split("## 5.", maxsplit=1)[0]

    expectations = {
        "R3Y-MUT-PROOF-001": "PROMPT_19",
        "R3Y-STAGED-REG-001": "β-2",
        "R3Y-PROMPT15-EVID-001": "fix/r3y-prompt15-evidence",
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
