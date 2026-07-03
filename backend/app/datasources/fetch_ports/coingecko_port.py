"""CoinGecko crypto spot reference fetch port (R3H-02 L3 greenfield).

No 1:1 upstream reference file; mock-first aggregator validation; internal pattern for R3H-04.
See R3H_02_REFERENCE_ADOPTION_AUDIT.md.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.normalizers.crypto_market import build_crypto_market_evidence_bundle
from backend.app.datasources.normalizers.evidence_bundle import finalize_bundle, reject_over_cap

MAX_ASSETS = 10

ASSET_WHITELIST = frozenset({"bitcoin", "ethereum", "solana"})


def _reject_unknown_asset(asset_id: str) -> None:
    if asset_id not in ASSET_WHITELIST:
        raise PortError("FAILED", f"asset not in coingecko whitelist: {asset_id!r}")


@dataclass(frozen=True)
class CoingeckoMockFetchPort:
    """Deterministic mock CoinGecko port (aggregator validation, no network)."""

    asset_ids: Sequence[str]
    max_assets: int

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(value=self.max_assets, cap=MAX_ASSETS, label="max_assets")
        asset_id = req.instrument_id or (self.asset_ids[0] if self.asset_ids else "")
        if not asset_id:
            raise PortError("FAILED", "missing instrument_id for CoinGecko mock fetch")
        _reject_unknown_asset(asset_id)

        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"coingecko-mock-{asset_id}-{uuid.uuid4().hex[:12]}"
        domain = req.data_domain or "crypto_spot_market"
        symbol = asset_id[:3]
        rows = [
            {
                "asset_id": asset_id,
                "symbol": symbol,
                "price_usd": 62000.5,
                "market_cap_usd": 1_200_000_000_000,
                "volume_24h_usd": 15_000_000_000,
                "source_used": "coingecko",
            }
        ]
        bundle = build_crypto_market_evidence_bundle(
            instruments=rows[: self.max_assets],
            data_domain=domain,
            source_id="coingecko",
            source_fetch_id=fetch_id,
            content_hash="pending",
            as_of_timestamp=retrieved_at,
            retrieved_at=retrieved_at,
        )
        bundle = finalize_bundle(bundle)
        content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=len(rows))


def create_coingecko_fetch_port(*, asset_ids: Sequence[str], max_assets: int, use_mock: bool = True):
    if len(asset_ids) > MAX_ASSETS:
        raise PortError("FAILED", f"max {MAX_ASSETS} assets allowed, got {len(asset_ids)}")
    if use_mock:
        return CoingeckoMockFetchPort(asset_ids=asset_ids, max_assets=max_assets)
    from backend.app.datasources.fetch_ports.tier_b_validation_live import CoingeckoLiveFetchPort
    from backend.app.datasources.product_live_gate import gate_live_fetch_port

    gate_live_fetch_port(source_id="coingecko")
    return CoingeckoLiveFetchPort(asset_ids=asset_ids, max_assets=max_assets)
