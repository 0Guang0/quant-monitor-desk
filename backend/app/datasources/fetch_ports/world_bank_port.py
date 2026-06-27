"""World Bank official macro fetch port (R3H-01 L2)."""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.normalizers.evidence_bundle import finalize_bundle, reject_over_cap
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.normalizers.official_macro import (
    build_world_bank_indicator_evidence_bundle,
)

COUNTRY_WHITELIST = frozenset({"US", "CN", "IN", "DE", "JP"})
INDICATOR_WHITELIST = frozenset({"NY.GDP.MKTP.CD", "SP.POP.TOTL", "SL.UEM.TOTL.ZS"})
MAX_INDICATORS = 5
MAX_COUNTRIES = 5
MAX_ROWS = 500

WorldBankDomain = Literal["development_indicator", "global_macro_reference"]


def _reject_unknown_pair(*, country_code: str, indicator_id: str) -> None:
    if country_code not in COUNTRY_WHITELIST:
        raise PortError("FAILED", f"country not in whitelist: {country_code!r}")
    if indicator_id not in INDICATOR_WHITELIST:
        raise PortError("FAILED", f"indicator not in whitelist: {indicator_id!r}")


@dataclass(frozen=True)
class WorldBankMockFetchPort:
    countries: Sequence[str]
    indicators: Sequence[str]
    max_rows: int
    data_domain: WorldBankDomain

    def _mock_rows(self, country_code: str, indicator_id: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for year in range(min(self.max_rows, 3)):
            rows.append(
                {
                    "country_code": country_code,
                    "indicator_id": indicator_id,
                    "observation_date": f"{2024 - year}-01-01",
                    "value": str(1e13 - year * 1e11),
                    "unit": "USD" if "GDP" in indicator_id else "count",
                    "source_used": "world_bank",
                }
            )
        return rows

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(value=self.max_rows, cap=MAX_ROWS)
        country = req.instrument_id or (self.countries[0] if self.countries else "")
        indicator = self.indicators[0] if self.indicators else ""
        if not country or not indicator:
            raise PortError("FAILED", "missing country/indicator for World Bank mock fetch")
        _reject_unknown_pair(country_code=country, indicator_id=indicator)

        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"wb-mock-{country}-{uuid.uuid4().hex[:12]}"
        observations = self._mock_rows(country, indicator)
        bundle = build_world_bank_indicator_evidence_bundle(
            observations=observations,
            source_fetch_id=fetch_id,
            content_hash="pending",
            as_of_timestamp=retrieved_at,
            retrieved_at=retrieved_at,
            data_domain=self.data_domain,
        )
        bundle = finalize_bundle(bundle)
        content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=len(observations))


def create_world_bank_fetch_port(
    *,
    countries: Sequence[str],
    indicators: Sequence[str],
    max_rows: int,
    data_domain: WorldBankDomain,
    use_mock: bool = True,
):
    if len(countries) > MAX_COUNTRIES:
        raise PortError("FAILED", f"max {MAX_COUNTRIES} countries allowed, got {len(countries)}")
    if len(indicators) > MAX_INDICATORS:
        raise PortError("FAILED", f"max {MAX_INDICATORS} indicators allowed, got {len(indicators)}")
    if not use_mock:
        raise PortError("FAILED", "live World Bank fetch not enabled in R3H-01; use mock")
    return WorldBankMockFetchPort(
        countries=countries,
        indicators=indicators,
        max_rows=max_rows,
        data_domain=data_domain,
    )
