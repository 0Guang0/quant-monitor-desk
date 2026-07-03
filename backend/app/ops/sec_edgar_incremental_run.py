"""SEC EDGAR incremental orchestration (R3-DCP-05 S09)."""

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
from backend.app.datasources.fetch_result import FetchResult
from backend.app.datasources.service import DataSourceService
from backend.app.ops.macro_incremental_common import (
    MacroIncrementalFetchProxy,
    _normalize_incremental_job_status,
    incremental_evidence_as_of,
    incremental_validation_patch_factory,
    load_incremental_route_bundle,
    persist_incremental_fetch_payload,
)
from backend.app.ops.sandbox_clean_write.clean_write_targets import resolve_clean_write_target
from backend.app.ops.sec_edgar_incremental_watermark import (
    STAGING_TABLE,
    read_filing_date_watermark,
    read_since_date_for_cik,
)
from backend.app.storage.raw_store import RawStore
from backend.app.sync.jobs import SyncJobSpec
from backend.app.sync.orchestrator import DataSyncOrchestrator

US_DISCLOSURE_STAGING_COLUMNS = (
    "accession_number",
    "cik",
    "form_type",
    "filing_date",
    "report_date",
    "primary_document_url",
    "data_domain",
    "source_used",
    "batch_id",
    "source_fetch_id",
    "content_hash",
    "schema_hash",
    "quality_flags",
    "created_at",
)
DISCLOSURE_REQUIRED_FIELDS = ("form_type", "filing_date", "source_used")
_WATERMARK_EMPTY_MSG = "no filings after sec_edgar watermark window"
_DEFAULT_CIK = "0000320193"


def us_disclosure_staging_rows_from_bundle(
    bundle: dict[str, Any],
    *,
    cik: str,
    start_date: str | None = None,
    cold_start_fallback: bool = False,
) -> list[dict[str, object]]:
    now = datetime.now(UTC)
    content_hash = str(bundle.get("content_hash") or "sec-edgar-hash")
    schema_hash = str(bundle.get("schema_hash") or "sec-edgar-schema")
    source_fetch_id = str(bundle.get("source_fetch_id") or "sec-edgar-unknown")
    rows: list[dict[str, object]] = []
    for filing in bundle.get("filings") or []:
        filing_date = str(filing.get("filing_date") or "")
        if not filing_date:
            continue
        if start_date and filing_date < start_date:
            continue
        accession = str(filing.get("accession_number") or "")
        if not accession:
            continue
        report_date = str(filing.get("report_date") or filing_date)
        rows.append(
            {
                "accession_number": accession,
                "cik": str(filing.get("cik") or cik),
                "form_type": str(filing.get("form_type") or ""),
                "filing_date": date.fromisoformat(filing_date[:10]),
                "report_date": date.fromisoformat(report_date[:10]),
                "primary_document_url": str(filing.get("primary_document_url") or ""),
                "data_domain": str(bundle.get("data_domain") or "us_filings"),
                "source_used": str(filing.get("source_used") or "sec_edgar"),
                "batch_id": "incremental",
                "source_fetch_id": source_fetch_id,
                "content_hash": content_hash,
                "schema_hash": schema_hash,
                "quality_flags": "INCREMENTAL",
                "created_at": now,
            }
        )
    if not rows and cold_start_fallback and start_date and bundle.get("filings"):
        return us_disclosure_staging_rows_from_bundle(
            bundle, cik=cik, start_date=None, cold_start_fallback=False
        )[:3]
    return rows


