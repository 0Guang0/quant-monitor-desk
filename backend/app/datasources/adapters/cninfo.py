"""CNINFO vendor adapter skeleton."""

from __future__ import annotations

from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase


class CninfoAdapter(SkeletonAdapterBase):
    source_id = "cninfo"
    supported_domains = frozenset({"cn_announcements", "cn_filings", "cn_pdf_reports"})
