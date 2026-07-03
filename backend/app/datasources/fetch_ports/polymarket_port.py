"""Polymarket prediction market probability fetch port (R3H-04 L3).

reference_adoption:
  - ladder: L3_greenfield (live urllib) + L2_copy_and_rewrite (mock from coingecko_port.py)
  - mock_template: backend/app/datasources/fetch_ports/coingecko_port.py
  - forbidden: factual_resolution / resolved=true semantics on resolution_source
See R3H_04_REFERENCE_ADOPTION_AUDIT.md.
Mock/replay-first; records liquidity/volume/spread and resolution_source URL metadata only.
"""

from __future__ import annotations

import json
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
POLYMARKET_API_BASE = "https://gamma-api.polymarket.com"

MARKET_WHITELIST = frozenset(
    {
        "will-fed-cut-rates-2024",
        "will-btc-above-100k-2024",
        "kraken-ipo-in-2025",
        "new-rhianna-album-before-gta-vi-926",
    }
)


def _reject_unknown_market(market_slug: str) -> None:
    if market_slug not in MARKET_WHITELIST:
        raise PortError("FAILED", f"market not in polymarket whitelist: {market_slug!r}")


def _resolve_instrument(req: FetchRequest, instruments: Sequence[str]) -> str:
    market_slug = req.instrument_id or (instruments[0] if instruments else "")
    if market_slug:
        _reject_unknown_market(market_slug)
    return market_slug


@dataclass(frozen=True)
class PolymarketMockFetchPort:
    """Deterministic mock Polymarket port (probability signal, no network)."""

    market_slugs: Sequence[str]
    max_markets: int

    def _mock_signals(self, market_slug: str) -> list[dict[str, Any]]:
        return [
            {
                "market_slug": market_slug,
                "yes_bid": 0.61,
                "yes_ask": 0.63,
                "probability": 0.62,
                "volume": 45000,
                "liquidity": 120000,
                "spread": 0.02,
                "resolution_source": "https://example.com/polymarket/resolution-rules",
                "source_used": "polymarket",
            }
        ]

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        return build_probability_market_fetch_payload(
            req,
            max_markets=self.max_markets,
            max_markets_cap=MAX_MARKETS,
            max_window_days=MAX_WINDOW_DAYS,
            instruments=self.market_slugs,
            source_id="polymarket",
            fetch_id_prefix="polymarket-mock",
            resolve_instrument=_resolve_instrument,
            build_signals=self._mock_signals,
            live=False,
        )


def _fetch_live_polymarket_market(market_slug: str) -> dict[str, Any]:
    """Bounded Polymarket gamma API fetch (network only; caller applies gate)."""
    url = f"{POLYMARKET_API_BASE}/markets/slug/{urllib.parse.quote(market_slug, safe='')}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            # ponytail: gamma API 403 without UA; upgrade path = dedicated client + retries
            "User-Agent": "QuantMonitorDesk/1.0 (polymarket-fetch)",
        },
        method="GET",
    )
    try:
        # ponytail: live urllib capped read; no auth header — env+YAML gate only for smoke
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = json.loads(
                read_bounded_http_body(response, label="Polymarket response").decode("utf-8")
            )
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise PortError("USER_AUTH_REQUIRED", f"Polymarket access denied: {exc}") from exc
        raise PortError("NETWORK_ERROR", str(exc)) from exc
    except urllib.error.URLError as exc:
        raise PortError("NETWORK_ERROR", str(exc)) from exc
    except json.JSONDecodeError as exc:
        raise PortError("FAILED", f"invalid Polymarket JSON: {exc}") from exc

    if isinstance(raw, list):
        markets = raw
    elif isinstance(raw, dict) and raw.get("slug"):
        markets = [raw]
    else:
        markets = raw.get("markets") or []
    if not markets:
        raise PortError("EMPTY_RESPONSE", f"Polymarket returned no market for slug {market_slug!r}")
    market = markets[0]
    outcome_prices = market.get("outcomePrices") or []
    if isinstance(outcome_prices, str):
        try:
            outcome_prices = json.loads(outcome_prices)
        except json.JSONDecodeError:
            outcome_prices = []
    try:
        yes_price = float(outcome_prices[0]) if outcome_prices else None
    except (TypeError, ValueError, IndexError):
        yes_price = None
    spread = market.get("spread")
    try:
        spread_f = float(spread) if spread is not None else None
    except (TypeError, ValueError):
        spread_f = None
    resolution_source = market.get("resolutionSource")
    return {
        "market_slug": market.get("slug") or market_slug,
        "yes_bid": yes_price,
        "yes_ask": yes_price,
        "probability": yes_price,
        "volume": market.get("volume"),
        "liquidity": market.get("liquidity"),
        "spread": spread_f,
        "resolution_source": str(resolution_source) if resolution_source else None,
        "source_used": "polymarket",
    }


def fetch_polymarket_smoke_live_payload(market_slug: str) -> FetchPayload:
    """Ops smoke entry — uses smoke env gate, not product live gate."""
    _reject_unknown_market(market_slug)
    signal = _fetch_live_polymarket_market(market_slug)
    if signal.get("probability") is None:
        raise PortError(
            "EMPTY_RESPONSE", f"Polymarket returned no probability for {market_slug}"
        )
    req = FetchRequest(
        run_id="r3h04-polymarket-live-smoke",
        source_id="polymarket",
        data_domain="prediction_market_probability",
        instrument_id=market_slug,
    )
    return build_probability_market_fetch_payload(
        req,
        max_markets=1,
        max_markets_cap=MAX_MARKETS,
        max_window_days=MAX_WINDOW_DAYS,
        instruments=(market_slug,),
        source_id="polymarket",
        fetch_id_prefix="polymarket-live-smoke",
        resolve_instrument=lambda _req, _inst: market_slug,
        build_signals=lambda _slug: [signal],
        live=True,
    )


@dataclass(frozen=True)
class PolymarketLiveFetchPort:
    """Bounded live Polymarket gamma API fetch (product live via ProductLiveGate only)."""

    market_slugs: Sequence[str]
    max_markets: int

    def _live_market(self, market_slug: str) -> dict[str, Any]:
        return _fetch_live_polymarket_market(market_slug)

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        market_slug = _resolve_instrument(req, self.market_slugs)
        signal = self._live_market(market_slug)
        if signal.get("probability") is None:
            raise PortError(
                "EMPTY_RESPONSE", f"Polymarket returned no probability for {market_slug}"
            )
        return build_probability_market_fetch_payload(
            req,
            max_markets=self.max_markets,
            max_markets_cap=MAX_MARKETS,
            max_window_days=MAX_WINDOW_DAYS,
            instruments=(market_slug,),
            source_id="polymarket",
            fetch_id_prefix="polymarket-live",
            resolve_instrument=lambda _req, _inst: market_slug,
            build_signals=lambda _slug: [signal],
            live=True,
        )


def create_polymarket_fetch_port(
    *,
    market_slugs: Sequence[str],
    max_markets: int,
    use_mock: bool = True,
):
    if len(market_slugs) > MAX_MARKETS:
        raise PortError("FAILED", f"max {MAX_MARKETS} markets allowed, got {len(market_slugs)}")
    if use_mock:
        return PolymarketMockFetchPort(market_slugs=market_slugs, max_markets=max_markets)
    from backend.app.datasources.product_live_gate import gate_live_fetch_port

    gate_live_fetch_port(source_id="polymarket")
    return PolymarketLiveFetchPort(market_slugs=market_slugs, max_markets=max_markets)
