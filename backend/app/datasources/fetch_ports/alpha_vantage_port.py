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
from pathlib import Path
from typing import Any

from backend.app.config import PROJECT_ROOT
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
from backend.app.datasources.normalizers.market_data import (
    MARKET_DATA_EVIDENCE_SCHEMA_VERSION,
    build_daily_bar_evidence_bundle,
    read_daily_bar_evidence_bundle,
)

MAX_SYMBOLS = 5
MAX_ROWS = 500
MAX_WINDOW_DAYS = 120
MAX_OPTION_STRIKES = 20

SYMBOL_WHITELIST = frozenset({"AAPL", "MSFT", "SPY", "QQQ", "GOOGL"})

REPLAY_FIXTURE = (
    PROJECT_ROOT / "tests/fixtures/replay/market_data/alpha_vantage/aapl_daily_replay.json"
)


def _filter_bars_by_window(
    bars: list[dict[str, Any]],
    *,
    start_time: str | None,
    end_time: str | None,
) -> list[dict[str, Any]]:
    from backend.app.datasources.normalizers.evidence_bundle import parse_fetch_window_date

    start = parse_fetch_window_date(start_time)
    end = parse_fetch_window_date(end_time)
    if start is None or end is None:
        return bars
    if start > end:
        return []
    filtered: list[dict[str, Any]] = []
    for bar in bars:
        trade = parse_fetch_window_date(str(bar.get("trade_date") or ""))
        if trade is not None and start <= trade <= end:
            filtered.append(bar)
    return filtered


def _alpha_vantage_api_key() -> str | None:
    raw = os.environ.get("ALPHA_VANTAGE_API_KEY")
    if not raw or not str(raw).strip():
        return None
    return str(raw).strip()


def _reject_unknown_symbol(symbol: str) -> None:
    if symbol not in SYMBOL_WHITELIST:
        raise PortError("FAILED", f"symbol not in whitelist: {symbol!r}")


def _mock_daily_bars(symbol: str, max_rows: int, *, data_domain: str) -> list[dict[str, Any]]:
    if is_us_equity_bar_fetch(data_domain=data_domain, instrument_id=symbol):
        return mock_us_equity_daily_bars(
            symbol=symbol,
            count=min(max_rows, 3),
            source_used="alpha_vantage",
            open_=185.0,
            high=186.0,
            low=184.5,
            close=185.5,
            volume=50000,
        )
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
    replay_path: Path = REPLAY_FIXTURE

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(value=self.max_rows, cap=MAX_ROWS, label="max_rows")
        reject_over_cap(
            value=self.max_option_strikes,
            cap=MAX_OPTION_STRIKES,
            label="max_option_strikes",
        )
        symbol = req.instrument_id or (self.symbols[0] if self.symbols else "")
        if not symbol:
            raise PortError("FAILED", "missing instrument_id for Alpha Vantage mock fetch")
        _reject_unknown_symbol(symbol)
        domain = req.data_domain or "us_equity_daily_bar"
        reject_fetch_window_span_over_cap(
            start_time=req.start_time,
            end_time=req.end_time,
            cap=MAX_WINDOW_DAYS,
            data_domain=domain,
            instrument_id=symbol,
        )

        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"av-mock-{symbol}-{uuid.uuid4().hex[:12]}"

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
            if self.replay_path.is_file() and domain == "us_equity_daily_bar":
                bundle = read_daily_bar_evidence_bundle(self.replay_path)
                bars = _filter_bars_by_window(
                    list(bundle.get("bars") or []),
                    start_time=req.start_time,
                    end_time=req.end_time,
                )
                bundle = build_daily_bar_evidence_bundle(
                    bars=bars,
                    data_domain=domain,
                    source_id="alpha_vantage",
                    source_fetch_id=str(bundle.get("source_fetch_id") or fetch_id),
                    content_hash=str(bundle.get("content_hash") or "pending"),
                    as_of_timestamp=str(bundle.get("as_of_timestamp") or retrieved_at),
                    retrieved_at=str(bundle.get("retrieved_at") or retrieved_at),
                    window_kind=us_equity_window_kind(data_domain=domain, instrument_id=symbol),
                )
                row_count = len(bars)
            else:
                bars = _mock_daily_bars(symbol, self.max_rows, data_domain=domain)
                window_kind = us_equity_window_kind(data_domain=domain, instrument_id=symbol)
                bundle = build_daily_bar_evidence_bundle(
                    bars=bars,
                    data_domain=domain,
                    source_id="alpha_vantage",
                    source_fetch_id=fetch_id,
                    content_hash="pending",
                    as_of_timestamp=retrieved_at,
                    retrieved_at=retrieved_at,
                    window_kind=window_kind,
                )
                row_count = len(bars)

        if domain != "us_option_chain":
            bundle = finalize_bundle(bundle)

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
    from backend.app.datasources.product_live_gate import gate_live_fetch_port

    gate_live_fetch_port(source_id="alpha_vantage")
    return AlphaVantageLiveFetchPort(
        symbols=symbols,
        max_rows=max_rows,
        max_option_strikes=max_option_strikes,
    )
