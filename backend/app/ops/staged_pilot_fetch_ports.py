"""Thin re-export shim — SSOT: datasources.fetch_ports.cn_rehearsal_live_ports (R3H-10)."""

from __future__ import annotations

from backend.app.datasources.fetch_ports.cn_rehearsal_live_ports import (  # noqa: F401
    AkshareEquityStagedFetchPort,
    BaostockStagedFetchPort,
    CninfoMetadataStagedFetchPort,
    create_staged_fetch_port,
)

__all__ = [
    "AkshareEquityStagedFetchPort",
    "BaostockStagedFetchPort",
    "CninfoMetadataStagedFetchPort",
    "create_staged_fetch_port",
]
