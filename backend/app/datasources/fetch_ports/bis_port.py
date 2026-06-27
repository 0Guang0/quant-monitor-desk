"""BIS official macro fetch port (R3H-01 L2)."""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.normalizers.official_macro import (
    build_bis_credit_gap_evidence_bundle,
    build_bis_policy_rate_evidence_bundle,
)

COUNTRY_WHITELIST = frozenset({"US", "GB", "JP", "DE", "CN"})
MAX_SERIES = 10
MAX_COUNTRIES = 5
MAX_ROWS = 500

BisDomain = Literal["central_bank_policy", "credit_gap"]


def _reject_unknown_country(country_code: str) -> None:
    if country_code not in COUNTRY_WHITELIST:
        raise PortError("FAILED", f"country not in whitelist: {country_code!r}")


def _reject_over_cap(*, max_rows: int) -> None:
    if max_rows <= 0 or max_rows > MAX_ROWS:
        raise PortError("FAILED", f"requested max_rows={max_rows} exceeds cap={MAX_ROWS}")


def _bundle_content_hash(bundle: dict[str, Any]) -> str:
    canonical = {k: v for k, v in bundle.items() if k != "content_hash"}
    payload = json.dumps(canonical, ensure_ascii=False, default=str, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _finalize_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    bundle = dict(bundle)
    bundle["content_hash"] = _bundle_content_hash(bundle)
    return bundle


@dataclass(frozen=True)
class BisMockFetchPort:
    countries: Sequence[str]
    max_rows: int
    data_domain: BisDomain

    def _mock_policy_rows(self, country_code: str) -> list[dict[str, Any]]:
        today = datetime.now(UTC).date()
        rows: list[dict[str, Any]] = []
        for offset in range(min(self.max_rows, 2)):
            rows.append(
                {
                    "country_code": country_code,
                    "observation_date": (today - timedelta(days=30 * offset)).isoformat(),
                    "policy_rate": str(5.25 - offset * 0.25),
                    "frequency": "monthly",
                    "source_used": "bis",
                }
            )
        return rows

    def _mock_credit_gap_rows(self, country_code: str) -> list[dict[str, Any]]:
        today = datetime.now(UTC).date()
        rows: list[dict[str, Any]] = []
        for offset in range(min(self.max_rows, 2)):
            rows.append(
                {
                    "country_code": country_code,
                    "observation_date": (today - timedelta(days=90 * offset)).isoformat(),
                    "credit_to_gdp_gap": str(2.5 - offset * 0.1),
                    "source_used": "bis",
                }
            )
        return rows

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        _reject_over_cap(max_rows=self.max_rows)
        country = req.instrument_id or (self.countries[0] if self.countries else "")
        if not country:
            raise PortError("FAILED", "missing country_code for BIS mock fetch")
        _reject_unknown_country(country)

        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"bis-mock-{country}-{uuid.uuid4().hex[:12]}"

        if self.data_domain == "central_bank_policy":
            observations = self._mock_policy_rows(country)
            bundle = build_bis_policy_rate_evidence_bundle(
                observations=observations,
                source_fetch_id=fetch_id,
                content_hash="pending",
                as_of_timestamp=retrieved_at,
                retrieved_at=retrieved_at,
            )
        else:
            observations = self._mock_credit_gap_rows(country)
            bundle = build_bis_credit_gap_evidence_bundle(
                observations=observations,
                source_fetch_id=fetch_id,
                content_hash="pending",
                as_of_timestamp=retrieved_at,
                retrieved_at=retrieved_at,
            )

        bundle = _finalize_bundle(bundle)
        content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=len(observations))


def create_bis_fetch_port(
    *,
    countries: Sequence[str],
    max_rows: int,
    data_domain: BisDomain,
    use_mock: bool = True,
):
    if len(countries) > MAX_COUNTRIES:
        raise PortError("FAILED", f"max {MAX_COUNTRIES} countries allowed, got {len(countries)}")
    if not use_mock:
        raise PortError("FAILED", "live BIS fetch not enabled in R3H-01; use mock")
    return BisMockFetchPort(countries=countries, max_rows=max_rows, data_domain=data_domain)
