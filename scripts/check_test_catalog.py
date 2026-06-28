#!/usr/bin/env python3
"""Bootstrap or validate tests/test_catalog.yaml against tests/test_*.py."""

from __future__ import annotations

import argparse
import re
import sys

import yaml

from loop_engineering_common import (
    REPO_ROOT,
    TEST_CATALOG_PATH,
    default_catalog_entry,
    discover_test_modules,
    path_exists,
    repo_relative,
)

REQUIRED_FIELDS = ("purpose", "type", "verifies", "command", "failure_meaning")
VERIFICATION_COMMANDS = REPO_ROOT / "docs/ops/verification_commands.md"
ROUND3_GATE_MODULES = {
    "tests/test_trellis_audit_trace_authority.py",
    "tests/test_round3_audit_registry_alignment.py",
    "tests/test_unresolved_item_task_coverage.py",
    "tests/test_batch25_production_data_gate.py",
    "tests/test_production_live_pilot_policy.py",
    "tests/test_batch3_staged_downstream_gate.py",
    "tests/test_fred_staged_semantics.py",
    "tests/test_fred_source_registry.py",
    "tests/test_fred_sandbox_pilot.py",
}

# Curated entries for high-signal gate and module tests.
CURATED: dict[str, dict] = {
    "tests/test_batch3_staged_downstream_gate.py": {
        "purpose": "确保 Batch 3 只能 staged-only，不得被误读为 production-live readiness",
        "type": "policy-contract",
        "verifies": {
            "docs": [
                "docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md",
                "docs/quality/production_live_pilot_policy.md",
                "docs/ROUND3_HANDOFF.md",
            ],
            "specs": [],
            "rules": ["docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md"],
        },
        "protected_claims": {
            "forbidden": ["production-live ready", "live production ingestion"],
            "required": ["staged-only", "does not open production-live"],
        },
        "command": "uv run python -m pytest tests/test_batch3_staged_downstream_gate.py -q",
        "failure_meaning": (
            "Batch 3 gate language or references drifted; "
            "downstream agent may wrongly assume live production readiness."
        ),
        "evidence_required": "pytest output + doc link check",
    },
    "tests/test_layer2_sensor_loader.py": {
        "purpose": "验证 Layer2 sensor loader、snapshot、observation、lineage、ResourceGuard 行为",
        "type": "runtime-contract",
        "verifies": {
            "docs": ["docs/modules/layer2_cross_asset_sensor.md"],
            "specs": [
                "specs/contracts/layer2_sensor_contract.yaml",
                "specs/contracts/snapshot_lineage_contract.yaml",
                "specs/contracts/resource_limits.yaml",
            ],
            "rules": [],
        },
        "command": "uv run python -m pytest tests/test_layer2_sensor_loader.py -q",
        "failure_meaning": "Layer2 runtime or ResourceGuard blocks batch when limits exceeded.",
        "evidence_required": "pytest output",
    },
    "tests/test_layer3_loader.py": {
        "purpose": "Layer 3 industry chain staged loader tests (020 Execute).",
        "type": "runtime-contract",
        "verifies": {
            "docs": ["docs/modules/layer3_industry_shock_anchor.md"],
            "specs": ["specs/contracts/layer3_loader_contract.yaml"],
            "rules": [],
        },
        "command": "uv run python -m pytest tests/test_layer3_loader.py -q",
        "failure_meaning": (
            "Layer3 staged loader contract validation or staged-only gate regressed."
        ),
        "evidence_required": "pytest output",
    },
    "tests/test_layer4_market_structure.py": {
        "purpose": "Layer 4 market structure staged snapshot tests (Round 3 task 022).",
        "type": "runtime-contract",
        "verifies": {
            "docs": ["docs/modules/layer4_market_structure.md"],
            "specs": [
                "specs/contracts/layer4_market_contract.yaml",
                "specs/contracts/snapshot_lineage_contract.yaml",
            ],
            "rules": [],
        },
        "command": "uv run python -m pytest tests/test_layer4_market_structure.py -q",
        "failure_meaning": "Layer4 staged market structure or lineage contract regressed.",
        "evidence_required": "pytest output",
    },
    "tests/test_round3f_lineage_layer3_registry_closure.py": {
        "purpose": "B3F-LIN acceptance gate for lineage/Layer3 registry closure pytest mapping.",
        "type": "runtime-contract",
        "verifies": {
            "docs": [
                "docs/implementation_tasks/ROUND_3_BATCH6_DATA_GOVERNANCE/BATCH_3F_BATCH6_DATA_GOVERNANCE/BATCH_3F_COORDINATOR_PLAYBOOK.md",
            ],
            "specs": ["specs/contracts/snapshot_lineage_contract.yaml"],
            "rules": [],
        },
        "command": (
            "uv run python -m pytest "
            "tests/test_round3f_lineage_layer3_registry_closure.py -q"
        ),
        "failure_meaning": "B3F-LIN closure gate broken; registry evidence chain invalid.",
        "evidence_required": "pytest output",
    },
    "tests/test_batch25_production_data_gate.py": {
        "purpose": "Batch 2.5 evidence is staged-only, not production-live readiness",
        "type": "policy-contract",
        "verifies": {
            "docs": [
                "docs/quality/production_live_pilot_policy.md",
                "docs/ROUND3_HANDOFF.md",
            ],
            "specs": [],
            "rules": ["docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md"],
        },
        "command": "uv run python -m pytest tests/test_batch25_production_data_gate.py -q",
        "failure_meaning": "Batch 2.5 staged vs production-live semantics drifted.",
        "evidence_required": "pytest output",
    },
    "tests/test_batch275_live_pilot_gate.py": {
        "purpose": "Batch 2.75 live pilot fail-closed gate and route readiness",
        "type": "policy-contract",
        "verifies": {
            "docs": [
                "docs/quality/production_live_pilot_policy.md",
                "docs/modules/source_route_plan.md",
            ],
            "specs": ["specs/contracts/source_route_contract.yaml"],
            "rules": ["docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md"],
        },
        "command": (
            'uv run python -m pytest tests/test_batch275_live_pilot_gate.py -q '
            '-m "not network"'
        ),
        "failure_meaning": "Live pilot gate no longer fail-closed on route/auth preconditions.",
        "evidence_required": "pytest output",
    },
    "tests/test_write_manager.py": {
        "purpose": "DuckDBWriteManager exclusive clean-table write path",
        "type": "negative-runtime",
        "verifies": {
            "docs": ["docs/modules/write_manager.md"],
            "specs": ["specs/contracts/write_contract.yaml"],
            "rules": ["docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md"],
        },
        "command": "uv run python -m pytest tests/test_write_manager.py -q",
        "failure_meaning": "WriteManager contract violated; direct writes may bypass validation.",
        "evidence_required": "pytest output",
    },
    "tests/test_resource_guard.py": {
        "purpose": "ResourceGuard HARD_STOP and metrics contract",
        "type": "negative-runtime",
        "verifies": {
            "docs": ["docs/ops/performance_limits.md"],
            "specs": ["specs/contracts/resource_limits.yaml"],
            "rules": ["docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md"],
        },
        "command": "uv run python -m pytest tests/test_resource_guard.py -q",
        "failure_meaning": "Resource limits no longer enforced; batch jobs may exceed safe bounds.",
        "evidence_required": "pytest output",
    },
    "tests/test_production_equivalent_smoke_budget.py": {
        "purpose": "Bounded production-equivalent smoke threshold artifact (R3F-HYG-06)",
        "type": "policy-contract",
        "verifies": {
            "docs": ["docs/ops/performance_limits.md"],
            "specs": ["specs/contracts/production_equivalent_smoke_budget.yaml"],
            "rules": [],
        },
        "command": "uv run python -m pytest tests/test_production_equivalent_smoke_budget.py -q",
        "failure_meaning": "Perf smoke budget thresholds missing or mis-evaluated.",
        "evidence_required": "pytest output + smoke budget JSON artifact",
    },
    "tests/test_layer1_sandbox_bootstrap.py": {
        "purpose": "Layer1 ingestion sandbox bootstrap PR-R2b (R3F-HYG-07)",
        "type": "runtime-contract",
        "verifies": {
            "docs": ["docs/architecture/layer1_ingestion_refactor_rollback_plan.md"],
            "specs": [],
            "rules": [],
        },
        "command": "uv run python -m pytest tests/test_layer1_sandbox_bootstrap.py -q",
        "failure_meaning": "Phase3/4 evidence sandbox bootstrap regressed; ingestion split rollback risk.",
        "evidence_required": "pytest output",
    },
    "tests/test_source_route_planner.py": {
        "purpose": "Source route planner READY gate and routing semantics",
        "type": "runtime-contract",
        "verifies": {
            "docs": ["docs/modules/source_route_plan.md"],
            "specs": ["specs/contracts/source_route_contract.yaml"],
            "rules": [],
        },
        "command": "uv run python -m pytest tests/test_source_route_planner.py -q",
        "failure_meaning": "Route planner may allow fetch before route READY.",
        "evidence_required": "pytest output",
    },
    "tests/test_layer1_axis_loader.py": {
        "purpose": "Layer1 axis loader registry and snapshot behavior",
        "type": "runtime-contract",
        "verifies": {
            "docs": ["docs/modules/layer1_global_regime_panel.md"],
            "specs": ["specs/contracts/layer1_axis_contract.yaml"],
            "rules": [],
        },
        "command": "uv run python -m pytest tests/test_layer1_axis_loader.py -q",
        "failure_meaning": "Layer1 axis loader behavior drifted from design.",
        "evidence_required": "pytest output",
    },
    "tests/test_fred_staged_semantics.py": {
        "purpose": "FRED / macro_supplementary staged-only semantics (B2.5-O-05)",
        "type": "policy-contract",
        "verifies": {
            "docs": [
                "docs/quality/production_live_pilot_policy.md",
                "docs/ROUND3_HANDOFF.md",
            ],
            "specs": [],
            "rules": ["docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md"],
        },
        "command": "uv run python -m pytest tests/test_fred_staged_semantics.py -q",
        "failure_meaning": (
            "FRED staged semantics drifted; macro supplementary may imply production-live."
        ),
        "evidence_required": "pytest output",
    },
    "tests/test_fred_source_registry.py": {
        "purpose": "FRED sandbox/disabled-by-default registry guard (B01-FRED FRED-01)",
        "type": "policy-contract",
        "verifies": {
            "docs": [],
            "specs": [
                "specs/datasource_registry/source_registry.yaml",
                "specs/datasource_registry/source_capabilities.yaml",
            ],
            "rules": [
                "docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/BATCH_01_MODEL_SOURCE_READINESS/BATCH_01_HARDENING_RULES.md",
            ],
        },
        "command": "uv run python -m pytest tests/test_fred_source_registry.py -q",
        "failure_meaning": (
            "FRED registry row missing or production-live; unauthorized FRED routing risk."
        ),
        "evidence_required": "pytest output",
    },
    "tests/test_fred_sandbox_pilot.py": {
        "purpose": "FRED-only sandbox pilot orchestration (B01-FRED FRED-02..07)",
        "type": "runtime-contract",
        "verifies": {
            "docs": [
                "docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/R3E_fred_authorized_sandbox_pilot.md",
            ],
            "specs": ["specs/contracts/datasource_service_contract.yaml"],
            "rules": ["docs/quality/production_live_pilot_policy.md"],
        },
        "command": "uv run python -m pytest tests/test_fred_sandbox_pilot.py -q",
        "failure_meaning": "FRED pilot route/fetch/health/closeout broken; B2.5-O-05 evidence gap.",
        "evidence_required": "pytest output",
    },
    "tests/test_source_health_snapshot.py": {
        "purpose": "Batch 3F B3F-SH source_health_snapshot writer and rollup persist (R3F-SH-01/04)",
        "type": "runtime-contract",
        "verifies": {
            "docs": [
                "docs/decisions/ADR-024-source-health-snapshot-boundary.md",
                "docs/modules/data_sources.md",
            ],
            "specs": [],
            "rules": [
                "docs/implementation_tasks/ROUND_3_BATCH6_DATA_GOVERNANCE/BATCH_3F_BATCH6_DATA_GOVERNANCE/BATCH_3F_HARDENING_RULES.md",
            ],
        },
        "command": "uv run python -m pytest tests/test_source_health_snapshot.py -q",
        "failure_meaning": "Snapshot writer or rollup persist broken; Batch6 source health tracking fails.",
        "evidence_required": "pytest output",
    },
    "tests/test_b3f_quality_runners.py": {
        "purpose": "Batch 3F quality runners — revision_audit and data_quality non-defer (R3F-SH-02/03)",
        "type": "runtime-contract",
        "verifies": {
            "docs": [
                "docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/014_implement_data_sync_orchestrator.md",
            ],
            "specs": ["specs/contracts/sync_job_contract.yaml"],
            "rules": [],
        },
        "command": "uv run python -m pytest tests/test_b3f_quality_runners.py -q",
        "failure_meaning": "Quality runners still defer; Batch6 job matrix not closed.",
        "evidence_required": "pytest output",
    },
    "tests/test_fred_live_primary_closeout.py": {
        "purpose": "FRED live primary authorization fail-closed gate (R3F-SH-06)",
        "type": "policy-contract",
        "verifies": {
            "docs": [
                "docs/quality/batch3f_fred_live_pilot_authorization_2026-06-25.md",
                "docs/quality/production_live_pilot_policy.md",
            ],
            "specs": ["specs/contracts/datasource_service_contract.yaml"],
            "rules": [
                "docs/implementation_tasks/ROUND_3_BATCH6_DATA_GOVERNANCE/BATCH_3F_BATCH6_DATA_GOVERNANCE/BATCH_3F_HARDENING_RULES.md",
            ],
        },
        "command": "uv run python -m pytest tests/test_fred_live_primary_closeout.py -q",
        "failure_meaning": "Unauthorized FRED live path may open; violates Batch 3F hardening.",
        "evidence_required": "pytest output",
    },
    "tests/test_b3f_sh_hard_constraints.py": {
        "purpose": "Batch 3F AkShare/Eastmoney no-false-close registry guard (R3F-SH-07)",
        "type": "policy-contract",
        "verifies": {
            "docs": [
                "docs/implementation_tasks/ROUND_3_BATCH6_DATA_GOVERNANCE/BATCH_3F_BATCH6_DATA_GOVERNANCE/BATCH_3F_HARDENING_RULES.md",
            ],
            "specs": [
                "specs/datasource_registry/source_registry.yaml",
                "specs/datasource_registry/source_capabilities.yaml",
            ],
            "rules": ["docs/UNRESOLVED_ISSUES_REGISTRY.md"],
        },
        "command": "uv run python -m pytest tests/test_b3f_sh_hard_constraints.py -q",
        "failure_meaning": "Sidecar evidence may falsely close AkShare/EM validation rows.",
        "evidence_required": "pytest output",
    },
    "tests/test_data_health_v2.py": {
        "purpose": (
            "Read-only data health v2 profiles (B01-DH2): "
            "whitelist BLOCKED, FRED/TDX/SP3/rollup/gate"
        ),
        "type": "runtime-contract",
        "verifies": {
            "docs": [
                "docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/R3E_readonly_data_health_v2.md",
                "docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/BATCH_01_MODEL_SOURCE_READINESS/BATCH_01_HARDENING_RULES.md",
            ],
            "specs": [],
            "rules": ["docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md"],
        },
        "command": "uv run python -m pytest tests/test_data_health_v2.py -q",
        "failure_meaning": (
            "v2 profile semantics drifted; missing WL may PASS or "
            "production-primary may slip through."
        ),
        "evidence_required": "pytest output",
    },
    "tests/test_production_live_pilot_policy.py": {
        "purpose": "Batch 2.75 fail-closed pilot policy documentation",
        "type": "policy-contract",
        "verifies": {
            "docs": ["docs/quality/production_live_pilot_policy.md"],
            "specs": [],
            "rules": ["docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md"],
        },
        "command": "uv run python -m pytest tests/test_production_live_pilot_policy.py -q",
        "failure_meaning": "Production-live pilot policy docs drifted from fail-closed controls.",
        "evidence_required": "pytest output",
    },
    "tests/test_db_validation_gate.py": {
        "purpose": "DB validation gate blocks invalid writes",
        "type": "negative-runtime",
        "verifies": {
            "docs": ["docs/modules/data_validation_write_concurrency.md"],
            "specs": ["specs/contracts/write_contract.yaml"],
            "rules": [],
        },
        "command": "uv run python -m pytest tests/test_db_validation_gate.py -q",
        "failure_meaning": "Invalid writes may pass validation gate.",
        "evidence_required": "pytest output",
    },
    "tests/test_api_security_contract.py": {
        "purpose": "API security contract fail-closed guardrails",
        "type": "policy-contract",
        "verifies": {
            "docs": [],
            "specs": ["specs/contracts/api_security_contract.yaml"],
            "rules": [],
        },
        "command": "uv run python -m pytest tests/test_api_security_contract.py -q",
        "failure_meaning": "API security contract drifted; unsafe endpoints may open.",
    },
    "tests/test_module_boundaries.py": {
        "purpose": "Module import boundary enforcement blocks forbidden cross-layer imports",
        "type": "policy-contract",
        "verifies": {
            "docs": ["docs/architecture/module_boundary_matrix.md"],
            "specs": ["specs/contracts/module_boundary_contract.yaml"],
            "rules": [],
        },
        "command": "uv run python -m pytest tests/test_module_boundaries.py -q",
        "failure_meaning": "Forbidden module imports may slip through boundary gate.",
    },
    "tests/test_data_quality_validator.py": {
        "purpose": "Data quality validator rejects invalid observations",
        "type": "negative-runtime",
        "verifies": {"docs": [], "specs": ["specs/contracts/data_quality_rules.yaml"], "rules": []},
        "command": "uv run python -m pytest tests/test_data_quality_validator.py -q",
        "failure_meaning": "Invalid data may pass quality validator.",
    },
    "tests/test_source_conflict_validator.py": {
        "purpose": "Source conflict validator blocks conflicting primary sources",
        "type": "negative-runtime",
        "verifies": {
            "docs": [],
            "specs": ["specs/contracts/source_conflict_rules.yaml"],
            "rules": [],
        },
        "command": "uv run python -m pytest tests/test_source_conflict_validator.py -q",
        "failure_meaning": "Conflicting sources may not be rejected.",
    },
    "tests/test_round3f_migration_residuals.py": {
        "purpose": "Round 3F B3F-MIG migration residuals (R3F-MIG-01..06)",
        "type": "contract",
        "verifies": {
            "docs": [
                "docs/schema/MIGRATION_COVERAGE.md",
                "docs/schema/MIGRATION_008_PLAN.md",
                "docs/decisions/ADR-002-db-check-vs-app-validation.md",
            ],
            "specs": ["specs/schema/schema.sql"],
            "rules": [],
        },
        "command": "uv run python -m pytest tests/test_round3f_migration_residuals.py -q",
        "failure_meaning": "Migration 012 residuals or 009 verify-only guard regressed; registry D2-P3-1 gap reopens.",
        "evidence_required": "pytest output",
    },
    "tests/test_staged_pilot.py": {
        "purpose": "Staged pilot sandbox boundaries; does not open production-live",
        "type": "policy-contract",
        "verifies": {
            "docs": ["docs/quality/production_live_pilot_policy.md"],
            "specs": ["specs/contracts/review_sandbox_contract.yaml"],
            "rules": [],
        },
        "command": "uv run python -m pytest tests/test_staged_pilot.py -q",
        "failure_meaning": "Staged pilot may be misread as production-live readiness.",
    },
    "tests/test_real_data_staged_pilot_v3.py": {
        "purpose": "Model-input-whitelist driven staged pilot v3 safety boundaries (B01-SP3)",
        "type": "policy-contract",
        "verifies": {
            "docs": [
                "docs/quality/production_live_pilot_policy.md",
                "docs/quality/staged_acceptance_policy.md",
            ],
            "specs": [
                "specs/model_inputs/README.md",
                "specs/contracts/source_conflict_rules.yaml",
            ],
            "rules": ["docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md"],
        },
        "command": "uv run python -m pytest tests/test_real_data_staged_pilot_v3.py -q",
        "failure_meaning": "v3 staged pilot may bypass WL caps or claim production-live readiness.",
    },
    "tests/test_reference_adoption_guardrails.py": {
        "purpose": "Reference adoption guardrails — static scans for forbidden copied patterns",
        "type": "policy-negative",
        "verifies": {
            "docs": [],
            "specs": ["specs/contracts/reference_adoption_guardrails.yaml"],
            "rules": ["docs/implementation_tasks/GLOBAL_TESTING_POLICY.md"],
        },
        "command": "uv run python -m pytest tests/test_reference_adoption_guardrails.py -q",
        "failure_meaning": (
            "Reference adoption guardrails fail-closed; backend/scripts must not copy "
            "forbidden trading, login, fallback, or reference-project runtime patterns."
        ),
    },
    "tests/test_r3h_adapter_evidence_matrix.py": {
        "purpose": "Round 3H adapter evidence-matrix planning gate",
        "type": "policy-contract",
        "verifies": {
            "docs": ["docs/quality/round3h_real_data_production_entry_audit.md"],
            "specs": [],
            "rules": ["docs/implementation_tasks/GLOBAL_TESTING_POLICY.md"],
        },
        "command": "uv run python -m pytest tests/test_r3h_adapter_evidence_matrix.py -q",
        "failure_meaning": "R3H audit template missing adapter/evidence fields; Round4 gate incomplete.",
    },
    "tests/test_r3h_layer_binding_audit.py": {
        "purpose": "Round 3H Layer1-5 binding and Round4 admission planning gate",
        "type": "policy-contract",
        "verifies": {
            "docs": ["docs/quality/round3h_real_data_production_entry_audit.md"],
            "specs": [],
            "rules": ["docs/implementation_tasks/GLOBAL_TESTING_POLICY.md"],
        },
        "command": "uv run python -m pytest tests/test_r3h_layer_binding_audit.py -q",
        "failure_meaning": "R3H layer binding or Round4 admission outcomes undefined in planning docs.",
    },
    "tests/test_r3h_source_final_decisions.py": {
        "purpose": "Round 3H source final-decision planning gate across R3H task cards",
        "type": "policy-contract",
        "verifies": {
            "docs": [
                "docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/README.md",
            ],
            "specs": ["specs/datasource_registry/source_registry.yaml"],
            "rules": ["docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md"],
        },
        "command": "uv run python -m pytest tests/test_r3h_source_final_decisions.py -q",
        "failure_meaning": "R3H task cards omit target sources or final-decision semantics.",
    },
    "tests/test_market_data_adapters.py": {
        "purpose": "R3H-02 跨资产/US 市场数据适配器测试（Batch 3H）。",
        "type": "runtime-contract",
        "verifies": {
            "docs": [],
            "specs": [
                "specs/datasource_registry/source_capabilities.yaml",
                "specs/contracts/source_route_contract.yaml",
            ],
            "rules": ["docs/implementation_tasks/GLOBAL_TESTING_POLICY.md"],
        },
        "command": "uv run python -m pytest tests/test_market_data_adapters.py -q",
        "failure_meaning": "R3H-02 market data adapters or evidence contract regressed.",
    },
    "tests/test_crypto_market_adapters.py": {
        "purpose": "R3H-02 加密市场数据适配器测试（Batch 3H）。",
        "type": "runtime-contract",
        "verifies": {
            "docs": [],
            "specs": [
                "specs/datasource_registry/source_capabilities.yaml",
                "specs/contracts/source_route_contract.yaml",
            ],
            "rules": ["docs/implementation_tasks/GLOBAL_TESTING_POLICY.md"],
        },
        "command": "uv run python -m pytest tests/test_crypto_market_adapters.py -q",
        "failure_meaning": "R3H-02 crypto market adapters or evidence contract regressed.",
    },
    "tests/test_prediction_market_adapters.py": {
        "purpose": "R3H-04 预测市场适配器测试（Batch 3H）。",
        "type": "runtime-contract",
        "verifies": {
            "docs": ["docs/modules/data_sources.md"],
            "specs": [
                "specs/contracts/source_capability_contract.yaml",
                "specs/contracts/source_route_contract.yaml",
                "specs/contracts/layer5_evidence_contract.yaml",
            ],
            "rules": ["docs/implementation_tasks/GLOBAL_TESTING_POLICY.md"],
        },
        "command": "uv run python -m pytest tests/test_prediction_market_adapters.py -q",
        "failure_meaning": "R3H-04 prediction market adapters or probability evidence regressed.",
    },
    "tests/test_web_evidence_adapter.py": {
        "purpose": "R3H-04 网页证据适配器测试（Batch 3H）。",
        "type": "runtime-contract",
        "verifies": {
            "docs": ["docs/modules/data_sources.md"],
            "specs": [
                "specs/contracts/layer5_evidence_contract.yaml",
                "specs/contracts/user_input_privacy_contract.yaml",
            ],
            "rules": ["docs/implementation_tasks/GLOBAL_TESTING_POLICY.md"],
        },
        "command": "uv run python -m pytest tests/test_web_evidence_adapter.py -q",
        "failure_meaning": "R3H-04 web evidence staging or manual-review binding regressed.",
    },
    "tests/test_no_clean_write_for_web_evidence.py": {
        "purpose": "R3H-04 三源 clean-write 负例与预测市场不得 resolve 事实。",
        "type": "negative-runtime",
        "verifies": {
            "docs": ["docs/modules/data_sources.md"],
            "specs": [
                "specs/contracts/source_route_contract.yaml",
                "specs/contracts/layer5_evidence_contract.yaml",
            ],
            "rules": ["docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md"],
        },
        "command": "uv run python -m pytest tests/test_no_clean_write_for_web_evidence.py -q",
        "failure_meaning": "R3H-04 source routed to clean writer or resolved factual outcomes.",
    },
    "tests/test_docstring_quadruple_coverage.py": {
        "purpose": "Gate — every test_* carries five-field Chinese docstring per hygiene plan",
        "type": "runtime-contract",
        "verifies": {
            "docs": ["docs/quality/ROUND3_TEST_DOCSTRING_HYGIENE_PLAN.md"],
            "specs": [],
            "rules": ["docs/implementation_tasks/GLOBAL_TESTING_POLICY.md"],
        },
        "command": "uv run python -m pytest tests/test_docstring_quadruple_coverage.py -q",
        "failure_meaning": (
            "Test self-description contract broke; docstring hygiene regresses silently."
        ),
    },
    "tests/test_tdx_manual_probe.py": {
        "purpose": "Batch 01 B01-TDX manual probe — mocked CI + auth-gated live (TDX-01..06)",
        "type": "policy-contract",
        "verifies": {
            "docs": [
                "docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/R3E_tdx_manual_probe_addendum.md",
                "docs/quality/tdx_pytdx_live_manual_probe_authorization_2026-06-24.md",
            ],
            "specs": [
                "specs/datasource_registry/source_registry.yaml",
                "specs/datasource_registry/source_capabilities.yaml",
            ],
            "rules": ["docs/implementation_tasks/GLOBAL_TESTING_POLICY.md"],
        },
        "command": "uv run python -m pytest tests/test_tdx_manual_probe.py -q",
        "failure_meaning": (
            "TDX manual probe regression; validation-only/disabled-by-default "
            "guard may be broken."
        ),
    },
    "tests/test_execution_index_protocol.py": {
        "purpose": "Plan 协议 v4：EXECUTION_INDEX 解析、manifest 生成与 validate_plan_freeze v4 门禁",
        "type": "policy-contract",
        "verifies": {
            "docs": [
                ".trellis/spec/guides/complex-task-planning-protocol.md",
                ".trellis/spec/guides/templates/EXECUTION_INDEX.md",
            ],
            "specs": [],
            "rules": ["docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md"],
        },
        "command": "uv run python -m pytest tests/test_execution_index_protocol.py -q",
        "failure_meaning": (
            "v4 frozen task card + index manifest drift; Execute/Audit SSOT gate broken."
        ),
        "evidence_required": "pytest output",
    },
    "tests/test_round3g_sandbox_clean_write_rehearsal.py": {
        "purpose": "Round 3G R3G-01 sandbox rehearsal contract fail-closed gates",
        "type": "policy-contract",
        "verifies": {
            "docs": [
                "docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_01_SANDBOX_CLEAN_WRITE_REHEARSAL.md",
            ],
            "specs": ["specs/contracts/sandbox_clean_write_contract.yaml"],
            "rules": ["docs/implementation_tasks/GLOBAL_TESTING_POLICY.md"],
        },
        "command": "uv run python -m pytest tests/test_round3g_sandbox_clean_write_rehearsal.py -q",
        "failure_meaning": (
            "R3G-01 rehearsal contract blocks production mutation or report fields drift."
        ),
    },
    "tests/test_round3g_sandbox_rehearsal_loader.py": {
        "purpose": "R3G-01 rehearsal loader bounded DataBundle from staged evidence",
        "type": "unit",
        "verifies": {
            "docs": [
                "docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_01_SANDBOX_CLEAN_WRITE_REHEARSAL.md",
            ],
            "specs": ["specs/contracts/sandbox_clean_write_contract.yaml"],
            "rules": ["docs/implementation_tasks/GLOBAL_TESTING_POLICY.md"],
        },
        "command": "uv run python -m pytest tests/test_round3g_sandbox_rehearsal_loader.py -q",
        "failure_meaning": (
            "R3G-01 loader accepts broad universe or fails to load capped fixture bundles."
        ),
    },
    "tests/test_round3g_sandbox_rehearsal_report.py": {
        "purpose": "R3G-01 rehearsal report required fields and data_health_summary shape",
        "type": "unit",
        "verifies": {
            "docs": [
                "docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_01_SANDBOX_CLEAN_WRITE_REHEARSAL.md",
            ],
            "specs": ["specs/contracts/sandbox_clean_write_contract.yaml"],
            "rules": ["docs/implementation_tasks/GLOBAL_TESTING_POLICY.md"],
        },
        "command": "uv run python -m pytest tests/test_round3g_sandbox_rehearsal_report.py -q",
        "failure_meaning": (
            "R3G-01 rehearsal report missing contract fields or DH summary counts."
        ),
    },
    "tests/test_round3g_pre_production_adversarial_audit.py": {
        "purpose": "Round 3G R3G-02 adversarial audit decision enum and block_if gates",
        "type": "policy-contract",
        "verifies": {
            "docs": [
                "docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_02_PRE_PRODUCTION_ADVERSARIAL_AUDIT.md",
            ],
            "specs": ["specs/contracts/sandbox_clean_write_contract.yaml"],
            "rules": ["docs/implementation_tasks/GLOBAL_TESTING_POLICY.md"],
        },
        "command": "uv run python -m pytest tests/test_round3g_pre_production_adversarial_audit.py -q",
        "failure_meaning": (
            "R3G-02 audit contract fails to reject reference runtime import or production write."
        ),
    },
    "tests/test_round3g_limited_production_clean_write.py": {
        "purpose": "Round 3G R3G-03 limited entry requires user approval and blocks agent write",
        "type": "policy-contract",
        "verifies": {
            "docs": [
                "docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_03_LIMITED_PRODUCTION_CLEAN_WRITE.md",
            ],
            "specs": ["specs/contracts/sandbox_clean_write_contract.yaml"],
            "rules": ["docs/implementation_tasks/GLOBAL_TESTING_POLICY.md"],
        },
        "command": "uv run python -m pytest tests/test_round3g_limited_production_clean_write.py -q",
        "failure_meaning": (
            "R3G-03 limited clean-write contract allows agent-triggered or unapproved entry."
        ),
    },
    "tests/test_round3g_limited_production_rollback.py": {
        "purpose": "Round 3G R3G-03 rollback dry-run and QMD gate contract",
        "type": "policy-contract",
        "verifies": {
            "docs": [
                "docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_03_LIMITED_PRODUCTION_CLEAN_WRITE.md",
            ],
            "specs": ["specs/contracts/sandbox_clean_write_contract.yaml"],
            "rules": ["docs/implementation_tasks/GLOBAL_TESTING_POLICY.md"],
        },
        "command": "uv run python -m pytest tests/test_round3g_limited_production_rollback.py -q",
        "failure_meaning": (
            "R3G-03 rollback contract missing dry-run requirement or WriteManager gate."
        ),
    },
    "tests/test_data_health_easyxt_profiles.py": {
        "purpose": "R3FR-02 market_bar_p0 profile engine and rule ID closure",
        "type": "runtime-contract",
        "verifies": {
            "docs": ["docs/ops/data_health_cli.md"],
            "specs": ["specs/contracts/data_quality_rules.yaml"],
            "rules": ["docs/implementation_tasks/GLOBAL_TESTING_POLICY.md"],
        },
        "command": "uv run python -m pytest tests/test_data_health_easyxt_profiles.py -q",
        "failure_meaning": (
            "market_bar_p0 profile incomplete, rule ID drift, or CLI/runtime disconnect."
        ),
    },
    "tests/test_r3fr07_legacy_wrapper_cleanup.py": {
        "purpose": "R3FR-07 legacy wrapper cleanup — doc redirect and batch-close guardrails.",
        "type": "runtime-contract",
        "verifies": {
            "docs": [
                "docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_07_LEGACY_WRAPPER_CLEANUP_AND_REDIRECTS.md",
                "docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_TASK_CARD_MANIFEST.md",
                "docs/ops/data_health_cli.md",
                "docs/ops/data_init_basic_cli.md",
            ],
            "specs": [
                "specs/contracts/data_cli_contract.yaml",
                "specs/contracts/reference_adoption_guardrails.yaml",
            ],
            "rules": [
                "docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_HARDENING_RULES.md",
            ],
        },
        "command": "uv run python -m pytest tests/test_r3fr07_legacy_wrapper_cleanup.py -q",
        "failure_meaning": (
            "Regression in test_r3fr07_legacy_wrapper_cleanup; inspect purpose and linked authorities."
        ),
    },
}


