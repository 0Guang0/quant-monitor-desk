"""TDX / pytdx disabled candidate adapter skeleton (018C — not factory-registered)."""

from __future__ import annotations

from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase
from backend.app.datasources.normalizers import tdx as tdx_normalizer

# Re-export normalizers for backward-compatible imports (R3FR-03 delegates here).
build_equity_bar_manifest = tdx_normalizer.build_equity_bar_manifest
build_index_bar_manifest = tdx_normalizer.build_index_bar_manifest
build_security_list_manifest = tdx_normalizer.build_security_list_manifest
manifest_content_hash = tdx_normalizer.manifest_content_hash
manifest_schema_hash = tdx_normalizer.manifest_schema_hash


class TdxPytdxAdapter(SkeletonAdapterBase):
    source_id = "tdx_pytdx"
    supported_domains = frozenset({"security_list", "cn_equity_daily_bar", "cn_index_daily_bar"})
