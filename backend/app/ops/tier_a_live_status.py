"""Shared Tier A live acceptance status constants and env validators (M-DATA-03)."""

from __future__ import annotations

import os

from backend.app.ops.macro_incremental_common import _SERIES_SUCCESS_STATUSES

PASS_SYNC_STATUSES = frozenset(_SERIES_SUCCESS_STATUSES | {"OK", "SUCCESS", "PLANNED"})

_BAR_SOURCE_IDS = frozenset({"baostock", "mootdx", "alpha_vantage"})
_MACRO_SOURCE_IDS = frozenset(
    {"fred", "us_treasury", "bis", "world_bank", "cftc_cot"}
)


def live_acceptance_mock_env_enabled() -> bool:
    return os.environ.get("QMD_FRED_INCREMENTAL_USE_MOCK", "0") != "0"


def validate_sec_edgar_user_agent(raw: str | None) -> str | None:
    """SEC fair-access identity — same rules as sec_edgar_port._sec_user_agent."""
    if not raw or not str(raw).strip():
        return None
    agent = str(raw).strip()
    if "@" not in agent and "contact" not in agent.lower():
        return None
    return agent


__all__ = [
    "PASS_SYNC_STATUSES",
    "_BAR_SOURCE_IDS",
    "_MACRO_SOURCE_IDS",
    "live_acceptance_mock_env_enabled",
    "validate_sec_edgar_user_agent",
]
