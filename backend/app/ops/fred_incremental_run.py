"""FRED macro incremental — thin binding to execute_binding (M-G1-03 S04).

ponytail: staging adapter patch stays here until track A extends sync/runners macro branch.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.datasources.adapters.fetch_port import FetchPort
from backend.app.datasources.fetch_ports.fred_port import P0_SERIES_WHITELIST
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.service import DataSourceService
from backend.app.ops.fred_incremental_watermark import read_since_dates_for_series
from backend.app.ops.macro_incremental_common import (
    enabled_source_registry,
    load_incremental_route_bundle,
    macro_staging_adapter_patch,
)
from backend.app.ops.sandbox_clean_write.clean_write_targets import resolve_clean_write_target
from backend.app.sync.binding_executor import execute_binding
from backend.app.sync.indicator_binding import (
    IndicatorBinding,
    UnknownIndicatorError,
    bindings_for_source,
    load_binding,
)
from backend.app.sync.mappers.macro_series import map_macro_series_bundle_to_axis_observations
from backend.app.sync.orchestrator import DataSyncOrchestrator

DEFAULT_SERIES = ("DGS10",)
_SERIES_SUCCESS_STATUSES = frozenset({"COMPLETED", "EMPTY_RESPONSE"})
_WATERMARK_EMPTY_MSG = "no observations after watermark window"


def macro_staging_rows_from_bundle(
    bundle: dict[str, Any],
    *,
    series_id: str,
    start_date: str | None = None,
) -> list[dict[str, object]]:
    """Map official_macro_evidence_v1 payload → axis_observation staging rows."""
    return map_macro_series_bundle_to_axis_observations(
        bundle, series_id=series_id, start_date=start_date
    )


class FredIncrementalFetchProxy:
    """Inject per-series watermark start_time before DataSourceService.fetch."""

    def __init__(self, inner: DataSourceService, since_by_series: dict[str, str]) -> None:
        self._inner = inner
        self._since = since_by_series

    def __getattr__(self, name: str):
        return getattr(self._inner, name)

    def fetch(self, req: FetchRequest, **kwargs):
        since = self._since.get(req.instrument_id or "")
        if since:
            req = req.model_copy(update={"start_time": since})
        kwargs["operation"] = "fetch_macro_series"
        return self._inner.fetch(req, **kwargs)


@dataclass(frozen=True)
class FredIncrementalRunReport:
    series_results: tuple[dict[str, Any], ...]
    total_rows_written: int
    overall_status: str


def _load_fred_incremental_route_bundle(source_registry=None):
    return load_incremental_route_bundle(
        source_id="fred",
        data_domain="macro_series",
        source_registry=source_registry or enabled_fred_source_registry(),
    )


def enabled_fred_source_registry():
    return enabled_source_registry(source_id="fred", data_domain="macro_series")


def build_fred_incremental_preview_service(*, source_registry=None) -> DataSourceService:
    """Dry-run route preview for macro_series/fred (L2 data_commands sync_plan)."""
    registry, caps, planner = _load_fred_incremental_route_bundle(source_registry)
    return DataSourceService(
        source_registry=registry,
        capability_registry=caps,
        route_planner=planner,
        staged_fixture_mode=False,
    )


def build_fred_incremental_service(
    *,
    data_root: Path,
    fetch_port: FetchPort,
    since_by_series: dict[str, str],
    job_events=None,
    source_registry=None,
) -> FredIncrementalFetchProxy:
    registry, caps, planner = _load_fred_incremental_route_bundle(source_registry)
    inner = DataSourceService(
        data_root=data_root,
        fetch_port=fetch_port,
        job_events=job_events,
        staged_fixture_mode=True,
        source_registry=registry,
        capability_registry=caps,
        route_planner=planner,
    )
    return FredIncrementalFetchProxy(inner, since_by_series)


def _binding_for_fred_series(series_id: str) -> IndicatorBinding:
    candidate = f"ENV-E1-{series_id}"
    try:
        return load_binding(candidate)
    except UnknownIndicatorError:
        pass
    for binding in bindings_for_source("fred"):
        if series_id in binding.indicator_id:
            return binding
    raise ValueError(f"no indicator binding for fred series_id={series_id!r}")


def _series_display_status(result) -> str:
    from backend.app.ops.macro_incremental_common import _normalize_incremental_job_status

    return _normalize_incremental_job_status(result)


def _compute_overall_status(series_statuses: Sequence[str]) -> str:
    if not series_statuses:
        return "COMPLETED"
    if all(s in _SERIES_SUCCESS_STATUSES for s in series_statuses):
        return "COMPLETED"
    if any(s in _SERIES_SUCCESS_STATUSES for s in series_statuses):
        return "PARTIAL_FAILURE"
    return "FAILED"


def run_fred_macro_incremental(
    orch: DataSyncOrchestrator,
    *,
    service: FredIncrementalFetchProxy,
    series_ids: Sequence[str] = DEFAULT_SERIES,
    use_mock: bool = True,
    source_registry=None,
) -> FredIncrementalRunReport:
    """Run incremental sync for each P0 series via execute_binding (S04 thin ops)."""
    target = resolve_clean_write_target("macro_series")
    cm = orch._jobs.connection_manager
    with cm.writer() as con:
        since_map = read_since_dates_for_series(con, series_ids)
    fetch_port = service._inner._fetch_port  # noqa: SLF001
    proxy = build_fred_incremental_service(
        data_root=service._inner._data_root,  # noqa: SLF001
        fetch_port=fetch_port,
        since_by_series=since_map,
        job_events=orch._jobs,
        source_registry=source_registry,
    )

    def _staging_rows(bundle, *, instrument_id: str, start_date: str | None = None):
        return map_macro_series_bundle_to_axis_observations(
            bundle, series_id=instrument_id, start_date=start_date
        )

    results: list[dict[str, Any]] = []
    total_rows = 0
    with macro_staging_adapter_patch(
        source_id="fred",
        data_domain="macro_series",
        fetch_port=fetch_port,
        staging_rows_fn=_staging_rows,
    ):
        for series_id in series_ids:
            if series_id not in P0_SERIES_WHITELIST:
                raise ValueError(f"series not in P0 whitelist: {series_id!r}")
            binding = _binding_for_fred_series(series_id)
            result = execute_binding(
                binding,
                "incremental",
                dry_run=False,
                orchestrator=orch,
                datasource_service=proxy,
                instrument_id=series_id,
                connection_manager=cm,
            )
            display_status = _series_display_status(result)
            row_count = 0
            if display_status in _SERIES_SUCCESS_STATUSES:
                with cm.writer() as con:
                    row_count = con.execute(
                        f"SELECT COUNT(*) FROM {target.target_table} WHERE indicator_id = ?",
                        [series_id],
                    ).fetchone()[0]
                if display_status == "COMPLETED":
                    total_rows += row_count
            results.append(
                {
                    "series_id": series_id,
                    "status": display_status,
                    "job_id": result.job_id,
                    "since": since_map.get(series_id),
                    "use_mock": use_mock,
                    "clean_row_count": row_count,
                }
            )
    statuses = [r["status"] for r in results]
    return FredIncrementalRunReport(
        series_results=tuple(results),
        total_rows_written=total_rows,
        overall_status=_compute_overall_status(statuses),
    )


def run_fred_macro_backfill(
    orch: DataSyncOrchestrator,
    *,
    service: FredIncrementalFetchProxy,
    date_start,
    date_end,
    series_ids: Sequence[str] = DEFAULT_SERIES,
    use_mock: bool = True,
    source_registry=None,
) -> FredIncrementalRunReport:
    """Bounded fred macro backfill via execute_binding."""
    target = resolve_clean_write_target("macro_series")
    cm = orch._jobs.connection_manager
    fetch_port = service._inner._fetch_port  # noqa: SLF001

    def _staging_rows(bundle, *, instrument_id: str, start_date: str | None = None):
        return map_macro_series_bundle_to_axis_observations(
            bundle, series_id=instrument_id, start_date=start_date
        )

    results: list[dict[str, Any]] = []
    total_rows = 0
    with macro_staging_adapter_patch(
        source_id="fred",
        data_domain="macro_series",
        fetch_port=fetch_port,
        staging_rows_fn=_staging_rows,
    ):
        for series_id in series_ids:
            if series_id not in P0_SERIES_WHITELIST:
                raise ValueError(f"series not in P0 whitelist: {series_id!r}")
            binding = _binding_for_fred_series(series_id)
            result = execute_binding(
                binding,
                "backfill",
                dry_run=False,
                date_start=date_start,
                date_end=date_end,
                orchestrator=orch,
                datasource_service=service,
                instrument_id=series_id,
                connection_manager=cm,
            )
            display_status = _series_display_status(result)
            row_count = 0
            if display_status in _SERIES_SUCCESS_STATUSES:
                with cm.writer() as con:
                    row_count = con.execute(
                        f"SELECT COUNT(*) FROM {target.target_table} WHERE indicator_id = ?",
                        [series_id],
                    ).fetchone()[0]
                if display_status == "COMPLETED":
                    total_rows += row_count
            results.append(
                {
                    "series_id": series_id,
                    "status": display_status,
                    "job_id": result.job_id,
                    "use_mock": use_mock,
                    "clean_row_count": row_count,
                }
            )
    statuses = [r["status"] for r in results]
    return FredIncrementalRunReport(
        series_results=tuple(results),
        total_rows_written=total_rows,
        overall_status=_compute_overall_status(statuses),
    )
