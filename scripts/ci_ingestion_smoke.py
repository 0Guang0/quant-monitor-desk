"""CI smoke: init_db + ingestion tables + orchestrator path (Batch D §8.9)."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from backend.app.config import DATA_ROOT
from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.datasources.fetch_result import FetchRequest, FetchResult
from backend.app.db.connection import ConnectionManager
from backend.app.sync.jobs import SyncJobSpec
from backend.app.sync.orchestrator import DataSyncOrchestrator

from scripts.init_db import main as init_db_main


class _SmokeAdapter:
    source_id = "baostock"
    supported_domains = frozenset({"market_bar_1d"})

    def fetch(self, req: FetchRequest, *, con, job_id: str | None = None) -> FetchResult:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS stg_smoke (
                instrument_id VARCHAR, trade_date VARCHAR, close DOUBLE,
                source_used VARCHAR, batch_id VARCHAR, source_id VARCHAR
            )
            """
        )
        con.execute("DELETE FROM stg_smoke")
        con.execute(
            "INSERT INTO stg_smoke VALUES ('AAPL','2026-06-15',100.0,'baostock','b1','baostock')"
        )
        return FetchResult(
            run_id=req.run_id,
            source_id=self.source_id,
            data_domain=req.data_domain,
            status="SUCCESS",
            row_count=1,
            fetch_time="2026-06-17T10:00:00Z",
            staging_table="stg_smoke",
            raw_file_paths=["/tmp/smoke.parquet"],
        )


def _orchestrator_smoke(db_path: Path) -> None:
    cm = ConnectionManager(db_path)
    orch = DataSyncOrchestrator(cm)
    spec = SyncJobSpec(
        run_id="smoke-run",
        job_id="smoke-job",
        job_type="incremental",
        data_domain="market_bar_1d",
        market_id="CN_A",
        source_id="baostock",
        adapter_id="baostock",
        date_start=None,
        date_end=None,
        instrument_id="AAPL",
        partition_key=None,
        trigger_reason=None,
    )
    original_check = ResourceGuard.check

    def _ok(self):
        return Decision.OK, ""

    ResourceGuard.check = _ok  # type: ignore[method-assign]
    try:
        orch.create_job(spec)
        orch._jobs.transition(spec.job_id, "PLANNED")
        if not orch.begin_fetching(spec.job_id):
            raise SystemExit("orchestrator smoke: guard blocked")
        with cm.writer() as con:
            result = _SmokeAdapter().fetch(
                FetchRequest(
                    run_id=spec.run_id,
                    source_id=spec.source_id,
                    data_domain=spec.data_domain,
                ),
                con=con,
                job_id=spec.job_id,
            )
        if result.status != "SUCCESS":
            raise SystemExit(f"orchestrator smoke: fetch failed {result.status}")
    finally:
        ResourceGuard.check = original_check  # type: ignore[method-assign]


def main() -> None:
    data_root = os.environ.get("QMD_DATA_ROOT", "data")
    os.environ["QMD_DATA_ROOT"] = data_root
    init_db_main()
    init_db_main()  # ponytail: idempotent second init proves migrate no-op on warm DB
    db_path = DATA_ROOT / "duckdb" / "quant_monitor.duckdb"
    if not db_path.is_file():
        raise SystemExit(f"duckdb not found at {db_path}")
    cm = ConnectionManager(db_path)
    with cm.reader() as con:
        tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
        versions = {
            row[0] for row in con.execute("SELECT version_id FROM schema_version").fetchall()
        }
    required_tables = {"source_registry", "fetch_log", "data_sync_job", "job_event_log"}
    if not required_tables.issubset(tables):
        raise SystemExit(f"missing tables: {required_tables - tables}")
    if "004_ingestion_sources" not in versions:
        raise SystemExit("004_ingestion_sources not applied")
    if "006_ingestion_sync" not in versions:
        raise SystemExit("006_ingestion_sync not applied")
    with tempfile.TemporaryDirectory() as tmp:
        smoke_db = Path(tmp) / "smoke.duckdb"
        smoke_cm = ConnectionManager(smoke_db)
        with smoke_cm.writer() as con:
            from backend.app.db.migrate import apply_migrations

            apply_migrations(con)
        _orchestrator_smoke(smoke_db)
    print(f"ci_ingestion_smoke: ok tables={sorted(required_tables)} data_root={data_root}")
    print("orchestrator_smoke: ok")


if __name__ == "__main__":
    main()
