"""FetchPort protocol and test doubles (Batch B)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from backend.app.datasources.fetch_result import FetchRequest

PortErrorStatus = Literal[
    "AUTH_FAILED",
    "RATE_LIMITED",
    "NETWORK_ERROR",
    "SCHEMA_DRIFT",
    "EMPTY_RESPONSE",
    "NOT_PUBLISHED_YET",
    "FAILED",
]


class PortError(Exception):
    status: PortErrorStatus
    message: str

    def __init__(self, status: PortErrorStatus, message: str) -> None:
        self.status = status
        self.message = message
        super().__init__(message)


@dataclass(frozen=True)
class FetchPayload:
    content: bytes
    file_type: str = "json"
    row_count: int | None = None
    schema_hash: str | None = None
    latency_ms: int | None = None
    retry_count: int = 0


class FetchPort(Protocol):
    def fetch_payload(self, req: FetchRequest) -> FetchPayload: ...


class StubFetchPort:
    def __init__(
        self,
        payload: bytes,
        *,
        file_type: str = "json",
        row_count: int | None = None,
        schema_hash: str | None = None,
        latency_ms: int | None = None,
        retry_count: int = 0,
    ) -> None:
        self._payload = payload
        self._file_type = file_type
        self._row_count = row_count
        self._schema_hash = schema_hash
        self._latency_ms = latency_ms
        self._retry_count = retry_count

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        return FetchPayload(
            content=self._payload,
            file_type=self._file_type,
            row_count=self._row_count,
            schema_hash=self._schema_hash,
            latency_ms=self._latency_ms,
            retry_count=self._retry_count,
        )


class FailingPort:
    def __init__(self, status: PortErrorStatus, message: str) -> None:
        self._status = status
        self._message = message

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        raise PortError(self._status, self._message)


class UnpublishedPort:
    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        raise PortError("NOT_PUBLISHED_YET", "announcement not published yet")
