"""Verify documentation index (Round 0 task 004)."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_docsIndex_linksArchitectureAndTasks_shouldBeNavigable() -> None:
    index = (PROJECT_ROOT / "docs/INDEX.md").read_text(encoding="utf-8")
    assert "00_project_overview.md" in index
    assert "implementation_tasks/README.md" in index
    assert "GLOBAL_EXECUTION_RULES.md" in index


def test_docsIndex_linksMigrationMap_shouldCrossReferenceRootMap() -> None:
    index = (PROJECT_ROOT / "docs/INDEX.md").read_text(encoding="utf-8")
    assert "MIGRATION_MAP.md" in index
