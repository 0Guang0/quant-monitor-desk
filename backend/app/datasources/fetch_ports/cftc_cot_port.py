"""CFTC COT official macro fetch port (R3H-01 L3 greenfield).

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
from typing import Any

from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.normalizers.evidence_bundle import finalize_bundle, reject_over_cap
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.normalizers.official_macro import build_cot_positioning_evidence_bundle

MARKET_WHITELIST = frozenset({"088691", "13874A", "12460P"})
MAX_MARKETS = 5
MAX_ROWS = 52

# L2 cite: CFTC Public Reporting Environment — Legacy Futures Only (jun7-fc8e)
CFTC_LEGACY_COT_URL = "https://publicreporting.cftc.gov/resource/jun7-fc8e.json"


def _reject_unknown_market(market_code: str) -> None:
    if market_code not in MARKET_WHITELIST:
        raise PortError("FAILED", f"market not in whitelist: {market_code!r}")


@dataclass(frozen=True)
class CftcCotMockFetchPort:
    markets: Sequence[str]
    max_rows: int

    def _mock_rows(self, market_code: str, *, start: date | None = None) -> list[dict[str, Any]]:
        today = datetime.now(UTC).date()
        rows: list[dict[str, Any]] = []
        for offset in range(min(self.max_rows, 3)):
            obs_date = today - timedelta(days=7 * offset)
            if start is not None and obs_date < start:
                continue
            rows.append(
                {
                    "market_code": market_code,
                    "report_date": obs_date.isoformat(),
                    "trader_category": "Noncommercial",
                    "long_contracts": str(100000 - offset * 1000),
                    "short_contracts": str(80000 + offset * 500),
                    "spread_contracts": str(5000),
                    "source_used": "cftc_cot",
                }
            )
        return rows

    def _resolve_start(self, req: FetchRequest) -> date | None:
        if req.start_time:
            return date.fromisoformat(req.start_time[:10])
        return None

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(value=self.max_rows, cap=MAX_ROWS)
        market = req.instrument_id or (self.markets[0] if self.markets else "")
        if not market:
            raise PortError("FAILED", "missing market_code for CFTC COT mock fetch")
        _reject_unknown_market(market)

        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"cftc-mock-{market}-{uuid.uuid4().hex[:12]}"
        start = self._resolve_start(req)
        observations = self._mock_rows(market, start=start)
        if not observations:
            raise PortError("EMPTY_RESPONSE", f"no mock observations on/after {start}")
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


@dataclass(frozen=True)
class CftcCotLiveFetchPort:
    markets: Sequence[str]
    max_rows: int

    def _resolve_start(self, req: FetchRequest) -> date | None:
        if req.start_time:
            return date.fromisoformat(req.start_time[:10])
        return None

    def _parse_report_date(self, raw: str) -> str:
        return raw[:10] if raw else ""

    def _fetch_rows(self, market: str, *, start: date | None) -> list[dict[str, Any]]:
        where_parts = [f"cftc_contract_market_code='{market}'"]
        if start is not None:
            where_parts.append(
                f"report_date_as_yyyy_mm_dd >= '{start.isoformat()}T00:00:00.000'"
            )
        params = urllib.parse.urlencode(
            {
                "$where": " AND ".join(where_parts),
                "$order": "report_date_as_yyyy_mm_dd DESC",
                "$limit": str(self.max_rows),
            }
        )
        url = f"{CFTC_LEGACY_COT_URL}?{params}"
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise PortError("NETWORK_ERROR", str(exc)) from exc
        except json.JSONDecodeError as exc:
            raise PortError("FAILED", f"invalid CFTC JSON: {exc}") from exc

        rows: list[dict[str, Any]] = []
        for row in payload[: self.max_rows]:
            report_date = self._parse_report_date(str(row.get("report_date_as_yyyy_mm_dd") or ""))
            long_c = row.get("noncomm_positions_long_all")
            short_c = row.get("noncomm_positions_short_all")
            if report_date in ("", ".") or long_c in (None, "", ".") or short_c in (None, "", "."):
                continue
            spread_c = row.get("noncomm_positions_spread_all")
            rows.append(
                {
                    "market_code": market,
                    "report_date": report_date,
                    "trader_category": "Noncommercial",
                    "long_contracts": str(long_c),
                    "short_contracts": str(short_c),
                    "spread_contracts": str(spread_c if spread_c not in (None, "", ".") else "0"),
                    "source_used": "cftc_cot",
                }
            )
        if not rows:
            raise PortError("EMPTY_RESPONSE", f"CFTC returned no usable rows for {market}")
        return rows

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(value=self.max_rows, cap=MAX_ROWS)
        market = req.instrument_id or (self.markets[0] if self.markets else "")
        if not market:
            raise PortError("FAILED", "missing market_code for CFTC COT live fetch")
        _reject_unknown_market(market)

        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"cftc-live-{market}-{uuid.uuid4().hex[:12]}"
        start = self._resolve_start(req)
        observations = self._fetch_rows(market, start=start)
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
    if use_mock:
        return CftcCotMockFetchPort(markets=markets, max_rows=max_rows)
    from backend.app.datasources.product_live_gate import gate_live_fetch_port

    gate_live_fetch_port(source_id="cftc_cot")
    return CftcCotLiveFetchPort(markets=markets, max_rows=max_rows)
