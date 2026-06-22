"""Shared read-only DuckDB table row counts (L1-11)."""

from __future__ import annotations

from pathlib import Path

import duckdb


def table_row_counts(db_path: Path | str, tables: tuple[str, ...]) -> dict[str, int | None]:
    con = duckdb.connect(str(db_path), read_only=True)
    counts: dict[str, int | None] = {}
    try:
        for name in tables:
            exists = con.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'main' AND table_name = ?
                """,
                [name],
            ).fetchone()[0]
            if not exists:
                counts[name] = None
                continue
            counts[name] = int(con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0])
    finally:
        con.close()
    return counts
