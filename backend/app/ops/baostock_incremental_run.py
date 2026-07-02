"""Baostock bar incremental orchestration (R3-DCP-05 S01).

L3: watermark window → port fetch → security_bar_1d clean (OpenBB fetcher phase align).
ADR-027: live only when QMD_ALLOW_LIVE_FETCH opts in; default replay mock fail-closed.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from backend.app.datasources.fetch_ports.baostock_port import create_baostock_fetch_port
from backend.app.datasources.product_live_gate import is_product_live_fetch_allowed
from backend.app.datasources.service import DataSourceService
from backend.app.ops.sandbox_clean_write.clean_write_targets import resolve_clean_write_target
from backend.app.sync.jobs import SyncJobSpec
from backend.app.sync.orchestrator import DataSyncOrchestrator
from backend.app.sync.watermark import IncrementalWindow


def resolve_baostock_incremental_use_mock() -> bool:
    """Return False when product live env gate opts in (ADR-027)."""
    return not is_product_live_fetch_allowed()


def build_baostock_incremental_service(
    *,
    data_root: Path,
    symbol: str,
    job_events,
    use_mock: bool | None = None,
) -> DataSourceService:
    """Construct DataSourceService for baostock bar incremental sync."""
    mock = resolve_baostock_incremental_use_mock() if use_mock is None else use_mock
    port = create_baostock_fetch_port(symbols=(symbol,), max_rows=500, use_mock=mock)
    return DataSourceService(
        data_root=data_root,
        fetch_port=port,
        job_events=job_events,
        product_live_mode=not mock,
    )


@dataclass(frozen=True)
class BaostockIncrementalRunResult:
    job_id: str
    status: str
    message: str | None
    product_live: bool


def run_baostock_bar_incremental(
    orch: DataSyncOrchestrator,
    *,
    service: DataSourceService,
    window: IncrementalWindow,
    symbol: str,
    product_live: bool,
    job_id: str | None = None,
) -> BaostockIncrementalRunResult:
    """Run one baostock incremental job via orchestrator gold path."""
    data_domain = "cn_equity_daily_bar"
    target = resolve_clean_write_target(data_domain)
    resolved_job_id = job_id or f"qmd-baostock-sync-{uuid.uuid4().hex[:10]}"
    spec = SyncJobSpec(
        run_id=resolved_job_id,
        job_id=resolved_job_id,
        job_type="incremental",
        data_domain=data_domain,
        market_id="CN_A",
        source_id="baostock",
        adapter_id="baostock",
        date_start=window.date_start,
        date_end=window.date_end,
        instrument_id=symbol,
        partition_key=None,
        trigger_reason="qmd_data_sync",
    )
    result = orch.run_incremental(
        spec,
        datasource_service=service,
        clean_table=target.target_table,
        write_mode=target.write_mode,
        primary_keys=target.primary_keys,
    )
    return BaostockIncrementalRunResult(
        job_id=result.job_id,
        status=result.status,
        message=result.message,
        product_live=product_live,
    )


@dataclass(frozen=True)
class BaostockBackfillRunResult:
    job_id: str
    statuses: tuple[str, ...]
    shard_count: int
    product_live: bool


def run_baostock_bar_backfill(
    orch: DataSyncOrchestrator,
    *,
    service: DataSourceService,
    date_start: date,
    date_end: date,
    symbol: str,
    product_live: bool,
    trigger_reason: str = "manual_request",
    job_id: str | None = None,
) -> BaostockBackfillRunResult:
    """Run bounded baostock backfill via orchestrator gold path."""
    from backend.app.sync.jobs import plan_backfill_shards

    data_domain = "cn_equity_daily_bar"
    target = resolve_clean_write_target(data_domain)
    resolved_job_id = job_id or f"qmd-baostock-backfill-{uuid.uuid4().hex[:10]}"
    spec = SyncJobSpec(
        run_id=resolved_job_id,
        job_id=resolved_job_id,
        job_type="backfill",
        data_domain=data_domain,
        market_id="CN_A",
        source_id="baostock",
        adapter_id="baostock",
        date_start=date_start,
        date_end=date_end,
        instrument_id=symbol,
        partition_key=None,
        trigger_reason=trigger_reason,
    )
    shards = plan_backfill_shards(date_start, date_end)
    results = orch.run_backfill(
        spec,
        datasource_service=service,
        clean_table=target.target_table,
        write_mode=target.write_mode,
        primary_keys=target.primary_keys,
    )
    return BaostockBackfillRunResult(
        job_id=resolved_job_id,
        statuses=tuple(r.status for r in results),
        shard_count=len(shards),
        product_live=product_live,
    )


__all__ = [
    "BaostockBackfillRunResult",
    "BaostockIncrementalRunResult",
    "build_baostock_incremental_service",
    "resolve_baostock_incremental_use_mock",
    "run_baostock_bar_backfill",
    "run_baostock_bar_incremental",
]
