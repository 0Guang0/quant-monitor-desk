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
from datetime import UTC, date, datetime, timedelta
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
    parse_fetch_window_date,
    reject_over_cap,
    replay_rows_caught_up_fallback,
)

MAX_SYMBOLS = 5
MAX_ROWS = 500
MAX_WINDOW_DAYS = 120
SYMBOL_WHITELIST = frozenset({"sh.600519", "sz.000001", "sh.601318"})

REPLAY_FIXTURE = (
    PROJECT_ROOT / "tests/fixtures/replay/cn_market/baostock/sh600519_daily_replay.json"
)


# L2 (R3-DCP-01): replay bar filter per FetchRequest window — see reference-adoption-dcp01.md §B
def _filter_bars_by_window(
    bars: list[dict],
    *,
    start_time: str | None,
    end_time: str | None,
) -> list[dict]:
    start = parse_fetch_window_date(start_time)
    end = parse_fetch_window_date(end_time)
    if start is None or end is None:
        return bars
    # ponytail: caught-up empty windows (start > end) return no bars; min/max only tolerates reversed ISO inputs
    if start > end:
        return []
    lo, hi = start, end
    filtered: list[dict] = []
    for bar in bars:
        trade = parse_fetch_window_date(str(bar.get("trade_date") or ""))
        if trade is not None and lo <= trade <= hi:
            filtered.append(bar)
    return filtered


def _reject_unknown_symbol(symbol: str) -> None:
    if symbol not in SYMBOL_WHITELIST:
        raise PortError("FAILED", f"symbol not in baostock whitelist: {symbol!r}")


@dataclass(frozen=True)
class BaostockMockFetchPort:
    symbols: Sequence[str]
    max_rows: int
    replay_path: Path = REPLAY_FIXTURE
    replay_caught_up_fallback: bool = False

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(value=self.max_rows, cap=MAX_ROWS)
        if req.start_time and req.end_time:
            start = parse_fetch_window_date(req.start_time)
            end = parse_fetch_window_date(req.end_time)
            if start is not None and end is not None:
                span_days = abs((end - start).days) + 1
                reject_over_cap(value=span_days, cap=MAX_WINDOW_DAYS, label="max_window_days")
        if len(self.symbols) > MAX_SYMBOLS:
            raise PortError("FAILED", f"max {MAX_SYMBOLS} symbols allowed")
        symbol = req.instrument_id or (self.symbols[0] if self.symbols else "")
        if not symbol:
            raise PortError("FAILED", "missing instrument_id for baostock fetch")
        _reject_unknown_symbol(symbol)

        if self.replay_path.is_file():
            bundle = read_cn_market_evidence_bundle(self.replay_path)
            all_bars = list(bundle.get("bars") or [])
            filtered = _filter_bars_by_window(
                all_bars,
                start_time=req.start_time,
                end_time=req.end_time,
            )
            bars = (
                replay_rows_caught_up_fallback(
                    all_bars,
                    filtered,
                    start_time=req.start_time,
                    end_time=req.end_time,
                    sort_key=lambda bar: str(bar.get("trade_date") or ""),
                    min_rows=2,
                )
                if self.replay_caught_up_fallback
                else filtered
            )
            bundle = {**bundle, "bars": bars}
            content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
            return FetchPayload(content=content, file_type="json", row_count=len(bars))

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
class BaostockLiveFetchPort:
    """Product live baostock port — real baostock API with cn_market evidence bundle."""

    symbols: Sequence[str]
    max_rows: int

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        try:
            import baostock as bs
        except ImportError as exc:
            raise PortError("FAILED", f"baostock package not installed: {exc}") from exc

        reject_over_cap(value=self.max_rows, cap=MAX_ROWS)
        symbol = req.instrument_id or (self.symbols[0] if self.symbols else "")
        if not symbol:
            raise PortError("FAILED", "missing instrument_id for baostock live fetch")
        _reject_unknown_symbol(symbol)
        if req.start_time and req.end_time:
            start = parse_fetch_window_date(req.start_time)
            end = parse_fetch_window_date(req.end_time)
            if start is not None and end is not None:
                span_days = abs((end - start).days) + 1
                reject_over_cap(value=span_days, cap=MAX_WINDOW_DAYS, label="max_window_days")
        end_date = parse_fetch_window_date(req.end_time) or datetime.now(UTC).date()
        start_date = parse_fetch_window_date(req.start_time) or (
            end_date - timedelta(days=MAX_WINDOW_DAYS - 1)
        )

        login = bs.login()
        if login.error_code != "0":
            raise PortError("AUTH_FAILED", login.error_msg or "baostock login failed")
        raw_rows: list[list[str]] = []
        try:
            rs = bs.query_history_k_data_plus(
                symbol,
                "date,code,open,high,low,close,volume",
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                frequency="d",
                adjustflag="3",
            )
            while rs.error_code == "0" and rs.next():
                raw_rows.append(rs.get_row_data())
                if len(raw_rows) >= self.max_rows:
                    break
            if rs.error_code != "0" and not raw_rows:
                raise PortError("NETWORK_ERROR", rs.error_msg or "baostock query failed")
        finally:
            bs.logout()

        if not raw_rows:
            raise PortError("EMPTY_RESPONSE", "baostock returned no rows")

        bars: list[dict] = []
        for row in raw_rows:
            bars.append(
                {
                    "instrument_id": symbol,
                    "trade_date": str(row[0] or ""),
                    "open": float(row[2] or 0.0),
                    "high": float(row[3] or 0.0),
                    "low": float(row[4] or 0.0),
                    "close": float(row[5] or 0.0),
                    "volume": float(row[6] or 0.0),
                    "source_used": "baostock",
                }
            )
        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"baostock-live-{symbol}-{uuid.uuid4().hex[:12]}"
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


def create_baostock_fetch_port(*, symbols: Sequence[str], max_rows: int, use_mock: bool = True):
    if len(symbols) > MAX_SYMBOLS:
        raise PortError("FAILED", f"max {MAX_SYMBOLS} symbols allowed, got {len(symbols)}")
    if use_mock:
        return BaostockMockFetchPort(symbols=symbols, max_rows=max_rows)
    from backend.app.datasources.product_live_gate import gate_live_fetch_port

    gate_live_fetch_port(source_id="baostock")
    return BaostockLiveFetchPort(symbols=symbols, max_rows=max_rows)
