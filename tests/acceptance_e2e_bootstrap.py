"""Generic live incremental e2e bootstrap (M-DATA-03 · ADR-015 acceptance DB path)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.sync.orchestrator import DataSyncOrchestrator
from tests.service_path_support import enable_source_route

ACCEPTANCE_DUCKDB_NAME = "quant_monitor.duckdb"


def acceptance_db_path(sandbox_root: Path) -> Path:
    """ADR-015 acceptance harness DB path (same as acceptance_isolation.ensure_isolated_db)."""
    return sandbox_root / "duckdb" / ACCEPTANCE_DUCKDB_NAME


def bootstrap_acceptance_cm(sandbox_root: Path) -> ConnectionManager:
    db_path = acceptance_db_path(sandbox_root)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    cm = ConnectionManager(db_path=db_path)
    with cm.writer() as con:
        apply_migrations(con)
    return cm


def bootstrap_port_live_e2e_ctx(
    sandbox_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    source_id: str,
    data_domain: str,
    port_factory: Callable[..., Any],
    service_builder: Callable[..., Any],
    registry_factory: Callable[[], Any],
    since_reader: Callable[..., dict[str, Any]] | None = None,
    instrument_ids: tuple[str, ...] = (),
    port_kwargs: dict[str, Any] | None = None,
    service_extra: dict[str, Any] | None = None,
    env_key: str | None = None,
) -> dict[str, Any]:
    """Bootstrap port-source live e2e under isolated sandbox with acceptance DuckDB path."""
    import os

    if env_key and not os.environ.get(env_key):
        pytest.skip(f"live e2e requires {env_key}")
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    enable_source_route(
        monkeypatch,
        source_id=source_id,
        data_domain=data_domain,
        primary_source_id=source_id,
    )
    cm = bootstrap_acceptance_cm(sandbox_root)
    raw_root = sandbox_root / "raw" / source_id
    raw_root.mkdir(parents=True, exist_ok=True)
    port = port_factory(use_mock=False, **(port_kwargs or {}))
    orch = DataSyncOrchestrator(cm)
    since_map: dict[str, Any] = {}
    if since_reader is not None:
        with cm.writer() as con:
            since_map = since_reader(con, instrument_ids)
    registry = registry_factory()
    service_kwargs: dict[str, Any] = {
        "data_root": raw_root,
        "fetch_port": port,
        "job_events": orch._jobs,
        "source_registry": registry,
    }
    if since_map:
        key = "since_by_series" if source_id == "fred" else "since_by_instrument"
        if source_id == "sec_edgar":
            key = "since_by_cik"
        service_kwargs[key] = since_map
    service_kwargs.update(service_extra or {})
    service = service_builder(**service_kwargs)
    return {
        "cm": cm,
        "orch": orch,
        "service": service,
        "registry": registry,
        "port": port,
        "raw_root": raw_root,
        "sandbox_root": sandbox_root,
    }


__all__ = [
    "ACCEPTANCE_DUCKDB_NAME",
    "acceptance_db_path",
    "bootstrap_acceptance_cm",
    "bootstrap_port_live_e2e_ctx",
]
