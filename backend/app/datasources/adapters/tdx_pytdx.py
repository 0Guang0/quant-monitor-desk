"""TDX / pytdx disabled candidate adapter skeleton (018C — not factory-registered)."""

from __future__ import annotations

from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase


class TdxPytdxAdapter(SkeletonAdapterBase):
    source_id = "tdx_pytdx"
    supported_domains = frozenset({"security_list", "cn_equity_daily_bar", "cn_index_daily_bar"})
