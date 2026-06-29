"""Baostock CN equity daily-bar fetch port (R3H-03).

L2 migrate from backend/app/ops/staged_pilot_fetch_ports.py (BaostockStagedFetchPort) and
backend/app/datasources/adapters/baostock.py skeleton field mapping; QMD cn_market_evidence_v1.
See R3H_03_REFERENCE_ADOPTION_AUDIT.md.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from backend.app.config import PROJECT_ROOT
from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.normalizers.cn_market import (
    build_cn_market_evidence_bundle,
    read_cn_market_evidence_bundle,
)
from backend.app.datasources.normalizers.evidence_bundle import (
    finalize_bundle,
    reject_over_cap,
    reject_window_span_over_cap,
)

MAX_SYMBOLS = 5
MAX_ROWS = 500
MAX_WINDOW_DAYS = 120
SYMBOL_WHITELIST = frozenset({"sh.600519", "sz.000001", "sh.601318"})

REPLAY_FIXTURE = (
    PROJECT_ROOT / "tests/fixtures/replay/cn_market/baostock/sh600519_daily_replay.json"
)


def _reject_unknown_symbol(symbol: str) -> None:
    if symbol not in SYMBOL_WHITELIST:
        raise PortError("FAILED", f"symbol not in baostock whitelist: {symbol!r}")


@dataclass(frozen=True)
class BaostockMockFetchPort:
    symbols: Sequence[str]
    max_rows: int
    replay_path: Path = REPLAY_FIXTURE

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(value=self.max_rows, cap=MAX_ROWS)
        reject_window_span_over_cap(
            start_time=req.start_time,
            end_time=req.end_time,
            cap=MAX_WINDOW_DAYS,
        )
        if len(self.symbols) > MAX_SYMBOLS:
            raise PortError("FAILED", f"max {MAX_SYMBOLS} symbols allowed")
        symbol = req.instrument_id or (self.symbols[0] if self.symbols else "")
        if not symbol:
            raise PortError("FAILED", "missing instrument_id for baostock fetch")
        _reject_unknown_symbol(symbol)

        if self.replay_path.is_file():
            bundle = read_cn_market_evidence_bundle(self.replay_path)
            content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
            return FetchPayload(content=content, file_type="json", row_count=len(bundle.get("bars") or []))

        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"baostock-mock-{symbol}-{uuid.uuid4().hex[:12]}"
        today = datetime.now(UTC).date()
        bars = [
            {
                "instrument_id": symbol,
                "trade_date": (today - timedelta(days=offset)).isoformat(),
                "open": 1400.0 - offset,
                "high": 1410.0 - offset,
                "low": 1395.0 - offset,
                "close": 1405.0 - offset,
                "volume": 1_000_000 - offset * 1000,
                "source_used": "baostock",
            }
            for offset in range(min(self.max_rows, 3))
        ]
        bundle = build_cn_market_evidence_bundle(
            bars=bars,
            data_domain=req.data_domain or "cn_equity_daily_bar",
            source_id="baostock",
            source_fetch_id=fetch_id,
            content_hash="pending",
            as_of_timestamp=retrieved_at,
            retrieved_at=retrieved_at,
        )
        bundle = finalize_bundle(bundle)
        content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=len(bars))


@dataclass(frozen=True)
class BaostockProductLiveFetchPort:
    """Product live baostock port (not rehearsal) — replay-first for CI; network via baostock SDK."""

    symbols: Sequence[str]
    max_rows: int
    replay_path: Path = REPLAY_FIXTURE

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        # ponytail: product live uses replay fixture in CI; upgrade = cn_rehearsal BaostockLiveFetchPort network path
        if self.replay_path.is_file():
            return BaostockMockFetchPort(
                symbols=self.symbols, max_rows=self.max_rows, replay_path=self.replay_path
            ).fetch_payload(req)
        from backend.app.datasources.fetch_ports.cn_rehearsal_live_ports import BaostockLiveFetchPort

        return BaostockLiveFetchPort(symbols=self.symbols, max_rows=self.max_rows).fetch_payload(req)


def create_baostock_fetch_port(*, symbols: Sequence[str], max_rows: int, use_mock: bool = True):
    if len(symbols) > MAX_SYMBOLS:
        raise PortError("FAILED", f"max {MAX_SYMBOLS} symbols allowed, got {len(symbols)}")
    if use_mock:
        return BaostockMockFetchPort(symbols=symbols, max_rows=max_rows)
    return BaostockProductLiveFetchPort(symbols=symbols, max_rows=max_rows)
