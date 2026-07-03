"""World Bank official macro fetch port (R3H-01 L3 greenfield).

No 1:1 upstream reference file; mock-first; official_macro_evidence_v1.
See R3H_01_REFERENCE_ADOPTION_AUDIT.md.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
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

WB_API_BASE = "https://api.worldbank.org/v2"


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

    def _mock_rows(self, country_code: str, indicator_id: str, *, start: date | None = None) -> list[dict[str, Any]]:
        today = datetime.now(UTC).date()
        rows: list[dict[str, Any]] = []
        for offset in range(min(self.max_rows, 3)):
            obs_date = today - timedelta(days=365 * offset)
            if start is not None and obs_date < start:
                continue
            rows.append(
                {
                    "country_code": country_code,
                    "indicator_id": indicator_id,
                    "observation_date": obs_date.isoformat(),
                    "value": str(1e13 - offset * 1e11),
                    "unit": "USD" if "GDP" in indicator_id else "count",
                    "source_used": "world_bank",
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
        indicator = self.indicators[0] if self.indicators else ""
        if not country or not indicator:
            raise PortError("FAILED", "missing country/indicator for World Bank mock fetch")
        _reject_unknown_pair(country_code=country, indicator_id=indicator)

        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"wb-mock-{country}-{uuid.uuid4().hex[:12]}"
        start = self._resolve_start(req)
        observations = self._mock_rows(country, indicator, start=start)
        if not observations:
            raise PortError("EMPTY_RESPONSE", f"no mock observations on/after {start}")
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


def _wb_live_observations(
    country_code: str,
    indicator_id: str,
    *,
    max_rows: int,
    start: date | None,
) -> list[dict[str, Any]]:
    params: dict[str, str | int] = {
        "format": "json",
        "per_page": max_rows,
    }
    if start is not None:
        params["date"] = f"{start.year}:{datetime.now(UTC).date().year}"
    query = urllib.parse.urlencode(params)
    url = f"{WB_API_BASE}/country/{country_code}/indicator/{indicator_id}?{query}"
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise PortError("NETWORK_ERROR", str(exc)) from exc
    except json.JSONDecodeError as exc:
        raise PortError("FAILED", f"invalid World Bank JSON: {exc}") from exc

    if not isinstance(payload, list) or len(payload) < 2:
        raise PortError("FAILED", "World Bank API returned unexpected envelope")
    rows = payload[1] or []
    observations: list[dict[str, Any]] = []
    for row in rows[:max_rows]:
        raw_value = row.get("value")
        if raw_value in (None, ""):
            continue
        obs_date = str(row.get("date") or "")
        if start is not None and obs_date:
            if len(obs_date) == 4:
                if int(obs_date) < start.year:
                    continue
            elif obs_date < start.isoformat():
                continue
        observations.append(
            {
                "country_code": country_code,
                "indicator_id": indicator_id,
                "observation_date": f"{obs_date}-01-01" if len(obs_date) == 4 else obs_date,
                "value": str(raw_value),
                "unit": "USD" if "GDP" in indicator_id else "count",
                "source_used": "world_bank",
            }
        )
    if not observations:
        raise PortError("EMPTY_RESPONSE", f"World Bank returned no rows for {country_code}/{indicator_id}")
    return observations


@dataclass(frozen=True)
class WorldBankLiveFetchPort:
    """Bounded live World Bank indicator API fetch."""

    countries: Sequence[str]
    indicators: Sequence[str]
    max_rows: int
    data_domain: WorldBankDomain

    def _resolve_start(self, req: FetchRequest) -> date | None:
        if req.start_time:
            return date.fromisoformat(req.start_time[:10])
        return None

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(value=self.max_rows, cap=MAX_ROWS)
        country = req.instrument_id or (self.countries[0] if self.countries else "")
        if not country:
            raise PortError("FAILED", "missing country for World Bank live fetch")
        start = self._resolve_start(req)
        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"wb-live-{country}-{uuid.uuid4().hex[:12]}"
        observations: list[dict[str, Any]] = []
        per_indicator_cap = max(1, self.max_rows // max(len(self.indicators), 1))
        for indicator in self.indicators:
            _reject_unknown_pair(country_code=country, indicator_id=indicator)
            try:
                observations.extend(
                    _wb_live_observations(
                        country,
                        indicator,
                        max_rows=per_indicator_cap,
                        start=start,
                    )
                )
            except PortError as exc:
                if exc.status == "NETWORK_ERROR" and len(self.indicators) > 1:
                    continue
                raise
            if len(observations) >= self.max_rows:
                observations = observations[: self.max_rows]
                break
        if not observations:
            raise PortError("EMPTY_RESPONSE", f"no World Bank observations for {country}")
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
    if use_mock:
        return WorldBankMockFetchPort(
            countries=countries,
            indicators=indicators,
            max_rows=max_rows,
            data_domain=data_domain,
        )
    from backend.app.datasources.product_live_gate import gate_live_fetch_port

    gate_live_fetch_port(source_id="world_bank")
    return WorldBankLiveFetchPort(
        countries=countries,
        indicators=indicators,
        max_rows=max_rows,
        data_domain=data_domain,
    )
