"""QMT xqshare remote terminal fetch port (R3H-03).

L2 migrate from qmt_xtdata auth-gated pattern; user Grill-me Q8 — implemented (no ADR).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from backend.app.datasources.adapters.fetch_port import PortError, FetchPayload
from backend.app.datasources.fetch_ports.qmt_mock_common import (
    MAX_ROWS,
    MAX_SYMBOLS,
    qmt_mock_fetch_payload,
)
from backend.app.datasources.fetch_result import FetchRequest


@dataclass(frozen=True)
class QmtXqshareMockFetchPort:
    symbols: Sequence[str]
    max_rows: int

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        return qmt_mock_fetch_payload(
            req,
            source_id="qmt_xqshare",
            symbols=self.symbols,
            max_rows=self.max_rows,
            bar_ohlcv=(1402.0, 1412.0, 1397.0, 1407.0, 550_000),
        )


def create_qmt_xqshare_fetch_port(*, symbols: Sequence[str], max_rows: int):
    if len(symbols) > MAX_SYMBOLS:
        raise PortError("FAILED", f"max {MAX_SYMBOLS} symbols allowed, got {len(symbols)}")
    return QmtXqshareMockFetchPort(symbols=symbols, max_rows=max_rows)
