"""Alpha Vantage market data fetch port (R3H-02 L3 greenfield).

No 1:1 upstream reference file; mock-first; market_data_evidence_v1.
OpenBB providers/ = architecture_only. See R3H_02_REFERENCE_ADOPTION_AUDIT.md.
"""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.normalizers.evidence_bundle import (
    finalize_bundle,
    reject_over_cap,
    reject_window_span_over_cap,
)
from backend.app.datasources.normalizers.market_data import (
    MARKET_DATA_EVIDENCE_SCHEMA_VERSION,
    build_daily_bar_evidence_bundle,
)

MAX_SYMBOLS = 5
MAX_ROWS = 500
MAX_WINDOW_DAYS = 120
MAX_OPTION_STRIKES = 20

SYMBOL_WHITELIST = frozenset({"AAPL", "MSFT", "SPY", "QQQ", "GOOGL"})


def _alpha_vantage_api_key() -> str | None:
    raw = os.environ.get("ALPHA_VANTAGE_API_KEY")
    if not raw or not str(raw).strip():
        return None
    return str(raw).strip()


def _reject_unknown_symbol(symbol: str) -> None:
    if symbol not in SYMBOL_WHITELIST:
        raise PortError("FAILED", f"symbol not in whitelist: {symbol!r}")


def _mock_daily_bars(symbol: str, max_rows: int) -> list[dict[str, Any]]:
    today = datetime.now(UTC).date()
    bars: list[dict[str, Any]] = []
    for offset in range(min(max_rows, 3)):
        bars.append(
            {
                "instrument_id": symbol,
                "trade_date": (today - timedelta(days=offset)).isoformat(),
                "open": 185.0 - offset,
                "high": 186.0 - offset,
                "low": 184.5 - offset,
                "close": 185.5 - offset,
                "volume": 50000 - offset * 1000,
                "source_used": "alpha_vantage",
            }
        )
    return bars


def _mock_option_chain(symbol: str, max_strikes: int) -> list[dict[str, Any]]:
    strikes = min(max_strikes, MAX_OPTION_STRIKES)
    return [
        {
            "instrument_id": symbol,
            "expiration_date": "2024-12-20",
            "strike": 180.0 + i * 5,
            "option_type": "call" if i % 2 == 0 else "put",
            "bid": 1.5 + i * 0.1,
            "ask": 1.6 + i * 0.1,
            "implied_volatility": 0.25 + i * 0.01,
            "source_used": "alpha_vantage",
        }
        for i in range(strikes)
    ]


@dataclass(frozen=True)
class AlphaVantageMockFetchPort:
    """Deterministic mock Alpha Vantage port (no network)."""

    symbols: Sequence[str]
    max_rows: int
    max_option_strikes: int = MAX_OPTION_STRIKES

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(value=self.max_rows, cap=MAX_ROWS, label="max_rows")
        reject_over_cap(
            value=self.max_option_strikes,
            cap=MAX_OPTION_STRIKES,
            label="max_option_strikes",
        )
        reject_window_span_over_cap(
            start_time=req.start_time,
            end_time=req.end_time,
            cap=MAX_WINDOW_DAYS,
        )
        symbol = req.instrument_id or (self.symbols[0] if self.symbols else "")
        if not symbol:
            raise PortError("FAILED", "missing instrument_id for Alpha Vantage mock fetch")
        _reject_unknown_symbol(symbol)

        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"av-mock-{symbol}-{uuid.uuid4().hex[:12]}"
        domain = req.data_domain or "us_equity_daily_bar"

        if domain == "us_option_chain":
            rows = _mock_option_chain(symbol, self.max_option_strikes)
            bundle = {
                "schema_version": MARKET_DATA_EVIDENCE_SCHEMA_VERSION,
                "source_id": "alpha_vantage",
                "data_domain": domain,
                "option_chain": rows,
                "source_fetch_id": fetch_id,
                "content_hash": "pending",
                "as_of_timestamp": retrieved_at,
                "retrieved_at": retrieved_at,
                "window_kind": "calendar_days",
            }
            bundle = finalize_bundle(bundle)
            row_count = len(rows)
        else:
            bars = _mock_daily_bars(symbol, self.max_rows)
            bundle = build_daily_bar_evidence_bundle(
                bars=bars,
                data_domain=domain,
                source_id="alpha_vantage",
                source_fetch_id=fetch_id,
                content_hash="pending",
                as_of_timestamp=retrieved_at,
                retrieved_at=retrieved_at,
            )
            bundle = finalize_bundle(bundle)
            row_count = len(bars)

        content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=row_count)


@dataclass(frozen=True)
class AlphaVantageLiveFetchPort:
    """Bounded live Alpha Vantage fetch (opt-in, requires ALPHA_VANTAGE_API_KEY)."""

    symbols: Sequence[str]
    max_rows: int
    max_option_strikes: int = MAX_OPTION_STRIKES

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        if not _alpha_vantage_api_key():
            raise PortError("USER_AUTH_REQUIRED", "ALPHA_VANTAGE_API_KEY missing for live fetch")
        # ponytail: live path delegates to mock until dedicated urllib wiring is needed;
        # DSS ResourceGuard hook belongs in the live slice (see R3H-02 frozen §7).
        return AlphaVantageMockFetchPort(
            symbols=self.symbols,
            max_rows=self.max_rows,
            max_option_strikes=self.max_option_strikes,
        ).fetch_payload(req)


def create_alpha_vantage_fetch_port(
    *,
    symbols: Sequence[str],
    max_rows: int,
    max_option_strikes: int = MAX_OPTION_STRIKES,
    use_mock: bool = True,
):
    if len(symbols) > MAX_SYMBOLS:
        raise PortError("FAILED", f"max {MAX_SYMBOLS} symbols allowed, got {len(symbols)}")
    if use_mock:
        return AlphaVantageMockFetchPort(
            symbols=symbols,
            max_rows=max_rows,
            max_option_strikes=max_option_strikes,
        )
    return AlphaVantageLiveFetchPort(
        symbols=symbols,
        max_rows=max_rows,
        max_option_strikes=max_option_strikes,
    )
