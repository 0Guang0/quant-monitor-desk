"""US Treasury official macro fetch port (R3H-01 L2).

Mock-first yield curve + inflation expectation reference; emits
official_macro_evidence_v1 via normalizer SSOT.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
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

    def _mock_yield_curve_rows(self, tenor: str) -> list[dict[str, Any]]:
        today = datetime.now(UTC).date()
        rows: list[dict[str, Any]] = []
        for offset in range(min(self.max_rows, 3)):
            rows.append(
                {
                    "observation_date": (today - timedelta(days=offset)).isoformat(),
                    "tenor": tenor,
                    "yield_percent": str(4.25 - offset * 0.01),
                    "source_used": "us_treasury",
                }
            )
        return rows

    def _mock_inflation_rows(self, metric_name: str) -> list[dict[str, Any]]:
        today = datetime.now(UTC).date()
        rows: list[dict[str, Any]] = []
        for offset in range(min(self.max_rows, 3)):
            rows.append(
                {
                    "observation_date": (today - timedelta(days=30 * offset)).isoformat(),
                    "metric_name": metric_name,
                    "metric_value": str(2.15 - offset * 0.02),
                    "source_used": "us_treasury",
                }
            )
        return rows

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(value=self.max_rows, cap=MAX_ROWS)
        instrument = req.instrument_id or (self.tenors[0] if self.tenors else "")
        if not instrument:
            raise PortError("FAILED", "missing instrument_id for US Treasury mock fetch")
        _reject_unknown_tenor(instrument, data_domain=self.data_domain)

        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"treasury-mock-{instrument}-{uuid.uuid4().hex[:12]}"

        if self.data_domain == "us_treasury_yield_curve":
            observations = self._mock_yield_curve_rows(instrument)
            bundle = build_yield_curve_evidence_bundle(
                observations=observations,
                source_fetch_id=fetch_id,
                content_hash="pending",
                as_of_timestamp=retrieved_at,
                retrieved_at=retrieved_at,
            )
        else:
            observations = self._mock_inflation_rows(instrument)
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


def create_us_treasury_fetch_port(
    *,
    tenors: Sequence[str],
    max_rows: int,
    data_domain: TreasuryDomain,
    use_mock: bool = True,
):
    if len(tenors) > MAX_TENORS:
        raise PortError("FAILED", f"max {MAX_TENORS} tenors allowed, got {len(tenors)}")
    if not use_mock:
        # ponytail: live Treasury API deferred; mock is default safe path for R3H-01
        raise PortError("FAILED", "live US Treasury fetch not enabled in R3H-01; use mock")
    return UsTreasuryMockFetchPort(tenors=tenors, max_rows=max_rows, data_domain=data_domain)
