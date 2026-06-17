"""FetchRequest / FetchResult Pydantic models (Batch A adapter contract)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

FetchStatus = Literal[
    "SUCCESS",
    "EMPTY_RESPONSE",
    "AUTH_FAILED",
    "RATE_LIMITED",
    "NETWORK_ERROR",
    "SCHEMA_DRIFT",
    "FAILED",
]


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
    row_count: int = 0
    content_hash: str | None = None
    schema_hash: str | None = None
    as_of_timestamp: str | None = None
    publish_timestamp: str | None = None
    fetch_time: str
    error_message: str | None = None
