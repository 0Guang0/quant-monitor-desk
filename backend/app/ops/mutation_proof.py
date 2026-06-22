"""Shared mutation-proof helpers for pilot and probe evidence (OP-02)."""

from __future__ import annotations

from pathlib import Path

from backend.app.db.connection import ConnectionManager
from backend.app.ops.db_inspector import KEY_TABLES


def key_table_row_counts(db_path: Path) -> dict[str, int | None]:
    """Read-only row counts for key tables used in no-mutation proofs."""
    if not db_path.is_file():
        return {}
    counts: dict[str, int | None] = {}
    cm = ConnectionManager(db_path, profile="eco")
    with cm.reader() as con:
        tables = {
            row[0]
            for row in con.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'main'
                """
            ).fetchall()
        }
        for name in KEY_TABLES:
            if name not in tables:
                counts[name] = None
                continue
            row_count = con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
            counts[name] = int(row_count)
    return counts
