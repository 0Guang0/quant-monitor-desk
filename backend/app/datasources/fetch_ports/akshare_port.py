"""AkShare validation-only CN equity fetch port (R3H-03).

L2 migrate from backend/app/datasources/adapters/akshare.py validation skeleton;
permanent validation_only — no primary elevation.
See R3H_03_REFERENCE_ADOPTION_AUDIT.md.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from backend.app.datasources.adapters.fetch_port import PortError, FetchPayload
from backend.app.datasources.fetch_ports.cn_validation_mock import cn_validation_mock_fetch_payload
from backend.app.datasources.fetch_result import FetchRequest

MAX_SYMBOLS = 3
MAX_ROWS = 200
SYMBOL_WHITELIST = frozenset({"sh.600519", "sz.000001"})


@dataclass(frozen=True)
class AkshareMockFetchPort:
    symbols: Sequence[str]
    max_rows: int

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        return cn_validation_mock_fetch_payload(
            req,
            source_id="akshare",
            symbols=self.symbols,
            max_rows=self.max_rows,
            max_rows_cap=MAX_ROWS,
            max_symbols_cap=MAX_SYMBOLS,
            symbol_whitelist=SYMBOL_WHITELIST,
            bar_ohlcv=(1399.0, 1408.0, 1394.0, 1404.0, 900_000),
        )


def create_akshare_fetch_port(*, symbols: Sequence[str], max_rows: int, use_mock: bool = True):
    if len(symbols) > MAX_SYMBOLS:
        raise PortError("FAILED", f"max {MAX_SYMBOLS} symbols allowed, got {len(symbols)}")
    if use_mock:
        return AkshareMockFetchPort(symbols=symbols, max_rows=max_rows)
    from backend.app.datasources.fetch_ports.tier_b_validation_live import AkshareLiveFetchPort
    from backend.app.datasources.product_live_gate import gate_live_fetch_port

    gate_live_fetch_port(source_id="akshare")
    return AkshareLiveFetchPort(symbols=symbols, max_rows=max_rows)
