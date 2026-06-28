"""Kalshi regulated event contract / probability fetch port (R3H-04 L3).

reference_adoption:
  - ladder: L3_greenfield (live urllib) + L2_copy_and_rewrite (mock from coingecko_port.py)
  - mock_template: backend/app/datasources/fetch_ports/coingecko_port.py
  - forbidden: factual_resolution / resolved_outcome fields
Mock/replay-first; probability signal only — never factual resolution.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.fetch_ports.prediction_market_port_common import (
    build_probability_market_fetch_payload,
    read_bounded_http_body,
)
from backend.app.datasources.fetch_result import FetchRequest

MAX_MARKETS = 5
MAX_WINDOW_DAYS = 30
KALSHI_API_BASE = "https://api.elections.kalshi.com/trade-api/v2"

MARKET_WHITELIST = frozenset({"KXHIGHNY-24", "KXFED-24"})


def _reject_unknown_market(market_ticker: str) -> None:
    if market_ticker not in MARKET_WHITELIST:
        raise PortError("FAILED", f"market not in kalshi whitelist: {market_ticker!r}")


def _kalshi_api_key() -> str | None:
    raw = os.environ.get("KALSHI_API_KEY")
    if not raw or not str(raw).strip():
        return None
    return str(raw).strip()


def _cents_to_probability(cents: Any) -> float | None:
    if cents is None:
        return None
    try:
        return round(float(cents) / 100.0, 4)
    except (TypeError, ValueError):
        return None


def _resolve_instrument(req: FetchRequest, instruments: Sequence[str]) -> str:
    market_ticker = req.instrument_id or (instruments[0] if instruments else "")
    if market_ticker:
        _reject_unknown_market(market_ticker)
    return market_ticker


@dataclass(frozen=True)
class KalshiMockFetchPort:
    """Deterministic mock Kalshi port (probability signal, no network)."""

    market_tickers: Sequence[str]
    max_markets: int

    def _mock_signals(self, market_ticker: str) -> list[dict[str, Any]]:
        return [
            {
                "market_ticker": market_ticker,
                "event_ticker": market_ticker.split("-")[0],
                "yes_bid": 0.42,
                "yes_ask": 0.45,
                "probability": 0.435,
                "volume": 1200,
                "liquidity": 5000,
                "source_used": "kalshi",
            }
        ]

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        return build_probability_market_fetch_payload(
            req,
            max_markets=self.max_markets,
            max_markets_cap=MAX_MARKETS,
            max_window_days=MAX_WINDOW_DAYS,
            instruments=self.market_tickers,
            source_id="kalshi",
            fetch_id_prefix="kalshi-mock",
            resolve_instrument=_resolve_instrument,
            build_signals=self._mock_signals,
            live=False,
        )


@dataclass(frozen=True)
class KalshiLiveFetchPort:
    """Bounded live Kalshi API fetch (opt-in via prediction_market_live_smoke gate)."""

    market_tickers: Sequence[str]
    max_markets: int

    def _live_market(self, market_ticker: str) -> dict[str, Any]:
        from backend.app.ops.prediction_market_live_smoke import validate_live_smoke_gate

        validate_live_smoke_gate(source_id="kalshi")
        url = f"{KALSHI_API_BASE}/markets/{urllib.parse.quote(market_ticker, safe='')}"
        headers: dict[str, str] = {"Accept": "application/json"}
        api_key = _kalshi_api_key()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        request = urllib.request.Request(url, headers=headers, method="GET")
        try:
            # ponytail: live urllib capped read; upgrade path = dedicated client with retries
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = json.loads(read_bounded_http_body(response, label="Kalshi response").decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise PortError("USER_AUTH_REQUIRED", f"Kalshi auth failed: {exc}") from exc
            raise PortError("NETWORK_ERROR", str(exc)) from exc
        except urllib.error.URLError as exc:
            raise PortError("NETWORK_ERROR", str(exc)) from exc
        except json.JSONDecodeError as exc:
            raise PortError("FAILED", f"invalid Kalshi JSON: {exc}") from exc

        market = raw.get("market") or raw
        yes_bid = _cents_to_probability(market.get("yes_bid"))
        yes_ask = _cents_to_probability(market.get("yes_ask"))
        last_price = _cents_to_probability(market.get("last_price"))
        probability = last_price
        if probability is None and yes_bid is not None and yes_ask is not None:
            probability = round((yes_bid + yes_ask) / 2.0, 4)
        return {
            "market_ticker": market.get("ticker") or market_ticker,
            "event_ticker": market.get("event_ticker"),
            "yes_bid": yes_bid,
            "yes_ask": yes_ask,
            "probability": probability,
            "volume": market.get("volume"),
            "liquidity": market.get("open_interest"),
            "source_used": "kalshi",
        }

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        market_ticker = _resolve_instrument(req, self.market_tickers)
        signal = self._live_market(market_ticker)
        if signal.get("probability") is None:
            raise PortError("EMPTY_RESPONSE", f"Kalshi returned no probability for {market_ticker}")
        return build_probability_market_fetch_payload(
            req,
            max_markets=self.max_markets,
            max_markets_cap=MAX_MARKETS,
            max_window_days=MAX_WINDOW_DAYS,
            instruments=(market_ticker,),
            source_id="kalshi",
            fetch_id_prefix="kalshi-live",
            resolve_instrument=lambda _req, _inst: market_ticker,
            build_signals=lambda _ticker: [signal],
            live=True,
        )


def create_kalshi_fetch_port(
    *,
    market_tickers: Sequence[str],
    max_markets: int,
    use_mock: bool = True,
):
    if len(market_tickers) > MAX_MARKETS:
        raise PortError("FAILED", f"max {MAX_MARKETS} markets allowed, got {len(market_tickers)}")
    if use_mock:
        return KalshiMockFetchPort(market_tickers=market_tickers, max_markets=max_markets)
    return KalshiLiveFetchPort(market_tickers=market_tickers, max_markets=max_markets)
