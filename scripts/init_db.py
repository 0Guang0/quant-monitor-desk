"""Initialize DuckDB with foundation schema migrations."""

from __future__ import annotations

from backend.app.config import DATA_ROOT
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations


def main() -> None:
    db_path = DATA_ROOT / "duckdb" / "quant_monitor.duckdb"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    cm = ConnectionManager(db_path)
    with cm.writer() as con:
        applied = apply_migrations(con)
    print(f"init_db: applied {applied or 'none (up to date)'}")


if __name__ == "__main__":
    main()
