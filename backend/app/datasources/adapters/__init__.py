"""Vendor adapter skeletons (Round 2 Batch B)."""

from __future__ import annotations

from pathlib import Path

from backend.app.datasources.adapters.akshare import AkshareAdapter
from backend.app.datasources.adapters.baostock import BaostockAdapter
from backend.app.datasources.adapters.cninfo import CninfoAdapter
from backend.app.datasources.adapters.fetch_port import FetchPort, StubFetchPort
from backend.app.datasources.adapters.qmt_xtdata import QmtXtdataAdapter
from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase
from backend.app.datasources.adapters.yahoo_finance import YahooFinanceAdapter
from backend.app.datasources.base_adapter import BaseDataAdapter
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.storage.file_registry import FileRegistry
from backend.app.storage.raw_store import RawStore

_ADAPTER_TYPES: dict[str, type[SkeletonAdapterBase]] = {
    "qmt_xtdata": QmtXtdataAdapter,
    "baostock": BaostockAdapter,
    "akshare": AkshareAdapter,
    "cninfo": CninfoAdapter,
    "yahoo_finance": YahooFinanceAdapter,
}


def create_adapter(
    source_id: str,
    registry: SourceRegistry,
    data_root: Path,
    *,
    fetch_port: FetchPort | None = None,
    file_registry: FileRegistry | None = None,
) -> BaseDataAdapter:
    adapter_cls = _ADAPTER_TYPES.get(source_id)
    if adapter_cls is None:
        raise KeyError(source_id)
    raw_store = RawStore(data_root)
    port = fetch_port if fetch_port is not None else StubFetchPort(payload=b"{}")
    return adapter_cls(
        registry,
        raw_store=raw_store,
        fetch_port=port,
        file_registry=file_registry,
    )


__all__ = [
    "AkshareAdapter",
    "BaostockAdapter",
    "CninfoAdapter",
    "QmtXtdataAdapter",
    "YahooFinanceAdapter",
    "create_adapter",
]
