#!/usr/bin/env python3
"""Bootstrap or validate tests/test_catalog.yaml against tests/test_*.py."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

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
        "failure_meaning": "Batch 3 gate language or references drifted; downstream agent may wrongly assume live production readiness.",
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
        "command": 'uv run python -m pytest tests/test_batch275_live_pilot_gate.py -q -m "not network"',
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
        "failure_meaning": "FRED staged semantics drifted; macro supplementary may imply production-live.",
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
        "verifies": {"docs": [], "specs": ["specs/contracts/api_security_contract.yaml"], "rules": []},
        "command": "uv run python -m pytest tests/test_api_security_contract.py -q",
        "failure_meaning": "API security contract drifted; unsafe endpoints may open.",
    },
    "tests/test_module_boundaries.py": {
        "purpose": "Module import boundary enforcement blocks forbidden cross-layer imports",
        "type": "policy-contract",
        "verifies": {"docs": ["docs/architecture/module_boundary_matrix.md"], "specs": ["specs/contracts/module_boundary_contract.yaml"], "rules": []},
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
        "verifies": {"docs": [], "specs": ["specs/contracts/source_conflict_rules.yaml"], "rules": []},
        "command": "uv run python -m pytest tests/test_source_conflict_validator.py -q",
        "failure_meaning": "Conflicting sources may not be rejected.",
    },
    "tests/test_staged_pilot.py": {
        "purpose": "Staged pilot sandbox boundaries; does not open production-live",
        "type": "policy-contract",
        "verifies": {"docs": ["docs/quality/production_live_pilot_policy.md"], "specs": ["specs/contracts/review_sandbox_contract.yaml"], "rules": []},
        "command": "uv run python -m pytest tests/test_staged_pilot.py -q",
        "failure_meaning": "Staged pilot may be misread as production-live readiness.",
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
