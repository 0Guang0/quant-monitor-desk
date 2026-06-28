"""Prediction-market capped live smoke gate (R3H-04 L3).

Env-gated live fetch for kalshi/polymarket; evidence lands under .audit-sandbox/round3h only.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import yaml

from backend.app.config import PROJECT_ROOT
from backend.app.datasources.adapters.fetch_port import FetchPayload
from backend.app.datasources.fetch_result import FetchRequest

PREDICTION_LIVE_AUTHORIZATION_DEFAULT = (
    PROJECT_ROOT / ".audit-sandbox/round3h/prediction_market_live_authorization.yaml"
)
KALSHI_LIVE_SMOKE_EVIDENCE = PROJECT_ROOT / ".audit-sandbox/round3h/kalshi_live_smoke_evidence.json"
POLYMARKET_LIVE_SMOKE_EVIDENCE = (
    PROJECT_ROOT / ".audit-sandbox/round3h/polymarket_live_smoke_evidence.json"
)

KALSHI_LIVE_SMOKE_ENV = "KALSHI_LIVE_SMOKE"
POLYMARKET_LIVE_SMOKE_ENV = "POLYMARKET_LIVE_SMOKE"


class PredictionMarketLiveSmokeError(RuntimeError):
    """Live smoke gate or evidence write failure."""


def _resolve_path(path: str | Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate.resolve()


def load_prediction_live_authorization(path: str | Path) -> dict[str, Any]:
    resolved = _resolve_path(path)
    if not resolved.is_file():
        raise PredictionMarketLiveSmokeError(f"authorization evidence missing: {path}")
    payload = yaml.safe_load(resolved.read_text(encoding="utf-8")) or {}
    if not payload.get("authorization_present"):
        raise PredictionMarketLiveSmokeError("authorization_present must be true")
    if payload.get("allow_production_clean_write"):
        raise PredictionMarketLiveSmokeError("allow_production_clean_write must be false")
    if payload.get("scope") != "prediction_market_live_smoke_sandbox_only":
        raise PredictionMarketLiveSmokeError(
            "scope must be prediction_market_live_smoke_sandbox_only"
        )
    return payload


def live_smoke_opted_in(*, source_id: str) -> bool:
    env_name = KALSHI_LIVE_SMOKE_ENV if source_id == "kalshi" else POLYMARKET_LIVE_SMOKE_ENV
    return os.environ.get(env_name, "").strip().lower() in {"1", "true", "yes"}


def validate_live_smoke_gate(
    *,
    source_id: str,
    authorization_path: str | Path | None = None,
) -> dict[str, Any]:
    """Fail-closed: live smoke requires env opt-in + authorization YAML."""
    if not live_smoke_opted_in(source_id=source_id):
        raise PredictionMarketLiveSmokeError(
            f"{KALSHI_LIVE_SMOKE_ENV if source_id == 'kalshi' else POLYMARKET_LIVE_SMOKE_ENV}"
            " must be set for live smoke"
        )
    auth_path = authorization_path or PREDICTION_LIVE_AUTHORIZATION_DEFAULT
    auth = load_prediction_live_authorization(auth_path)
    section = auth.get(source_id) or {}
    if not section.get("enabled"):
        raise PredictionMarketLiveSmokeError(f"{source_id} not enabled in authorization YAML")
    return auth


def write_live_smoke_evidence(
    *,
    source_id: str,
    payload: FetchPayload,
    evidence_path: Path | None = None,
) -> Path:
    """Persist capped live smoke bundle under audit-sandbox (never main DB)."""
    if source_id == "kalshi":
        out = evidence_path or KALSHI_LIVE_SMOKE_EVIDENCE
    elif source_id == "polymarket":
        out = evidence_path or POLYMARKET_LIVE_SMOKE_EVIDENCE
    else:
        raise PredictionMarketLiveSmokeError(f"unsupported live smoke source: {source_id}")
    out = _resolve_path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    body = json.loads(payload.content.decode("utf-8"))
    record = {
        "source_id": source_id,
        "live_smoke": True,
        "sandbox_only": True,
        "production_clean_write": False,
        "bundle": body,
    }
    out.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def run_prediction_market_live_smoke(
    *,
    source_id: str,
    instrument_id: str,
    authorization_path: str | Path | None = None,
    evidence_path: Path | None = None,
) -> Path:
    """Capped live smoke for kalshi or polymarket (env + YAML gated)."""
    validate_live_smoke_gate(source_id=source_id, authorization_path=authorization_path)
    if source_id == "kalshi":
        from backend.app.datasources.fetch_ports.kalshi_port import create_kalshi_fetch_port

        port = create_kalshi_fetch_port(
            market_tickers=(instrument_id,), max_markets=1, use_mock=False
        )
        run_id = "r3h04-kalshi-live-smoke"
    elif source_id == "polymarket":
        from backend.app.datasources.fetch_ports.polymarket_port import create_polymarket_fetch_port

        port = create_polymarket_fetch_port(
            market_slugs=(instrument_id,), max_markets=1, use_mock=False
        )
        run_id = "r3h04-polymarket-live-smoke"
    else:
        raise PredictionMarketLiveSmokeError(f"unsupported live smoke source: {source_id}")
    req = FetchRequest(
        run_id=run_id,
        source_id=source_id,
        data_domain="prediction_market_probability",
        instrument_id=instrument_id,
    )
    payload = port.fetch_payload(req)
    return write_live_smoke_evidence(
        source_id=source_id, payload=payload, evidence_path=evidence_path
    )


def run_kalshi_live_smoke(
    *,
    market_ticker: str,
    authorization_path: str | Path | None = None,
    evidence_path: Path | None = None,
) -> Path:
    return run_prediction_market_live_smoke(
        source_id="kalshi",
        instrument_id=market_ticker,
        authorization_path=authorization_path,
        evidence_path=evidence_path,
    )


def run_polymarket_live_smoke(
    *,
    market_slug: str,
    authorization_path: str | Path | None = None,
    evidence_path: Path | None = None,
) -> Path:
    return run_prediction_market_live_smoke(
        source_id="polymarket",
        instrument_id=market_slug,
        authorization_path=authorization_path,
        evidence_path=evidence_path,
    )
