"""Real-network FetchPort implementations for PROMPT_14 staged pilot (bounded)."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.ops.live_pilot_fetch_ports import (
    AkshareEquityLiveFetchPort,
    BaostockLiveFetchPort,
    _run_akshare_call,
)


def _cninfo_numeric_symbol(raw_symbol: str) -> str:
    lowered = raw_symbol.lower()
    if lowered.startswith("sh.") or lowered.startswith("sz."):
        return lowered[3:]
    if "." in lowered:
        return lowered.split(".", 1)[1]
    return lowered


@dataclass(frozen=True)
class CninfoMetadataFetchPort:
    """Metadata-only cninfo announcement index via public disclosure API."""

    symbols: Sequence[str]
    max_rows: int

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        try:
            import akshare as ak
        except ImportError as exc:
            raise PortError("FAILED", f"akshare package not installed: {exc}") from exc

        raw_symbol = req.instrument_id or (self.symbols[0] if self.symbols else "")
        numeric = _cninfo_numeric_symbol(raw_symbol)
        if not numeric:
            raise PortError("FAILED", "missing instrument_id for cninfo metadata fetch")

        end = datetime.now(UTC).date()
        start = end - timedelta(days=14)

        def _fetch_disclosure():
            return ak.stock_zh_a_disclosure_report_cninfo(
                symbol=numeric,
                start_date=start.strftime("%Y%m%d"),
                end_date=end.strftime("%Y%m%d"),
            )

        try:
            frame = _run_akshare_call(_fetch_disclosure)
        except PortError:
            raise
        except Exception as exc:
            raise PortError("NETWORK_ERROR", str(exc)) from exc

        if frame is None or frame.empty:
            raise PortError("EMPTY_RESPONSE", "cninfo disclosure metadata returned no rows")

        trimmed = frame.tail(self.max_rows)
        records = trimmed.to_dict(orient="records")
        content = json.dumps(
            {
                "symbol": raw_symbol,
                "source": "cninfo",
                "output": "metadata",
                "vendor_api": "stock_zh_a_disclosure_report_cninfo",
                "rows": records,
            },
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=len(records))


def create_staged_fetch_port(
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
    if source_id == "cninfo" and operation == "fetch_announcement_index":
        return CninfoMetadataFetchPort(symbols=symbols_or_indicators, max_rows=max_rows)
    raise PortError("FAILED", f"no staged fetch port for {source_id}/{operation}")
