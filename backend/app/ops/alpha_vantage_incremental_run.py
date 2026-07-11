"""Alpha Vantage US equity bar incremental orchestration (R3-DCP-05 S10)."""

from __future__ import annotations

import json
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from backend.app.datasources.adapters.fetch_port import FetchPort, PortError
from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase, _utc_now_iso
from backend.app.datasources.fetch_result import FetchRequest, FetchResult
from backend.app.datasources.service import DataSourceService
from backend.app.ops.macro_incremental_common import (
    incremental_evidence_as_of,
    persist_incremental_fetch_payload,
)
from backend.app.ops.sandbox_clean_write.clean_write_targets import resolve_clean_write_target
from backend.app.storage.raw_store import RawStore
from backend.app.sync.jobs import SyncJobSpec
from backend.app.sync.orchestrator import DataSyncOrchestrator
from backend.app.sync.watermark import compute_incremental_window, read_bar_trade_date_watermark

_BAR_STAGING_TABLE = "stg_foundation_smoke"
_BAR_REQUIRED_FIELDS = ("close", "source_used")
_WATERMARK_EMPTY_MSG = "no bars after alpha_vantage watermark window"
_DEFAULT_SYMBOL = "AAPL"


def _make_alpha_vantage_staging_adapter_class():
    class AlphaVantageBarStagingAdapter(SkeletonAdapterBase):
        source_id = "alpha_vantage"
        supported_domains = frozenset({"us_equity_daily_bar"})

        def fetch(self, req, *, con, job_id=None, record_fetch_log: bool = True):
            fetch_time = _utc_now_iso()
            try:
                payload = self._fetch_port.fetch_payload(req)
            except PortError as exc:
                return FetchResult(
                    run_id=req.run_id,
                    source_id=self.source_id,
                    data_domain=req.data_domain,
                    status=exc.status,
                    row_count=0,
                    fetch_time=fetch_time,
                    error_message=exc.message,
                )
            try:
                bundle = json.loads(payload.content.decode("utf-8"))
            except json.JSONDecodeError as exc:
                return FetchResult(
                    run_id=req.run_id,
                    source_id=self.source_id,
                    data_domain=req.data_domain,
                    status="FAILED",
                    row_count=0,
                    fetch_time=fetch_time,
                    error_message=f"invalid market data evidence JSON: {exc}",
                )
            bars = bundle.get("bars") or []
            start = req.start_time[:10] if req.start_time else None
            end = req.end_time[:10] if req.end_time else None
            filtered: list[dict[str, Any]] = []
            for bar in bars:
                trade = str(bar.get("trade_date") or "")
                if start and trade < start:
                    continue
                if end and trade > end:
                    continue
                filtered.append(bar)
            if not filtered:
                return FetchResult(
                    run_id=req.run_id,
                    source_id=self.source_id,
                    data_domain=req.data_domain,
                    status="EMPTY_RESPONSE",
                    row_count=0,
                    fetch_time=fetch_time,
                    error_message=_WATERMARK_EMPTY_MSG,
                )
            persist_incremental_fetch_payload(
                self,
                payload,
                req,
                as_of=str(filtered[-1].get("trade_date") or fetch_time[:10]),
            )
            con.execute(f"DELETE FROM {_BAR_STAGING_TABLE}")
            for bar in filtered:
                close = float(bar.get("close") or 0.0)
                con.execute(
                    f"""
                    INSERT INTO {_BAR_STAGING_TABLE} (
                        instrument_id, trade_date, open, high, low, close, pre_close, volume, amount,
                        adjustment_type, source_used, batch_id, quality_flags, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, NULL, ?, NULL, 'none', ?, 'incremental', NULL, CURRENT_TIMESTAMP)
                    """,
                    [
                        str(bar.get("instrument_id") or req.instrument_id or ""),
                        str(bar.get("trade_date") or ""),
                        float(bar.get("open") or close),
                        float(bar.get("high") or close),
                        float(bar.get("low") or close),
                        close,
                        float(bar.get("volume") or 0.0),
                        str(bar.get("source_used") or "alpha_vantage"),
                    ],
                )
            return FetchResult(
                run_id=req.run_id,
                source_id=self.source_id,
                data_domain=req.data_domain,
                status="SUCCESS",
                row_count=len(filtered),
                fetch_time=fetch_time,
                staging_table=_BAR_STAGING_TABLE,
                content_hash=str(bundle.get("content_hash")),
                schema_hash=str(bundle.get("schema_hash")),
            )

    return AlphaVantageBarStagingAdapter


