"""确保未闭合项不会在 Plan 阶段因只读原始任务卡而遗漏。"""

from __future__ import annotations

from pathlib import Path

from tests.contract_gate_support import PROJECT_ROOT

COVERAGE = PROJECT_ROOT / "docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md"
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
    readme = _read(TASK_README)
    index = _read(TASK_INDEX)

    assert "UNRESOLVED_ITEM_TASK_COVERAGE.md" in readme
    assert "UNRESOLVED_ITEM_TASK_COVERAGE.md" in index
    assert "Plan" in readme and "Plan" in index


def test_coverageIndex_mentionsEveryCurrentUnresolvedId() -> None:
    text = _read(COVERAGE)
    missing = sorted(item_id for item_id in EXPECTED_UNRESOLVED_IDS if item_id not in text)
    assert not missing, f"unresolved IDs missing from coverage index: {missing}"


def test_taskCardsMentionMappedUnresolvedIds() -> None:
    missing: dict[str, list[str]] = {}
    for relative_path, expected_ids in TASK_CARD_EXPECTATIONS.items():
        path = PROJECT_ROOT / "docs/implementation_tasks" / relative_path
        text = _read(path)
        not_found = sorted(item_id for item_id in expected_ids if item_id not in text)
        if not_found:
            missing[relative_path] = not_found

    assert not missing, f"mapped unresolved IDs missing from task cards: {missing}"
