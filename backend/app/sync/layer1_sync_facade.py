"""Layer1 sync seam — thin wrapper over binding executor (M-G1-03 §9.2 · P1-13)."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Literal

from backend.app.sync.binding_executor import execute_binding
from backend.app.sync.indicator_binding import load_binding
from backend.app.sync.jobs import SyncJobResult

JobType = Literal["incremental", "backfill", "full_load"]

# Re-export for layer1_axes (must not import datasources.service directly).
from backend.app.datasources.service import ResourceGuardBlockedError  # noqa: E402

__all__ = [
    "JobType",
    "ResourceGuardBlockedError",
    "build_staged_fixture_sync_client",
    "create_default_layer1_sync_client",
    "sync_indicator",
]


def sync_indicator(
    indicator_id: str,
    job_type: JobType,
    *,
    dry_run: bool = True,
    date_start: date | None = None,
    date_end: date | None = None,
    connection_manager=None,
    orchestrator=None,
    datasource_service=None,
) -> SyncJobResult:
    """Layer-facing seam: load_binding + execute_binding (no source-specific logic)."""
    binding = load_binding(indicator_id)
    return execute_binding(
        binding,
        job_type,
        dry_run=dry_run,
        date_start=date_start,
        date_end=date_end,
        connection_manager=connection_manager,
        orchestrator=orchestrator,
        datasource_service=datasource_service,
    )


def create_default_layer1_sync_client(*, data_root: Path) -> Any:
    """Production sync client factory for Layer1 ingestion (lives in sync seam)."""
    from backend.app.datasources.service import DataSourceService

    return DataSourceService(data_root=data_root)


def build_staged_fixture_sync_client(
    *,
    data_root: Path,
    fixture_path: Path,
    row_count: int = 1,
) -> Any:
    """Staged micro-fetch client for Layer1 evidence paths."""
    from backend.app.datasources.service import build_staged_fixture_service

    return build_staged_fixture_service(
        data_root=data_root,
        fixture_path=fixture_path,
        row_count=row_count,
    )
