"""QMT xtdata authorization-gated fetch port (R3H-03).

L2 migrate from backend/app/datasources/adapters/qmt_xtdata.py skeleton; license_gate default DISABLED.
See R3H_03_REFERENCE_ADOPTION_AUDIT.md.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from backend.app.datasources.adapters.fetch_port import PortError, FetchPayload
from backend.app.datasources.fetch_ports.qmt_mock_common import (
    MAX_ROWS,
    MAX_SYMBOLS,
    MINUTE_BARS_ENABLED,
    qmt_mock_fetch_payload,
)
from backend.app.datasources.fetch_result import FetchRequest


@dataclass(frozen=True)
class QmtXtdataMockFetchPort:
    symbols: Sequence[str]
    max_rows: int

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        return qmt_mock_fetch_payload(
            req,
            source_id="qmt_xtdata",
            symbols=self.symbols,
            max_rows=self.max_rows,
            bar_ohlcv=(1401.0, 1411.0, 1396.0, 1406.0, 600_000),
        )


def create_qmt_xtdata_fetch_port(*, symbols: Sequence[str], max_rows: int):
    if len(symbols) > MAX_SYMBOLS:
        raise PortError("FAILED", f"max {MAX_SYMBOLS} symbols allowed, got {len(symbols)}")
    return QmtXtdataMockFetchPort(symbols=symbols, max_rows=max_rows)


__all__ = ["MINUTE_BARS_ENABLED", "MAX_ROWS", "MAX_SYMBOLS", "QmtXtdataMockFetchPort", "create_qmt_xtdata_fetch_port"]
