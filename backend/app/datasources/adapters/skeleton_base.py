"""Skeleton adapter base — FetchPort + RawStore + optional FileRegistry."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from backend.app.datasources.adapters.fetch_port import FetchPayload, FetchPort, PortError
from backend.app.datasources.base_adapter import BaseDataAdapter, _utc_now_iso
from backend.app.datasources.fetch_result import FetchRequest, FetchResult
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.storage.file_registry import FileRegistry
from backend.app.storage.raw_store import RawStore

DEFAULT_MAX_PAYLOAD_BYTES = 10 * 1024 * 1024


def _infer_schema_hash(payload: FetchPayload) -> str | None:
    if payload.schema_hash is not None:
        return payload.schema_hash
    if payload.file_type != "json":
        return None
    try:
        obj = json.loads(payload.content)
        if isinstance(obj, dict):
            keys_json = json.dumps(sorted(obj.keys()), separators=(",", ":"))
            return hashlib.sha256(keys_json.encode()).hexdigest()
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return None


class SkeletonAdapterBase(BaseDataAdapter):
    def __init__(
        self,
        registry: SourceRegistry,
        *,
        raw_store: RawStore,
        fetch_port: FetchPort,
        file_registry: FileRegistry | None = None,
        max_payload_bytes: int = DEFAULT_MAX_PAYLOAD_BYTES,
    ) -> None:
        super().__init__(registry)
        self._raw_store = raw_store
        self._fetch_port = fetch_port
        self._file_registry = file_registry
        self._max_payload_bytes = max_payload_bytes

    def _resolve_as_of(self, req: FetchRequest) -> str:
        if req.end_time:
            return req.end_time[:10]
        return datetime.now(UTC).strftime("%Y-%m-%d")

    def _fetch_impl(self, req: FetchRequest) -> FetchResult:
        fetch_time = _utc_now_iso()
        as_of = self._resolve_as_of(req)
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

        if len(payload.content) > self._max_payload_bytes:
            return FetchResult(
                run_id=req.run_id,
                source_id=self.source_id,
                data_domain=req.data_domain,
                status="FAILED",
                row_count=0,
                fetch_time=fetch_time,
                error_message=(
                    f"payload too large ({len(payload.content)} > "
                    f"{self._max_payload_bytes} bytes)"
                ),
            )

        saved = self._raw_store.save(
            payload.content,
            source=self.source_id,
            data_domain=req.data_domain,
            file_type=payload.file_type,
            as_of=as_of,
        )
        if self._file_registry is not None:
            self._file_registry.register(saved)

        row_count = payload.row_count if payload.row_count is not None else 1
        return FetchResult(
            run_id=req.run_id,
            source_id=self.source_id,
            data_domain=req.data_domain,
            status="SUCCESS",
            row_count=row_count,
            fetch_time=fetch_time,
            raw_file_paths=[saved.local_path],
            content_hash=saved.content_hash,
            schema_hash=_infer_schema_hash(payload),
            as_of_timestamp=as_of,
            latency_ms=payload.latency_ms,
            retry_count=payload.retry_count,
        )
