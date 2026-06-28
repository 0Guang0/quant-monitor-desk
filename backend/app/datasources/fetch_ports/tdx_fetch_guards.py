"""Shared TDX fetch guards and caps (tdx_pytdx + mootdx)."""

from __future__ import annotations

from backend.app.datasources.adapters.fetch_port import PortError
from backend.app.datasources.fetch_result import FetchRequest

SECURITY_LIST_MAX_ROWS = 20
EQUITY_INDEX_MAX_ROWS = 3
MAX_NETWORK_CALLS = 5
MINUTE_BARS_ENABLED = False
FULL_MARKET_SCAN_ENABLED = False

SUPPORTED_DOMAINS = frozenset({"security_list", "cn_equity_daily_bar", "cn_index_daily_bar"})
FULL_MARKET_MARKERS = frozenset({"*", "__FULL_MARKET__", "__SCAN_ALL__"})


def parse_equity_symbol(symbol: str) -> tuple[int, str]:
    lowered = symbol.strip().lower()
    if lowered.startswith("sh."):
        return 1, symbol[3:]
    if lowered.startswith("sz."):
        return 0, symbol[3:]
    raise PortError("FAILED", f"unsupported equity instrument_id: {symbol!r}")


def domain_cap(data_domain: str) -> int:
    if data_domain == "security_list":
        return SECURITY_LIST_MAX_ROWS
    if data_domain in {"cn_equity_daily_bar", "cn_index_daily_bar"}:
        return EQUITY_INDEX_MAX_ROWS
    return 0


def reject_unsupported_domain(req: FetchRequest, *, source_id: str = "tdx_pytdx") -> None:
    domain = req.data_domain
    if "minute" in domain:
        raise PortError(
            "FAILED",
            f"minute bars rejected for {source_id} (minute_bars_enabled={MINUTE_BARS_ENABLED})",
        )
    if domain not in SUPPORTED_DOMAINS:
        raise PortError("FAILED", f"unsupported data_domain for {source_id}: {domain!r}")


def reject_full_market_scan(req: FetchRequest, *, source_id: str = "tdx_pytdx") -> None:
    if FULL_MARKET_SCAN_ENABLED:
        return
    instrument = (req.instrument_id or "").strip()
    if instrument in FULL_MARKET_MARKERS:
        raise PortError(
            "FAILED",
            f"full market scan rejected for {source_id} (full_market_scan_enabled=false)",
        )
    if req.data_domain != "security_list" and not instrument:
        raise PortError(
            "FAILED",
            "full market scan rejected: missing instrument_id for bounded daily bar fetch",
        )


def reject_over_cap(*, data_domain: str, max_rows: int, source_id: str = "tdx") -> None:
    cap = domain_cap(data_domain)
    if max_rows > cap:
        raise PortError(
            "FAILED",
            f"requested max_rows={max_rows} exceeds cap={cap} for {data_domain}",
        )
