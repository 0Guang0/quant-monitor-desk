"""AkShare vendor adapter skeleton."""

from __future__ import annotations

from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase


class AkshareAdapter(SkeletonAdapterBase):
    source_id = "akshare"
    supported_domains = frozenset({"cn_equity_daily_bar", "macro_supplementary"})
