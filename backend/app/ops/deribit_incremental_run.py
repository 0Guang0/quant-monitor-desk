"""Deribit crypto derivative incremental orchestration (R3-DCP-05 S11)."""

from __future__ import annotations

import json
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.app.datasources.adapters.fetch_port import FetchPort, PortError
from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase, _utc_now_iso
from backend.app.datasources.fetch_result import FetchRequest, FetchResult
from backend.app.datasources.service import DataSourceService
from backend.app.ops.deribit_incremental_watermark import STAGING_TABLE, read_since_date_for_instrument
from backend.app.ops.macro_incremental_common import (
    incremental_validation_patch_factory,
    load_incremental_route_bundle,
)
from backend.app.ops.sandbox_clean_write.clean_write_targets import resolve_clean_write_target
from backend.app.storage.raw_store import RawStore
from backend.app.sync.jobs import SyncJobSpec
from backend.app.sync.orchestrator import DataSyncOrchestrator

CRYPTO_STAGING_COLUMNS = (
    "instrument_name",
    "as_of_timestamp",
    "data_domain",
    "expiration_timestamp",
    "strike",
    "option_type",
    "mark_iv",
    "source_used",
    "batch_id",
    "source_fetch_id",
    "content_hash",
    "schema_hash",
    "quality_flags",
    "created_at",
)
CRYPTO_REQUIRED_FIELDS = ("mark_iv", "source_used")
_WATERMARK_EMPTY_MSG = "no instruments after deribit watermark window"
_DEFAULT_INSTRUMENT = "BTC-28JUN24-65000-C"


def _parse_as_of_ts(raw: object) -> datetime:
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=UTC)
    text = str(raw or "")
    if not text:
        return datetime.now(UTC)
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def deribit_staging_rows_from_bundle(
    bundle: dict[str, Any],
    *,
    instrument_name: str,
    start_date: str | None = None,
) -> list[dict[str, object]]:
    now = datetime.now(UTC)
    content_hash = str(bundle.get("content_hash") or "deribit-hash")
    schema_hash = str(bundle.get("schema_hash") or "deribit-schema")
    source_fetch_id = str(bundle.get("source_fetch_id") or "deribit-unknown")
    as_of = _parse_as_of_ts(bundle.get("as_of_timestamp") or bundle.get("retrieved_at"))
    if start_date and as_of.date().isoformat() < start_date:
        return []
    domain = str(bundle.get("data_domain") or "crypto_options_surface")
    rows: list[dict[str, object]] = []
    for inst in bundle.get("instruments") or []:
        name = str(inst.get("instrument_name") or instrument_name)
        if name != instrument_name:
            continue
        rows.append(
            {
                "instrument_name": name,
                "as_of_timestamp": as_of,
                "data_domain": domain,
                "expiration_timestamp": inst.get("expiration_timestamp"),
                "strike": inst.get("strike"),
                "option_type": inst.get("option_type"),
                "mark_iv": inst.get("mark_iv"),
                "source_used": str(inst.get("source_used") or "deribit"),
                "batch_id": "incremental",
                "source_fetch_id": source_fetch_id,
                "content_hash": content_hash,
                "schema_hash": schema_hash,
                "quality_flags": "INCREMENTAL",
                "created_at": now,
            }
        )
    return rows


