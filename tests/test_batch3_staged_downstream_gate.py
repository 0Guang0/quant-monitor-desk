"""Batch 3 staged-only downstream gate document tests."""

from __future__ import annotations

from pathlib import Path

from tests.contract_gate_support import PROJECT_ROOT

GATE_DOC = PROJECT_ROOT / "docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md"
TASK_019 = (
    PROJECT_ROOT
    / "docs/implementation_tasks/ROUND_3_MODELING_LAYERS/019_implement_layer2_cross_asset_sensor.md"
)
ROUND3_MAP = PROJECT_ROOT / "ROUND3_BATCH_IMPLEMENTATION_MAP.md"
HANDOFF = PROJECT_ROOT / "docs/ROUND3_HANDOFF.md"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing expected document: {path}"
    return path.read_text(encoding="utf-8")


def test_batch3_staged_gate_records_fail_closed_decisions() -> None:
    text = _read(GATE_DOC)
    for token in (
        "R3-B3-STAGED-DOWNSTREAM-GATE",
        "PILOT_FAIL_SOURCE",
        "R3-B2.75-REQ2-EM",
        "staged-only",
        "does not open production-live",
        "018C",
        "does not unblock production-live",
        "Fail-closed production-live language",
        "`019` staged-only start conditions",
        "**CLOSED**",
    ):
        assert token in text
    for token in (
        "live FRED primary",
        "production clean DB mutation",
        "QMT/xqshare/Yahoo",
        "full-market/full-history",
    ):
        assert token in text


def test_task019_and_handoff_require_closed_gate_before_runtime() -> None:
    assert "R3-B3-STAGED-DOWNSTREAM-GATE" in _read(TASK_019)
    assert "feature/round3-batch3-staged-gate" in _read(TASK_019)
    handoff = _read(HANDOFF)
    assert "PILOT_FAIL_SOURCE" in handoff
    assert "R3-B2.75-REQ2-EM" in handoff
    assert "CLOSED" in handoff
    assert "Do not start `feature/round3-019-layer2-sensor`" in _read(ROUND3_MAP)
