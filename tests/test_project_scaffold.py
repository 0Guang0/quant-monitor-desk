"""Verify project scaffold directories (Round 0 task 001)."""

from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DIRS = [
    "backend/app/api",
    "backend/app/db",
    "backend/app/layer1_axes",
    "backend/app/layer3_chains",
    "backend/app/agents",
    "frontend/src",
    "scripts",
    "tests",
    "data/duckdb",
    "configs",
    "docs/architecture",
    "specs/schema",
    "specs/contracts",
]


@pytest.mark.parametrize("relative_dir", REQUIRED_DIRS)
def test_scaffoldDirectory_exists_shouldBePresent(relative_dir: str) -> None:
    assert (PROJECT_ROOT / relative_dir).is_dir(), f"missing directory: {relative_dir}"


def test_migrationMap_exists_shouldGuideNavigation() -> None:
    content = (PROJECT_ROOT / "MIGRATION_MAP.md").read_text(encoding="utf-8")
    assert "Five-layer model" in content
    assert "docs/implementation_tasks/" in content
