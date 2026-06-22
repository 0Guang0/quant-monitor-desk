"""Live vendor FetchPort implementations for Batch 2.75 pilot (real network)."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import TypeVar

from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.fetch_result import FetchRequest

_T = TypeVar("_T")

_PROXY_HINT = (
    "Windows system proxy may route domestic vendors (eastmoney/sina) through "
    "127.0.0.1:7897 and fail; set those hosts to DIRECT in Clash/V2Ray or "
    "disable system proxy for the live pilot run"
)


@contextmanager
def _bypass_system_proxy() -> Iterator[None]:
    """Use direct connections for CN domestic endpoints (ignore Windows proxy)."""
    import requests

    original_request = requests.api.request
    original_get = requests.get
    original_post = requests.post
    original_session_init = requests.Session.__init__

    def _direct_request(method: str, url: str, **kwargs: object):
        with requests.Session() as session:
            session.trust_env = False
            return session.request(method, url, **kwargs)

    def _direct_session_init(self, *args: object, **kwargs: object) -> None:
        original_session_init(self, *args, **kwargs)
        self.trust_env = False

    requests.api.request = _direct_request
    requests.get = lambda url, **kwargs: _direct_request("GET", url, **kwargs)
    requests.post = lambda url, **kwargs: _direct_request("POST", url, **kwargs)
    requests.Session.__init__ = _direct_session_init
    try:
        yield
    finally:
        requests.api.request = original_request
        requests.get = original_get
        requests.post = original_post
        requests.Session.__init__ = original_session_init


def _run_akshare_call(fn: Callable[[], _T]) -> _T:
    """Try system proxy first, then direct — either path may work depending on Clash rules."""
    errors: list[str] = []

    try:
        return fn()
    except Exception as proxy_exc:
        errors.append(f"proxy: {proxy_exc}")

    try:
        with _bypass_system_proxy():
            return fn()
    except Exception as direct_exc:
        errors.append(f"direct: {direct_exc}")

    combined = "; ".join(errors)
    raise PortError("NETWORK_ERROR", f"{combined}; {_PROXY_HINT}")


_DATE_WINDOW_RE = re.compile(
    r"^recent\s+(\d+)\s+(trading|calendar)\s+days$",
    re.IGNORECASE,
)


def parse_pilot_date_window(date_window: str) -> int:
    """Map authorized ``date_window`` label to a calendar-day span for vendor APIs."""
    match = _DATE_WINDOW_RE.match(date_window.strip())
    if not match:
        raise ValueError(f"unsupported pilot date_window label: {date_window!r}")
    days = int(match.group(1))
    unit = match.group(2).lower()
    if unit == "calendar":
        return days
    # Trading days: conservative calendar span (~1.5x + weekend buffer).
    return int(days * 1.5) + 2


def _recent_window_start(*, calendar_days: int = 14) -> date:
    return datetime.now(UTC).date() - timedelta(days=calendar_days)


def _window_start_for_label(date_window: str | None) -> date:
    if date_window is None:
        return _recent_window_start()
    return _recent_window_start(calendar_days=parse_pilot_date_window(date_window))


def _akshare_hist_symbol(raw_symbol: str) -> str:
    """Convert baostock-style sh.600519 to akshare stock_zh_a_hist numeric code."""
    lowered = raw_symbol.lower()
    if lowered.startswith("sh."):
        return lowered[3:]
    if lowered.startswith("sz."):
        return lowered[3:]
    if "." in lowered:
        return lowered.split(".", 1)[1]
    return lowered


@dataclass(frozen=True)
class BaostockLiveFetchPort:
    symbols: Sequence[str]
    max_rows: int
    date_window: str | None = None

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        try:
            import baostock as bs
        except ImportError as exc:
            raise PortError("FAILED", f"baostock package not installed: {exc}") from exc

        symbol = req.instrument_id or (self.symbols[0] if self.symbols else None)
        if not symbol:
            raise PortError("FAILED", "missing instrument_id for baostock fetch")

        start = _window_start_for_label(self.date_window)
        end = datetime.now(UTC).date()
        login = bs.login()
        if login.error_code != "0":
            raise PortError("AUTH_FAILED", login.error_msg or "baostock login failed")
        rows: list[list[str]] = []
        try:
            rs = bs.query_history_k_data_plus(
                symbol,
                "date,code,open,high,low,close,volume",
                start_date=start.isoformat(),
                end_date=end.isoformat(),
                frequency="d",
                adjustflag="3",
            )
            while rs.error_code == "0" and rs.next():
                rows.append(rs.get_row_data())
                if len(rows) >= self.max_rows:
                    break
            if rs.error_code != "0" and not rows:
                raise PortError("NETWORK_ERROR", rs.error_msg or "baostock query failed")
        finally:
            bs.logout()

        if not rows:
            raise PortError("EMPTY_RESPONSE", "baostock returned no rows")

        content = json.dumps(
            {"symbol": symbol, "source": "baostock", "rows": rows},
            ensure_ascii=False,
        ).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=len(rows))


@dataclass(frozen=True)
class AkshareEquityLiveFetchPort:
    symbols: Sequence[str]
    max_rows: int
    date_window: str | None = None

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        try:
            import akshare as ak
        except ImportError as exc:
            raise PortError("FAILED", f"akshare package not installed: {exc}") from exc

        raw_symbol = req.instrument_id or (self.symbols[0] if self.symbols else "")
        hist_symbol = _akshare_hist_symbol(raw_symbol)
        if not hist_symbol:
            raise PortError("FAILED", "missing instrument_id for akshare equity fetch")

        start = _window_start_for_label(self.date_window)
        end = datetime.now(UTC).date()

        def _fetch_equity():
            return ak.stock_zh_a_hist(
                symbol=hist_symbol,
                period="daily",
                start_date=start.strftime("%Y%m%d"),
                end_date=end.strftime("%Y%m%d"),
                adjust="",
            )

        try:
            frame = _run_akshare_call(_fetch_equity)
        except PortError:
            raise
        except Exception as exc:
            raise PortError("NETWORK_ERROR", str(exc)) from exc

        if frame is None or frame.empty:
            raise PortError("EMPTY_RESPONSE", "akshare equity returned no rows")

        trimmed = frame.tail(self.max_rows)
        records = trimmed.to_dict(orient="records")
        content = json.dumps(
            {
                "symbol": raw_symbol,
                "source": "akshare",
                "vendor_api": "stock_zh_a_hist",
                "rows": records,
            },
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=len(records))


@dataclass(frozen=True)
class AkshareMacroLiveFetchPort:
    indicators: Sequence[str]
    max_rows: int

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        try:
            import akshare as ak
        except ImportError as exc:
            raise PortError("FAILED", f"akshare package not installed: {exc}") from exc

        indicator = req.instrument_id or (self.indicators[0] if self.indicators else "")

        def _fetch_macro():
            return ak.bond_zh_us_rate()

        try:
            frame = _run_akshare_call(_fetch_macro)
        except PortError:
            raise
        except Exception as exc:
            raise PortError("NETWORK_ERROR", str(exc)) from exc

        if frame is None or frame.empty:
            raise PortError("EMPTY_RESPONSE", "akshare bond_zh_us_rate returned no rows")

        trimmed = frame.tail(self.max_rows)
        records = trimmed.to_dict(orient="records")
        content = json.dumps(
            {
                "indicator": indicator,
                "source": "akshare",
                "note": "macro shape probe only; FRED primary remains deferred (B2.5-O-05)",
                "rows": records,
            },
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=len(records))


def create_live_fetch_port(
    *,
    source_id: str,
    operation: str,
    symbols_or_indicators: Sequence[str],
    max_rows: int,
):
    if source_id == "baostock":
        return BaostockLiveFetchPort(symbols=symbols_or_indicators, max_rows=max_rows)
    if source_id == "akshare" and operation == "fetch_daily_bar_validation":
        return AkshareEquityLiveFetchPort(symbols=symbols_or_indicators, max_rows=max_rows)
    if source_id == "akshare" and operation == "fetch_macro_series":
        return AkshareMacroLiveFetchPort(indicators=symbols_or_indicators, max_rows=max_rows)
    raise PortError("FAILED", f"no live fetch port for {source_id}/{operation}")
