"""Tests for Trellis manifest protocol (E1–E20)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / ".trellis" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from common.manifest_protocol import (  # noqa: E402
    is_negative_implement_path,
    parse_master_section9_paths,
    parse_trace_manifest,
    suggest_implement_context,
    validate_manifest_freeze,
    validate_plan_manifest_audit,
)
from common.validate_plan_freeze import validate_plan_freeze  # noqa: E402

BATCH_D_SLUG = "06-18-round2-batch-d-orchestrator"
BATCH_D = REPO / ".trellis/tasks" / BATCH_D_SLUG
if not BATCH_D.exists():
    BATCH_D = REPO / ".trellis/tasks/archive/2026-06" / BATCH_D_SLUG


def _resolve_task_artifact(rel: str) -> Path | None:
    """Resolve implement.jsonl task artifact paths across active/archive locations."""
    full = REPO / rel
    if full.is_file():
        return full
    if not rel.startswith(".trellis/tasks/"):
        return None
    parts = Path(rel).parts
    if len(parts) < 3:
        return None
    slug = parts[2]
    suffix = Path(*parts[3:]) if len(parts) > 3 else Path()
    candidates = [
        REPO / ".trellis/tasks" / slug / suffix,
        REPO / ".trellis/tasks/archive/2026-06" / slug / suffix,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def test_negative_implement_paths():
    assert is_negative_implement_path("backend/app/sync/orchestrator.py")
    assert is_negative_implement_path("scripts/sync_registry.py")
    assert not is_negative_implement_path("backend/app/db/migrate.py")


def test_parse_trace_manifest_required():
    trace = BATCH_D / "research/original-plan-trace.md"
    manifest = parse_trace_manifest(trace)
    assert manifest.get("docs/modules/data_sync_orchestrator.md") == "required"
    assert manifest.get("scripts/sync_registry.py") == "deferred"


def test_batch_d_suggest_implement_empty():
    suggestions = suggest_implement_context(BATCH_D, REPO)
    assert suggestions == []


def test_batch_d_manifest_freeze_passes():
    errors = validate_plan_freeze(BATCH_D, REPO)
    assert errors == [], f"unexpected errors: {errors}"


def test_plan_manifest_audit_present():
    errors: list[str] = []
    validate_plan_manifest_audit(BATCH_D, errors)
    assert errors == []


def test_section9_paths_parsed_from_master():
    master = (BATCH_D / "MASTER.plan.md").read_text(encoding="utf-8")
    paths = parse_master_section9_paths(master)
    assert any("test_sync_migration.py" in p for p in paths) or any(
        "test_batch_d" in p for p in paths
    )


def test_implement_jsonl_paths_exist():
    impl = BATCH_D / "implement.jsonl"
    task_prefix = f".trellis/tasks/{BATCH_D_SLUG}/"
    for line in impl.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        rel = obj.get("file") or obj.get("path")
        if not rel:
            continue
        if rel.startswith(task_prefix):
            suffix = rel[len(task_prefix) :]
            assert (BATCH_D / suffix).is_file(), rel
            continue
        if rel.startswith(".trellis/tasks/"):
            resolved = _resolve_task_artifact(rel)
            assert resolved is not None and resolved.is_file(), rel
            continue
        assert (REPO / rel).is_file(), rel


def test_batch_d_v3_artifacts():
    errors: list[str] = []
    from common.manifest_protocol import (
        validate_input_inventory,
        validate_integration_audit,
        validate_integration_ledger,
    )

    validate_input_inventory(BATCH_D, errors)
    validate_integration_ledger(BATCH_D, REPO, errors)
    validate_integration_audit(BATCH_D, errors)
    assert errors == [], errors


def test_batch_d_manifest_protocol_version():
    import json

    data = json.loads((BATCH_D / "task.json").read_text(encoding="utf-8"))
    assert data.get("meta", {}).get("manifest_protocol_version") == "3"


def test_batch_d_v7_implement_reasons():
    from common.manifest_protocol import validate_implement_reason_coverage

    errors: list[str] = []
    validate_implement_reason_coverage(BATCH_D, errors)
    assert errors == [], errors


def test_batch_d_v8_ledger_anchors():
    from common.manifest_protocol import validate_ledger_master_anchors

    errors: list[str] = []
    validate_ledger_master_anchors(BATCH_D, errors)
    assert errors == [], errors


def test_batch_d_v9_integration_ledger_in_implement():
    from common.manifest_protocol import validate_integration_ledger_in_implement

    errors: list[str] = []
    validate_integration_ledger_in_implement(BATCH_D, errors)
    assert errors == [], errors


def test_validate_manifest_freeze_bundle():
    errors: list[str] = []
    validate_manifest_freeze(BATCH_D, REPO, errors)
    assert errors == [], errors
