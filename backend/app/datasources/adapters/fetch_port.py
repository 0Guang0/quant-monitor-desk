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


class FetchPort(Protocol):
    def fetch_payload(self, req: FetchRequest) -> FetchPayload: ...


class StubFetchPort:
    def __init__(self, payload: bytes, *, file_type: str = "json") -> None:
        self._payload = payload
        self._file_type = file_type

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        return FetchPayload(content=self._payload, file_type=self._file_type)


class FailingPort:
    def __init__(self, status: PortErrorStatus, message: str) -> None:
        self._status = status
        self._message = message

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        raise PortError(self._status, self._message)


class UnpublishedPort:
    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        raise PortError("EMPTY_RESPONSE", "announcement not published yet")
