"""Live pilot — types (split from live_pilot.py, OP-01)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

class LivePilotOutcome(StrEnum):
    PILOT_PASS_RAW_ONLY = "PILOT_PASS_RAW_ONLY"
    PILOT_PASS_SANDBOX_CLEAN = "PILOT_PASS_SANDBOX_CLEAN"
    PILOT_FAIL_SOURCE = "PILOT_FAIL_SOURCE"
    PILOT_FAIL_VALIDATION = "PILOT_FAIL_VALIDATION"
    PILOT_REDEFERRED = "PILOT_REDEFERRED"


class LivePilotAuthorizationError(RuntimeError):
    """Raised when authorization evidence or request parameters fail fail-closed gate."""


class LivePilotDisabledSourceError(RuntimeError):
    """Raised when source_id is not authorized for Batch 2.75 live pilot."""


class LivePilotRouteNotReadyError(RuntimeError):
    """Raised when explicit source route is not READY before live fetch."""


class LivePilotFixtureForbiddenError(RuntimeError):
    """Raised when staged/fixture fetch port is used for live pilot evidence."""


@dataclass(frozen=True)
class LivePilotRequest:
    source_id: str
    data_domain: str
    operation: str
    symbols_or_indicators: tuple[str, ...]
    date_window: str
    max_rows: int
    authorization_evidence: str
    dry_run: bool = True
    raw_only: bool = True
    write_target: str = "sandbox"
    allow_clean_write: bool = False
