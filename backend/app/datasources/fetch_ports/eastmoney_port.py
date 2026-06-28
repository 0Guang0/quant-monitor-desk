"""Eastmoney validation fetch port (R3H-03).

L3 greenfield: no EasyXT 1:1; mock/replay + conflict_evidence vs baostock primary.
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

_CONFLICT_EVIDENCE = {
    "primary_source_id": "baostock",
    "validation_source_id": "eastmoney",
    "conflict_role": "validation",
    "rule_set": "source_conflict_rules.yaml#market_bar_1d",
}


@dataclass(frozen=True)
class EastmoneyMockFetchPort:
    symbols: Sequence[str]
    max_rows: int

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        return cn_validation_mock_fetch_payload(
            req,
            source_id="eastmoney",
            symbols=self.symbols,
            max_rows=self.max_rows,
            max_rows_cap=MAX_ROWS,
            max_symbols_cap=MAX_SYMBOLS,
            symbol_whitelist=SYMBOL_WHITELIST,
            bar_ohlcv=(1398.0, 1407.0, 1393.0, 1403.0, 800_000),
            conflict_evidence=_CONFLICT_EVIDENCE,
        )


def create_eastmoney_fetch_port(*, symbols: Sequence[str], max_rows: int):
    if len(symbols) > MAX_SYMBOLS:
        raise PortError("FAILED", f"max {MAX_SYMBOLS} symbols allowed, got {len(symbols)}")
    return EastmoneyMockFetchPort(symbols=symbols, max_rows=max_rows)
