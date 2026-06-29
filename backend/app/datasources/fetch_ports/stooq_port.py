"""Stooq validation market data fetch port (R3H-02 L3 greenfield).

No 1:1 upstream reference file; validation-only global/FX/commodity daily bar.
See R3H_02_REFERENCE_ADOPTION_AUDIT.md.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.fetch_window import (
    is_us_equity_bar_fetch,
    mock_us_equity_daily_bars,
    reject_fetch_window_span_over_cap,
    us_equity_window_kind,
)
from backend.app.datasources.normalizers.evidence_bundle import (
    finalize_bundle,
    reject_over_cap,
)
from backend.app.datasources.normalizers.market_data import build_daily_bar_evidence_bundle

MAX_SYMBOLS = 5
MAX_WINDOW_DAYS = 120
MAX_ROWS = 500

SYMBOL_WHITELIST = frozenset({"AAPL.US", "EURUSD", "XAUUSD"})


def _reject_unknown_symbol(symbol: str) -> None:
    if symbol not in SYMBOL_WHITELIST:
        raise PortError("FAILED", f"symbol not in stooq whitelist: {symbol!r}")


@dataclass(frozen=True)
class StooqMockFetchPort:
    """Deterministic mock Stooq port (validation-only, no network)."""

    symbols: Sequence[str]
    max_rows: int

    def _mock_bars(self, symbol: str, *, data_domain: str) -> list[dict[str, Any]]:
        if is_us_equity_bar_fetch(data_domain=data_domain, instrument_id=symbol):
            return mock_us_equity_daily_bars(
                symbol=symbol,
                count=min(self.max_rows, 3),
                source_used="stooq",
            )
        today = datetime.now(UTC).date()
        bars: list[dict[str, Any]] = []
        for offset in range(min(self.max_rows, 3)):
            bars.append(
                {
                    "instrument_id": symbol,
                    "trade_date": (today - timedelta(days=offset)).isoformat(),
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.5,
                    "close": 100.5,
                    "volume": 10000,
                    "source_used": "stooq",
                }
            )
        return bars

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(value=self.max_rows, cap=MAX_ROWS, label="max_rows")
        symbol = req.instrument_id or (self.symbols[0] if self.symbols else "")
        if not symbol:
            raise PortError("FAILED", "missing instrument_id for Stooq mock fetch")
        _reject_unknown_symbol(symbol)
        domain = req.data_domain or "global_market_daily_bar"
        reject_fetch_window_span_over_cap(
            start_time=req.start_time,
            end_time=req.end_time,
            cap=MAX_WINDOW_DAYS,
            data_domain=domain,
            instrument_id=symbol,
        )

        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"stooq-mock-{symbol}-{uuid.uuid4().hex[:12]}"
        bars = self._mock_bars(symbol, data_domain=domain)
        window_kind = us_equity_window_kind(data_domain=domain, instrument_id=symbol)
        bundle = build_daily_bar_evidence_bundle(
            bars=bars,
            data_domain=domain,
            source_id="stooq",
            source_fetch_id=fetch_id,
            content_hash="pending",
            as_of_timestamp=retrieved_at,
            retrieved_at=retrieved_at,
            window_kind=window_kind,
        )
        bundle = finalize_bundle(bundle)
        content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=len(bars))


def create_stooq_fetch_port(*, symbols: Sequence[str], max_rows: int):
    if len(symbols) > MAX_SYMBOLS:
        raise PortError("FAILED", f"max {MAX_SYMBOLS} symbols allowed, got {len(symbols)}")
    return StooqMockFetchPort(symbols=symbols, max_rows=max_rows)
