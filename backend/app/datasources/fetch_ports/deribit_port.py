"""Deribit crypto derivatives fetch port (R3H-02 L3 greenfield).

No 1:1 upstream reference file; mock surface only — no trading/account API scope.
See R3H_02_REFERENCE_ADOPTION_AUDIT.md.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.app.config import PROJECT_ROOT
from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.normalizers.crypto_market import (
    build_crypto_market_evidence_bundle,
    read_crypto_market_evidence_bundle,
)
from backend.app.datasources.normalizers.evidence_bundle import finalize_bundle, reject_over_cap

MAX_INSTRUMENTS = 5
MAX_SURFACE_ROWS = 50

INSTRUMENT_WHITELIST = frozenset(
    {"BTC-28JUN24-65000-C", "BTC-PERPETUAL", "ETH-28JUN24-3500-P"}
)

REPLAY_FIXTURE = (
    PROJECT_ROOT / "tests/fixtures/replay/crypto_market/deribit/btc_options_surface_replay.json"
)


def _reject_unknown_instrument(name: str) -> None:
    if name not in INSTRUMENT_WHITELIST:
        raise PortError("FAILED", f"instrument not in deribit whitelist: {name!r}")


@dataclass(frozen=True)
class DeribitMockFetchPort:
    """Deterministic mock Deribit port (read-only market data, no account APIs)."""

    instruments: Sequence[str]
    max_surface_rows: int
    replay_path: Path = REPLAY_FIXTURE

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(
            value=self.max_surface_rows,
            cap=MAX_SURFACE_ROWS,
            label="max_surface_rows",
        )
        name = req.instrument_id or (self.instruments[0] if self.instruments else "")
        if not name:
            raise PortError("FAILED", "missing instrument_id for Deribit mock fetch")
        _reject_unknown_instrument(name)

        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"deribit-mock-{name}-{uuid.uuid4().hex[:12]}"
        domain = req.data_domain or "crypto_options_surface"
        if self.replay_path.is_file():
            bundle = read_crypto_market_evidence_bundle(self.replay_path)
            rows = list(bundle.get("instruments") or [])[: self.max_surface_rows]
            bundle = build_crypto_market_evidence_bundle(
                instruments=rows,
                data_domain=domain,
                source_id="deribit",
                source_fetch_id=str(bundle.get("source_fetch_id") or fetch_id),
                content_hash=str(bundle.get("content_hash") or "pending"),
                as_of_timestamp=str(bundle.get("as_of_timestamp") or retrieved_at),
                retrieved_at=str(bundle.get("retrieved_at") or retrieved_at),
            )
        else:
            rows = [
                {
                    "instrument_name": name,
                    "expiration_timestamp": 1719580800,
                    "strike": 65000,
                    "option_type": "call",
                    "mark_iv": 0.52,
                    "source_used": "deribit",
                }
            ]
            bundle = build_crypto_market_evidence_bundle(
                instruments=rows[: self.max_surface_rows],
                data_domain=domain,
                source_id="deribit",
                source_fetch_id=fetch_id,
                content_hash="pending",
                as_of_timestamp=retrieved_at,
                retrieved_at=retrieved_at,
            )
        bundle = finalize_bundle(bundle)
        content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=len(rows))


@dataclass(frozen=True)
class DeribitLiveFetchPort:
    """Bounded live Deribit public API fetch (read-only, no account APIs)."""

    instruments: Sequence[str]
    max_surface_rows: int

    def _book_summary_mark_iv(self, instrument_name: str) -> float:
        """get_instruments omits mark_iv; book summary is the minimal live IV source."""
        encoded = urllib.parse.quote(instrument_name, safe="")
        url = (
            "https://www.deribit.com/api/v2/public/get_book_summary_by_instrument"
            f"?instrument_name={encoded}"
        )
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise PortError("NETWORK_ERROR", str(exc)) from exc
        except json.JSONDecodeError as exc:
            raise PortError("FAILED", f"invalid Deribit book summary JSON: {exc}") from exc
        result = raw.get("result") or []
        if not result:
            raise PortError("EMPTY_RESPONSE", f"Deribit book summary empty for {instrument_name!r}")
        mark_iv = result[0].get("mark_iv")
        if mark_iv is None:
            raise PortError("EMPTY_RESPONSE", f"Deribit book summary missing mark_iv for {instrument_name!r}")
        return float(mark_iv)

    def _live_instruments(self, currency: str = "BTC") -> list[dict[str, Any]]:
        url = f"https://www.deribit.com/api/v2/public/get_instruments?currency={currency}&kind=option"
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise PortError("NETWORK_ERROR", str(exc)) from exc
        except json.JSONDecodeError as exc:
            raise PortError("FAILED", f"invalid Deribit JSON: {exc}") from exc
        result = raw.get("result") or []
        rows: list[dict[str, Any]] = []
        for item in result[: self.max_surface_rows]:
            rows.append(
                {
                    "instrument_name": item.get("instrument_name"),
                    "expiration_timestamp": item.get("expiration_timestamp"),
                    "strike": item.get("strike"),
                    "option_type": "call" if item.get("option_type") == "call" else "put",
                    "mark_iv": item.get("mark_iv"),
                    "source_used": "deribit",
                }
            )
        if not rows:
            raise PortError("EMPTY_RESPONSE", "Deribit returned no instruments")
        return rows

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(
            value=self.max_surface_rows,
            cap=MAX_SURFACE_ROWS,
            label="max_surface_rows",
        )
        name = req.instrument_id or (self.instruments[0] if self.instruments else "")
        if not name:
            raise PortError("FAILED", "missing instrument_id for Deribit live fetch")

        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"deribit-live-{name}-{uuid.uuid4().hex[:12]}"
        domain = req.data_domain or "crypto_options_surface"
        rows = self._live_instruments()
        target = next((row for row in rows if row.get("instrument_name") == name), rows[0])
        target_name = str(target.get("instrument_name") or name)
        target["mark_iv"] = self._book_summary_mark_iv(target_name)
        rows = [target]
        bundle = build_crypto_market_evidence_bundle(
            instruments=rows[: self.max_surface_rows],
            data_domain=domain,
            source_id="deribit",
            source_fetch_id=fetch_id,
            content_hash="pending",
            as_of_timestamp=retrieved_at,
            retrieved_at=retrieved_at,
        )
        bundle = finalize_bundle(bundle)
        content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=len(rows))


def create_deribit_fetch_port(
    *,
    instruments: Sequence[str],
    max_surface_rows: int,
    use_mock: bool = True,
):
    if len(instruments) > MAX_INSTRUMENTS:
        raise PortError("FAILED", f"max {MAX_INSTRUMENTS} instruments allowed, got {len(instruments)}")
    if use_mock:
        return DeribitMockFetchPort(instruments=instruments, max_surface_rows=max_surface_rows)
    from backend.app.datasources.product_live_gate import gate_live_fetch_port

    gate_live_fetch_port(source_id="deribit")
    return DeribitLiveFetchPort(instruments=instruments, max_surface_rows=max_surface_rows)
