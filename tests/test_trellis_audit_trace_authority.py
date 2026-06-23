"""Trellis Audit Trace Authority — Batch 2.75 plan freeze gate tests."""

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
    paths = _audit_jsonl_paths()
    for required in REQUIRED_AUDIT_PATHS:
        assert required in paths, f"audit.jsonl missing trace authority: {required}"
        assert (PROJECT_ROOT / required).is_file(), f"missing on disk: {required}"


def test_auditPlan_assignsA1A5A8SourceTraceDuties() -> None:
    text = AUDIT_PLAN.read_text(encoding="utf-8")
    assert "Trace Authority Set" in text
    assert "A1 必须执行 original-source trace" in text
    assert "A5 必须执行 AC source-chain trace" in text
    assert "A8 必须执行 original-red-flags test-gap trace" in text
    assert "A1 / A5 / A8 必须倒查原始任务卡" in text


def test_auditPlan_includesTraceAuthorityTable() -> None:
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
    text = PLAN_FREEZE.read_text(encoding="utf-8")
    assert "Audit source trace gate" in text
    assert "audit.jsonl` includes original task card" in text
    assert "A1 / A5 / A8" in text
    assert "PH-B0 includes source trace authority check" in text


def test_phB0_includesB07SourceTraceCheck() -> None:
    text = AUDIT_PLAN.read_text(encoding="utf-8")
    assert "B0-7" in text
    assert "original-source trace authority set" in text


def test_followup018C_documentsExternalReferencesAndBoundaries() -> None:
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
    text = (PROJECT_ROOT / "ROUND3_BATCH_IMPLEMENTATION_MAP.md").read_text(encoding="utf-8")
    assert "R3-B2.75-FOLLOWUP-DATA-INTERFACE-PROBE" in text
    assert "018C_tdx_pytdx_low_cost_probe.md" in text
    assert "cannot close Batch 2.75 Request 2" in text
    assert "Batch 2.75 follow-up" in text
