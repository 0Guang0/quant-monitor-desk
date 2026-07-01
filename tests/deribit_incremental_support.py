"""Shared Deribit incremental test bootstrap (R3-DCP-05 S11)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest

from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.datasources.fetch_ports.deribit_port import create_deribit_fetch_port
from backend.app.ops.deribit_incremental_run import build_deribit_incremental_service
from backend.app.ops.deribit_incremental_watermark import (
    enabled_deribit_source_registry,
    read_since_date_for_instrument,
)
from backend.app.sync.orchestrator import DataSyncOrchestrator

INSTRUMENT = "BTC-28JUN24-65000-C"
AS_OF_DATE = date(2024, 6, 25)


def bootstrap_db(tmp_path: Path) -> ConnectionManager:
    db = tmp_path / "deribit_incr.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    return cm


def seed_watermark_row(con, as_of_date: str) -> None:
    con.execute("DELETE FROM crypto_derivative_clean WHERE instrument_name = ?", [INSTRUMENT])
    as_of_ts = datetime.combine(date.fromisoformat(as_of_date), datetime.min.time(), tzinfo=UTC)
    con.execute(
        """
        INSERT INTO crypto_derivative_clean (
            instrument_name, as_of_timestamp, data_domain, strike, option_type, mark_iv,
            source_used, batch_id, created_at
        ) VALUES (?, ?, 'crypto_options_surface', 65000, 'call', 0.50, 'seed', 'b0', CURRENT_TIMESTAMP)
        """,
        [INSTRUMENT, as_of_ts],
    )


@pytest.fixture
def deribit_incremental_e2e_ctx(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    cm = bootstrap_db(tmp_path)
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    port = create_deribit_fetch_port(instruments=(INSTRUMENT,), max_surface_rows=50, use_mock=True)
    orch = DataSyncOrchestrator(cm)
    registry = enabled_deribit_source_registry()
    with cm.writer() as con:
        since = read_since_date_for_instrument(con, INSTRUMENT)
    service = build_deribit_incremental_service(
        data_root=raw_root,
        fetch_port=port,
        since_by_instrument={INSTRUMENT: since},
        job_events=orch._jobs,
        source_registry=registry,
    )
    return {"cm": cm, "orch": orch, "service": service, "registry": registry}
