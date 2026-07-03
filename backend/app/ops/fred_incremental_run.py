"""FRED macro incremental orchestration (R3-DCP-02).

L1: DataSourceService + DataSyncOrchestrator.run_incremental (reference-adoption-dcp02.md §2).
L2: FetchRequest.start_time → fred_port observation_start (execute-reference-read-evidence.md R1).
L3: macro_staging_rows_from_bundle + ops watermark reader (reference-adoption-dcp02.md §2 fred watermark).
ponytail: macro validation patch until track A extends IncrementalJobRunner bar defaults.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Any

from backend.app.datasources.adapters.fetch_port import FetchPort, PortError
from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase, _utc_now_iso
from backend.app.datasources.fetch_ports.fred_port import P0_SERIES_WHITELIST
from backend.app.datasources.fetch_result import FetchRequest, FetchResult
from backend.app.datasources.service import DataSourceService
from backend.app.layer1_axes.observation_contract import AXIS_OBSERVATION_DDL_COLUMNS
from backend.app.ops.fred_incremental_watermark import STAGING_TABLE, read_since_dates_for_series
from backend.app.ops.macro_incremental_common import (
    incremental_evidence_as_of,
    persist_incremental_fetch_payload,
)
from backend.app.ops.sandbox_clean_write.clean_write_targets import resolve_clean_write_target
from backend.app.storage.raw_store import RawStore
from backend.app.sync.jobs import SyncJobSpec
from backend.app.sync.orchestrator import DataSyncOrchestrator
from backend.app.validators.data_quality import DataQualityRequest

MACRO_REQUIRED_FIELDS = ("raw_value", "source_used")
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
    content_hash = str(bundle.get("content_hash") or "fred-hash")
    schema_hash = str(bundle.get("schema_hash") or "fred-schema")
    fetch_time_raw = bundle.get("retrieved_at") or bundle.get("as_of_timestamp")
    if isinstance(fetch_time_raw, str):
        fetch_time = datetime.fromisoformat(fetch_time_raw.replace("Z", "+00:00"))
        if fetch_time.tzinfo is None:
            fetch_time = fetch_time.replace(tzinfo=UTC)
    else:
        fetch_time = datetime.now(UTC)
    rows: list[dict[str, object]] = []
    for obs in bundle.get("observations") or []:
        obs_date = str(obs.get("observation_date") or "")
        if not obs_date:
            continue
        if start_date and obs_date < start_date:
            continue
        raw_value = obs.get("value")
        if raw_value in (None, ".", ""):
            continue
        indicator_id = str(obs.get("series_id") or series_id)
        as_of = date.fromisoformat(obs_date)
        as_of_dt = datetime.combine(as_of, time(16, 0), tzinfo=UTC)
        publish_dt = datetime.combine(as_of, time(0, 0), tzinfo=UTC)
        obs_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{indicator_id}|{obs_date}|{content_hash}"))
        rows.append(
            {
                "observation_id": obs_id,
                "indicator_id": indicator_id,
                "as_of_timestamp": as_of_dt,
                "publish_timestamp": publish_dt,
                "fetch_time": fetch_time,
                "raw_value": float(raw_value),
                "raw_unit": "index",
                "frequency": "daily",
                "source_used": str(bundle.get("source_id") or "fred"),
                "source_channel_id": str(bundle.get("source_id") or "fred"),
                "data_lag_days": 0.0,
                "stale_reason": None,
                "quality_flags": "INCREMENTAL",
                "content_hash": content_hash,
                "schema_hash": schema_hash,
                "source_switched": False,
                "created_at": datetime.now(UTC),
            }
        )
    return rows


def _make_fred_macro_staging_adapter_class():
    class FredMacroStagingAdapter(SkeletonAdapterBase):
        source_id = "fred"
        supported_domains = frozenset({"macro_series"})

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
                    error_message=f"invalid macro evidence JSON: {exc}",
                )
            rows = macro_staging_rows_from_bundle(
                bundle,
                series_id=req.instrument_id or "",
                start_date=req.start_time[:10] if req.start_time else None,
            )
            if not rows:
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
                as_of=incremental_evidence_as_of(
                    bundle,
                    fetch_time=fetch_time,
                    start_date=req.start_time[:10] if req.start_time else None,
                ),
            )
            con.execute(f"DELETE FROM {STAGING_TABLE}")
            col_list = ", ".join(AXIS_OBSERVATION_DDL_COLUMNS)
            placeholders = ", ".join("?" for _ in AXIS_OBSERVATION_DDL_COLUMNS)
            for row in rows:
                con.execute(
                    f"INSERT INTO {STAGING_TABLE} ({col_list}) VALUES ({placeholders})",
                    [row[col] for col in AXIS_OBSERVATION_DDL_COLUMNS],
                )
            return FetchResult(
                run_id=req.run_id,
                source_id=self.source_id,
                data_domain=req.data_domain,
                status="SUCCESS",
                row_count=len(rows),
                fetch_time=fetch_time,
                staging_table=STAGING_TABLE,
                content_hash=str(bundle.get("content_hash")),
                schema_hash=str(bundle.get("schema_hash")),
            )

    return FredMacroStagingAdapter


@contextmanager
def _fred_staging_adapter_patch(fetch_port: FetchPort):
    import backend.app.datasources.adapters as adapters_mod

    staging_cls = _make_fred_macro_staging_adapter_class()
    original = adapters_mod.create_test_adapter

    def factory(source_id: str, registry, data_root: Path, **kwargs):
        if source_id == "fred":
            port = kwargs.get("fetch_port") or fetch_port
            return staging_cls(
                registry,
                raw_store=RawStore(data_root),
                fetch_port=port,
            )
        return original(source_id, registry, data_root, **kwargs)

    adapters_mod.create_test_adapter = factory
    try:
        yield
    finally:
        adapters_mod.create_test_adapter = original


@contextmanager
def _macro_incremental_validation_patch():
    """L1 run_incremental validate path; ponytail: bar-domain expected_columns in runners.

    Upgrade = track A macro branch in sync/runners.py (reference-adoption-dcp02.md §2).
    """
    from backend.app.sync.runners import _DEFAULT_QUALITY_RULE_SET, _PipelineMixin

    original = _PipelineMixin._validate_staging

    def _macro_validate_staging(
        self,
        con,
        *,
        spec: SyncJobSpec,
        job_id: str,
        staging_table: str,
        conflict_staging_table: str | None,
        primary_keys: tuple[str, ...],
        required_fields: tuple[str, ...],
    ):
        if conflict_staging_table is not None:
            raise ValueError("macro incremental does not use conflict staging")
        self._jobs.emit_custom_event(
            job_id,
            event_type="CONFLICT_CHECK_SKIPPED",
            message="macro incremental: conflict validation skipped",
            payload_json='{"decision":"conflict_check_skipped"}',
            con=con,
        )
        return self._validation.validate_staging(
            con,
            quality_request=DataQualityRequest(
                run_id=spec.run_id,
                job_id=job_id,
                data_domain=spec.data_domain,
                source_id=spec.source_id,
                staging_table=staging_table,
                primary_keys=primary_keys,
                required_fields=required_fields,
                rule_set_id=_DEFAULT_QUALITY_RULE_SET,
            ),
            expected_columns=AXIS_OBSERVATION_DDL_COLUMNS,
            timestamp_fields=("as_of_timestamp", "publish_timestamp", "fetch_time"),
            conflict_request=None,
            conflict_staging_table=None,
        )

    _PipelineMixin._validate_staging = _macro_validate_staging
    try:
        yield
    finally:
        _PipelineMixin._validate_staging = original


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
    from backend.app.datasources.capability_registry import SourceCapabilityRegistry
    from backend.app.datasources.route_planner import SourceRoutePlanner
    from backend.app.ops.fred_incremental_watermark import enabled_fred_source_registry

    registry = source_registry
    if registry is None:
        registry = enabled_fred_source_registry()
    caps = SourceCapabilityRegistry()
    caps.load()
    planner = SourceRoutePlanner(source_registry=registry, capability_registry=caps)
    # ponytail: registry yaml disabled-by-default; runtime enable until reconcile (RB-13).
    planner._platform_allows = lambda _sid: (True, None)
    return registry, caps, planner


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


def _series_display_status(result) -> str:
    if result.status != "FAILED_FINAL":
        return result.status
    msg = result.message or ""
    if msg.startswith(_WATERMARK_EMPTY_MSG):
        return "EMPTY_RESPONSE"
    if "no mock observations on/after" in msg or msg == "EMPTY_RESPONSE":
        return "EMPTY_RESPONSE"
    return result.status


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
    """Run incremental sync for each P0 series via gold path (L1 run_incremental)."""
    target = resolve_clean_write_target("macro_series")
    cm = orch._jobs.connection_manager
    results: list[dict[str, Any]] = []
    total_rows = 0
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

    with _fred_staging_adapter_patch(fetch_port), _macro_incremental_validation_patch():
        for series_id in series_ids:
            if series_id not in P0_SERIES_WHITELIST:
                raise ValueError(f"series not in P0 whitelist: {series_id!r}")
            spec = SyncJobSpec(
                run_id=f"fred-inc-{series_id}-{uuid.uuid4().hex[:8]}",
                job_id=f"job-fred-inc-{series_id}-{uuid.uuid4().hex[:8]}",
                job_type="incremental",
                data_domain="macro_series",
                market_id="GLOBAL",
                source_id="fred",
                adapter_id="fred",
                date_start=None,
                date_end=None,
                instrument_id=series_id,
                partition_key=None,
                trigger_reason="fred_macro_incremental",
            )
            result = orch.run_incremental(
                spec,
                datasource_service=proxy,
                clean_table=target.target_table,
                write_mode=target.write_mode,
                primary_keys=target.primary_keys,
                required_fields=MACRO_REQUIRED_FIELDS,
            )
            display_status = _series_display_status(result)
            row_count = 0
            if display_status == "COMPLETED":
                with cm.writer() as con:
                    row_count = con.execute(
                        f"SELECT COUNT(*) FROM {target.target_table} WHERE indicator_id = ?",
                        [series_id],
                    ).fetchone()[0]
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