def _make_deribit_staging_adapter_class():
    class DeribitStagingAdapter(SkeletonAdapterBase):
        source_id = "deribit"
        supported_domains = frozenset({"crypto_options_surface"})

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
                    error_message=f"invalid crypto market evidence JSON: {exc}",
                )
            rows = deribit_staging_rows_from_bundle(
                bundle,
                instrument_name=req.instrument_id or _DEFAULT_INSTRUMENT,
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
            con.execute(f"DELETE FROM {STAGING_TABLE}")
            col_list = ", ".join(CRYPTO_STAGING_COLUMNS)
            placeholders = ", ".join("?" for _ in CRYPTO_STAGING_COLUMNS)
            for row in rows:
                con.execute(
                    f"INSERT INTO {STAGING_TABLE} ({col_list}) VALUES ({placeholders})",
                    [row[col] for col in CRYPTO_STAGING_COLUMNS],
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

    return DeribitStagingAdapter


@contextmanager
def _deribit_incremental_validation_patch():
    with incremental_validation_patch_factory(
        CRYPTO_STAGING_COLUMNS,
        ("as_of_timestamp",),
        label="deribit",
    ):
        yield


@contextmanager
def _deribit_staging_adapter_patch(fetch_port: FetchPort):
    import backend.app.datasources.adapters as adapters_mod

    staging_cls = _make_deribit_staging_adapter_class()
    original = adapters_mod.create_test_adapter

    def factory(source_id: str, registry, data_root: Path, **kwargs):
        if source_id == "deribit":
            port = kwargs.get("fetch_port") or fetch_port
            return staging_cls(registry, raw_store=RawStore(data_root), fetch_port=port)
        return original(source_id, registry, data_root, **kwargs)

    adapters_mod.create_test_adapter = factory
    try:
        yield
    finally:
        adapters_mod.create_test_adapter = original


class DeribitIncrementalFetchProxy:
    def __init__(self, inner: DataSourceService, since_by_instrument: dict[str, str]) -> None:
        self._inner = inner
        self._since = since_by_instrument

    def __getattr__(self, name: str):
        return getattr(self._inner, name)

    def fetch(self, req: FetchRequest, **kwargs):
        since = self._since.get(req.instrument_id or "")
        if since:
            req = req.model_copy(update={"start_time": since})
        kwargs["operation"] = "fetch_derivatives_instruments"
        return self._inner.fetch(req, **kwargs)


@dataclass(frozen=True)
class DeribitIncrementalRunReport:
    instrument_results: tuple[dict[str, Any], ...]
    overall_status: str


def build_deribit_incremental_service(
    *,
    data_root: Path,
    fetch_port: FetchPort,
    since_by_instrument: dict[str, str],
    job_events=None,
    source_registry=None,
) -> DeribitIncrementalFetchProxy:
    registry, caps, planner = load_incremental_route_bundle(
        source_id="deribit",
        data_domain="crypto_options_surface",
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
    return DeribitIncrementalFetchProxy(inner, since_by_instrument)


def _display_status(result) -> str:
    if result.status != "FAILED_FINAL":
        return result.status
    msg = result.message or ""
    if msg.startswith(_WATERMARK_EMPTY_MSG):
        return "EMPTY_RESPONSE"
    return result.status


def run_deribit_incremental(
    orch: DataSyncOrchestrator,
    *,
    service: DeribitIncrementalFetchProxy,
    instruments: tuple[str, ...] = (_DEFAULT_INSTRUMENT,),
    source_registry=None,
) -> DeribitIncrementalRunReport:
    target = resolve_clean_write_target("crypto_options_surface")
    cm = orch._jobs.connection_manager
    results: list[dict[str, Any]] = []
    fetch_port = service._inner._fetch_port  # noqa: SLF001
    with cm.writer() as con:
        since_map = {
            name: read_since_date_for_instrument(con, name, data_domain="crypto_options_surface")
            for name in instruments
        }
    proxy = build_deribit_incremental_service(
        data_root=service._inner._data_root,  # noqa: SLF001
        fetch_port=fetch_port,
        since_by_instrument=since_map,
        job_events=orch._jobs,
        source_registry=source_registry,
    )
    with _deribit_staging_adapter_patch(fetch_port), _deribit_incremental_validation_patch():
        for name in instruments:
            spec = SyncJobSpec(
                run_id=f"deribit-inc-{name}-{uuid.uuid4().hex[:8]}",
                job_id=f"job-deribit-inc-{name}-{uuid.uuid4().hex[:8]}",
                job_type="incremental",
                data_domain="crypto_options_surface",
                market_id="CRYPTO",
                source_id="deribit",
                adapter_id="deribit",
                date_start=None,
                date_end=None,
                instrument_id=name,
                partition_key=None,
                trigger_reason="deribit_incremental",
            )
            result = orch.run_incremental(
                spec,
                datasource_service=proxy,
                clean_table=target.target_table,
                write_mode=target.write_mode,
                primary_keys=target.primary_keys,
                required_fields=CRYPTO_REQUIRED_FIELDS,
            )
            display = _display_status(result)
            row_count = 0
            if display == "COMPLETED":
                with cm.writer() as con:
                    row_count = con.execute(
                        f"SELECT COUNT(*) FROM {target.target_table} WHERE instrument_name = ?",
                        [name],
                    ).fetchone()[0]
            results.append(
                {
                    "instrument_name": name,
                    "status": display,
                    "job_id": result.job_id,
                    "since": since_map.get(name),
                    "clean_row_count": row_count,
                }
            )
    statuses = [r["status"] for r in results]
    overall = "COMPLETED" if all(s in {"COMPLETED", "EMPTY_RESPONSE"} for s in statuses) else "FAILED"
    return DeribitIncrementalRunReport(instrument_results=tuple(results), overall_status=overall)
