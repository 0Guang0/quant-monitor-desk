"""FRED official macro fetch port (R3H-01 L2 copy_and_rewrite).

L2 migrate from backend/app/ops/fred_fetch_ports.py; OpenBB fred provider = architecture_only.
MIT attribution: urllib live fetch pattern (QMD-owned); no AGPL runtime.
See R3H_01_REFERENCE_ADOPTION_AUDIT.md.
"""

from __future__ import annotations

import json
import os
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
from backend.app.datasources.normalizers.official_macro import build_fred_evidence_bundle

# R3H-01 caps SSOT (frozen §7 production-entry defaults)
P0_SERIES_WHITELIST = frozenset({"DGS10", "T10Y3M", "VIXCLS", "SP500", "DFII10"})
MAX_SERIES = 10
MAX_ROWS_PER_SERIES = 500
MAX_WINDOW_DAYS = 120


def _fred_api_key() -> str | None:
    raw = os.environ.get("FRED_API_KEY")
    if not raw or not str(raw).strip():
        return None
    # ponytail: FRED requires 32-char lowercase; normalize to avoid 400 on mixed case
    return str(raw).strip().lower()


def _reject_unknown_series(series_id: str) -> None:
    if series_id not in P0_SERIES_WHITELIST:
        raise PortError("FAILED", f"series not in P0 whitelist: {series_id!r}")


@dataclass(frozen=True)
class FredMockFetchPort:
    """Deterministic mock FRED port emitting official_macro_evidence_v1 (no network)."""

    series_ids: Sequence[str]
    max_rows: int
    date_window: str = "3y"

    def _mock_observations(self, series_id: str) -> list[dict[str, Any]]:
        today = datetime.now(UTC).date()
        observations: list[dict[str, Any]] = []
        for offset in range(min(self.max_rows, 3)):
            observations.append(
                {
                    "series_id": series_id,
                    "observation_date": (today - timedelta(days=30 * offset)).isoformat(),
                    "value": str(4.25 - offset * 0.01),
                }
            )
        return observations

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(value=self.max_rows, cap=MAX_ROWS_PER_SERIES)
        series_id = req.instrument_id or (self.series_ids[0] if self.series_ids else "")
        if not series_id:
            raise PortError("FAILED", "missing series_id for FRED mock fetch")
        _reject_unknown_series(series_id)

        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"fred-mock-{series_id}-{uuid.uuid4().hex[:12]}"
        bundle = build_fred_evidence_bundle(
            observations=self._mock_observations(series_id),
            series_id=series_id,
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
class FredLiveFetchPort:
    """Bounded live FRED API fetch (opt-in, requires FRED_API_KEY)."""

    series_ids: Sequence[str]
    max_rows: int
    date_window: str = "3y"

    def _window_start(self) -> date:
        # ponytail: L2 port caps window at MAX_WINDOW_DAYS; R3E pilot auth layer may apply stricter bounds
        days = min(MAX_WINDOW_DAYS, 365 * 3 if self.date_window == "3y" else MAX_WINDOW_DAYS)
        return datetime.now(UTC).date() - timedelta(days=days)

    def _live_observations(self, series_id: str) -> list[dict[str, Any]]:
        api_key = _fred_api_key()
        if not api_key:
            raise PortError("USER_AUTH_REQUIRED", "FRED_API_KEY missing for live fetch")

        start = self._window_start()
        params = urllib.parse.urlencode(
            {
                "series_id": series_id,
                "api_key": api_key,
                "file_type": "json",
                "observation_start": start.isoformat(),
                "sort_order": "desc",
                "limit": self.max_rows,
            }
        )
        url = f"https://api.stlouisfed.org/fred/series/observations?{params}"
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise PortError("NETWORK_ERROR", str(exc)) from exc
        except json.JSONDecodeError as exc:
            raise PortError("FAILED", f"invalid FRED JSON: {exc}") from exc

        observations: list[dict[str, Any]] = []
        for obs in (raw.get("observations") or [])[: self.max_rows]:
            value = obs.get("value")
            if value in (None, ".", ""):
                continue
            observations.append(
                {
                    "series_id": series_id,
                    "observation_date": obs.get("date"),
                    "value": value,
                }
            )
        if not observations:
            raise PortError("EMPTY_RESPONSE", f"FRED returned no usable rows for {series_id}")
        return observations

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(value=self.max_rows, cap=MAX_ROWS_PER_SERIES)
        series_id = req.instrument_id or (self.series_ids[0] if self.series_ids else "")
        if not series_id:
            raise PortError("FAILED", "missing series_id for FRED live fetch")
        _reject_unknown_series(series_id)

        observations = self._live_observations(series_id)
        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"fred-live-{series_id}-{uuid.uuid4().hex[:12]}"
        bundle = build_fred_evidence_bundle(
            observations=observations,
            series_id=series_id,
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


def create_fred_fetch_port(
    *,
    series_ids: Sequence[str],
    max_rows: int,
    date_window: str = "3y",
    use_mock: bool = True,
):
    if len(series_ids) > MAX_SERIES:
        raise PortError("FAILED", f"max {MAX_SERIES} series allowed, got {len(series_ids)}")
    if use_mock:
        return FredMockFetchPort(series_ids=series_ids, max_rows=max_rows, date_window=date_window)
    from backend.app.datasources.product_live_gate import gate_live_fetch_port

    gate_live_fetch_port(source_id="fred")
    return FredLiveFetchPort(series_ids=series_ids, max_rows=max_rows, date_window=date_window)
