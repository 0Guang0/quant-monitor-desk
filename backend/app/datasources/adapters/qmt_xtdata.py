"""QMT xtdata vendor adapter skeleton."""

from __future__ import annotations

from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase


class QmtXtdataAdapter(SkeletonAdapterBase):
    source_id = "qmt_xtdata"
    supported_domains = frozenset({"cn_equity_minute_bar", "cn_equity_daily_bar"})
