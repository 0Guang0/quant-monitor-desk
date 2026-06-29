"""Prediction-market capped live smoke gate (R3H-04 L3).

Env-gated live fetch for kalshi/polymarket; evidence lands under .audit-sandbox/round3h only.
Ops entry re-exports datasources implementation (no port→ops inversion).
"""

from __future__ import annotations

from backend.app.datasources.prediction_market_live_smoke_gate import (
    KALSHI_LIVE_SMOKE_ENV,
    KALSHI_LIVE_SMOKE_EVIDENCE,
    POLYMARKET_LIVE_SMOKE_ENV,
    POLYMARKET_LIVE_SMOKE_EVIDENCE,
    PREDICTION_LIVE_AUTHORIZATION_DEFAULT,
    PredictionMarketLiveSmokeError,
    live_smoke_opted_in,
    load_prediction_live_authorization,
    run_kalshi_live_smoke,
    run_polymarket_live_smoke,
    run_prediction_market_live_smoke,
    validate_live_smoke_gate,
    write_live_smoke_evidence,
)

__all__ = [
    "KALSHI_LIVE_SMOKE_ENV",
    "KALSHI_LIVE_SMOKE_EVIDENCE",
    "POLYMARKET_LIVE_SMOKE_ENV",
    "POLYMARKET_LIVE_SMOKE_EVIDENCE",
    "PREDICTION_LIVE_AUTHORIZATION_DEFAULT",
    "PredictionMarketLiveSmokeError",
    "live_smoke_opted_in",
    "load_prediction_live_authorization",
    "run_kalshi_live_smoke",
    "run_polymarket_live_smoke",
    "run_prediction_market_live_smoke",
    "validate_live_smoke_gate",
    "write_live_smoke_evidence",
]
