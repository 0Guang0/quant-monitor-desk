"""Shared mock fetch for QMT authorization-gated ports (R3H-03 ponytail)."""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.auth.license_gate import require_license_gate
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.normalizers.cn_market import build_cn_market_evidence_bundle
from backend.app.datasources.normalizers.evidence_bundle import finalize_bundle, reject_over_cap

MAX_SYMBOLS = 3
MAX_ROWS = 3
MINUTE_BARS_ENABLED = False


def qmt_mock_fetch_payload(
    req: FetchRequest,
    *,
    source_id: str,
    symbols: Sequence[str],
    max_rows: int,
    bar_ohlcv: tuple[float, float, float, float, int],
) -> FetchPayload:
    """Mock daily-bar fetch for QMT xtdata / xqshare after license_gate."""
    require_license_gate(source_id)
    domain = req.data_domain or "cn_equity_daily_bar"
    if "minute" in domain:
        raise PortError("FAILED", f"minute bars rejected (minute_bars_enabled={MINUTE_BARS_ENABLED})")
    reject_over_cap(value=max_rows, cap=MAX_ROWS)
    symbol = req.instrument_id or (symbols[0] if symbols else "")
    if not symbol:
        raise PortError("FAILED", f"missing instrument_id for {source_id} fetch")

    open_, high, low, close, volume = bar_ohlcv
    retrieved_at = datetime.now(UTC).isoformat()
    fetch_id = f"{source_id.split('_')[-1]}-mock-{symbol}-{uuid.uuid4().hex[:12]}"
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
        for offset in range(min(max_rows, MAX_ROWS))
    ]
    bundle = build_cn_market_evidence_bundle(
        bars=bars,
        data_domain=domain,
        source_id=source_id,
        source_fetch_id=fetch_id,
        content_hash="pending",
        as_of_timestamp=retrieved_at,
        retrieved_at=retrieved_at,
    )
    bundle = finalize_bundle(bundle)
    content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
    return FetchPayload(content=content, file_type="json", row_count=len(bars))
