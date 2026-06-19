"""Initialize DuckDB with foundation schema migrations."""

from __future__ import annotations

import argparse
from pathlib import Path

from backend.app.config import DATA_ROOT
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Initialize local DuckDB schema")
    parser.add_argument(
        "--db",
        help="Override DuckDB file path (default: $QMD_DATA_ROOT/duckdb/quant_monitor.duckdb)",
    )
    args = parser.parse_args(argv)
    if args.db:
        db_path = Path(args.db)
    else:
        db_path = DATA_ROOT / "duckdb" / "quant_monitor.duckdb"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    cm = ConnectionManager(db_path)
    with cm.writer() as con:
        applied = apply_migrations(con)
    print(f"init_db: applied {applied or 'none (up to date)'}")
    print(f"init_db: database at {db_path}")
    print("init_db: run scripts/sync_registry.py after first init to load configs/sources.yaml")


if __name__ == "__main__":
    main()
