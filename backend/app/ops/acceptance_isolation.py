"""Shared acceptance DB/data-root isolation helpers for spine and legacy harnesses."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from backend.app.config import DATA_ROOT, PROJECT_ROOT
from backend.app.ops.sandbox_clean_write.path_utils import resolve_sandbox_path

M_DATA_03_SANDBOX_SEGMENT = "m-data-03"


class AcceptanceIsolationError(RuntimeError):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


def canonical_main_db_paths() -> frozenset[Path]:
    return frozenset(
        {
            (PROJECT_ROOT / "data" / "duckdb" / "quant_monitor.duckdb").resolve(),
            (DATA_ROOT / "duckdb" / "quant_monitor.duckdb").resolve(),
        }
    )


def is_canonical_main_db_path(path: Path | str) -> bool:
    return resolve_sandbox_path(path).resolve() in canonical_main_db_paths()


def is_canonical_main_data_root(data_root: Path | str) -> bool:
    resolved = resolve_sandbox_path(data_root).resolve()
    if resolved == (PROJECT_ROOT / "data").resolve():
        return True
    return is_canonical_main_db_path(resolved / "duckdb" / "quant_monitor.duckdb")


def assert_isolated_live_data_root(
    data_root: Path | str,
    *,
    required_segment: str,
) -> Path:
    """Reject canonical main DB paths; require `.audit-sandbox/<required_segment>`."""
    resolved = resolve_sandbox_path(data_root).resolve()
    posix = resolved.as_posix()
    isolated_shape = ".audit-sandbox" in posix and required_segment in posix
    if not isolated_shape and (
        is_canonical_main_db_path(resolved) or is_canonical_main_data_root(resolved)
    ):
        raise AcceptanceIsolationError(
            f"canonical main DB/data root rejected for live acceptance: {resolved}",
            code="CANONICAL_MAIN_DB_REJECTED",
        )
    if not isolated_shape:
        raise AcceptanceIsolationError(
            f"DATA_ROOT must be under .audit-sandbox/{required_segment}: {resolved}",
            code="ISOLATED_ROOT_REQUIRED",
        )
    return resolved


def ensure_isolated_db(data_root: Path) -> Path:
    """Create isolated DuckDB under data_root; apply migrations + registry sync."""
    return _ensure_isolated_db_cached(str(data_root.resolve()))


@lru_cache(maxsize=8)
def _ensure_isolated_db_cached(resolved_data_root: str) -> Path:
    data_root = Path(resolved_data_root)
    import duckdb
    from backend.app.datasources.source_registry import SourceRegistry
    from backend.app.db.connection import ConnectionManager
    from backend.app.db.migrate import apply_migrations

    db = data_root / "duckdb" / "quant_monitor.duckdb"
    db.parent.mkdir(parents=True, exist_ok=True)
    if not db.is_file():
        con = duckdb.connect(str(db))
        try:
            apply_migrations(con)
        finally:
            con.close()
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
        registry = SourceRegistry()
        registry.load()
        registry.sync_to_db(con, tombstone_missing=True)
    return db
