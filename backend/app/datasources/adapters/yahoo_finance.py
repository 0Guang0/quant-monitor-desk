"""Yahoo Finance vendor adapter skeleton."""

from __future__ import annotations

from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase


class YahooFinanceAdapter(SkeletonAdapterBase):
    source_id = "yahoo_finance"
    supported_domains = frozenset({"market_bar_1d"})
