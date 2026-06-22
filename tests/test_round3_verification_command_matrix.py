"""Round 3 verification command matrix — doc index and gate-test discoverability.

These tests do not exercise runtime behavior. They ensure operators and merge
coordinators can find staged-only vs production-live guard tests from one place.
"""

from __future__ import annotations

from pathlib import Path

from tests.contract_gate_support import PROJECT_ROOT

VERIFICATION_COMMANDS = PROJECT_ROOT / "docs/ops/verification_commands.md"
ROUND3_MAP = PROJECT_ROOT / "ROUND3_BATCH_IMPLEMENTATION_MAP.md"

# Canonical Round 3 gate hygiene commands (PROMPT_05 + staged/live guards).
ROUND3_GATE_COMMANDS: tuple[tuple[str, str, str], ...] = (
    (
        "audit-trace-authority",
        "tests/test_trellis_audit_trace_authority.py",
        "uv run python -m pytest tests/test_trellis_audit_trace_authority.py -q",
    ),
    (
        "audit-registry-alignment",
        "tests/test_round3_audit_registry_alignment.py",
        "uv run python -m pytest tests/test_round3_audit_registry_alignment.py -q",
    ),
    (
        "unresolved-item-coverage",
        "tests/test_unresolved_item_task_coverage.py",
        "uv run python -m pytest tests/test_unresolved_item_task_coverage.py -q",
    ),
    (
        "batch25-staged-not-live",
        "tests/test_batch25_production_data_gate.py",
        "uv run python -m pytest tests/test_batch25_production_data_gate.py -q",
    ),
    (
        "production-live-pilot-policy",
        "tests/test_production_live_pilot_policy.py",
        "uv run python -m pytest tests/test_production_live_pilot_policy.py -q",
    ),
    (
        "batch3-staged-downstream-gate",
        "tests/test_batch3_staged_downstream_gate.py",
        "uv run python -m pytest tests/test_batch3_staged_downstream_gate.py -q",
    ),
    (
        "fred-staged-semantics",
        "tests/test_fred_staged_semantics.py",
        "uv run python -m pytest tests/test_fred_staged_semantics.py -q",
    ),
)

DOC_LINK_CHECK = "uv run python scripts/check_doc_links.py"

# Related Batch 2.75 pilot gate — includes @pytest.mark.network cases; not default CI.
BATCH275_PILOT_GATE_MODULE = "tests/test_batch275_live_pilot_gate.py"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing expected document: {path}"
    return path.read_text(encoding="utf-8")


def test_round3GateTestModules_existOnDisk() -> None:
    for _gate_id, module, _command in ROUND3_GATE_COMMANDS:
        assert (PROJECT_ROOT / module).is_file(), f"missing gate test module: {module}"


def test_verificationCommandsDoc_listsRound3GateMatrix() -> None:
    text = _read(VERIFICATION_COMMANDS)
    assert "## Round 3 gate hygiene" in text
    assert DOC_LINK_CHECK in text
    for gate_id, module, command in ROUND3_GATE_COMMANDS:
        assert gate_id in text, f"verification_commands.md missing gate id: {gate_id}"
        assert module in text, f"verification_commands.md missing module: {module}"
        assert command in text, f"verification_commands.md missing command for {gate_id}"


def test_verificationCommandsDoc_distinguishesStagedFromProductionLive() -> None:
    text = _read(VERIFICATION_COMMANDS)
    for token in (
        "staged-only",
        "production-live",
        "does not open production-live",
        "test_batch25_production_data_gate.py",
        "test_batch3_staged_downstream_gate.py",
        "test_fred_staged_semantics.py",
        "test_production_live_pilot_policy.py",
    ):
        assert token in text, f"verification_commands.md missing staged/live token: {token}"


def test_verificationCommandsDoc_notesBatch275NetworkExclusion() -> None:
    text = _read(VERIFICATION_COMMANDS)
    assert BATCH275_PILOT_GATE_MODULE in text
    assert "not default CI" in text or "not default Round 3 CI" in text
    assert "network" in text.lower()


def test_round3BatchMap_pointsToVerificationCommandMatrix() -> None:
    text = _read(ROUND3_MAP)
    assert "docs/ops/verification_commands.md" in text
    assert "Round 3 gate hygiene" in text or "gate hygiene command matrix" in text
