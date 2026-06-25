"""Shared Layer1 ingestion sandbox DB/data_root bootstrap (PR-R2b)."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

import duckdb
from backend.app.db.migrate import apply_migrations
from backend.app.layer1_axes.ingestion_inventory import TARGET_DB_RELATIVE

PHASE3_SANDBOX_DIRNAME = ".phase3-micro-fetch-sandbox"
PHASE4_SANDBOX_DIRNAME = ".phase4-clean-write-sandbox"


@dataclass(frozen=True)
class IngestionSandboxLayout:
    base_dir: Path
    db_path: Path
    data_root: Path


def _reset_tree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def bootstrap_empty_migrated_db(db_path: Path) -> None:
    """Create an empty DuckDB file with migrations applied."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    try:
        apply_migrations(con)
    finally:
        con.close()


def prepare_phase3_sandbox(evidence_out: Path) -> IngestionSandboxLayout:
    """Fresh isolated DB + data_root for Phase 3 micro-fetch evidence."""
    sandbox_base = evidence_out / PHASE3_SANDBOX_DIRNAME
    _reset_tree(sandbox_base)
    db_path = sandbox_base / TARGET_DB_RELATIVE
    data_root = sandbox_base / "data"
    bootstrap_empty_migrated_db(db_path)
    data_root.mkdir(parents=True, exist_ok=True)
    return IngestionSandboxLayout(base_dir=sandbox_base, db_path=db_path, data_root=data_root)


def prepare_phase4_fallback_sandbox(evidence_out: Path) -> IngestionSandboxLayout:
    """Fresh fallback DB + data_root when Phase 1 baseline copy is unavailable."""
    sandbox_base = evidence_out / PHASE4_SANDBOX_DIRNAME
    _reset_tree(sandbox_base)
    db_path = sandbox_base / TARGET_DB_RELATIVE
    data_root = sandbox_base / "data"
    bootstrap_empty_migrated_db(db_path)
    data_root.mkdir(parents=True, exist_ok=True)
    return IngestionSandboxLayout(base_dir=sandbox_base, db_path=db_path, data_root=data_root)


def prepare_phase4_data_root(evidence_out: Path) -> Path:
    """Ensure Phase 4 staged data_root exists under the phase4 sandbox tree."""
    data_root = evidence_out / PHASE4_SANDBOX_DIRNAME / "data"
    data_root.mkdir(parents=True, exist_ok=True)
    return data_root
