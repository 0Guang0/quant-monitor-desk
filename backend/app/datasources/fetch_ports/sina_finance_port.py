"""Sina Finance validation fetch port (R3H-03).

L3 greenfield: no EasyXT 1:1; mock/replay + conflict_evidence vs baostock primary.
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

_CONFLICT_EVIDENCE = {
    "primary_source_id": "baostock",
    "validation_source_id": "sina_finance",
    "conflict_role": "validation",
    "rule_set": "source_conflict_rules.yaml#market_bar_1d",
}


@dataclass(frozen=True)
class SinaFinanceMockFetchPort:
    symbols: Sequence[str]
    max_rows: int

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        return cn_validation_mock_fetch_payload(
            req,
            source_id="sina_finance",
            symbols=self.symbols,
            max_rows=self.max_rows,
            max_rows_cap=MAX_ROWS,
            max_symbols_cap=MAX_SYMBOLS,
            symbol_whitelist=SYMBOL_WHITELIST,
            bar_ohlcv=(1397.0, 1406.0, 1392.0, 1402.0, 700_000),
            conflict_evidence=_CONFLICT_EVIDENCE,
        )


def create_sina_finance_fetch_port(*, symbols: Sequence[str], max_rows: int):
    if len(symbols) > MAX_SYMBOLS:
        raise PortError("FAILED", f"max {MAX_SYMBOLS} symbols allowed, got {len(symbols)}")
    return SinaFinanceMockFetchPort(symbols=symbols, max_rows=max_rows)
