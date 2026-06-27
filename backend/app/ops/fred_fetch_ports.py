"""FRED sandbox pilot fetch ports — mock and optional live (B01-FRED)."""

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

from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.fetch_result import FetchRequest


def _fred_api_key() -> str | None:
    raw = os.environ.get("FRED_API_KEY")
    if not raw or not str(raw).strip():
        return None
    # ponytail: FRED requires 32-char lowercase; normalize to avoid 400 on mixed case
    return str(raw).strip().lower()


@dataclass(frozen=True)
class FredMockFetchPort:
    """Deterministic mock FRED payload for sandbox pilot (no network)."""

    series_ids: Sequence[str]
    max_rows: int
    date_window: str = "3y"

    def fetch_series_payload(self, series_id: str) -> dict:
        today = datetime.now(UTC).date()
        rows = []
        for offset in range(min(self.max_rows, 3)):
            obs_date = (today - timedelta(days=30 * offset)).isoformat()
            rows.append(
                {
                    "series_id": series_id,
                    "observation_date": obs_date,
                    "value": str(4.25 - offset * 0.01),
                }
            )
        fetch_id = f"fred-mock-{series_id}-{uuid.uuid4().hex[:12]}"
        retrieved_at = datetime.now(UTC).isoformat()
        return {
            "series_id": series_id,
            "source": "fred",
            "date_window": self.date_window,
            "rows": rows,
            "source_fetch_id": fetch_id,
            "as_of_timestamp": retrieved_at,
            "retrieved_at": retrieved_at,
        }

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        series_id = req.instrument_id or (self.series_ids[0] if self.series_ids else "")
        if not series_id:
            raise PortError("FAILED", "missing series_id for FRED mock fetch")
        payload = self.fetch_series_payload(series_id)
        content = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=len(payload["rows"]))


@dataclass(frozen=True)
class FredLiveFetchPort:
    """Bounded live FRED API fetch (opt-in, requires FRED_API_KEY)."""

    series_ids: Sequence[str]
    max_rows: int
    date_window: str = "3y"

    def _window_start(self) -> date:
        # ponytail: coarse 3y window; upgrade path = parse date_window label
        return datetime.now(UTC).date() - timedelta(days=365 * 3)

    def fetch_series_payload(self, series_id: str) -> dict:
        api_key = _fred_api_key()
        if not api_key:
            raise PortError("FAILED", "FRED_API_KEY missing for live fetch")

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

        observations = raw.get("observations") or []
        rows = []
        for obs in observations[: self.max_rows]:
            value = obs.get("value")
            if value in (None, ".", ""):
                continue
            rows.append(
                {
                    "series_id": series_id,
                    "observation_date": obs.get("date"),
                    "value": value,
                }
            )
        if not rows:
            raise PortError("EMPTY_RESPONSE", f"FRED returned no usable rows for {series_id}")

        fetch_id = f"fred-live-{series_id}-{uuid.uuid4().hex[:12]}"
        retrieved_at = datetime.now(UTC).isoformat()
        return {
            "series_id": series_id,
            "source": "fred",
            "date_window": self.date_window,
            "rows": rows,
            "source_fetch_id": fetch_id,
            "as_of_timestamp": retrieved_at,
            "retrieved_at": retrieved_at,
        }

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        series_id = req.instrument_id or (self.series_ids[0] if self.series_ids else "")
        if not series_id:
            raise PortError("FAILED", "missing series_id for FRED live fetch")
        payload = self.fetch_series_payload(series_id)
        content = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=len(payload["rows"]))


def create_fred_fetch_port(
    *,
    series_ids: Sequence[str],
    max_rows: int,
    date_window: str = "3y",
    use_mock: bool = True,
):
    if use_mock:
        return FredMockFetchPort(series_ids=series_ids, max_rows=max_rows, date_window=date_window)
    return FredLiveFetchPort(series_ids=series_ids, max_rows=max_rows, date_window=date_window)
