"""Shared Alpha Vantage incremental test bootstrap (R3-DCP-05 S10)."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.datasources.fetch_ports.alpha_vantage_port import create_alpha_vantage_fetch_port
from backend.app.ops.alpha_vantage_incremental_run import build_alpha_vantage_incremental_service
from backend.app.sync.orchestrator import DataSyncOrchestrator
from tests.live_incremental_support import bootstrap_acceptance_cm

SYMBOL = "AAPL"
FIXTURE_END = date(2024, 1, 3)
TRADE_DATE = "2024-01-03"


def bootstrap_db(tmp_path: Path) -> ConnectionManager:
    db = tmp_path / "alpha_vantage_incr.duckdb"
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
        ) VALUES (?, ?, 185.0, 186.0, 184.5, 185.0, NULL, 50000, NULL, 'none', 'seed', 'b0', NULL, CURRENT_TIMESTAMP)
        """,
        [SYMBOL, trade_date],
    )


def bootstrap_alpha_vantage_live_e2e_ctx(
    sandbox_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, Any]:
    """Bootstrap Alpha Vantage live e2e under isolated M-DATA-03 sandbox (ADR-034)."""
    import os

    if not os.environ.get("ALPHA_VANTAGE_API_KEY"):
        pytest.skip("live e2e requires ALPHA_VANTAGE_API_KEY")
    from backend.app.ops.alpha_vantage_incremental_run import enabled_alpha_vantage_source_registry

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    cm = bootstrap_acceptance_cm(sandbox_root)
    raw_root = sandbox_root / "raw" / "alpha_vantage"
    raw_root.mkdir(parents=True, exist_ok=True)
    port = create_alpha_vantage_fetch_port(symbols=(SYMBOL,), max_rows=500, use_mock=False)
    orch = DataSyncOrchestrator(cm)
    registry = enabled_alpha_vantage_source_registry()
    service = build_alpha_vantage_incremental_service(
        data_root=raw_root,
        fetch_port=port,
        job_events=orch._jobs,
        source_registry=registry,
    )
    return {
        "cm": cm,
        "orch": orch,
        "service": service,
        "registry": registry,
        "raw_root": raw_root,
        "sandbox_root": sandbox_root,
    }


@pytest.fixture
def alpha_vantage_incremental_e2e_ctx(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> dict[str, Any]:
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    from backend.app.ops.alpha_vantage_incremental_run import enabled_alpha_vantage_source_registry

    cm = bootstrap_db(tmp_path)
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    port = create_alpha_vantage_fetch_port(symbols=(SYMBOL,), max_rows=500, use_mock=True)
    orch = DataSyncOrchestrator(cm)
    registry = enabled_alpha_vantage_source_registry()
    service = build_alpha_vantage_incremental_service(
        data_root=raw_root,
        fetch_port=port,
        job_events=orch._jobs,
        source_registry=registry,
    )
    return {"cm": cm, "orch": orch, "service": service, "registry": registry}
