"""Shared mootdx incremental test bootstrap (DCP-05 S08)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.datasources.fetch_ports.mootdx_port import create_mootdx_fetch_port
from backend.app.datasources.fetch_ports.tdx_fetch_guards import EQUITY_INDEX_MAX_ROWS
from backend.app.datasources.normalizers.evidence_bundle import attach_bundle_metadata, finalize_bundle
from backend.app.datasources.service import DataSourceService
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.storage.path_compat import read_bytes
from backend.app.sync.jobs import SyncJobSpec
from backend.app.sync.orchestrator import DataSyncOrchestrator, SyncJobResult
from backend.app.sync.watermark import compute_incremental_window, read_bar_trade_date_watermark

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


def build_live_service(
    cm: ConnectionManager,
    raw_root: Path,
    monkeypatch: Any,
) -> tuple[DataSourceService, DataSyncOrchestrator]:
    """Product live mootdx service (use_mock=False, ADR-008 opt-in)."""
    from backend.app.ops.mootdx_incremental_run import build_mootdx_incremental_service

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    orch = DataSyncOrchestrator(cm)
    service = build_mootdx_incremental_service(
        data_root=raw_root,
        symbol=SYMBOL,
        job_events=orch._jobs,
        use_mock=False,
    )
    return service, orch


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


def run_mootdx_replay_incremental(
    tmp_path: Path,
    monkeypatch: Any,
    *,
    job_id: str,
    seed_date: str = "2024-06-24",
) -> tuple[ConnectionManager, Path, SyncJobResult]:
    """Run one mootdx replay incremental into security_bar_1d (shared e2e bootstrap)."""
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    cm = bootstrap_db(tmp_path)
    with cm.writer() as con:
        seed_watermark_row(con, seed_date)
        wm = read_bar_trade_date_watermark(con, instrument_id=SYMBOL)
    window = compute_incremental_window(wm, end=FIXTURE_DATE)
    service, orch = build_service(cm, tmp_path)
    result = orch.run_incremental(
        incremental_spec(window, job_id=job_id),
        datasource_service=service,
        clean_table="security_bar_1d",
        write_mode="upsert_by_pk",
        primary_keys=("instrument_id", "trade_date", "adjustment_type"),
    )
    return cm, tmp_path, result


def fetch_security_bar_row(con, trade_date: str):
    return con.execute(
        """
        SELECT trade_date, close, source_used FROM security_bar_1d
        WHERE instrument_id = ? AND trade_date = ?
        """,
        [SYMBOL, trade_date],
    ).fetchone()


def load_mootdx_raw_bundle_from_fetch_log(con, job_id: str) -> dict:
    """Load finalized mootdx evidence bundle for a completed incremental job."""
    rows = con.execute(
        """
        SELECT raw_file_paths, source_id, status
        FROM fetch_log
        WHERE job_id = ? AND status = 'SUCCESS'
        ORDER BY fetch_time DESC
        """,
        [job_id],
    ).fetchall()
    if not rows:
        raise AssertionError(f"no SUCCESS fetch_log row for job_id={job_id!r}")
    for raw_paths_json, _source_id, _status in rows:
        raw_paths = json.loads(raw_paths_json or "[]")
        for raw_path in raw_paths:
            payload = json.loads(read_bytes(Path(raw_path)).decode("utf-8"))
            bundle = finalize_bundle(attach_bundle_metadata(payload))
            if bundle.get("source_id") == "mootdx":
                return bundle
    raise AssertionError(f"no mootdx raw bundle in fetch_log for job_id={job_id!r}")