@contextmanager
def _alpha_vantage_staging_adapter_patch(fetch_port: FetchPort):
    import backend.app.datasources.adapters as adapters_mod

    staging_cls = _make_alpha_vantage_staging_adapter_class()
    original = adapters_mod.create_test_adapter

    def factory(source_id: str, registry, data_root: Path, **kwargs):
        if source_id == "alpha_vantage":
            port = kwargs.get("fetch_port") or fetch_port
            return staging_cls(registry, raw_store=RawStore(data_root), fetch_port=port)
        return original(source_id, registry, data_root, **kwargs)

    adapters_mod.create_test_adapter = factory
    try:
        yield
    finally:
        adapters_mod.create_test_adapter = original


def build_alpha_vantage_incremental_service(
    *,
    data_root: Path,
    fetch_port: FetchPort,
    job_events=None,
    source_registry=None,
    platform_matrix_path=None,
    route_planner=None,
) -> DataSourceService:
    from backend.app.ops.macro_incremental_common import load_incremental_route_bundle

    if route_planner is not None:
        registry = route_planner.source_registry
        caps = route_planner.capability_registry
        planner = route_planner
    else:
        registry, caps, planner = load_incremental_route_bundle(
            source_id="alpha_vantage",
            data_domain="us_equity_daily_bar",
            source_registry=source_registry,
            platform_matrix_path=platform_matrix_path,
        )
    return DataSourceService(
        data_root=data_root,
        fetch_port=fetch_port,
        job_events=job_events,
        staged_fixture_mode=True,
        source_registry=registry,
        capability_registry=caps,
        route_planner=planner,
    )


@dataclass(frozen=True)
class AlphaVantageIncrementalRunReport:
    symbol_results: tuple[dict[str, Any], ...]
    overall_status: str


def run_alpha_vantage_incremental(
    orch: DataSyncOrchestrator,
    *,
    service: DataSourceService,
    symbols: tuple[str, ...] = (_DEFAULT_SYMBOL,),
    end: date | None = None,
    source_registry=None,
) -> AlphaVantageIncrementalRunReport:
    target = resolve_clean_write_target("us_equity_daily_bar")
    cm = orch._jobs.connection_manager
    results: list[dict[str, Any]] = []
    fetch_port = service._fetch_port
    with _alpha_vantage_staging_adapter_patch(fetch_port):
        for symbol in symbols:
            with cm.writer() as con:
                wm = read_bar_trade_date_watermark(con, instrument_id=symbol)
            window = compute_incremental_window(wm, end=end)
            if window.date_start > window.date_end:
                results.append(
                    {
                        "instrument_id": symbol,
                        "status": "EMPTY_RESPONSE",
                        "watermark": wm.isoformat() if wm else None,
                        "clean_row_count": 0,
                    }
                )
                continue
            spec = SyncJobSpec(
                run_id=f"av-inc-{symbol}-{uuid.uuid4().hex[:8]}",
                job_id=f"job-av-inc-{symbol}-{uuid.uuid4().hex[:8]}",
                job_type="incremental",
                data_domain="us_equity_daily_bar",
                market_id="US",
                source_id="alpha_vantage",
                adapter_id="alpha_vantage",
                date_start=window.date_start,
                date_end=window.date_end,
                instrument_id=symbol,
                partition_key=None,
                trigger_reason="alpha_vantage_incremental",
            )
            result = orch.run_incremental(
                spec,
                datasource_service=service,
                clean_table=target.target_table,
                write_mode=target.write_mode,
                primary_keys=target.primary_keys,
                required_fields=_BAR_REQUIRED_FIELDS,
            )
            display = result.status
            if result.status == "FAILED_FINAL" and (result.message or "").startswith(_WATERMARK_EMPTY_MSG):
                display = "EMPTY_RESPONSE"
            row_count = 0
            if display == "COMPLETED":
                with cm.writer() as con:
                    row_count = con.execute(
                        "SELECT COUNT(*) FROM security_bar_1d WHERE instrument_id = ?",
                        [symbol],
                    ).fetchone()[0]
            results.append(
                {
                    "instrument_id": symbol,
                    "status": display,
                    "job_id": result.job_id,
                    "window_start": window.date_start.isoformat(),
                    "window_end": window.date_end.isoformat(),
                    "clean_row_count": row_count,
                }
            )
    statuses = [r["status"] for r in results]
    overall = "COMPLETED" if all(s in {"COMPLETED", "EMPTY_RESPONSE", "SKIPPED"} for s in statuses) else "FAILED"
    return AlphaVantageIncrementalRunReport(symbol_results=tuple(results), overall_status=overall)
