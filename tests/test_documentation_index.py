"""Verify documentation index (Round 0 task 004)."""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = PROJECT_ROOT / "docs/INDEX.md"
LINK_PATTERN = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def _is_external(link: str) -> bool:
    lowered = link.lower()
    return (
        lowered.startswith("http://")
        or lowered.startswith("https://")
        or lowered.startswith("mailto:")
        or link.startswith("#")
    )


def test_docsIndex_linksArchitectureAndTasks_shouldBeNavigable() -> None:
    index = INDEX_PATH.read_text(encoding="utf-8")
    assert "00_project_overview.md" in index
    assert "implementation_tasks/README.md" in index
    assert "GLOBAL_EXECUTION_RULES.md" in index


def test_docsIndex_linksMigrationMap_shouldCrossReferenceRootMap() -> None:
    index = INDEX_PATH.read_text(encoding="utf-8")
    assert "MIGRATION_MAP.md" in index


def test_docsIndex_relativeLinks_resolveToExistingFiles() -> None:
    """GPT: parse INDEX.md links and verify targets exist."""
    index = INDEX_PATH.read_text(encoding="utf-8")
    broken: list[str] = []
    for match in LINK_PATTERN.finditer(index):
        link = match.group(1).strip()
        if not link or _is_external(link):
            continue
        path_part = link.split("#", 1)[0]
        if not path_part:
            continue
        target = (INDEX_PATH.parent / path_part).resolve()
        if not target.exists():
            broken.append(link)
    assert not broken, f"broken INDEX.md links: {broken}"
