"""Storage ports for datasource adapters — decouple adapters from concrete storage."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class RawEvidenceStore(Protocol):
    """Minimal raw evidence write contract used by adapter skeletons."""

    def write_raw(
        self,
        *,
        source_id: str,
        data_domain: str,
        as_of: str,
        content: bytes,
        file_type: str = "json",
    ) -> Path: ...


class FileRegistryPort(Protocol):
    """Minimal file registry contract for evidence indexing."""

    def register(
        self,
        *,
        local_path: str,
        content_hash: str,
        source: str,
        file_type: str,
        as_of_timestamp: str | None = None,
    ) -> str: ...
