"""Shared mutation-proof helpers for pilot and probe evidence (OP-02)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from backend.app.db.connection import ConnectionManager
from backend.app.ops.db_inspector import KEY_TABLES

ProofStatus = Literal["VERIFIED", "INCONCLUSIVE"]


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


def build_production_mutation_proof(
    db_path: Path,
    *,
    before_counts: dict[str, int | None] | None = None,
    before_bytes: bytes | None = None,
    after_counts: dict[str, int | None] | None = None,
    after_bytes: bytes | None = None,
) -> dict[str, Any]:
    """Build fail-closed production DB no-mutation proof payload.

    When the production DB file is absent, ``proof_status`` is ``INCONCLUSIVE``
    and hash/count equality fields are ``None`` (ADV-POST14-A-001).
    """
    resolved = Path(db_path)
    if not resolved.is_file():
        return {
            "production_db_path": str(resolved),
            "proof_status": "INCONCLUSIVE",
            "db_hash_unchanged": None,
            "row_counts_unchanged": None,
            "before_key_table_counts": {},
            "after_key_table_counts": {},
            "reason": "production_db_file_missing",
        }

    before_counts = before_counts if before_counts is not None else key_table_row_counts(resolved)
    after_counts = after_counts if after_counts is not None else key_table_row_counts(resolved)
    if before_bytes is None:
        before_bytes = resolved.read_bytes()
    if after_bytes is None:
        after_bytes = resolved.read_bytes()

    hash_unchanged = before_bytes == after_bytes
    counts_unchanged = before_counts == after_counts
    return {
        "production_db_path": str(resolved),
        "proof_status": "VERIFIED",
        "db_hash_unchanged": hash_unchanged,
        "row_counts_unchanged": counts_unchanged,
        "before_key_table_counts": before_counts,
        "after_key_table_counts": after_counts,
    }
