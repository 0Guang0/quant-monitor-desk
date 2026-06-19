"""Vendor fixture E2E through real orchestrator path (Round2 audit P1-03)."""

from __future__ import annotations

import json
from pathlib import Path

from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.datasources.adapters.fetch_port import LocalFixtureFetchPort
from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.storage.raw_store import RawStore
from backend.app.sync.jobs import SyncJobSpec
from backend.app.sync.orchestrator import DataSyncOrchestrator

FIXTURE_JSON = Path(__file__).parent / "fixtures" / "vendor_bar_fixture.json"
STG_TABLE = "stg_vendor_e2e"
CLEAN_TABLE = "clean_vendor_e2e"


def test_vendorFixtureFetch_e2eOrchestratorPath(
    tmp_path: Path, registry_yaml_fixture: Path, monkeypatch
) -> None:
    FIXTURE_JSON.write_text(
        json.dumps([{"symbol": "000001", "close": 10.5, "trade_date": "2026-06-15"}]),
        encoding="utf-8",
    )
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))

    db = tmp_path / "vendor_e2e.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
        con.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {STG_TABLE} (
                instrument_id VARCHAR, trade_date VARCHAR, close DOUBLE,
                source_used VARCHAR, batch_id VARCHAR, source_id VARCHAR
            )
            """
        )
        con.execute(
            f"CREATE TABLE IF NOT EXISTS {CLEAN_TABLE} AS SELECT * FROM {STG_TABLE} WHERE 1=0"
        )

    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    with cm.writer() as con:
        reg.sync_to_db(con, tombstone_missing=False)

    class FixtureStagingAdapter(SkeletonAdapterBase):
        source_id = "baostock"
        supported_domains = frozenset({"market_bar_1d"})

        def fetch(self, req, *, con, job_id=None):
            result = super().fetch(req, con=con, job_id=job_id)
            if result.status == "SUCCESS":
                con.execute(f"DELETE FROM {STG_TABLE}")
                con.execute(
                    f"""
                    INSERT INTO {STG_TABLE} VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    ["000001", "2026-06-15", 10.5, "baostock", "v1", "baostock"],
                )
                return result.model_copy(update={"staging_table": STG_TABLE, "row_count": 1})
            return result

    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    adapter = FixtureStagingAdapter(
        reg,
        raw_store=RawStore(raw_root),
        fetch_port=LocalFixtureFetchPort(FIXTURE_JSON, row_count=1),
    )
    orch = DataSyncOrchestrator(cm)
    spec = SyncJobSpec(
        run_id="run-vendor-e2e",
        job_id="job-vendor-e2e",
        job_type="incremental",
        data_domain="market_bar_1d",
        market_id="CN_A",
        source_id="baostock",
        adapter_id="baostock",
        date_start=None,
        date_end=None,
        instrument_id="000001",
        partition_key=None,
        trigger_reason=None,
    )
    result = orch.run_incremental(spec, adapter=adapter, clean_table=CLEAN_TABLE)
    assert result.status == "COMPLETED"
    with cm.writer() as con:
        fetch_count = con.execute(
            "SELECT COUNT(*) FROM fetch_log WHERE job_id = ?", ["job-vendor-e2e"]
        ).fetchone()[0]
        report_count = con.execute(
            "SELECT COUNT(*) FROM validation_report WHERE job_id = ?", ["job-vendor-e2e"]
        ).fetchone()[0]
        audit_count = con.execute(
            "SELECT COUNT(*) FROM write_audit_log WHERE job_id = ?", ["job-vendor-e2e"]
        ).fetchone()[0]
        clean_count = con.execute(f"SELECT COUNT(*) FROM {CLEAN_TABLE}").fetchone()[0]
    assert fetch_count >= 1
    assert report_count >= 1
    assert audit_count >= 1
    assert clean_count == 1
