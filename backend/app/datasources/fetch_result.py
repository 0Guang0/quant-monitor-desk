"""FetchRequest / FetchResult Pydantic models (Batch A adapter contract)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

FetchStatus = Literal[
    "SUCCESS",
    "EMPTY_RESPONSE",
    "NOT_PUBLISHED_YET",
    "AUTH_FAILED",
    "RATE_LIMITED",
    "NETWORK_ERROR",
    "SCHEMA_DRIFT",
    "FAILED",
]

_FAILURE_STATUSES = frozenset({
    "AUTH_FAILED",
    "RATE_LIMITED",
    "NETWORK_ERROR",
    "SCHEMA_DRIFT",
    "FAILED",
})

_NO_EVIDENCE_STATUSES = frozenset({"EMPTY_RESPONSE", "NOT_PUBLISHED_YET"})


class FetchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    source_id: str
    data_domain: str
    market_id: str | None = None
    instrument_id: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    cursor: str | None = None
    force_refresh: bool = False


class FetchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    source_id: str
    data_domain: str
    status: FetchStatus
    raw_file_paths: list[str] = Field(default_factory=list)
    staging_table: str | None = None
    row_count: int = Field(default=0, ge=0)
    content_hash: str | None = None
    schema_hash: str | None = None
    as_of_timestamp: str | None = None
    publish_timestamp: str | None = None
    fetch_time: str
    error_message: str | None = None
    latency_ms: int | None = Field(default=None, ge=0)
    retry_count: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_status_contract(self) -> FetchResult:
        if self.status == "SUCCESS":
            if self.row_count <= 0:
                raise ValueError("SUCCESS requires row_count > 0")
            if not self.raw_file_paths and not self.staging_table:
                raise ValueError("SUCCESS requires raw_file_paths or staging_table")
        elif self.status in _NO_EVIDENCE_STATUSES:
            if self.row_count != 0:
                raise ValueError(f"{self.status} requires row_count == 0")
            if self.raw_file_paths or self.staging_table:
                raise ValueError(f"{self.status} must not carry raw/staging evidence")
        elif self.status in _FAILURE_STATUSES:
            if not self.error_message:
                raise ValueError(f"{self.status} requires error_message")
        if not self.fetch_time or not self.fetch_time.strip():
            raise ValueError("fetch_time must be non-empty")
        return self
