"""CNINFO metadata incremental orchestration (R3-DCP-05 S07)."""

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
from backend.app.ops.cninfo_incremental_watermark import STAGING_TABLE, read_since_date_for_instrument
from backend.app.ops.macro_incremental_common import (
    incremental_evidence_as_of,
    incremental_validation_patch_factory,
    load_incremental_route_bundle,
    persist_incremental_fetch_payload,
)
from backend.app.ops.sandbox_clean_write.clean_write_targets import resolve_clean_write_target
from backend.app.storage.raw_store import RawStore
from backend.app.sync.jobs import SyncJobSpec
from backend.app.sync.orchestrator import DataSyncOrchestrator

DISCLOSURE_STAGING_COLUMNS = (
    "announcement_id",
    "instrument_id",
    "title",
    "publish_timestamp",
    "announcement_url",
    "announcement_type",
    "data_domain",
    "source_used",
    "pdf_file_id",
    "extracted_text_file_id",
    "content_status",
    "batch_id",
    "source_fetch_id",
    "content_hash",
    "schema_hash",
    "quality_flags",
    "created_at",
)
DISCLOSURE_REQUIRED_FIELDS = ("title", "source_used", "content_status")
_WATERMARK_EMPTY_MSG = "no filings after metadata watermark window"
_DEFAULT_SYMBOL = "sh.600519"


def _parse_publish_ts(raw: object) -> datetime:
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=UTC)
    text = str(raw or "")
    if not text:
        return datetime.now(UTC)
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def cninfo_staging_rows_from_bundle(
    bundle: dict[str, Any],
    *,
    instrument_id: str,
    start_date: str | None = None,
) -> list[dict[str, object]]:
    """Map cn_market_evidence_v1 filings → stg_disclosure_smoke rows."""
    now = datetime.now(UTC)
    content_hash = str(bundle.get("content_hash") or "cninfo-hash")
    schema_hash = str(bundle.get("schema_hash") or "cninfo-schema")
    source_fetch_id = str(bundle.get("source_fetch_id") or "cninfo-unknown")
    rows: list[dict[str, object]] = []
    for filing in bundle.get("filings") or []:
        obs_date = str(filing.get("observation_date") or filing.get("publish_timestamp") or "")[:10]
        if not obs_date:
            continue
        if start_date and obs_date < start_date:
            continue
        announcement_id = str(
            filing.get("filing_id") or filing.get("announcement_id") or filing.get("id") or ""
        )
        if not announcement_id:
            continue
        rows.append(
            {
                "announcement_id": announcement_id,
                "instrument_id": str(filing.get("instrument_id") or instrument_id),
                "title": str(filing.get("title") or ""),
                "publish_timestamp": _parse_publish_ts(filing.get("publish_timestamp") or obs_date),
                "announcement_url": filing.get("url"),
                "announcement_type": filing.get("announcement_type"),
                "data_domain": str(bundle.get("data_domain") or "cn_announcements"),
                "source_used": str(filing.get("source_used") or bundle.get("source_id") or "cninfo"),
                "pdf_file_id": None,
                "extracted_text_file_id": None,
                "content_status": "metadata_only",
                "batch_id": "incremental",
                "source_fetch_id": source_fetch_id,
                "content_hash": content_hash,
                "schema_hash": schema_hash,
                "quality_flags": "INCREMENTAL",
                "created_at": now,
            }
        )
    return rows


