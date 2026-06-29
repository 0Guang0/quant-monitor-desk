#!/usr/bin/env python3
"""Patch implement.jsonl reasons from integration-ledger.md + default v3 reasons."""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Fallback extract/for for paths not in ledger (V7 closure).
_DEFAULT_REASONS: dict[str, tuple[str, str]] = {
    "docs/implementation_tasks/README.md": (
        "Round/batch order and task index",
        "global protocol / P0o",
    ),
    "docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md": (
        "Execute boundaries and evidence rules",
        "global protocol / §0.3",
    ),
    "docs/implementation_tasks/GLOBAL_TESTING_POLICY.md": (
        "TDD policy and assertion style",
        "global protocol / §8 RED-GREEN",
    ),
    "docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md": (
        "eco mode and ResourceGuard limits",
        "AC-5 / §8.4",
    ),
    "docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md": (
        "Task artifact structure reference",
        "global protocol / P0o",
    ),
    "docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/014_implement_data_sync_orchestrator.md": (
        "task card §3 inputs and §5 deliverables",
        "AC-1–12 / §8",
    ),
    "docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/BATCH_C_REPAIR_STATUS.md": (
        "Batch C deferred items and handoff",
        "AC scope / §3.2",
    ),
    "docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/BATCH_C_LEDGER.md": (
        "C-C1 transaction and C-C2 fetch_log policy",
        "AC-6 / §8.5",
    ),
    "docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/README.md": (
        "Round 2 batch order and Batch D prerequisites",
        "P0o / scope",
    ),
    "docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/BATCH_B_REPAIR_STATUS.md": (
        "DECISIONS §9 cross-batch defer ledger",
        "§3.2 defer",
    ),
    "docs/architecture/07_project_directory_structure.md": (
        "backend/app path normalization",
        "DECISIONS §1 / wiring",
    ),
    "docs/quality/final_package_rules.md": (
        "task card §5 final package rules",
        "AC-11 / §10",
    ),
    "docs/modules/data_validation_and_conflict.md": (
        "validator/gate module spec orchestrator wires",
        "AC-6 / §8.5",
    ),
    "docs/modules/data_sources.md": (
        "fetch_log and source_registry authority",
        "AC-6 / §8.5",
    ),
    "docs/modules/write_manager.md": (
        "job_id write_audit via WriteManager",
        "AC-8 / §8.5",
    ),
    "docs/modules/duckdb_and_parquet.md": (
        "table/archive rules from orchestrator spec refs",
        "AC-8 / §8.5",
    ),
    "backend/app/datasources/adapters/__init__.py": (
        "create_adapter factory entry",
        "AC-6 / §8.5",
    ),
    "backend/app/validators/data_quality.py": (
        "DataQualityValidator VALIDATING stage",
        "AC-6 / §8.5",
    ),
    "backend/app/validators/source_conflict.py": (
        "SourceConflictValidator reconcile delegate",
        "AC-6 / §8.7",
    ),
    "backend/app/db/migrate.py": (
        "migration 006 runner registration",
        "AC-7 / §8.1",
    ),
    "scripts/init_db.py": (
        "init_db idempotency; does NOT default registry sync",
        "AC-7 / §8.1 (not AC-10)",
    ),
    "backend/app/db/connection.py": (
        "ConnectionManager writer single-writer lock",
        "AC-6 / §8.5",
    ),
    "backend/app/datasources/fetch_log.py": (
        "fetch_log persistence via adapter.fetch writer con",
        "AC-6 / §8.5",
    ),
    "backend/app/datasources/fetch_result.py": (
        "FetchStatus/FetchResult for FETCHING stage",
        "AC-6 / §8.5",
    ),
    "backend/app/datasources/adapters/fetch_port.py": (
        "PortErrorStatus mapping at adapter boundary",
        "AC-6 / §8.5",
    ),
    "backend/app/db/migrations/005_ingestion_validation.sql": (
        "validation_gate tables orchestrator wires",
        "AC-6 / §8.5",
    ),
    "specs/datasource_registry/source_registry.yaml": (
        "Registry YAML authority for sync_registry",
        "AC-10 / §8.8",
    ),
    "backend/app/config.py": (
        "DATA_ROOT / QMD_DATA_ROOT for smoke and init_db",
        "AC-9 / §8.9",
    ),
    "backend/app/util/error_redaction.py": (
        "error message redaction policy",
        "AC trace / §8 wiring",
    ),
    "tests/test_write_manager.py": (
        "§9.2 Tier B write_audit with job_id regression",
        "AC-8 / §9.2",
    ),
    "tests/test_source_registry.py": (
        "tombstone_missing baseline for §8.8",
        "AC-10 / §8.8",
    ),
    "tests/test_resource_guard.py": (
        "ResourceGuard decision semantics",
        "AC-5 / §8.4",
    ),
    "tests/test_db_validation_gate.py": (
        "Batch C gate behavior to preserve",
        "AC-6 / §8.5",
    ),
    "tests/test_data_quality_validator.py": (
        "VALIDATING stage validator baseline",
        "AC-6 / §8.5",
    ),
    "tests/test_source_conflict_validator.py": (
        "reconcile delegate baseline",
        "AC-6 / §8.7",
    ),
    "tests/conftest.py": (
        "migrated_con and registry fixtures",
        "§8 tests / §9.2",
    ),
    "scripts/check_doc_links.py": (
        "§9.3 Tier C doc link gate",
        "AC-11 / §9.3",
    ),
    ".trellis/spec/backend/index.md": (
        "backend guidelines index",
        "implementation quality / §12",
    ),
    ".trellis/spec/backend/database-guidelines.md": (
        "DuckDB migration conventions",
        "AC-7 / §8.1",
    ),
    ".trellis/spec/backend/datasource-adapters.md": (
        "adapter factory contracts",
        "AC-6 / §8.5",
    ),
    ".trellis/spec/backend/quality-guidelines.md": (
        "forbidden patterns for orchestrator",
        "§12 / code quality",
    ),
    ".trellis/spec/guides/index.md": (
        "cross-package guides index",
        "protocol / §12",
    ),
}


