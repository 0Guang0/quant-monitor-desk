"""Baostock vendor adapter skeleton."""

from __future__ import annotations

from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase


class BaostockAdapter(SkeletonAdapterBase):
    source_id = "baostock"
    supported_domains = frozenset({"market_bar_1d", "fundamental"})
