"""Shared mootdx incremental test bootstrap (DCP-05 S08)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from backend.app.datasources.fetch_ports.mootdx_port import create_mootdx_fetch_port
from backend.app.datasources.fetch_ports.tdx_fetch_guards import EQUITY_INDEX_MAX_ROWS
from backend.app.datasources.service import DataSourceService
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.sync.jobs import SyncJobSpec
from backend.app.sync.orchestrator import DataSyncOrchestrator

SYMBOL = "sh.600519"
FIXTURE_DATE = date(2024, 6, 25)


def bootstrap_db(tmp_path: Path) -> ConnectionManager:
    db = tmp_path / "mootdx_incr.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    return cm


def seed_watermark_row(con, trade_date: str) -> None:
    con.execute("DELETE FROM security_bar_1d WHERE instrument_id = ?", [SYMBOL])
    con.execute(
        """
        INSERT INTO security_bar_1d (
            instrument_id, trade_date, open, high, low, close, pre_close, volume, amount,
            adjustment_type, source_used, batch_id, quality_flags, created_at
        ) VALUES (?, ?, 1390.0, 1395.0, 1385.0, 1390.0, NULL, 900000, NULL, 'none', 'seed', 'b0', NULL, CURRENT_TIMESTAMP)
        """,
        [SYMBOL, trade_date],
    )


def build_service(cm: ConnectionManager, raw_root: Path) -> tuple[DataSourceService, DataSyncOrchestrator]:
    orch = DataSyncOrchestrator(cm)
    port = create_mootdx_fetch_port(symbols=(SYMBOL,), max_rows=EQUITY_INDEX_MAX_ROWS, use_mock=True)
    service = DataSourceService(
        data_root=raw_root,
        fetch_port=port,
        job_events=orch._jobs,
    )
    return service, orch


def incremental_spec(window, *, job_id: str) -> SyncJobSpec:
    return SyncJobSpec(
        run_id=job_id,
        job_id=job_id,
        job_type="incremental",
        data_domain="cn_equity_daily_bar",
        market_id="CN_A",
        source_id="mootdx",
        adapter_id="mootdx",
        date_start=window.date_start,
        date_end=window.date_end,
        instrument_id=SYMBOL,
        partition_key=None,
        trigger_reason="test",
    )
