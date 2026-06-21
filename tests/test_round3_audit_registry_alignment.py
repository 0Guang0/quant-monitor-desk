"""Round 3 Batch 2.5 / Batch 2.75 audit follow-up 文档对齐测试。"""

from __future__ import annotations

from pathlib import Path

from tests.contract_gate_support import PROJECT_ROOT

UNRESOLVED = PROJECT_ROOT / "docs/UNRESOLVED_ISSUES_REGISTRY.md"
RESOLVED = PROJECT_ROOT / "docs/RESOLVED_ISSUES_REGISTRY.md"
ROUND3_MAP = PROJECT_ROOT / "ROUND3_BATCH_IMPLEMENTATION_MAP.md"
TASK_018B = (
    PROJECT_ROOT
    / "docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018B_production_live_pilot_gate.md"
)
TASK_019 = (
    PROJECT_ROOT
    / "docs/implementation_tasks/ROUND_3_MODELING_LAYERS/019_implement_layer2_cross_asset_sensor.md"
)
GITIGNORE = PROJECT_ROOT / ".gitignore"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing expected document: {path}"
    return path.read_text(encoding="utf-8")


def test_batch25ClosedItems_areResolvedAndNotStillOpen() -> None:
    unresolved = _read(UNRESOLVED)
    resolved = _read(RESOLVED)
    gitignore = _read(GITIGNORE)

    for item_id in ("R3-B25-DOC-01", "A08-P1-02", "R3-B25-HYG-04"):
        assert item_id in resolved
        assert f"| {item_id} | OPEN" not in unresolved
        assert f"| {item_id} | OPEN " not in unresolved

    assert "BATCH3_STAGED_DOWNSTREAM_GATE.md" in resolved
    assert "pytest slow marker" in resolved
    assert ".audit-sandboxpytest-*/" in gitignore


def test_hyg03_keepsOnlyPerformanceBudgetGapOpen() -> None:
    unresolved = _read(UNRESOLVED)

    assert "R3-B25-HYG-03" in unresolved
    assert "test tier 已补" in unresolved
    assert "A08-P2-01 / A08-P2-02" in unresolved
    assert "production-equivalent benchmark" in unresolved
    assert "performance-budget artifact" in unresolved
    assert "无 test tier / 新 A6 benchmark" not in unresolved


def test_task019_requiresBatch3StagedOnlyDownstreamGate() -> None:
    text = _read(TASK_019)

    for token in (
        "Batch 3 staged-only downstream gate",
        "docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md",
        "ingestion type 是 staged，不是 production-live",
        "018A_layer1_observation_ingestion_bridge.md",
        "R3-B2.75-01",
        "production-live readiness",
    ):
        assert token in text


def test_round3Map_tracksCompleteBatch275Scope() -> None:
    text = _read(ROUND3_MAP)

    for token in (
        "Batch 2.75 must include, and only include",
        "R3-B2.75-PROD-LIVE-PILOT",
        "R3-B2.75-01",
        "GLOBAL-P2-01",
        "B2.5-O-05",
        "R3-B25-PERF-BUDGET-01",
        "R3-B25-HYG-03",
        "production-equivalent benchmark",
        "performance-budget evidence artifact",
        "scripts/production_equivalent_smoke.py",
        "PILOT_PASS_RAW_ONLY",
        "PILOT_PASS_SANDBOX_CLEAN",
        "PILOT_FAIL_SOURCE",
        "PILOT_FAIL_VALIDATION",
        "PILOT_REDEFERRED",
        "Batch 3 handoff note",
    ):
        assert token in text

    for token in (
        "migration 008 CHECK closeout",
        "ingestion split R2b–R2d",
        "frontend Vitest/bundle budget",
        "Batch 3 modeling implementation",
    ):
        assert token in text


def test_task018B_declaresCompleteBatch275ScopeAndCloseout() -> None:
    text = _read(TASK_018B)

    for token in (
        "Batch 2.75 scope ledger",
        "R3-B2.75-PROD-LIVE-PILOT",
        "R3-B2.75-01",
        "GLOBAL-P2-01",
        "B2.5-O-05",
        "R3-B25-PERF-BUDGET-01",
        "R3-B25-HYG-03",
        "Phase -1 — current-state reconciliation",
        "Phase 4.5 — performance-budget evidence gate",
        "production_equivalent_smoke.py",
        "Batch 3 handoff note",
        "not in Batch 2.75",
        "CI nightly / Batch6",
    ):
        assert token in text

    for token in (
        "No migration 008 CHECK closeout",
        "No ingestion monolith split / R2b-R2d refactor",
        "No frontend Vitest or bundle budget implementation",
        "No Batch 3 Layer 2 modeling implementation",
        "No Batch6 production CLI/backfill/reconcile/source-health release gate closure",
    ):
        assert token in text


def test_round3Map_tracksPostAuditIngestionAndRound4References() -> None:
    text = _read(ROUND3_MAP)

    for token in (
        "R3-B25-INGEST-SPLIT-R2B",
        "R3-B25-INGEST-MONOLITH-R2C-R2D",
        "layer1_ingestion_refactor_rollback_plan.md",
        "R2b/R2c/R2d",
        "R3-B25-FE-BUNDLE-BUDGET",
        "Round4 cross-reference only",
    ):
        assert token in text
