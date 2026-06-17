"""Data source adapters (Round 2)."""

from backend.app.datasources.adapters import create_adapter
from backend.app.datasources.base_adapter import BaseDataAdapter
from backend.app.datasources.exceptions import SourceMismatchError
from backend.app.datasources.fetch_log import FetchLogWriter
from backend.app.datasources.fetch_result import FetchRequest, FetchResult
from backend.app.datasources.source_registry import (
    DomainNotAllowedError,
    DomainRoleBinding,
    InvalidRegistryError,
    LegacyRoleError,
    SourceDisabledError,
    SourceNotFoundError,
    SourceRecord,
    SourceRegistry,
)

__all__ = [
    "BaseDataAdapter",
    "create_adapter",
    "DomainNotAllowedError",
    "DomainRoleBinding",
    "FetchLogWriter",
    "FetchRequest",
    "FetchResult",
    "InvalidRegistryError",
    "LegacyRoleError",
    "SourceDisabledError",
    "SourceMismatchError",
    "SourceNotFoundError",
    "SourceRecord",
    "SourceRegistry",
]
