"""Minimal live HTTP fetch ports for Tier B validation_fetch (M-DATA-03 AC-7)."""

from __future__ import annotations

import csv
import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from io import StringIO
from typing import Any

import urllib.error
import urllib.parse
import urllib.request

from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.fetch_ports.cn_rehearsal_live_ports import (
    _akshare_hist_symbol,
    _akshare_sina_daily_symbol,
    _run_akshare_call,
    _run_akshare_call_with_retry,
)
from backend.app.ops.live_pilot_constants import (
    ORIGINAL_REQUEST2_ENDPOINT_HOST,
    ORIGINAL_REQUEST2_VENDOR_API,
    SIDECAR_REQUEST2_ENDPOINT_HOST,
    SIDECAR_REQUEST2_VENDOR_API,
)
from backend.app.datasources.normalizers.cn_market import (
    aggregator_quality_flags,
    build_cn_market_evidence_bundle,
)
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.fetch_window import (
    filter_us_trading_day_bars,
    is_us_equity_bar_fetch,
    us_equity_window_kind,
)
from backend.app.datasources.normalizers.crypto_market import build_crypto_market_evidence_bundle
from backend.app.datasources.normalizers.evidence_bundle import finalize_bundle, reject_over_cap
from backend.app.datasources.normalizers.market_data import build_daily_bar_evidence_bundle


def _http_json(url: str, *, headers: dict[str, str] | None = None) -> Any:
    request = urllib.request.Request(
        url,
        headers=headers or {"Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise PortError("NETWORK_ERROR", str(exc)) from exc
    except urllib.error.URLError as exc:
        raise PortError("NETWORK_ERROR", str(exc)) from exc
    except json.JSONDecodeError as exc:
        raise PortError("FAILED", f"invalid JSON from {url}: {exc}") from exc


@dataclass(frozen=True)
class YahooFinanceLiveFetchPort:
    symbols: Sequence[str]
    max_rows: int

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(value=self.max_rows, cap=500, label="max_rows")
        symbol = req.instrument_id or (self.symbols[0] if self.symbols else "")
        if not symbol:
            raise PortError("FAILED", "missing instrument_id for Yahoo Finance live fetch")
        domain = req.data_domain or "us_equity_daily_bar"
        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}"
            f"?interval=1d&range=5d"
        )
        raw = _http_json(url, headers={"User-Agent": "QuantMonitorDesk/1.0"})
        result = (raw.get("chart") or {}).get("result") or []
        if not result:
            raise PortError("EMPTY_RESPONSE", f"Yahoo chart returned no result for {symbol}")
        timestamps = (result[0].get("timestamp") or [])[-self.max_rows :]
        quote = (result[0].get("indicators") or {}).get("quote") or [{}]
        q0 = quote[0] if quote else {}
        bars: list[dict[str, Any]] = []
        for idx, ts in enumerate(timestamps):
            trade_date = datetime.fromtimestamp(ts, tz=UTC).date().isoformat()
            bars.append(
                {
                    "instrument_id": symbol,
                    "trade_date": trade_date,
                    "open": q0.get("open", [None])[idx],
                    "high": q0.get("high", [None])[idx],
                    "low": q0.get("low", [None])[idx],
                    "close": q0.get("close", [None])[idx],
                    "volume": q0.get("volume", [None])[idx],
                    "source_used": "yahoo_finance",
                }
            )
        bars = [b for b in bars if b.get("close") is not None]
        if is_us_equity_bar_fetch(data_domain=domain, instrument_id=symbol):
            bars = filter_us_trading_day_bars(bars)
        if not bars:
            raise PortError("EMPTY_RESPONSE", f"Yahoo returned no usable bars for {symbol}")
        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"yahoo-live-{symbol}-{uuid.uuid4().hex[:12]}"
        bundle = build_daily_bar_evidence_bundle(
            bars=bars[: self.max_rows],
            data_domain=domain,
            source_id="yahoo_finance",
            source_fetch_id=fetch_id,
            content_hash="pending",
            as_of_timestamp=retrieved_at,
            retrieved_at=retrieved_at,
            window_kind=us_equity_window_kind(data_domain=domain, instrument_id=symbol),
        )
        bundle = finalize_bundle(bundle)
        content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=len(bars))


