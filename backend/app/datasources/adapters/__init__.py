"""Vendor adapter skeletons (Round 2 Batch B)."""

from __future__ import annotations

from pathlib import Path

from backend.app.datasources.adapters.akshare import AkshareAdapter
from backend.app.datasources.adapters.baostock import BaostockAdapter
from backend.app.datasources.adapters.cninfo import CninfoAdapter
from backend.app.datasources.adapters.fetch_port import FetchPort, StubFetchPort
from backend.app.datasources.adapters.qmt_xtdata import QmtXtdataAdapter
from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase
from backend.app.datasources.adapters.tdx_pytdx import TdxPytdxAdapter
from backend.app.datasources.adapters.yahoo_finance import YahooFinanceAdapter, create_yahoo_finance_fetch_port
from backend.app.datasources.base_adapter import BaseDataAdapter
from backend.app.datasources.exceptions import (
    AdapterConfigurationError,
    AdapterNotSupportedError,
)
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.storage.file_registry import FileRegistry
from backend.app.storage.raw_store import RawStore

_ADAPTER_TYPES: dict[str, type[SkeletonAdapterBase]] = {
    "qmt_xtdata": QmtXtdataAdapter,
    "baostock": BaostockAdapter,
    "akshare": AkshareAdapter,
    "cninfo": CninfoAdapter,
    "yahoo_finance": YahooFinanceAdapter,
    "tdx_pytdx": TdxPytdxAdapter,
}


def _build_adapter(
    source_id: str,
    registry: SourceRegistry,
    data_root: Path,
    *,
    fetch_port: FetchPort,
    file_registry: FileRegistry | None,
    require_file_registry: bool,
    max_payload_bytes: int | None = None,
) -> BaseDataAdapter:
    if require_file_registry and file_registry is None:
        raise AdapterConfigurationError(
            f"file_registry is required for source_id={source_id!r}; "
            "inject FileRegistry for production evidence indexing"
        )
    adapter_cls = _ADAPTER_TYPES.get(source_id)
    if adapter_cls is None:
        raise AdapterNotSupportedError(source_id, tuple(_ADAPTER_TYPES.keys()))
    raw_store = RawStore(data_root)
    kwargs: dict = {
        "registry": registry,
        "raw_store": raw_store,
        "fetch_port": fetch_port,
        "file_registry": file_registry,
    }
    if max_payload_bytes is not None:
        kwargs["max_payload_bytes"] = max_payload_bytes
    return adapter_cls(**kwargs)


def create_fetch_port_for_source(source_id: str) -> FetchPort:
    """Return the default mock-first L2 fetch port for R3H-02 market sources."""
    if source_id == "yahoo_finance":
        return create_yahoo_finance_fetch_port(symbols=("AAPL",), max_rows=500)
    raise AdapterNotSupportedError(source_id, ("yahoo_finance",))


def create_adapter(
    source_id: str,
    registry: SourceRegistry,
    data_root: Path,
    *,
    fetch_port: FetchPort | None = None,
    file_registry: FileRegistry | None = None,
    max_payload_bytes: int | None = None,
) -> BaseDataAdapter:
    """Production factory — requires explicit FetchPort and FileRegistry."""
    if fetch_port is None:
        raise AdapterConfigurationError(
            f"fetch_port is required for source_id={source_id!r}; "
            "use StubFetchPort explicitly in tests via create_test_adapter()"
        )
    return _build_adapter(
        source_id,
        registry,
        data_root,
        fetch_port=fetch_port,
        file_registry=file_registry,
        require_file_registry=True,
        max_payload_bytes=max_payload_bytes,
    )


def create_test_adapter(
    source_id: str,
    registry: SourceRegistry,
    data_root: Path,
    *,
    fetch_port: FetchPort | None = None,
    file_registry: FileRegistry | None = None,
    require_file_registry: bool = False,
    max_payload_bytes: int | None = None,
) -> BaseDataAdapter:
    """Test factory — defaults StubFetchPort; FileRegistry optional unless required."""
    port = fetch_port if fetch_port is not None else StubFetchPort(payload=b"{}")
    return _build_adapter(
        source_id,
        registry,
        data_root,
        fetch_port=port,
        file_registry=file_registry,
        require_file_registry=require_file_registry,
        max_payload_bytes=max_payload_bytes,
    )


__all__ = [
    "AkshareAdapter",
    "BaostockAdapter",
    "CninfoAdapter",
    "QmtXtdataAdapter",
    "YahooFinanceAdapter",
    "TdxPytdxAdapter",
    "AdapterConfigurationError",
    "AdapterNotSupportedError",
    "create_adapter",
    "create_fetch_port_for_source",
    "create_test_adapter",
    "create_yahoo_finance_fetch_port",
]
