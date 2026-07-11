"""Shared macro incremental helpers (DCP-05 S03–S06).

ponytail: extracted from fred_incremental_* to avoid four full copies; fred keeps its module.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Any

from backend.app.datasources.adapters.fetch_port import FetchPort, PortError
from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase, _utc_now_iso
from backend.app.datasources.fetch_ports.fred_port import MAX_WINDOW_DAYS
from backend.app.datasources.fetch_result import FetchRequest, FetchResult
from backend.app.datasources.service import DataSourceService
from backend.app.layer1_axes.observation_contract import AXIS_OBSERVATION_DDL_COLUMNS
from backend.app.ops.sandbox_clean_write.clean_write_targets import resolve_clean_write_target
from backend.app.storage.raw_store import RawStore
from backend.app.sync.jobs import SyncJobSpec
from backend.app.sync.orchestrator import DataSyncOrchestrator
from backend.app.sync.watermark import compute_since_date, read_observation_date_watermark
from backend.app.validators.data_quality import DataQualityRequest

MACRO_REQUIRED_FIELDS = ("raw_value", "source_used")
STAGING_TABLE = "stg_axis_observation_smoke"
_SERIES_SUCCESS_STATUSES = frozenset({"COMPLETED", "EMPTY_RESPONSE"})
_WATERMARK_EMPTY_MSG = "no observations after watermark window"
_RAW_FILE_TYPES = frozenset({"json", "csv", "parquet"})
_NETWORK_FAILURE_MARKERS = (
    "network_error",
    "urlopen error",
    "ssl",
    "timed out",
    "connection reset",
    "connection refused",
)


def _normalize_incremental_job_status(result) -> str:
    """Map orchestrator FAILED_FINAL to domain sync status (EMPTY_RESPONSE / NETWORK_ERROR)."""
    status = str(getattr(result, "status", "") or "")
    if status != "FAILED_FINAL":
        return status
    msg = (getattr(result, "message", None) or "").lower()
    if msg.startswith(_WATERMARK_EMPTY_MSG.lower()) or "watermark window" in msg:
        return "EMPTY_RESPONSE"
    if "returned no usable rows" in msg or "returned no rows for" in msg:
        return "EMPTY_RESPONSE"
    if "no world bank observations for" in msg:
        return "EMPTY_RESPONSE"
    if any(marker in msg for marker in _NETWORK_FAILURE_MARKERS):
        return "NETWORK_ERROR"
    if "no mock observations on/after" in msg or msg == "empty_response":
        return "EMPTY_RESPONSE"
    return status


def incremental_evidence_as_of(
    bundle: dict[str, Any], *, fetch_time: str, start_date: str | None
) -> str:
    for key in ("as_of_timestamp", "retrieved_at", "filing_date", "report_date"):
        raw = bundle.get(key)
        if isinstance(raw, str) and len(raw) >= 10:
            return raw[:10]
    if start_date:
        return start_date[:10]
    return fetch_time[:10]


def persist_incremental_fetch_payload(
    adapter: SkeletonAdapterBase,
    payload: Any,
    req: FetchRequest,
    *,
    as_of: str,
) -> None:
    """Persist live fetch JSON for F0 data health (staging adapters bypass SkeletonAdapterBase.fetch)."""
    file_type = getattr(payload, "file_type", None) or "json"
    if file_type not in _RAW_FILE_TYPES:
        file_type = "json"
    adapter._raw_store.save(
        payload.content,
        source=adapter.source_id,
        data_domain=req.data_domain,
        file_type=file_type,
        as_of=as_of,
    )


def compute_bis_since_date(watermark: date | None, *, cap_days: int = MAX_WINDOW_DAYS) -> date:
    """BIS monthly: advance to first day of month after watermark (idempotent re-fetch)."""
    if watermark is None:
        return compute_since_date(None, cap_days=cap_days)
    y, m = watermark.year, watermark.month
    if m == 12:
        return date(y + 1, 1, 1)
    return date(y, m + 1, 1)


def compute_world_bank_since_date(watermark: date | None, *, cap_days: int = 365 * 10) -> date:
    """World Bank annual: cold-start cap; watermark → next calendar year (idempotent re-fetch)."""
    if watermark is None:
        return compute_since_date(None, cap_days=cap_days)
    return date(watermark.year + 1, 1, 1)


def read_since_dates_for_instruments(
    con,
    instrument_ids: Sequence[str],
    *,
    cap_days: int = MAX_WINDOW_DAYS,
    today: date | None = None,
    advance_days: int = 1,
) -> dict[str, str]:
    """Per-instrument ISO since dates for FetchRequest.start_time injection."""
    return {
        instrument_id: compute_since_date(
            read_observation_date_watermark(con, instrument_id),
            cap_days=cap_days,
            today=today,
            advance_days=advance_days,
        ).isoformat()
        for instrument_id in instrument_ids
    }


def enabled_source_registry(*, source_id: str, data_domain: str):
    """Enable one source + domain on a loaded SourceRegistry (incremental CLI/tests)."""
    from backend.app.datasources.source_registry import DomainRoleBinding, SourceRegistry

    registry = SourceRegistry()
    registry.load()
    rec = registry.get(source_id)
    object.__setattr__(rec, "is_enabled", True)
    orig = registry.get_domain_roles

    def _domain_enabled(domain: str):
        binding = orig(domain)
        if domain != data_domain:
            return binding
        return DomainRoleBinding(
            primary_source_id=source_id,
            validation_source_id=binding.validation_source_id,
            fallback_policy=binding.fallback_policy,
            domain_enabled_by_default=True,
            fallback_source_ids=binding.fallback_source_ids,
        )

    registry.get_domain_roles = _domain_enabled  # type: ignore[method-assign]
    return registry


def build_axis_observation_row(
    *,
    indicator_id: str,
    obs_date: str,
    raw_value: float,
    source_used: str,
    content_hash: str,
    schema_hash: str,
    frequency: str,
    fetch_time: datetime,
    raw_unit: str = "index",
) -> dict[str, object]:
    as_of = date.fromisoformat(obs_date[:10])
    as_of_dt = datetime.combine(as_of, time(16, 0), tzinfo=UTC)
    publish_dt = datetime.combine(as_of, time(0, 0), tzinfo=UTC)
    # ponytail: PK from indicator+date only — live bundle content_hash changes per fetch
    obs_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{indicator_id}|{obs_date}"))
    return {
        "observation_id": obs_id,
        "indicator_id": indicator_id,
        "as_of_timestamp": as_of_dt,
        "publish_timestamp": publish_dt,
        "fetch_time": fetch_time,
        "raw_value": raw_value,
        "raw_unit": raw_unit,
        "frequency": frequency,
        "source_used": source_used,
        "source_channel_id": source_used,
        "data_lag_days": 0.0,
        "stale_reason": None,
        "quality_flags": "INCREMENTAL",
        "content_hash": content_hash,
        "schema_hash": schema_hash,
        "source_switched": False,
        "created_at": datetime.now(UTC),
    }


@contextmanager
def incremental_validation_patch_factory(
    expected_columns: tuple[str, ...],
    timestamp_fields: tuple[str, ...],
    *,
    label: str = "incremental",
):
    """Patch run_incremental validate_staging for domain-specific staging columns."""
    from backend.app.sync.runners import _DEFAULT_QUALITY_RULE_SET, _PipelineMixin

    original = _PipelineMixin._validate_staging

    def _patched_validate_staging(
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
            raise ValueError(f"{label} incremental does not use conflict staging")
        self._jobs.emit_custom_event(
            job_id,
            event_type="CONFLICT_CHECK_SKIPPED",
            message=f"{label} incremental: conflict validation skipped",
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
            expected_columns=expected_columns,
            timestamp_fields=timestamp_fields,
            conflict_request=None,
            conflict_staging_table=None,
        )

    _PipelineMixin._validate_staging = _patched_validate_staging
    try:
        yield
    finally:
        _PipelineMixin._validate_staging = original


@contextmanager
def macro_incremental_validation_patch():
    """L1 run_incremental validate path for macro domains."""
    with incremental_validation_patch_factory(
        AXIS_OBSERVATION_DDL_COLUMNS,
        ("as_of_timestamp", "publish_timestamp", "fetch_time"),
        label="macro",
    ):
        yield


def _make_macro_staging_adapter_class(
    *,
    source_id: str,
    data_domain: str,
    staging_rows_fn: Callable[..., list[dict[str, object]]],
):
    class MacroStagingAdapter(SkeletonAdapterBase):
        supported_domains = frozenset({data_domain})

        def __init__(self, registry, *, raw_store, fetch_port: FetchPort):
            super().__init__(registry, raw_store=raw_store, fetch_port=fetch_port)
            self.source_id = source_id

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
            rows = staging_rows_fn(
                bundle,
                instrument_id=req.instrument_id or "",
                start_date=req.start_time[:10] if req.start_time else None,
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

    return MacroStagingAdapter


@contextmanager
def macro_staging_adapter_patch(
    *,
    source_id: str,
    data_domain: str,
    fetch_port: FetchPort,
    staging_rows_fn: Callable[..., list[dict[str, object]]],
):
    import backend.app.datasources.adapters as adapters_mod

    staging_cls = _make_macro_staging_adapter_class(
        source_id=source_id,
        data_domain=data_domain,
        staging_rows_fn=staging_rows_fn,
    )
    original = adapters_mod.create_test_adapter

    def factory(sid: str, registry, data_root: Path, **kwargs):
        if sid == source_id:
            port = kwargs.get("fetch_port") or fetch_port
            return staging_cls(registry, raw_store=RawStore(data_root), fetch_port=port)
        return original(sid, registry, data_root, **kwargs)

    adapters_mod.create_test_adapter = factory
    try:
        yield
    finally:
        adapters_mod.create_test_adapter = original


class MacroIncrementalFetchProxy:
    """Inject per-instrument watermark start_time before DataSourceService.fetch."""

    def __init__(
        self,
        inner: DataSourceService,
        since_by_instrument: dict[str, str],
        *,
        operation: str,
    ) -> None:
        self._inner = inner
        self._since = since_by_instrument
        self._operation = operation

    def __getattr__(self, name: str):
        return getattr(self._inner, name)

    def fetch(self, req: FetchRequest, **kwargs):
        since = self._since.get(req.instrument_id or "")
        if since:
            req = req.model_copy(update={"start_time": since})
        kwargs["operation"] = self._operation
        return self._inner.fetch(req, **kwargs)


@dataclass(frozen=True)
class MacroIncrementalRunReport:
    instrument_results: tuple[dict[str, Any], ...]
    total_rows_written: int
    overall_status: str


@dataclass(frozen=True)
class MacroIncrementalSourceConfig:
    source_id: str
    data_domain: str
    adapter_id: str
    operation: str
    trigger_reason: str
    staging_rows_fn: Callable[..., list[dict[str, object]]]
    validate_instrument: Callable[[str], None] | None = None
    advance_days: int = 1
    since_date_fn: Callable[[date | None], date] | None = None
    indicator_resolver: Callable[[str], str] | None = None


def load_incremental_route_bundle(*, source_id: str, data_domain: str, source_registry=None):
    from backend.app.datasources.capability_registry import SourceCapabilityRegistry
    from backend.app.datasources.route_planner import SourceRoutePlanner

    registry = source_registry or enabled_source_registry(
        source_id=source_id, data_domain=data_domain
    )
    caps = SourceCapabilityRegistry()
    caps.load()
    planner = SourceRoutePlanner(source_registry=registry, capability_registry=caps)
    planner._platform_allows = lambda _sid: (True, None)
    return registry, caps, planner


def build_macro_incremental_service(
    *,
    config: MacroIncrementalSourceConfig,
    data_root: Path,
    fetch_port: FetchPort,
    since_by_instrument: dict[str, str],
    job_events=None,
    source_registry=None,
) -> MacroIncrementalFetchProxy:
    registry, caps, planner = load_incremental_route_bundle(
        source_id=config.source_id,
        data_domain=config.data_domain,
        source_registry=source_registry,
    )
    inner = DataSourceService(
        data_root=data_root,
        fetch_port=fetch_port,
        job_events=job_events,
        staged_fixture_mode=True,
        source_registry=registry,
        capability_registry=caps,
        route_planner=planner,
    )
    return MacroIncrementalFetchProxy(
        inner, since_by_instrument, operation=config.operation
    )


def _instrument_display_status(result) -> str:
    return _normalize_incremental_job_status(result)


def _compute_overall_status(statuses: Sequence[str]) -> str:
    if not statuses:
        return "COMPLETED"
    if all(s in _SERIES_SUCCESS_STATUSES for s in statuses):
        return "COMPLETED"
    if any(s in _SERIES_SUCCESS_STATUSES for s in statuses):
        return "PARTIAL_FAILURE"
    return "FAILED"


def run_macro_incremental(
    orch: DataSyncOrchestrator,
    *,
    config: MacroIncrementalSourceConfig,
    service: MacroIncrementalFetchProxy,
    instrument_ids: Sequence[str],
    use_mock: bool = True,
    source_registry=None,
) -> MacroIncrementalRunReport:
    """Run incremental sync for each instrument via gold path."""
    target = resolve_clean_write_target(config.data_domain)
    cm = orch._jobs.connection_manager
    resolve = config.indicator_resolver or (lambda instrument_id: instrument_id)
    with cm.writer() as con:
        since_map = {
            instrument_id: (
                config.since_date_fn(read_observation_date_watermark(con, resolve(instrument_id)))
                if config.since_date_fn is not None
                else compute_since_date(
                    read_observation_date_watermark(con, resolve(instrument_id)),
                    advance_days=config.advance_days,
                )
            ).isoformat()
            for instrument_id in instrument_ids
        }
    fetch_port = service._inner._fetch_port  # noqa: SLF001
    proxy = build_macro_incremental_service(
        config=config,
        data_root=service._inner._data_root,  # noqa: SLF001
        fetch_port=fetch_port,
        since_by_instrument=since_map,
        job_events=orch._jobs,
        source_registry=source_registry,
    )
    results: list[dict[str, Any]] = []
    total_rows = 0
    with macro_staging_adapter_patch(
        source_id=config.source_id,
        data_domain=config.data_domain,
        fetch_port=fetch_port,
        staging_rows_fn=config.staging_rows_fn,
    ), macro_incremental_validation_patch():
        for instrument_id in instrument_ids:
            if config.validate_instrument is not None:
                config.validate_instrument(instrument_id)
            spec = SyncJobSpec(
                run_id=f"{config.source_id}-inc-{instrument_id}-{uuid.uuid4().hex[:8]}",
                job_id=f"job-{config.source_id}-inc-{instrument_id}-{uuid.uuid4().hex[:8]}",
                job_type="incremental",
                data_domain=config.data_domain,
                market_id="GLOBAL",
                source_id=config.source_id,
                adapter_id=config.adapter_id,
                date_start=None,
                date_end=None,
                instrument_id=instrument_id,
                partition_key=None,
                trigger_reason=config.trigger_reason,
            )
            result = orch.run_incremental(
                spec,
                datasource_service=proxy,
                clean_table=target.target_table,
                write_mode=target.write_mode,
                primary_keys=target.primary_keys,
                required_fields=MACRO_REQUIRED_FIELDS,
            )
            display_status = _instrument_display_status(result)
            row_count = 0
            if display_status in _SERIES_SUCCESS_STATUSES:
                clean_indicator = resolve(instrument_id)
                with cm.writer() as con:
                    row_count = con.execute(
                        f"SELECT COUNT(*) FROM {target.target_table} WHERE indicator_id = ?",
                        [clean_indicator],
                    ).fetchone()[0]
                if display_status == "COMPLETED":
                    total_rows += row_count
            results.append(
                {
                    "instrument_id": instrument_id,
                    "status": display_status,
                    "job_id": result.job_id,
                    "since": since_map.get(instrument_id),
                    "use_mock": use_mock,
                    "clean_row_count": row_count,
                }
            )
    statuses = [r["status"] for r in results]
    return MacroIncrementalRunReport(
        instrument_results=tuple(results),
        total_rows_written=total_rows,
        overall_status=_compute_overall_status(statuses),
    )