@dataclass(frozen=True)
class StooqLiveFetchPort:
    symbols: Sequence[str]
    max_rows: int

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(value=self.max_rows, cap=500, label="max_rows")
        symbol = req.instrument_id or (self.symbols[0] if self.symbols else "")
        if not symbol:
            raise PortError("FAILED", "missing instrument_id for Stooq live fetch")
        domain = req.data_domain or "global_market_daily_bar"
        url = f"https://stooq.com/q/d/l/?s={urllib.parse.quote(symbol.lower())}&i=d"
        request = urllib.request.Request(url, headers={"User-Agent": "QuantMonitorDesk/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                text = response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            raise PortError("NETWORK_ERROR", str(exc)) from exc
        stripped = text.lstrip().lower()
        if stripped.startswith("<!doctype") or stripped.startswith("<html"):
            raise PortError(
                "NETWORK_ERROR",
                "Stooq returned HTML instead of CSV (bot/geo block)",
            )
        reader = csv.DictReader(StringIO(text))
        bars: list[dict[str, Any]] = []
        for row in reader:
            bars.append(
                {
                    "instrument_id": symbol,
                    "trade_date": row.get("Date") or "",
                    "open": row.get("Open"),
                    "high": row.get("High"),
                    "low": row.get("Low"),
                    "close": row.get("Close"),
                    "volume": row.get("Volume"),
                    "source_used": "stooq",
                }
            )
        bars = [b for b in bars if b.get("close") not in (None, "")][-self.max_rows :]
        if not bars:
            raise PortError("EMPTY_RESPONSE", f"Stooq returned no rows for {symbol}")
        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"stooq-live-{symbol}-{uuid.uuid4().hex[:12]}"
        bundle = build_daily_bar_evidence_bundle(
            bars=bars,
            data_domain=domain,
            source_id="stooq",
            source_fetch_id=fetch_id,
            content_hash="pending",
            as_of_timestamp=retrieved_at,
            retrieved_at=retrieved_at,
            window_kind=us_equity_window_kind(data_domain=domain, instrument_id=symbol),
        )
        bundle = finalize_bundle(bundle)
        content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=len(bars))


@dataclass(frozen=True)
class CoingeckoLiveFetchPort:
    asset_ids: Sequence[str]
    max_assets: int

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(value=self.max_assets, cap=10, label="max_assets")
        asset_id = req.instrument_id or (self.asset_ids[0] if self.asset_ids else "")
        if not asset_id:
            raise PortError("FAILED", "missing asset_id for CoinGecko live fetch")
        url = (
            "https://api.coingecko.com/api/v3/simple/price?"
            + urllib.parse.urlencode(
                {
                    "ids": asset_id,
                    "vs_currencies": "usd",
                    "include_market_cap": "true",
                    "include_24hr_vol": "true",
                }
            )
        )
        raw = _http_json(url, headers={"User-Agent": "QuantMonitorDesk/1.0"})
        price_block = raw.get(asset_id) or {}
        if not price_block.get("usd"):
            raise PortError("EMPTY_RESPONSE", f"CoinGecko returned no price for {asset_id}")
        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"coingecko-live-{asset_id}-{uuid.uuid4().hex[:12]}"
        rows = [
            {
                "asset_id": asset_id,
                "symbol": asset_id[:3],
                "price_usd": price_block.get("usd"),
                "market_cap_usd": price_block.get("usd_market_cap"),
                "volume_24h_usd": price_block.get("usd_24h_vol"),
                "source_used": "coingecko",
            }
        ]
        bundle = build_crypto_market_evidence_bundle(
            instruments=rows,
            data_domain=req.data_domain or "crypto_spot_market",
            source_id="coingecko",
            source_fetch_id=fetch_id,
            content_hash="pending",
            as_of_timestamp=retrieved_at,
            retrieved_at=retrieved_at,
        )
        bundle = finalize_bundle(bundle)
        content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=1)


def _bars_from_akshare_dataframe(
    frame: Any,
    *,
    symbol: str,
    source_id: str,
    max_rows: int,
) -> list[dict[str, Any]]:
    trimmed = frame.tail(max_rows)
    bars: list[dict[str, Any]] = []
    for _, row in trimmed.iterrows():
        trade_date = str(row.get("日期") or row.get("date") or "")[:10]
        bars.append(
            {
                "instrument_id": symbol,
                "trade_date": trade_date,
                "open": float(row.get("开盘") or row.get("open") or 0),
                "high": float(row.get("最高") or row.get("high") or 0),
                "low": float(row.get("最低") or row.get("low") or 0),
                "close": float(row.get("收盘") or row.get("close") or 0),
                "volume": int(row.get("成交量") or row.get("volume") or 0),
                "source_used": source_id,
            }
        )
    return bars


def _cn_equity_live_fetch_payload(
    bars: list[dict[str, Any]],
    req: FetchRequest,
    *,
    source_id: str,
    vendor_api: str,
    upstream: str,
) -> FetchPayload:
    if not bars:
        raise PortError("EMPTY_RESPONSE", f"{source_id} returned no rows")
    retrieved_at = datetime.now(UTC).isoformat()
    symbol = bars[0]["instrument_id"]
    fetch_id = f"{source_id}-live-{symbol}-{uuid.uuid4().hex[:12]}"
    bundle = build_cn_market_evidence_bundle(
        bars=bars,
        data_domain=req.data_domain or "cn_equity_daily_bar",
        source_id=source_id,
        source_fetch_id=fetch_id,
        content_hash="pending",
        as_of_timestamp=retrieved_at,
        retrieved_at=retrieved_at,
        quality_flags=aggregator_quality_flags(source_id=source_id),
    )
    bundle["vendor_api"] = vendor_api
    bundle["upstream"] = upstream
    bundle = finalize_bundle(bundle)
    content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
    return FetchPayload(content=content, file_type="json", row_count=len(bars))


