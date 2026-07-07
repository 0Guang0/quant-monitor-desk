"""Shared macro incremental staging adapters for tier-A F0 tests."""

from __future__ import annotations

from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase


class FredMacroStubAdapter(SkeletonAdapterBase):
    """Minimal fred adapter for persist_incremental_fetch_payload smoke tests."""

    source_id = "fred"
    supported_domains = frozenset({"macro_series"})
