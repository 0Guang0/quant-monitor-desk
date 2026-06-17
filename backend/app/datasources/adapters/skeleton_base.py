"""Skeleton adapter base — FetchPort + RawStore + optional FileRegistry."""

from __future__ import annotations

from datetime import UTC, datetime

from backend.app.datasources.adapters.fetch_port import FetchPort, PortError
from backend.app.datasources.base_adapter import BaseDataAdapter, _utc_now_iso
from backend.app.datasources.fetch_result import FetchRequest, FetchResult
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.storage.file_registry import FileRegistry
from backend.app.storage.raw_store import RawStore


class SkeletonAdapterBase(BaseDataAdapter):
    def __init__(
        self,
        registry: SourceRegistry,
        *,
        raw_store: RawStore,
        fetch_port: FetchPort,
        file_registry: FileRegistry | None = None,
    ) -> None:
        super().__init__(registry)
        self._raw_store = raw_store
        self._fetch_port = fetch_port
        self._file_registry = file_registry

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

        saved = self._raw_store.save(
            payload.content,
            source=self.source_id,
            data_domain=req.data_domain,
            file_type=payload.file_type,
            as_of=as_of,
        )
        if self._file_registry is not None:
            self._file_registry.register(saved)

        return FetchResult(
            run_id=req.run_id,
            source_id=self.source_id,
            data_domain=req.data_domain,
            status="SUCCESS",
            row_count=1,
            fetch_time=fetch_time,
            raw_file_paths=[saved.local_path],
            content_hash=saved.content_hash,
            as_of_timestamp=as_of,
        )
