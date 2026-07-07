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
from tests.acceptance_e2e_bootstrap import bootstrap_acceptance_cm, bootstrap_port_live_e2e_ctx

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
    """Bootstrap Alpha Vantage live e2e under isolated M-DATA-03 sandbox (ADR-015)."""
    from backend.app.ops.alpha_vantage_incremental_run import (
        build_alpha_vantage_incremental_service,
        enabled_alpha_vantage_source_registry,
    )

    return bootstrap_port_live_e2e_ctx(
        sandbox_root,
        monkeypatch,
        source_id="alpha_vantage",
        data_domain="us_equity_daily_bar",
        port_factory=lambda **kw: create_alpha_vantage_fetch_port(
            symbols=(SYMBOL,), max_rows=500, **kw
        ),
        service_builder=build_alpha_vantage_incremental_service,
        registry_factory=enabled_alpha_vantage_source_registry,
        env_key="ALPHA_VANTAGE_API_KEY",
    )


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