def _norm(path: str) -> str:
    return path.replace("\\", "/").strip()


def main() -> int:
    task = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        ".trellis/tasks/06-18-round2-batch-d-orchestrator"
    )
    ledger = task / "research/integration-ledger.md"
    impl_path = task / "implement.jsonl"
    mapping: dict[str, tuple[str, str]] = dict(_DEFAULT_REASONS)

    if ledger.is_file():
        for line in ledger.read_text(encoding="utf-8").splitlines():
            if not line.startswith("|") or "---" in line:
                continue
            cols = [c.strip().strip("`") for c in line.split("|") if c.strip()]
            if len(cols) < 6 or cols[0].lower() == "source":
                continue
            src, strat, extract, for_ac = cols[0], cols[2].lower(), cols[4], cols[5]
            if src and "pointer" in strat:
                mapping[_norm(src)] = (extract, for_ac)

    task_slug = task.name
    mapping[_norm(f".trellis/tasks/{task_slug}/research/gitnexus-summary.md")] = (
        "Plan-phase graph baseline only",
        "6.pre gitnexus-execute-summary / §0.1",
    )
    mapping[_norm(f".trellis/tasks/{task_slug}/research/orchestrator-tests.md")] = (
        "RED/GREEN tracer names per §8 step",
        "§8 RED-GREEN evidence",
    )
    mapping[_norm(f".trellis/tasks/{task_slug}/research/original-plan-trace.md")] = (
        "P0o AC mapping manifest column",
        "traceability / Audit A5",
    )
    mapping[_norm(".trellis/tasks/06-17-round2-batch-c-validation-conflict/finish.md")] = (
        "Batch C READY_FOR_BATCH_D handoff",
        "scope gate / §0",
    )

    patched = 0
    out: list[str] = []
    for line in impl_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        f = _norm(obj.get("file", ""))
        if f in mapping and not (
            "extract:" in str(obj.get("reason", "")).lower()
            and "for:" in str(obj.get("reason", "")).lower()
        ):
            ex, fac = mapping[f]
            obj["reason"] = f"extract: {ex} | for: {fac}"
            patched += 1
        out.append(json.dumps(obj, ensure_ascii=False))
    impl_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"patched {patched} implement reasons ({len(mapping)} known mappings)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