def _cn_equity_live_bars_hist(
    req: FetchRequest,
    *,
    source_id: str,
    symbols: Sequence[str],
    max_rows: int,
) -> FetchPayload:
    try:
        import akshare as ak
    except ImportError as exc:
        raise PortError("FAILED", f"akshare package not installed: {exc}") from exc

    symbol = req.instrument_id or (symbols[0] if symbols else "")
    if not symbol:
        raise PortError("FAILED", f"missing instrument_id for {source_id} live fetch")
    end = datetime.now(UTC).date()
    start = end - timedelta(days=60)
    numeric = _akshare_hist_symbol(symbol)

    def _fetch():
        return ak.stock_zh_a_hist(
            symbol=numeric,
            period="daily",
            start_date=start.strftime("%Y%m%d"),
            end_date=end.strftime("%Y%m%d"),
            adjust="",
        )

    try:
        frame = _run_akshare_call_with_retry(_fetch)
    except PortError:
        raise
    except Exception as exc:
        raise PortError("NETWORK_ERROR", str(exc)) from exc
    if frame is None or frame.empty:
        raise PortError("EMPTY_RESPONSE", f"akshare returned no rows for {symbol}")

    bars = _bars_from_akshare_dataframe(
        frame, symbol=symbol, source_id=source_id, max_rows=max_rows
    )
    return _cn_equity_live_fetch_payload(
        bars,
        req,
        source_id=source_id,
        vendor_api=ORIGINAL_REQUEST2_VENDOR_API,
        upstream=ORIGINAL_REQUEST2_ENDPOINT_HOST,
    )


def _cn_equity_live_bars_sina(
    req: FetchRequest,
    *,
    symbols: Sequence[str],
    max_rows: int,
) -> FetchPayload:
    try:
        import akshare as ak
    except ImportError as exc:
        raise PortError("FAILED", f"akshare package not installed: {exc}") from exc

    symbol = req.instrument_id or (symbols[0] if symbols else "")
    if not symbol:
        raise PortError("FAILED", "missing instrument_id for sina_finance live fetch")
    end = datetime.now(UTC).date()
    start = end - timedelta(days=60)
    daily_symbol = _akshare_sina_daily_symbol(symbol)

    def _fetch():
        return ak.stock_zh_a_daily(
            symbol=daily_symbol,
            start_date=start.strftime("%Y%m%d"),
            end_date=end.strftime("%Y%m%d"),
            adjust="",
        )

    try:
        frame = _run_akshare_call(_fetch)
    except PortError:
        raise
    except Exception as exc:
        raise PortError("NETWORK_ERROR", str(exc)) from exc
    if frame is None or frame.empty:
        raise PortError("EMPTY_RESPONSE", f"akshare stock_zh_a_daily returned no rows for {symbol}")

    bars = _bars_from_akshare_dataframe(
        frame, symbol=symbol, source_id="sina_finance", max_rows=max_rows
    )
    return _cn_equity_live_fetch_payload(
        bars,
        req,
        source_id="sina_finance",
        vendor_api=SIDECAR_REQUEST2_VENDOR_API,
        upstream=SIDECAR_REQUEST2_ENDPOINT_HOST,
    )


def _cn_equity_live_bars_from_akshare(
    req: FetchRequest,
    *,
    source_id: str,
    symbols: Sequence[str],
    max_rows: int,
) -> FetchPayload:
    """Deprecated shim — hist path only; prefer _cn_equity_live_bars_hist / _sina."""
    return _cn_equity_live_bars_hist(
        req, source_id=source_id, symbols=symbols, max_rows=max_rows
    )


@dataclass(frozen=True)
class AkshareLiveFetchPort:
    symbols: Sequence[str]
    max_rows: int

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        return _cn_equity_live_bars_hist(
            req, source_id="akshare", symbols=self.symbols, max_rows=self.max_rows
        )


@dataclass(frozen=True)
class EastmoneyLiveFetchPort:
    symbols: Sequence[str]
    max_rows: int

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        return _cn_equity_live_bars_hist(
            req, source_id="eastmoney", symbols=self.symbols, max_rows=self.max_rows
        )


@dataclass(frozen=True)
class SinaFinanceLiveFetchPort:
    symbols: Sequence[str]
    max_rows: int

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        return _cn_equity_live_bars_sina(req, symbols=self.symbols, max_rows=self.max_rows)
