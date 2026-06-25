"""Initialize DuckDB with foundation schema migrations."""

from __future__ import annotations

import argparse
from pathlib import Path

from backend.app.config import DATA_ROOT
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Initialize local DuckDB schema")
    parser.add_argument(
        "--db",
        help="Override DuckDB file path (default: $QMD_DATA_ROOT/duckdb/quant_monitor.duckdb)",
    )
    parser.add_argument(
        "--sync-registry",
        action="store_true",
        help="After migrations, sync specs source_registry YAML into DuckDB (R3F-CLI-03)",
    )
    args = parser.parse_args(argv)
    if args.db:
        db_path = Path(args.db)
    else:
        db_path = DATA_ROOT / "duckdb" / "quant_monitor.duckdb"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    cm = ConnectionManager(db_path)
    registry_rows: int | None = None
    with cm.writer() as con:
        applied = apply_migrations(con)
        if args.sync_registry:
            registry = SourceRegistry()
            registry.load()
            registry_rows = registry.sync_to_db(con, tombstone_missing=True)
    print(f"init_db: applied {applied or 'none (up to date)'}")
    print(f"init_db: database at {db_path}")
    if args.sync_registry:
        print(f"init_db: sync_registry rows={registry_rows}")
    else:
        print(
            "init_db: run scripts/sync_registry.py or re-run with --sync-registry "
            "to load configs/sources.yaml"
        )


if __name__ == "__main__":
    main()