def _make_cninfo_staging_adapter_class():
    class CninfoMetadataStagingAdapter(SkeletonAdapterBase):
        source_id = "cninfo"
        supported_domains = frozenset({"cn_announcements"})

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
                    error_message=f"invalid cn market evidence JSON: {exc}",
                )
            rows = cninfo_staging_rows_from_bundle(
                bundle,
                instrument_id=req.instrument_id or _DEFAULT_SYMBOL,
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
            col_list = ", ".join(DISCLOSURE_STAGING_COLUMNS)
            placeholders = ", ".join("?" for _ in DISCLOSURE_STAGING_COLUMNS)
            for row in rows:
                con.execute(
                    f"INSERT INTO {STAGING_TABLE} ({col_list}) VALUES ({placeholders})",
                    [row[col] for col in DISCLOSURE_STAGING_COLUMNS],
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

    return CninfoMetadataStagingAdapter


@contextmanager
def _cninfo_incremental_validation_patch():
    """ponytail: bar-domain validate_staging defaults until track A branches by staging table."""
    with incremental_validation_patch_factory(
        DISCLOSURE_STAGING_COLUMNS,
        ("publish_timestamp",),
        label="cninfo",
    ):
        yield


@contextmanager
def _cninfo_staging_adapter_patch(fetch_port: FetchPort):
    import backend.app.datasources.adapters as adapters_mod

    staging_cls = _make_cninfo_staging_adapter_class()
    original = adapters_mod.create_test_adapter

    def factory(source_id: str, registry, data_root: Path, **kwargs):
        if source_id == "cninfo":
            port = kwargs.get("fetch_port") or fetch_port
            return staging_cls(registry, raw_store=RawStore(data_root), fetch_port=port)
        return original(source_id, registry, data_root, **kwargs)

    adapters_mod.create_test_adapter = factory
    try:
        yield
    finally:
        adapters_mod.create_test_adapter = original


class CninfoIncrementalFetchProxy:
    def __init__(self, inner: DataSourceService, since_by_instrument: dict[str, str]) -> None:
        self._inner = inner
        self._since = since_by_instrument

    def __getattr__(self, name: str):
        return getattr(self._inner, name)

    def fetch(self, req: FetchRequest, **kwargs):
        since = self._since.get(req.instrument_id or "")
        if since:
            req = req.model_copy(update={"start_time": since})
        kwargs["operation"] = "fetch_announcement_index"
        return self._inner.fetch(req, **kwargs)


@dataclass(frozen=True)
class CninfoIncrementalRunReport:
    instrument_results: tuple[dict[str, Any], ...]
    overall_status: str


def build_cninfo_incremental_service(
    *,
    data_root: Path,
    fetch_port: FetchPort,
    since_by_instrument: dict[str, str],
    job_events=None,
    source_registry=None,
) -> CninfoIncrementalFetchProxy:
    registry, caps, planner = load_incremental_route_bundle(
        source_id="cninfo",
        data_domain="cn_announcements",
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
    return CninfoIncrementalFetchProxy(inner, since_by_instrument)


def _display_status(result) -> str:
    if result.status != "FAILED_FINAL":
        return result.status
    msg = result.message or ""
    if msg.startswith(_WATERMARK_EMPTY_MSG):
        return "EMPTY_RESPONSE"
    return result.status


def run_cninfo_incremental(
    orch: DataSyncOrchestrator,
    *,
    service: CninfoIncrementalFetchProxy,
    symbols: tuple[str, ...] = (_DEFAULT_SYMBOL,),
    source_registry=None,
) -> CninfoIncrementalRunReport:
    target = resolve_clean_write_target("cn_announcements")
    cm = orch._jobs.connection_manager
    results: list[dict[str, Any]] = []
    fetch_port = service._inner._fetch_port  # noqa: SLF001
    with cm.writer() as con:
        since_map = {sym: read_since_date_for_instrument(con, sym) for sym in symbols}
    proxy = build_cninfo_incremental_service(
        data_root=service._inner._data_root,  # noqa: SLF001
        fetch_port=fetch_port,
        since_by_instrument=since_map,
        job_events=orch._jobs,
        source_registry=source_registry,
    )
    with _cninfo_staging_adapter_patch(fetch_port), _cninfo_incremental_validation_patch():
        for symbol in symbols:
            spec = SyncJobSpec(
                run_id=f"cninfo-inc-{symbol}-{uuid.uuid4().hex[:8]}",
                job_id=f"job-cninfo-inc-{symbol}-{uuid.uuid4().hex[:8]}",
                job_type="incremental",
                data_domain="cn_announcements",
                market_id="CN_A",
                source_id="cninfo",
                adapter_id="cninfo",
                date_start=None,
                date_end=None,
                instrument_id=symbol,
                partition_key=None,
                trigger_reason="cninfo_metadata_incremental",
            )
            result = orch.run_incremental(
                spec,
                datasource_service=proxy,
                clean_table=target.target_table,
                write_mode=target.write_mode,
                primary_keys=target.primary_keys,
                required_fields=DISCLOSURE_REQUIRED_FIELDS,
            )
            display = _display_status(result)
            row_count = 0
            if display == "COMPLETED":
                with cm.writer() as con:
                    row_count = con.execute(
                        f"SELECT COUNT(*) FROM {target.target_table} WHERE instrument_id = ?",
                        [symbol],
                    ).fetchone()[0]
            results.append(
                {
                    "instrument_id": symbol,
                    "status": display,
                    "job_id": result.job_id,
                    "since": since_map.get(symbol),
                    "clean_row_count": row_count,
                }
            )
    statuses = [r["status"] for r in results]
    overall = "COMPLETED" if all(s in {"COMPLETED", "EMPTY_RESPONSE"} for s in statuses) else "FAILED"
    return CninfoIncrementalRunReport(instrument_results=tuple(results), overall_status=overall)
