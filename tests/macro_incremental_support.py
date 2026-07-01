"""Shared helpers for macro incremental e2e tests (DCP-05 S03–S06)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.ops.macro_incremental_common import MacroIncrementalFetchProxy
from backend.app.sync.orchestrator import DataSyncOrchestrator
from tests.fred_macro_incremental_support import insert_axis_observation
from tests.service_path_support import enable_source_route


def bootstrap_macro_incremental_db(tmp_path: Path) -> ConnectionManager:
    db = tmp_path / "macro_inc.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    return cm


def build_macro_e2e_ctx(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    source_id: str,
    data_domain: str,
    fetch_port,
    since_reader: Callable,
    instrument_ids: tuple[str, ...],
    service_builder: Callable,
    registry_factory: Callable,
) -> dict[str, Any]:
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    enable_source_route(
        monkeypatch,
        source_id=source_id,
        data_domain=data_domain,
        primary_source_id=source_id,
    )
    cm = bootstrap_macro_incremental_db(tmp_path)
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    orch = DataSyncOrchestrator(cm)
    with cm.writer() as con:
        since_map = since_reader(con, instrument_ids)
    registry = registry_factory()
    service = service_builder(
        data_root=raw_root,
        fetch_port=fetch_port,
        since_by_instrument=since_map,
        job_events=orch._jobs,
        source_registry=registry,
    )
    return {
        "cm": cm,
        "orch": orch,
        "service": service,
        "registry": registry,
        "port": fetch_port,
        "raw_root": raw_root,
    }


__all__ = ["build_macro_e2e_ctx", "bootstrap_macro_incremental_db", "insert_axis_observation"]
