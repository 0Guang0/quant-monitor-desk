"""QMT xtdata vendor adapter skeleton."""

from __future__ import annotations

from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase


class QmtXtdataAdapter(SkeletonAdapterBase):
    source_id = "qmt_xtdata"
    supported_domains = frozenset({"market_bar_1m", "market_bar_1d"})
