"""Sandbox DB resolution for Layer1 phase evidence tasks (L1-04)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import duckdb
from backend.app.db.migrate import apply_migrations


@dataclass(frozen=True)
class TaskSandboxDb:
    inspect_db: Path
    db_capture_strategy: str
    baseline_db_relative: str | None = None


def resolve_task_sandbox_db(
    *,
    evidence_dir: Path,
    sandbox_db: Path,
    target_db: Path,
    target_db_exists: bool,
    copy_sandbox_db,
    fallback_sandbox_db: Path | None = None,
    fallback_strategy: str = "fresh_phase4_sandbox_fallback",
) -> TaskSandboxDb:
    """Resolve inspect DB for phase2/4 task evidence (deduped sandbox branches)."""
    baseline_db_relative = None
    if sandbox_db.is_file():
        return TaskSandboxDb(
            inspect_db=sandbox_db,
            db_capture_strategy="phase1_sandbox_copy_reused",
            baseline_db_relative=str(sandbox_db),
        )
    if target_db_exists:
        sandbox_db.parent.mkdir(parents=True, exist_ok=True)
        copy_sandbox_db(target_db, sandbox_db)
        return TaskSandboxDb(
            inspect_db=sandbox_db,
            db_capture_strategy="sandbox_copy_aligned_with_phase1",
            baseline_db_relative=str(sandbox_db),
        )
    if fallback_sandbox_db is not None:
        fallback_sandbox_db.parent.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect(str(fallback_sandbox_db))
        try:
            apply_migrations(con)
        finally:
            con.close()
        return TaskSandboxDb(
            inspect_db=fallback_sandbox_db,
            db_capture_strategy=fallback_strategy,
        )
    sandbox_db.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(sandbox_db))
    try:
        apply_migrations(con)
    finally:
        con.close()
    return TaskSandboxDb(
        inspect_db=sandbox_db,
        db_capture_strategy="synthetic_migrated_schema_only",
        baseline_db_relative=str(sandbox_db),
    )
