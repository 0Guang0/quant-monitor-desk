"""Sync source_registry YAML into DuckDB (Batch D §8.8 / GPT-init_db)."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from backend.app.datasources.source_registry import SourceRegistry
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync source_registry YAML to DuckDB")
    parser.add_argument(
        "--yaml",
        type=Path,
        default=None,
        help="Path to source_registry YAML (default: specs/.../source_registry.yaml)",
    )
    args = parser.parse_args(argv)
    data_root = Path(os.environ.setdefault("QMD_DATA_ROOT", "data"))
    db_path = data_root / "duckdb" / "quant_monitor.duckdb"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    cm = ConnectionManager(db_path)
    with cm.writer() as con:
        apply_migrations(con)
        registry = SourceRegistry(args.yaml) if args.yaml else SourceRegistry()
        registry.load(args.yaml)
        count = registry.sync_to_db(con, tombstone_missing=True)
    print(f"sync_registry: ok rows={count} data_root={data_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
