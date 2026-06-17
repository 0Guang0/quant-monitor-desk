"""Base data adapter template (Batch A)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime

from backend.app.datasources.exceptions import SourceMismatchError
from backend.app.datasources.fetch_log import FetchLogWriter
from backend.app.datasources.fetch_result import FetchRequest, FetchResult
from backend.app.datasources.source_registry import DomainNotAllowedError, SourceRegistry


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class BaseDataAdapter(ABC):
    source_id: str
    supported_domains: frozenset[str]

    def __init__(self, registry: SourceRegistry) -> None:
        self.registry = registry
        self._log_writer = FetchLogWriter()

    def fetch(
        self,
        req: FetchRequest,
        *,
        con,
        job_id: str | None = None,
    ) -> FetchResult:
        if req.source_id != self.source_id:
            raise SourceMismatchError(
                f"request source_id {req.source_id!r} does not match "
                f"adapter source_id {self.source_id!r}"
            )
        self.registry.assert_enabled(req.source_id)
        self.registry.assert_domain_allowed(req.source_id, req.data_domain)
        if req.data_domain not in self.supported_domains:
            raise DomainNotAllowedError(
                f"adapter {self.source_id!r} does not support domain {req.data_domain!r}"
            )
        try:
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
            result = result.model_copy(update={"source_id": self.source_id})

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
