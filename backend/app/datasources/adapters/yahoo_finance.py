"""Yahoo Finance adapter — thin boundary over yahoo_finance_port (R3H-02)."""

from __future__ import annotations

from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase
from backend.app.datasources.fetch_ports.yahoo_finance_port import create_yahoo_finance_fetch_port

__all__ = ["YahooFinanceAdapter", "create_yahoo_finance_fetch_port"]


class YahooFinanceAdapter(SkeletonAdapterBase):
    source_id = "yahoo_finance"
    supported_domains = frozenset(
        {"us_equity_daily_bar", "etf_daily_bar", "global_asset_reference"}
    )
