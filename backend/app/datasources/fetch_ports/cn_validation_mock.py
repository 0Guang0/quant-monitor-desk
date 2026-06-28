"""Shared mock bar fetch for CN validation aggregator ports (R3H-03 ponytail)."""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.normalizers.cn_market import (
    aggregator_quality_flags,
    build_cn_market_evidence_bundle,
)
from backend.app.datasources.normalizers.evidence_bundle import finalize_bundle, reject_over_cap


def cn_validation_mock_fetch_payload(
    req: FetchRequest,
    *,
    source_id: str,
    symbols: Sequence[str],
    max_rows: int,
    max_rows_cap: int,
    max_symbols_cap: int,
    symbol_whitelist: frozenset[str],
    bar_ohlcv: tuple[float, float, float, float, int],
    conflict_evidence: dict[str, Any] | None = None,
) -> FetchPayload:
    """Build deterministic mock daily-bar evidence for validation-only CN sources."""
    reject_over_cap(value=max_rows, cap=max_rows_cap)
    if len(symbols) > max_symbols_cap:
        raise PortError("FAILED", f"max {max_symbols_cap} symbols allowed")
    symbol = req.instrument_id or (symbols[0] if symbols else "")
    if not symbol:
        raise PortError("FAILED", f"missing instrument_id for {source_id} fetch")
    if symbol not in symbol_whitelist:
        raise PortError("FAILED", f"symbol not in {source_id} whitelist: {symbol!r}")

    open_, high, low, close, volume = bar_ohlcv
    retrieved_at = datetime.now(UTC).isoformat()
    fetch_id = f"{source_id}-mock-{symbol}-{uuid.uuid4().hex[:12]}"
    today = datetime.now(UTC).date()
    bars = [
        {
            "instrument_id": symbol,
            "trade_date": (today - timedelta(days=offset)).isoformat(),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
            "source_used": source_id,
        }
        for offset in range(min(max_rows, 2))
    ]
    bundle = build_cn_market_evidence_bundle(
        bars=bars,
        data_domain=req.data_domain or "cn_equity_daily_bar",
        source_id=source_id,
        source_fetch_id=fetch_id,
        content_hash="pending",
        as_of_timestamp=retrieved_at,
        retrieved_at=retrieved_at,
        quality_flags=aggregator_quality_flags(source_id=source_id),
        conflict_evidence=conflict_evidence,
    )
    bundle = finalize_bundle(bundle)
    content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
    return FetchPayload(content=content, file_type="json", row_count=len(bars))
