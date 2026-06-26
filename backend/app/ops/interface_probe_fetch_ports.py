"""Sandbox fetch ports for 018C data-interface probe.

TDX probe boundary: ``TdxPytdxProbeFetchPort`` is a thin delegate to QMD-owned
``TdxPytdxFetchPort`` (``backend.app.datasources.fetch_ports.tdx_pytdx_port``).
Do not grow TDX download logic here (R3FR-03 canonical provider).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.fetch_ports.tdx_pytdx_port import TdxPytdxFetchPort
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.ops.tdx_live_manual_probe_gate import TdxPytdxAuthorization
from backend.app.ops.fetch_port_common import recent_window_start
from backend.app.ops.live_pilot_fetch_ports import _akshare_hist_symbol, _run_akshare_call

EASTMONEY_HIST_VENDOR_API = "stock_zh_a_hist"
SINA_DAILY_VENDOR_API = "stock_zh_a_daily"


@dataclass(frozen=True)
class AkshareSinaDailyValidationFetchPort:
    """018C sandbox validation-only; triggers live akshare network — not a default CLI path."""

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
    """Thin delegate to QMD-owned TdxPytdxFetchPort (R3FR-03)."""

    symbols: Sequence[str]
    max_rows: int
    host: str | None = None
    port: int | None = None
    authorization: TdxPytdxAuthorization | None = None
    authorization_verified: bool = False
    remaining_network_calls: int | None = None

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        if self.authorization is None:
            raise PortError(
                "USER_AUTH_REQUIRED",
                "tdx_pytdx fetch blocked: use run_tdx_live_manual_probe after "
                "tdx_live_manual_probe_gate.validate_tdx_live_manual_probe_authorization",
            )
        port = TdxPytdxFetchPort(
            self.symbols,
            self.max_rows,
            authorization=self.authorization,
            remaining_network_calls=self.remaining_network_calls,
        )
        return port.fetch_payload(req)


def content_hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
