"""US Treasury official macro fetch port (R3H-01 L3 greenfield).

No 1:1 upstream reference file; evidence via official_macro_evidence_v1 (same normalizer as fred).
OpenBB providers/ = architecture_only. See R3H_01_REFERENCE_ADOPTION_AUDIT.md.
"""

from __future__ import annotations

import csv
import json
import urllib.error
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
    build_inflation_expectation_evidence_bundle,
    build_yield_curve_evidence_bundle,
)

# R3H-01 caps SSOT (frozen §7 production-entry defaults)
YIELD_CURVE_TENOR_WHITELIST = frozenset(
    {"1M", "2M", "3M", "4M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"}
)
INFLATION_METRIC_WHITELIST = frozenset({"breakeven_10y", "breakeven_5y", "tips_real_yield_10y"})
MAX_TENORS = 20
MAX_ROWS = 500

# L2 cite: Treasury Data Center daily par yield curve CSV (home.treasury.gov)
TREASURY_YIELD_CSV_URL = (
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
    "daily-treasury-rates.csv/{year}/all?type=daily_treasury_yield_curve"
)
TENOR_TO_CSV_COLUMN: dict[str, str] = {
    "1M": "1 Mo",
    "2M": "2 Mo",
    "3M": "3 Mo",
    "4M": "4 Mo",
    "6M": "6 Mo",
    "1Y": "1 Yr",
    "2Y": "2 Yr",
    "3Y": "3 Yr",
    "5Y": "5 Yr",
    "7Y": "7 Yr",
    "10Y": "10 Yr",
    "20Y": "20 Yr",
    "30Y": "30 Yr",
}

TreasuryDomain = Literal["us_treasury_yield_curve", "inflation_expectation"]


def _reject_unknown_tenor(tenor: str, *, data_domain: TreasuryDomain) -> None:
    if data_domain == "us_treasury_yield_curve":
        if tenor not in YIELD_CURVE_TENOR_WHITELIST:
            raise PortError("FAILED", f"tenor not in whitelist: {tenor!r}")
    elif tenor not in INFLATION_METRIC_WHITELIST:
        raise PortError("FAILED", f"metric not in whitelist: {tenor!r}")


@dataclass(frozen=True)
class UsTreasuryMockFetchPort:
    """Deterministic mock US Treasury port (no network)."""

    tenors: Sequence[str]
    max_rows: int
    data_domain: TreasuryDomain

    def _mock_yield_curve_rows(self, tenor: str, *, start: date | None = None) -> list[dict[str, Any]]:
        today = datetime.now(UTC).date()
        rows: list[dict[str, Any]] = []
        for offset in range(min(self.max_rows, 3)):
            obs_date = today - timedelta(days=offset)
            if start is not None and obs_date < start:
                continue
            rows.append(
                {
                    "observation_date": obs_date.isoformat(),
                    "tenor": tenor,
                    "yield_percent": str(4.25 - offset * 0.01),
                    "source_used": "us_treasury",
                }
            )
        return rows

    def _mock_inflation_rows(self, metric_name: str, *, start: date | None = None) -> list[dict[str, Any]]:
        today = datetime.now(UTC).date()
        rows: list[dict[str, Any]] = []
        for offset in range(min(self.max_rows, 3)):
            obs_date = today - timedelta(days=30 * offset)
            if start is not None and obs_date < start:
                continue
            rows.append(
                {
                    "observation_date": obs_date.isoformat(),
                    "metric_name": metric_name,
                    "metric_value": str(2.15 - offset * 0.02),
                    "source_used": "us_treasury",
                }
            )
        return rows

    def _resolve_start(self, req: FetchRequest) -> date | None:
        if req.start_time:
            return date.fromisoformat(req.start_time[:10])
        return None

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(value=self.max_rows, cap=MAX_ROWS)
        instrument = req.instrument_id or (self.tenors[0] if self.tenors else "")
        if not instrument:
            raise PortError("FAILED", "missing instrument_id for US Treasury mock fetch")
        _reject_unknown_tenor(instrument, data_domain=self.data_domain)

        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"treasury-mock-{instrument}-{uuid.uuid4().hex[:12]}"
        start = self._resolve_start(req)

        if self.data_domain == "us_treasury_yield_curve":
            observations = self._mock_yield_curve_rows(instrument, start=start)
            if not observations:
                raise PortError("EMPTY_RESPONSE", f"no mock observations on/after {start}")
            bundle = build_yield_curve_evidence_bundle(
                observations=observations,
                source_fetch_id=fetch_id,
                content_hash="pending",
                as_of_timestamp=retrieved_at,
                retrieved_at=retrieved_at,
            )
        else:
            observations = self._mock_inflation_rows(instrument, start=start)
            if not observations:
                raise PortError("EMPTY_RESPONSE", f"no mock observations on/after {start}")
            bundle = build_inflation_expectation_evidence_bundle(
                observations=observations,
                source_fetch_id=fetch_id,
                content_hash="pending",
                as_of_timestamp=retrieved_at,
                retrieved_at=retrieved_at,
            )

        bundle = finalize_bundle(bundle)
        content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(
            content=content,
            file_type="json",
            row_count=len(bundle["observations"]),
        )