def _make_sec_edgar_staging_adapter_class():
    class SecEdgarStagingAdapter(SkeletonAdapterBase):
        source_id = "sec_edgar"
        supported_domains = frozenset({"us_filings"})

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
                    error_message=f"invalid sec edgar evidence JSON: {exc}",
                )
            cik = req.instrument_id or _DEFAULT_CIK
            cold_start = read_filing_date_watermark(con, cik) is None
            rows = us_disclosure_staging_rows_from_bundle(
                bundle,
                cik=cik,
                start_date=req.start_time[:10] if req.start_time else None,
                cold_start_fallback=cold_start,
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
            col_list = ", ".join(US_DISCLOSURE_STAGING_COLUMNS)
            placeholders = ", ".join("?" for _ in US_DISCLOSURE_STAGING_COLUMNS)
            for row in rows:
                con.execute(
                    f"INSERT INTO {STAGING_TABLE} ({col_list}) VALUES ({placeholders})",
                    [row[col] for col in US_DISCLOSURE_STAGING_COLUMNS],
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

    return SecEdgarStagingAdapter


@contextmanager
def _sec_edgar_incremental_validation_patch():
    with incremental_validation_patch_factory(
        US_DISCLOSURE_STAGING_COLUMNS,
        ("filing_date", "report_date"),
        label="sec_edgar",
    ):
        yield


@contextmanager
def _sec_edgar_staging_adapter_patch(fetch_port: FetchPort):
    import backend.app.datasources.adapters as adapters_mod

    staging_cls = _make_sec_edgar_staging_adapter_class()
    original = adapters_mod.create_test_adapter

    def factory(source_id: str, registry, data_root: Path, **kwargs):
        if source_id == "sec_edgar":
            port = kwargs.get("fetch_port") or fetch_port
            return staging_cls(registry, raw_store=RawStore(data_root), fetch_port=port)
        return original(source_id, registry, data_root, **kwargs)

    adapters_mod.create_test_adapter = factory
    try:
        yield
    finally:
        adapters_mod.create_test_adapter = original


@dataclass(frozen=True)
class SecEdgarIncrementalRunReport:
    cik_results: tuple[dict[str, Any], ...]
    overall_status: str


def build_sec_edgar_incremental_service(
    *,
    data_root: Path,
    fetch_port: FetchPort,
    since_by_cik: dict[str, str],
    job_events=None,
    source_registry=None,
) -> MacroIncrementalFetchProxy:
    registry, caps, planner = load_incremental_route_bundle(
        source_id="sec_edgar",
        data_domain="us_filings",
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
    return MacroIncrementalFetchProxy(inner, since_by_cik, operation="fetch_filings")


def _display_status(result) -> str:
    return _normalize_incremental_job_status(result)


def run_sec_edgar_incremental(
    orch: DataSyncOrchestrator,
    *,
    service: MacroIncrementalFetchProxy,
    ciks: tuple[str, ...] = (_DEFAULT_CIK,),
    source_registry=None,
) -> SecEdgarIncrementalRunReport:
    target = resolve_clean_write_target("us_filings")
    cm = orch._jobs.connection_manager
    results: list[dict[str, Any]] = []
    fetch_port = service._inner._fetch_port  # noqa: SLF001
    with cm.writer() as con:
        since_map = {cik: read_since_date_for_cik(con, cik) for cik in ciks}
    proxy = build_sec_edgar_incremental_service(
        data_root=service._inner._data_root,  # noqa: SLF001
        fetch_port=fetch_port,
        since_by_cik=since_map,
        job_events=orch._jobs,
        source_registry=source_registry,
    )
    with _sec_edgar_staging_adapter_patch(fetch_port), _sec_edgar_incremental_validation_patch():
        for cik in ciks:
            spec = SyncJobSpec(
                run_id=f"sec-edgar-inc-{cik}-{uuid.uuid4().hex[:8]}",
                job_id=f"job-sec-edgar-inc-{cik}-{uuid.uuid4().hex[:8]}",
                job_type="incremental",
                data_domain="us_filings",
                market_id="US",
                source_id="sec_edgar",
                adapter_id="sec_edgar",
                date_start=None,
                date_end=None,
                instrument_id=cik,
                partition_key=None,
                trigger_reason="sec_edgar_incremental",
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
                        f"SELECT COUNT(*) FROM {target.target_table} WHERE cik = ?",
                        [cik],
                    ).fetchone()[0]
            results.append(
                {
                    "cik": cik,
                    "status": display,
                    "job_id": result.job_id,
                    "since": since_map.get(cik),
                    "clean_row_count": row_count,
                }
            )
    statuses = [r["status"] for r in results]
    overall = (
        "COMPLETED"
        if all(s in {"COMPLETED", "EMPTY_RESPONSE"} for s in statuses)
        else "NETWORK_ERROR"
        if statuses and all(s in {"COMPLETED", "EMPTY_RESPONSE", "NETWORK_ERROR"} for s in statuses)
        and any(s == "NETWORK_ERROR" for s in statuses)
        else "FAILED"
    )
    return SecEdgarIncrementalRunReport(cik_results=tuple(results), overall_status=overall)
