"""Mootdx bar incremental orchestration (R3-DCP-05 S08).

L3: watermark window → mootdx port (window-filtered replay) → security_bar_1d clean.
ponytail: mirrors baostock_incremental_run; CLI router deferred to S12.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

from backend.app.datasources.fetch_ports.mootdx_port import create_mootdx_fetch_port
from backend.app.datasources.fetch_ports.tdx_fetch_guards import EQUITY_INDEX_MAX_ROWS
from backend.app.datasources.product_live_gate import is_product_live_fetch_allowed
from backend.app.datasources.service import DataSourceService
from backend.app.ops.sandbox_clean_write.clean_write_targets import resolve_clean_write_target
from backend.app.sync.jobs import SyncJobSpec
from backend.app.sync.orchestrator import DataSyncOrchestrator
from backend.app.sync.watermark import IncrementalWindow

MOOTDX_MAX_ROWS = EQUITY_INDEX_MAX_ROWS


def resolve_mootdx_incremental_use_mock() -> bool:
    return not is_product_live_fetch_allowed()


def build_mootdx_incremental_service(
    *,
    data_root: Path,
    symbol: str,
    job_events,
    use_mock: bool | None = None,
    route_planner=None,
    source_registry=None,
) -> DataSourceService:
    mock = resolve_mootdx_incremental_use_mock() if use_mock is None else use_mock
    port = create_mootdx_fetch_port(symbols=(symbol,), max_rows=MOOTDX_MAX_ROWS, use_mock=mock)
    kwargs: dict = {
        "data_root": data_root,
        "fetch_port": port,
        "job_events": job_events,
        "product_live_mode": not mock,
    }
    if route_planner is not None:
        kwargs["route_planner"] = route_planner
        kwargs["source_registry"] = source_registry or route_planner.source_registry
        kwargs["capability_registry"] = route_planner.capability_registry
    elif source_registry is not None:
        kwargs["source_registry"] = source_registry
    return DataSourceService(**kwargs)


@dataclass(frozen=True)
class MootdxIncrementalRunResult:
    job_id: str
    status: str
    message: str | None
    product_live: bool


def run_mootdx_bar_incremental(
    orch: DataSyncOrchestrator,
    *,
    service: DataSourceService,
    window: IncrementalWindow,
    symbol: str,
    product_live: bool,
    job_id: str | None = None,
) -> MootdxIncrementalRunResult:
    data_domain = "cn_equity_daily_bar"
    target = resolve_clean_write_target(data_domain)
    resolved_job_id = job_id or f"qmd-mootdx-sync-{uuid.uuid4().hex[:10]}"
    spec = SyncJobSpec(
        run_id=resolved_job_id,
        job_id=resolved_job_id,
        job_type="incremental",
        data_domain=data_domain,
        market_id="CN_A",
        source_id="mootdx",
        adapter_id="mootdx",
        date_start=window.date_start,
        date_end=window.date_end,
        instrument_id=symbol,
        partition_key=None,
        trigger_reason="mootdx_bar_incremental",
    )
    result = orch.run_incremental(
        spec,
        datasource_service=service,
        clean_table=target.target_table,
        write_mode=target.write_mode,
        primary_keys=target.primary_keys,
    )
    return MootdxIncrementalRunResult(
        job_id=result.job_id,
        status=result.status,
        message=result.message,
        product_live=product_live,
    )


__all__ = [
    "MootdxIncrementalRunResult",
    "build_mootdx_incremental_service",
    "resolve_mootdx_incremental_use_mock",
    "run_mootdx_bar_incremental",
]
