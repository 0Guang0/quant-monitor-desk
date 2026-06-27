"""CFTC COT official macro fetch port (R3H-01 L2)."""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.normalizers.evidence_bundle import finalize_bundle, reject_over_cap
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.normalizers.official_macro import build_cot_positioning_evidence_bundle

MARKET_WHITELIST = frozenset({"088691", "13874A", "12460P"})
MAX_MARKETS = 5
MAX_ROWS = 52


def _reject_unknown_market(market_code: str) -> None:
    if market_code not in MARKET_WHITELIST:
        raise PortError("FAILED", f"market not in whitelist: {market_code!r}")


@dataclass(frozen=True)
class CftcCotMockFetchPort:
    markets: Sequence[str]
    max_rows: int

    def _mock_rows(self, market_code: str) -> list[dict[str, Any]]:
        today = datetime.now(UTC).date()
        rows: list[dict[str, Any]] = []
        for offset in range(min(self.max_rows, 3)):
            rows.append(
                {
                    "market_code": market_code,
                    "report_date": (today - timedelta(days=7 * offset)).isoformat(),
                    "trader_category": "Noncommercial",
                    "long_contracts": str(100000 - offset * 1000),
                    "short_contracts": str(80000 + offset * 500),
                    "spread_contracts": str(5000),
                    "source_used": "cftc_cot",
                }
            )
        return rows

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(value=self.max_rows, cap=MAX_ROWS)
        market = req.instrument_id or (self.markets[0] if self.markets else "")
        if not market:
            raise PortError("FAILED", "missing market_code for CFTC COT mock fetch")
        _reject_unknown_market(market)

        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"cftc-mock-{market}-{uuid.uuid4().hex[:12]}"
        observations = self._mock_rows(market)
        bundle = build_cot_positioning_evidence_bundle(
            observations=observations,
            source_fetch_id=fetch_id,
            content_hash="pending",
            as_of_timestamp=retrieved_at,
            retrieved_at=retrieved_at,
        )
        bundle = finalize_bundle(bundle)
        content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=len(observations))


def create_cftc_cot_fetch_port(*, markets: Sequence[str], max_rows: int, use_mock: bool = True):
    if len(markets) > MAX_MARKETS:
        raise PortError("FAILED", f"max {MAX_MARKETS} markets allowed, got {len(markets)}")
    if not use_mock:
        raise PortError("FAILED", "live CFTC COT fetch not enabled in R3H-01; use mock")
    return CftcCotMockFetchPort(markets=markets, max_rows=max_rows)
