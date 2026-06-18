"""Batch C validation smoke for production-path DuckDB."""

from __future__ import annotations

from backend.app.config import DATA_ROOT
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations


def main() -> None:
    db_path = DATA_ROOT / "duckdb" / "quant_monitor.duckdb"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    cm = ConnectionManager(db_path)
    with cm.writer() as con:
        apply_migrations(con)
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
    required = {
        "validation_report",
        "data_quality_log",
        "source_conflict",
        "manual_review_queue",
    }
    missing = sorted(required - tables)
    if missing:
        raise SystemExit(f"missing validation tables: {missing}")
    print("ci_validation_smoke: ok")


if __name__ == "__main__":
    main()
