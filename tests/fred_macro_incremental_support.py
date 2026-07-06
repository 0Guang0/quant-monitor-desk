"""Shared helpers for fred macro incremental tests."""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Any

import pytest

from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.datasources.fetch_ports.fred_port import create_fred_fetch_port
from backend.app.layer1_axes.observation_contract import AXIS_OBSERVATION_DDL_COLUMNS
from backend.app.ops.fred_incremental_run import (
    FredIncrementalFetchProxy,
    build_fred_incremental_service,
)
from backend.app.ops.fred_incremental_watermark import (
    enabled_fred_source_registry,
    read_since_dates_for_series,
)
from backend.app.sync.orchestrator import DataSyncOrchestrator
from tests.live_incremental_support import bootstrap_acceptance_cm, bootstrap_port_live_e2e_ctx
from tests.service_path_support import enable_source_route


def insert_axis_observation(
    con,
    *,
    observation_id: str,
    indicator_id: str,
    obs_date: date,
    raw_value: float = 4.25,
    content_hash: str = "hash-a",
    quality_flags: str = "TEST",
) -> None:
    publish_dt = datetime.combine(obs_date, time(0, 0), tzinfo=UTC)
    as_of_dt = datetime.combine(obs_date, time(16, 0), tzinfo=UTC)
    now = datetime.now(UTC)
    row = {
        "observation_id": observation_id,
        "indicator_id": indicator_id,
        "as_of_timestamp": as_of_dt,
        "publish_timestamp": publish_dt,
        "fetch_time": now,
        "raw_value": raw_value,
        "raw_unit": "index",
        "frequency": "daily",
        "source_used": "fred",
        "source_channel_id": "fred",
        "data_lag_days": 0.0,
        "stale_reason": None,
        "quality_flags": quality_flags,
        "content_hash": content_hash,
        "schema_hash": "schema-a",
        "source_switched": False,
        "created_at": now,
    }
    cols = ", ".join(AXIS_OBSERVATION_DDL_COLUMNS)
    placeholders = ", ".join("?" for _ in AXIS_OBSERVATION_DDL_COLUMNS)
    con.execute(
        f"INSERT INTO axis_observation ({cols}) VALUES ({placeholders})",
        [row[c] for c in AXIS_OBSERVATION_DDL_COLUMNS],
    )


def bootstrap_fred_incremental_db(tmp_path: Path) -> ConnectionManager:
    db = tmp_path / "fred_inc.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    return cm


def bootstrap_fred_live_e2e_ctx(
    sandbox_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, Any]:
    """Bootstrap fred live e2e under isolated M-DATA-03 sandbox (ADR-015)."""
    return bootstrap_port_live_e2e_ctx(
        sandbox_root,
        monkeypatch,
        source_id="fred",
        data_domain="macro_series",
        port_factory=lambda **kw: create_fred_fetch_port(
            series_ids=("DGS10",), max_rows=3, **kw
        ),
        service_builder=build_fred_incremental_service,
        registry_factory=enabled_fred_source_registry,
        since_reader=lambda con, _ids: read_since_dates_for_series(con, ("DGS10",)),
        env_key="FRED_API_KEY",
    )


@pytest.fixture
def fred_incremental_e2e_ctx(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Shared e2e bootstrap: isolated DB, mock port, orchestrator, service."""
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    enable_source_route(
        monkeypatch, source_id="fred", data_domain="macro_series", primary_source_id="fred"
    )
    cm = bootstrap_fred_incremental_db(tmp_path)
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    port = create_fred_fetch_port(series_ids=("DGS10", "VIXCLS"), max_rows=3, use_mock=True)
    orch = DataSyncOrchestrator(cm)
    with cm.writer() as con:
        since_map = read_since_dates_for_series(con, ("DGS10", "VIXCLS"))
    registry = enabled_fred_source_registry()
    service = build_fred_incremental_service(
        data_root=raw_root,
        fetch_port=port,
        since_by_series=since_map,
        job_events=orch._jobs,
        source_registry=registry,
    )
    return {
        "cm": cm,
        "orch": orch,
        "service": service,
        "registry": registry,
        "port": port,
        "raw_root": raw_root,
    }
