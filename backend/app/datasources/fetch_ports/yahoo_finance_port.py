"""Yahoo Finance validation market data fetch port (R3H-02 L2 copy_and_rewrite).

L2 migrate from 3G fixture semantics → replay tests/fixtures/replay/market_data/yahoo_finance/.
validation_only permanent; not OpenBB runtime copy. See R3H_02_REFERENCE_ADOPTION_AUDIT.md.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from backend.app.config import PROJECT_ROOT
from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.normalizers.evidence_bundle import (
    finalize_bundle,
    reject_over_cap,
    reject_window_span_over_cap,
)
from backend.app.datasources.normalizers.market_data import (
    build_daily_bar_evidence_bundle,
    read_daily_bar_evidence_bundle,
)

MAX_SYMBOLS = 3
MAX_ROWS = 500
MAX_WINDOW_DAYS = 120

REPLAY_FIXTURE = (
    PROJECT_ROOT / "tests/fixtures/replay/market_data/yahoo_finance/aapl_validation_replay.json"
)
SYMBOL_WHITELIST = frozenset({"AAPL", "MSFT", "SPY"})


def _reject_unknown_symbol(symbol: str) -> None:
    if symbol not in SYMBOL_WHITELIST:
        raise PortError("FAILED", f"symbol not in yahoo whitelist: {symbol!r}")


@dataclass(frozen=True)
class YahooFinanceMockFetchPort:
    """Deterministic mock Yahoo Finance port (validation-only, no network)."""

    symbols: Sequence[str]
    max_rows: int
    replay_path: Path = REPLAY_FIXTURE

    def _mock_bars(self, symbol: str) -> list[dict[str, Any]]:
        if self.replay_path.is_file():
            bundle = read_daily_bar_evidence_bundle(self.replay_path)
            bars = [
                bar
                for bar in bundle.get("bars") or []
                if bar.get("instrument_id") == symbol or symbol in ("AAPL", "MSFT")
            ]
            if bars:
                return bars[: min(self.max_rows, len(bars))]
        today = datetime.now(UTC).date()
        return [
            {
                "instrument_id": symbol,
                "trade_date": (today - timedelta(days=offset)).isoformat(),
                "open": 185.0,
                "high": 186.0,
                "low": 184.5,
                "close": 185.5,
                "volume": 50000,
                "source_used": "yahoo_finance",
            }
            for offset in range(min(self.max_rows, 2))
        ]

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(value=self.max_rows, cap=MAX_ROWS, label="max_rows")
        reject_window_span_over_cap(
            start_time=req.start_time,
            end_time=req.end_time,
            cap=MAX_WINDOW_DAYS,
        )
        symbol = req.instrument_id or (self.symbols[0] if self.symbols else "")
        if not symbol:
            raise PortError("FAILED", "missing instrument_id for Yahoo Finance mock fetch")
        _reject_unknown_symbol(symbol)

        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"yahoo-mock-{symbol}-{uuid.uuid4().hex[:12]}"
        domain = req.data_domain or "us_equity_daily_bar"
        bars = self._mock_bars(symbol)
        bundle = build_daily_bar_evidence_bundle(
            bars=bars,
            data_domain=domain,
            source_id="yahoo_finance",
            source_fetch_id=fetch_id,
            content_hash="pending",
            as_of_timestamp=retrieved_at,
            retrieved_at=retrieved_at,
        )
        bundle = finalize_bundle(bundle)
        content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=len(bars))


def create_yahoo_finance_fetch_port(*, symbols: Sequence[str], max_rows: int):
    if len(symbols) > MAX_SYMBOLS:
        raise PortError("FAILED", f"max {MAX_SYMBOLS} symbols allowed, got {len(symbols)}")
    return YahooFinanceMockFetchPort(symbols=symbols, max_rows=max_rows)
