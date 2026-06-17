"""CI smoke: init_db + ingestion tables (Batch A Tier B)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.config import DATA_ROOT  # noqa: E402
from backend.app.db.connection import ConnectionManager  # noqa: E402
from scripts.init_db import main as init_db_main  # noqa: E402


def main() -> None:
    data_root = os.environ.get("QMD_DATA_ROOT", "data")
    os.environ["QMD_DATA_ROOT"] = data_root
    init_db_main()
    init_db_main()
    db_path = DATA_ROOT / "duckdb" / "quant_monitor.duckdb"
    if not db_path.is_file():
        raise SystemExit(f"duckdb not found at {db_path}")
    cm = ConnectionManager(db_path)
    with cm.reader() as con:
        tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
        versions = {
            row[0]
            for row in con.execute("SELECT version_id FROM schema_version").fetchall()
        }
    required_tables = {"source_registry", "fetch_log"}
    if not required_tables.issubset(tables):
        raise SystemExit(f"missing tables: {required_tables - tables}")
    if "004_ingestion_sources" not in versions:
        raise SystemExit("004_ingestion_sources not applied")
    print(f"ci_ingestion_smoke: ok tables={sorted(required_tables)} data_root={data_root}")


if __name__ == "__main__":
    main()
