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
    assert "五层模型" in content
    assert "docs/architecture/" in content or "docs/modules/" in content
    assert "MANIFEST.json" in content


def test_initDb_createsDuckDbDirectory(tmp_path, monkeypatch) -> None:
    import scripts.init_db as init_db_mod

    data_root = tmp_path / "data"
    monkeypatch.setattr(init_db_mod, "DATA_ROOT", data_root)
    init_db_mod.main()
    assert (data_root / "duckdb").is_dir()
    assert (data_root / "duckdb" / "quant_monitor.duckdb").is_file()
