"""Thin re-export shim — SSOT: datasources.fetch_ports.cn_rehearsal_live_ports (R3H-10)."""

from __future__ import annotations

from backend.app.datasources.fetch_ports.cn_rehearsal_live_ports import (  # noqa: F401
    AkshareEquityLiveFetchPort,
    AkshareMacroLiveFetchPort,
    BaostockLiveFetchPort,
    create_live_fetch_port,
    parse_pilot_date_window,
    _akshare_hist_symbol,
    _run_akshare_call,
    _window_start_for_label,
)

__all__ = [
    "AkshareEquityLiveFetchPort",
    "AkshareMacroLiveFetchPort",
    "BaostockLiveFetchPort",
    "create_live_fetch_port",
    "parse_pilot_date_window",
]
