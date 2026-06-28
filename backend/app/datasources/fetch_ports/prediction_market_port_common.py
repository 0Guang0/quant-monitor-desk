"""Shared kalshi/polymarket probability fetch helpers (R3H-04).

ponytail: per-source ports stay split for whitelist/API isolation; only fetch_payload
finalization is shared. Upgrade path = extract live urllib if a third prediction source appears.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Any

from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.normalizers.evidence_bundle import (
    finalize_bundle,
    reject_over_cap,
    reject_window_span_over_cap,
)
from backend.app.datasources.normalizers.probability_signal import (
    build_probability_signal_evidence_bundle,
)

MAX_LIVE_RESPONSE_BYTES = 1_048_576


def read_bounded_http_body(response: Any, *, label: str = "response") -> bytes:
    """ponytail: cap live body read at 1MiB; upgrade path = streaming JSON parser."""
    raw = response.read(MAX_LIVE_RESPONSE_BYTES + 1)
    if len(raw) > MAX_LIVE_RESPONSE_BYTES:
        raise PortError("FAILED", f"{label} exceeds {MAX_LIVE_RESPONSE_BYTES} bytes")
    return raw


def build_probability_market_fetch_payload(
    req: FetchRequest,
    *,
    max_markets: int,
    max_markets_cap: int,
    max_window_days: int,
    instruments: Sequence[str],
    source_id: str,
    fetch_id_prefix: str,
    resolve_instrument: Callable[[FetchRequest, Sequence[str]], str],
    build_signals: Callable[[str], list[dict[str, Any]]],
    live: bool,
) -> FetchPayload:
    reject_over_cap(value=max_markets, cap=max_markets_cap, label="max_markets")
    reject_window_span_over_cap(
        start_time=req.start_time,
        end_time=req.end_time,
        cap=max_window_days,
    )
    instrument = resolve_instrument(req, instruments)
    if not instrument:
        mode = "live" if live else "mock"
        raise PortError("FAILED", f"missing instrument_id for {source_id} {mode} fetch")

    retrieved_at = datetime.now(UTC).isoformat()
    fetch_id = f"{fetch_id_prefix}-{instrument}-{uuid.uuid4().hex[:12]}"
    domain = req.data_domain or "prediction_market_probability"
    signals = build_signals(instrument)
    bundle = build_probability_signal_evidence_bundle(
        signals=signals[:max_markets],
        data_domain=domain,
        source_id=source_id,
        source_fetch_id=fetch_id,
        content_hash="pending",
        as_of_timestamp=retrieved_at,
        retrieved_at=retrieved_at,
    )
    bundle = finalize_bundle(bundle)
    content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
    return FetchPayload(content=content, file_type="json", row_count=len(signals))
