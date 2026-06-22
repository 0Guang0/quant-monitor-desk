"""B2.5-O-05 FRED / macro_supplementary staged-semantics gate tests."""

from __future__ import annotations

from pathlib import Path

from tests.contract_gate_support import PROJECT_ROOT

POLICY = PROJECT_ROOT / "docs/quality/production_live_pilot_policy.md"
GATE_DOC = PROJECT_ROOT / "docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md"
HANDOFF = PROJECT_ROOT / "docs/ROUND3_HANDOFF.md"
ROUND3_MAP = PROJECT_ROOT / "ROUND3_BATCH_IMPLEMENTATION_MAP.md"
TASK_018A = (
    PROJECT_ROOT
    / "docs/implementation_tasks/ROUND_3_MODELING_LAYERS"
    / "018A_layer1_observation_ingestion_bridge.md"
)
TASK_019 = (
    PROJECT_ROOT
    / "docs/implementation_tasks/ROUND_3_MODELING_LAYERS/019_implement_layer2_cross_asset_sensor.md"
)
AUDIT_DEFERRED = PROJECT_ROOT / "docs/AUDIT_DEFERRED_REGISTRY.md"
UNRESOLVED = PROJECT_ROOT / "docs/UNRESOLVED_ISSUES_REGISTRY.md"
PENDING_FIX = PROJECT_ROOT / "docs/quality/ROUND3_BATCH25_PENDING_FIX_REGISTRY.md"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing expected document: {path}"
    return path.read_text(encoding="utf-8")


def test_b250o05_remainsDeferred_withExplicitClosureCommand() -> None:
    audit = _read(AUDIT_DEFERRED)
    unresolved = _read(UNRESOLVED)
    pending = _read(PENDING_FIX)

    for registry in (audit, unresolved, pending):
        assert "B2.5-O-05" in registry

    for token in (
        "RE-DEFERRED",
        "Request 3",
        "FRED:DGS10",
        "macro_supplementary",
        "Batch 6",
        "test_fred_staged_semantics.py",
    ):
        assert token in audit or token in unresolved or token in pending


def test_policy_and_gate_forbidFredPrimaryMisreadFromRequest3() -> None:
    policy = _read(POLICY)
    gate = _read(GATE_DOC)

    for token in (
        "B2.5-O-05",
        "Request 3",
        "does **not** close `B2.5-O-05`",
        "macro_supplementary",
        "not be cited as live FRED primary",
        "staged supplementary route",
    ):
        assert token in policy

    assert "B2.5-O-05" in gate
    assert "Request 3" in gate
    assert "does **not** close" in gate
    assert "macro_supplementary" in gate


def test_handoff_map_and_taskCards_preserveStagedMacroSemantics() -> None:
    handoff = _read(HANDOFF)
    round3_map = _read(ROUND3_MAP)
    task_018a = _read(TASK_018A)
    task_019 = _read(TASK_019)

    for text in (handoff, round3_map, task_018a, task_019):
        assert "B2.5-O-05" in text
        assert "macro_supplementary" in text

    assert "does **not** close" in handoff
    assert "does **not** close" in round3_map
    assert "supplementary macro shape evidence only" in task_018a
    assert "Request 3" in task_019
