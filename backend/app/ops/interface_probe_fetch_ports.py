"""Sandbox fetch ports for 018C data-interface probe."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.ops.fetch_port_common import recent_window_start
from backend.app.ops.live_pilot_fetch_ports import _akshare_hist_symbol, _run_akshare_call

EASTMONEY_HIST_VENDOR_API = "stock_zh_a_hist"
SINA_DAILY_VENDOR_API = "stock_zh_a_daily"


@dataclass(frozen=True)
class AkshareSinaDailyValidationFetchPort:
    symbols: Sequence[str]
    max_rows: int

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        try:
            import akshare as ak
        except ImportError as exc:
            raise PortError("FAILED", f"akshare package not installed: {exc}") from exc

        raw_symbol = req.instrument_id or (self.symbols[0] if self.symbols else "")
        hist_symbol = _akshare_hist_symbol(raw_symbol)
        if not hist_symbol:
            raise PortError("FAILED", "missing instrument_id for akshare sina validation fetch")

        start = recent_window_start()
        end = datetime.now(UTC).date()

        def _fetch_sina():
            return ak.stock_zh_a_daily(
                symbol=hist_symbol,
                start_date=start.strftime("%Y%m%d"),
                end_date=end.strftime("%Y%m%d"),
                adjust="qfq",
            )

        frame = _run_akshare_call(_fetch_sina)
        if frame is None or frame.empty:
            raise PortError("EMPTY_RESPONSE", "akshare stock_zh_a_daily returned no rows")

        trimmed = frame.tail(self.max_rows)
        records = trimmed.to_dict(orient="records")
        content = json.dumps(
            {
                "symbol": raw_symbol,
                "source": "akshare",
                "operation": "fetch_daily_bar_sina_validation",
                "vendor_api": SINA_DAILY_VENDOR_API,
                "upstream": "finance.sina.com.cn",
                "not_equivalent_to": EASTMONEY_HIST_VENDOR_API,
                "rows": records,
            },
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=len(records))


@dataclass(frozen=True)
class TdxPytdxProbeFetchPort:
    symbols: Sequence[str]
    max_rows: int
    host: str | None = None
    port: int | None = None
    authorization_verified: bool = False

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        if not self.authorization_verified or not self.host or self.port is None:
            raise PortError(
                "USER_AUTH_REQUIRED",
                "tdx_pytdx fetch blocked: use run_tdx_live_manual_probe after "
                "tdx_live_manual_probe_gate.validate_tdx_live_manual_probe_authorization",
            )
        try:
            from pytdx.hq import TdxHq_API
        except ImportError as exc:
            raise PortError("DISABLED_SOURCE", f"pytdx not installed: {exc}") from exc

        symbol = req.instrument_id or (self.symbols[0] if self.symbols else "")
        if symbol.lower().startswith(("sh.", "sz.")):
            market, code = (1, symbol[3:]) if symbol.lower().startswith("sh.") else (0, symbol[3:])
        else:
            from backend.app.ops.tdx_live_manual_probe_gate import parse_index_instrument

            market, code = parse_index_instrument(symbol)
        api = TdxHq_API()
        if not api.connect(self.host, self.port):
            raise PortError("NETWORK_ERROR", "tdx_pytdx probe could not connect")
        try:
            bars = api.get_security_bars(9, market, code, 0, self.max_rows)
        finally:
            api.disconnect()
        if not bars:
            raise PortError("EMPTY_RESPONSE", "tdx_pytdx returned no daily bars")
        content = json.dumps(
            {
                "symbol": symbol,
                "source": "tdx_pytdx",
                "upstream": f"tdx_hq_host:{self.host}:{self.port}",
                "rows": list(bars)[-self.max_rows :],
            },
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=len(bars))


def content_hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
