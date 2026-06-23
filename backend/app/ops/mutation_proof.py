"""Shared mutation-proof helpers for pilot and probe evidence (OP-02)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from backend.app.db.connection import ConnectionManager
from backend.app.ops.db_inspector import KEY_TABLES

ProofStatus = Literal["VERIFIED", "INCONCLUSIVE", "MUTATION_DETECTED"]


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


def all_table_row_counts(db_path: Path) -> dict[str, int]:
    """Read-only row counts for every main-schema table (R3Y-MUT-PROOF-001)."""
    if not db_path.is_file():
        return {}
    counts: dict[str, int] = {}
    cm = ConnectionManager(db_path, profile="eco")
    with cm.reader() as con:
        tables = [
            row[0]
            for row in con.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'main'
                ORDER BY table_name
                """
            ).fetchall()
        ]
        for name in tables:
            row_count = con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
            counts[name] = int(row_count)
    return counts


def _derive_proof_status(
    *,
    hash_unchanged: bool,
    key_counts_unchanged: bool,
    all_counts_unchanged: bool,
) -> ProofStatus:
    """R3Y-MUT-PROOF-001: VERIFIED only when hash and all counts unchanged."""
    if not key_counts_unchanged or not all_counts_unchanged:
        return "MUTATION_DETECTED"
    if hash_unchanged:
        return "VERIFIED"
    return "INCONCLUSIVE"


def build_production_mutation_proof(
    db_path: Path,
    *,
    before_counts: dict[str, int | None] | None = None,
    before_bytes: bytes | None = None,
    after_counts: dict[str, int | None] | None = None,
    after_bytes: bytes | None = None,
    before_all_counts: dict[str, int] | None = None,
    after_all_counts: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Build fail-closed production DB no-mutation proof payload.

    When the production DB file is absent, ``proof_status`` is ``INCONCLUSIVE``
    and hash/count equality fields are ``None`` (ADV-POST14-A-001).

    ``proof_status=VERIFIED`` only when file hash and all table row counts are
    unchanged (R3Y-MUT-PROOF-001).
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
            "before_all_table_counts": {},
            "after_all_table_counts": {},
            "reason": "production_db_file_missing",
        }

    before_counts = before_counts if before_counts is not None else key_table_row_counts(resolved)
    after_counts = after_counts if after_counts is not None else key_table_row_counts(resolved)
    before_all = (
        before_all_counts if before_all_counts is not None else all_table_row_counts(resolved)
    )
    after_all = after_all_counts if after_all_counts is not None else all_table_row_counts(resolved)
    if before_bytes is None:
        before_bytes = resolved.read_bytes()
    if after_bytes is None:
        after_bytes = resolved.read_bytes()

    hash_unchanged = before_bytes == after_bytes
    key_counts_unchanged = before_counts == after_counts
    all_counts_unchanged = before_all == after_all
    row_counts_unchanged = key_counts_unchanged and all_counts_unchanged
    proof_status = _derive_proof_status(
        hash_unchanged=hash_unchanged,
        key_counts_unchanged=key_counts_unchanged,
        all_counts_unchanged=all_counts_unchanged,
    )
    return {
        "production_db_path": str(resolved),
        "proof_status": proof_status,
        "db_hash_unchanged": hash_unchanged,
        "row_counts_unchanged": row_counts_unchanged,
        "before_key_table_counts": before_counts,
        "after_key_table_counts": after_counts,
        "before_all_table_counts": before_all,
        "after_all_table_counts": after_all,
    }