def _load_catalog() -> dict:
    if not TEST_CATALOG_PATH.is_file():
        return {}
    data = yaml.safe_load(TEST_CATALOG_PATH.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _verification_command_modules() -> set[str]:
    if not VERIFICATION_COMMANDS.is_file():
        return set()
    text = VERIFICATION_COMMANDS.read_text(encoding="utf-8")
    return set(re.findall(r"tests/[a-zA-Z0-9_./-]+\.py", text))


def _validate_entry(rel: str, entry: dict) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in entry:
            errors.append(f"{rel}: missing field {field}")
    verifies = entry.get("verifies") or {}
    if not isinstance(verifies, dict):
        errors.append(f"{rel}: verifies must be a mapping")
        return errors
    for bucket in ("docs", "specs", "rules"):
        for path in verifies.get(bucket) or []:
            if not path_exists(str(path)):
                errors.append(f"{rel}: missing verifies.{bucket} path: {path}")
    command = str(entry.get("command", ""))
    if rel not in command:
        errors.append(f"{rel}: command must reference the test module")
    return errors


def build_catalog() -> dict:
    catalog = _load_catalog()
    for rel, curated in CURATED.items():
        catalog[rel] = curated
    for rel in discover_test_modules():
        if rel not in catalog:
            catalog[rel] = default_catalog_entry(rel)
    return dict(sorted(catalog.items()))


def write_catalog(catalog: dict) -> None:
    TEST_CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEST_CATALOG_PATH.write_text(
        yaml.safe_dump(catalog, sort_keys=True, allow_unicode=True),
        encoding="utf-8",
    )


def check_catalog() -> list[str]:
    errors: list[str] = []
    catalog = _load_catalog()
    if not catalog:
        return ["tests/test_catalog.yaml missing or empty"]

    discovered = set(discover_test_modules())
    catalog_keys = set(catalog.keys())
    for rel in sorted(discovered - catalog_keys):
        errors.append(f"unregistered test module: {rel}")
    for rel in sorted(catalog_keys - discovered):
        errors.append(f"catalog entry without test file: {rel}")

    for rel, entry in catalog.items():
        errors.extend(_validate_entry(rel, entry))

    for rel in ROUND3_GATE_MODULES:
        if rel not in catalog:
            errors.append(f"Round 3 gate test missing from catalog: {rel}")

    for rel in _verification_command_modules():
        if rel not in catalog:
            errors.append(f"verification_commands.md test missing from catalog: {rel}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write-defaults",
        action="store_true",
        help="Merge curated + default entries into tests/test_catalog.yaml",
    )
    args = parser.parse_args()

    if args.write_defaults:
        write_catalog(build_catalog())
        print(f"Wrote {repo_relative(TEST_CATALOG_PATH)}")
        return 0

    errors = check_catalog()
    if errors:
        print("test catalog check FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print(f"OK: test catalog covers {len(_load_catalog())} modules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