@dataclass(frozen=True)
class UsTreasuryLiveFetchPort:
    tenors: Sequence[str]
    max_rows: int
    data_domain: TreasuryDomain

    def _resolve_start(self, req: FetchRequest) -> date | None:
        if req.start_time:
            return date.fromisoformat(req.start_time[:10])
        return None

    def _fetch_yield_csv(self, year: int) -> str:
        url = TREASURY_YIELD_CSV_URL.format(year=year)
        req = urllib.request.Request(url, headers={"User-Agent": "quant-monitor-desk/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            raise PortError("NETWORK_ERROR", str(exc)) from exc

    def _parse_csv_date(self, raw: str) -> str:
        month, day, year = raw.split("/")
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    def _yield_curve_rows(self, tenor: str, *, start: date | None) -> list[dict[str, Any]]:
        column = TENOR_TO_CSV_COLUMN.get(tenor)
        if column is None:
            raise PortError("FAILED", f"no Treasury CSV column for tenor {tenor!r}")

        today = datetime.now(UTC).date()
        years = {today.year}
        if start is not None:
            years.add(start.year)

        rows: list[dict[str, Any]] = []
        for year in sorted(years, reverse=True):
            csv_text = self._fetch_yield_csv(year)
            reader = csv.DictReader(StringIO(csv_text))
            if not reader.fieldnames or column not in reader.fieldnames:
                raise PortError("FAILED", f"Treasury yield CSV missing column {column!r}")
            for row in reader:
                raw_date = str(row.get("Date") or "").strip()
                raw_yield = str(row.get(column) or "").strip()
                if not raw_date or raw_yield in ("", ".", "N/A"):
                    continue
                obs_date = self._parse_csv_date(raw_date)
                if start is not None and obs_date < start.isoformat():
                    continue
                rows.append(
                    {
                        "observation_date": obs_date,
                        "tenor": tenor,
                        "yield_percent": raw_yield,
                        "source_used": "us_treasury",
                    }
                )
                if len(rows) >= self.max_rows:
                    break
            if len(rows) >= self.max_rows:
                break

        rows.sort(key=lambda item: item["observation_date"], reverse=True)
        rows = rows[: self.max_rows]
        if not rows:
            raise PortError("EMPTY_RESPONSE", f"Treasury returned no usable rows for {tenor}")
        return rows

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(value=self.max_rows, cap=MAX_ROWS)
        instrument = req.instrument_id or (self.tenors[0] if self.tenors else "")
        if not instrument:
            raise PortError("FAILED", "missing instrument_id for US Treasury live fetch")
        _reject_unknown_tenor(instrument, data_domain=self.data_domain)

        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"treasury-live-{instrument}-{uuid.uuid4().hex[:12]}"
        start = self._resolve_start(req)

        if self.data_domain == "us_treasury_yield_curve":
            observations = self._yield_curve_rows(instrument, start=start)
            bundle = build_yield_curve_evidence_bundle(
                observations=observations,
                source_fetch_id=fetch_id,
                content_hash="pending",
                as_of_timestamp=retrieved_at,
                retrieved_at=retrieved_at,
            )
        else:
            # ponytail: inflation_expectation live deferred; upgrade = Treasury TIPS/breakeven dataset
            raise PortError(
                "FAILED",
                "live us_treasury inflation_expectation deferred; use us_treasury_yield_curve",
            )

        bundle = finalize_bundle(bundle)
        content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(
            content=content,
            file_type="json",
            row_count=len(bundle["observations"]),
        )


def create_us_treasury_fetch_port(
    *,
    tenors: Sequence[str],
    max_rows: int,
    data_domain: TreasuryDomain,
    use_mock: bool = True,
):
    if len(tenors) > MAX_TENORS:
        raise PortError("FAILED", f"max {MAX_TENORS} tenors allowed, got {len(tenors)}")
    if use_mock:
        return UsTreasuryMockFetchPort(tenors=tenors, max_rows=max_rows, data_domain=data_domain)
    from backend.app.datasources.product_live_gate import gate_live_fetch_port

    gate_live_fetch_port(source_id="us_treasury")
    return UsTreasuryLiveFetchPort(tenors=tenors, max_rows=max_rows, data_domain=data_domain)
