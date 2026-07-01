"""BIS official macro fetch port (R3H-01 L3 greenfield).

No 1:1 upstream reference file; mock-first; official_macro_evidence_v1.
See R3H_01_REFERENCE_ADOPTION_AUDIT.md.
"""

from __future__ import annotations

import csv
import json
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from io import StringIO
from typing import Any, Literal

from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.normalizers.evidence_bundle import finalize_bundle, reject_over_cap
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.normalizers.official_macro import (
    build_bis_credit_gap_evidence_bundle,
    build_bis_policy_rate_evidence_bundle,
)

COUNTRY_WHITELIST = frozenset({"US", "GB", "JP", "DE", "CN"})
MAX_COUNTRIES = 5
MAX_ROWS = 500

BisDomain = Literal["central_bank_policy", "credit_gap"]

# L2 cite: digital-oracle bis.py L13-14, L46-66 CSV URL/parse
BIS_BASE_URL = "https://stats.bis.org/api/v1"


def _reject_unknown_country(country_code: str) -> None:
    if country_code not in COUNTRY_WHITELIST:
        raise PortError("FAILED", f"country not in whitelist: {country_code!r}")


@dataclass(frozen=True)
class BisMockFetchPort:
    countries: Sequence[str]
    max_rows: int
    data_domain: BisDomain

    def _mock_policy_rows(self, country_code: str, *, start: date | None = None) -> list[dict[str, Any]]:
        today = datetime.now(UTC).date()
        rows: list[dict[str, Any]] = []
        for offset in range(min(self.max_rows, 2)):
            obs_date = today - timedelta(days=30 * offset)
            if start is not None and obs_date < start:
                continue
            rows.append(
                {
                    "country_code": country_code,
                    "observation_date": obs_date.isoformat(),
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

    def _resolve_start(self, req: FetchRequest) -> date | None:
        if req.start_time:
            return date.fromisoformat(req.start_time[:10])
        return None

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(value=self.max_rows, cap=MAX_ROWS)
        country = req.instrument_id or (self.countries[0] if self.countries else "")
        if not country:
            raise PortError("FAILED", "missing country_code for BIS mock fetch")
        _reject_unknown_country(country)

        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"bis-mock-{country}-{uuid.uuid4().hex[:12]}"
        start = self._resolve_start(req)

        if self.data_domain == "central_bank_policy":
            observations = self._mock_policy_rows(country, start=start)
            if not observations:
                raise PortError("EMPTY_RESPONSE", f"no mock observations on/after {start}")
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

        bundle = finalize_bundle(bundle)
        content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=len(observations))


@dataclass(frozen=True)
class BisLiveFetchPort:
    """Bounded live BIS CSV fetch (L2: digital-oracle bis.py L46-66)."""

    countries: Sequence[str]
    max_rows: int
    data_domain: BisDomain

    def _fetch_csv(self, *, path: str, country: str, start_year: int) -> str:
        country_codes = "+".join(self.countries) if len(self.countries) > 1 else country
        url = f"{BIS_BASE_URL}/data/{path}/M.{country_codes}"
        params = urllib.parse.urlencode(
            {"startPeriod": start_year, "detail": "dataonly", "format": "csv"}
        )
        full_url = f"{url}?{params}"
        try:
            with urllib.request.urlopen(full_url, timeout=30) as response:
                return response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            raise PortError("NETWORK_ERROR", str(exc)) from exc

    def _parse_policy_csv(self, payload: str, country: str) -> list[dict[str, Any]]:
        reader = csv.DictReader(StringIO(payload))
        if not reader.fieldnames:
            raise PortError("FAILED", "BIS policy rates CSV has no headers")
        required = {"REF_AREA", "TIME_PERIOD", "OBS_VALUE"}
        if not required.issubset(set(reader.fieldnames)):
            raise PortError("FAILED", "BIS policy rates CSV missing required columns")
        rows: list[dict[str, Any]] = []
        for row in reader:
            if row.get("REF_AREA") != country:
                continue
            rows.append(
                {
                    "country_code": country,
                    "observation_date": f"{row['TIME_PERIOD']}-01",
                    "policy_rate": row["OBS_VALUE"],
                    "frequency": "monthly",
                    "source_used": "bis",
                }
            )
            if len(rows) >= self.max_rows:
                break
        if not rows:
            raise PortError("EMPTY_RESPONSE", f"BIS returned no policy rows for {country}")
        return rows

    def _resolve_start_year(self, req: FetchRequest) -> int:
        if req.start_time:
            return int(req.start_time[:4])
        return datetime.now(UTC).date().year - 5

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(value=self.max_rows, cap=MAX_ROWS)
        country = req.instrument_id or (self.countries[0] if self.countries else "")
        if not country:
            raise PortError("FAILED", "missing country_code for BIS live fetch")
        _reject_unknown_country(country)

        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"bis-live-{country}-{uuid.uuid4().hex[:12]}"
        start_year = self._resolve_start_year(req)

        if self.data_domain == "central_bank_policy":
            csv_text = self._fetch_csv(path="WS_CBPOL", country=country, start_year=start_year)
            observations = self._parse_policy_csv(csv_text, country)
            bundle = build_bis_policy_rate_evidence_bundle(
                observations=observations,
                source_fetch_id=fetch_id,
                content_hash="pending",
                as_of_timestamp=retrieved_at,
                retrieved_at=retrieved_at,
            )
        else:
            # ponytail: credit_gap live CSV deferred; upgrade = bis.py L68-80 credit gap path
            raise PortError("FAILED", "live BIS credit_gap fetch deferred; use central_bank_policy")

        bundle = finalize_bundle(bundle)
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
        from backend.app.datasources.product_live_gate import gate_live_fetch_port

        gate_live_fetch_port(source_id="bis")
        return BisLiveFetchPort(countries=countries, max_rows=max_rows, data_domain=data_domain)
    return BisMockFetchPort(countries=countries, max_rows=max_rows, data_domain=data_domain)
