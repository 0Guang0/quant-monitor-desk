"""Base data adapter template (Batch A)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from time import perf_counter
from typing import Any

from backend.app.datasources.exceptions import SourceMismatchError
from backend.app.datasources.fetch_log import FetchLogWriter
from backend.app.datasources.fetch_result import FetchRequest, FetchResult
from backend.app.datasources.source_registry import (
    DomainDisabledError,
    DomainNotAllowedError,
    SourceDisabledError,
    SourceRegistry,
)


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class BaseDataAdapter(ABC):
    source_id: str
    supported_domains: frozenset[str]

    def __init__(self, registry: SourceRegistry) -> None:
        self.registry = registry
        self._log_writer = FetchLogWriter()

    def health_check(self) -> dict[str, Any]:
        """Contract stub: adapters may override; default reports registry reachability only."""
        return {
            "source_id": self.source_id,
            "status": "STUB_OK",
            "supported_domains": sorted(self.supported_domains),
            "registry_loaded": bool(self.registry._sources),
        }

    def fetch(
        self,
        req: FetchRequest,
        *,
        con,
        job_id: str | None = None,
        record_fetch_log: bool = True,
    ) -> FetchResult:
        if req.source_id != self.source_id:
            raise SourceMismatchError(
                f"request source_id {req.source_id!r} does not match "
                f"adapter source_id {self.source_id!r}"
            )
        try:
            self.registry.assert_domain_schedulable(req.data_domain)
        except DomainDisabledError as exc:
            result = FetchResult(
                run_id=req.run_id,
                source_id=self.source_id,
                data_domain=req.data_domain,
                status="DISABLED_SOURCE",
                fetch_time=_utc_now_iso(),
                error_message=str(exc),
            )
            if record_fetch_log:
                self._log_writer.write(
                    con,
                    result,
                    req=req,
                    job_id=job_id,
                    market_id=req.market_id,
                    instrument_id=req.instrument_id,
                )
            return result
        try:
            self.registry.assert_domain_allowed(req.source_id, req.data_domain)
            self.registry.assert_enabled(req.source_id)
        except (SourceDisabledError, DomainNotAllowedError) as exc:
            result = FetchResult(
                run_id=req.run_id,
                source_id=self.source_id,
                data_domain=req.data_domain,
                status="DISABLED_SOURCE",
                fetch_time=_utc_now_iso(),
                error_message=str(exc),
            )
            if record_fetch_log:
                self._log_writer.write(
                    con,
                    result,
                    req=req,
                    job_id=job_id,
                    market_id=req.market_id,
                    instrument_id=req.instrument_id,
                )
            return result
        if req.data_domain not in self.supported_domains:
            raise DomainNotAllowedError(
                f"adapter {self.source_id!r} does not support domain {req.data_domain!r}"
            )
        try:
            started = perf_counter()
            result = self._fetch_impl(req)
        except Exception as exc:
            result = FetchResult(
                run_id=req.run_id,
                source_id=self.source_id,
                data_domain=req.data_domain,
                status="FAILED",
                fetch_time=_utc_now_iso(),
                error_message=str(exc),
            )
        else:
            elapsed_ms = int((perf_counter() - started) * 1000)
            updates: dict = {"source_id": self.source_id}
            if result.latency_ms is None:
                updates["latency_ms"] = elapsed_ms
            result = result.model_copy(update=updates)

        if record_fetch_log:
            self._log_writer.write(
                con,
                result,
                req=req,
                job_id=job_id,
                market_id=req.market_id,
                instrument_id=req.instrument_id,
            )
        return result

    @abstractmethod
    def _fetch_impl(self, req: FetchRequest) -> FetchResult:
        """Subclass implements fetch logic; must not write fetch_log or clean tables."""
