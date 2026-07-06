"""Live pilot — auth (split from live_pilot.py, OP-01)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from backend.app.config import PROJECT_ROOT
from backend.app.datasources.source_registry import SourceNotFoundError, SourceRegistry
from backend.app.ops.live_pilot_constants import (
    APPROVED_PILOT_REQUESTS,
    APPROVED_PILOT_REQUEST_ENVELOPES,
    DISABLED_PILOT_SOURCE_IDS,
    LIVE_PILOT_AUTHORIZATION_ENV,
    MAX_PILOT_ROW_CAP,
)
from backend.app.ops.live_pilot_types import (
    LivePilotAuthorizationError,
    LivePilotDisabledSourceError,
    LivePilotRequest,
    LivePilotRouteNotReadyError,
)

def _default_authorization_evidence() -> str:
    env = os.environ.get(LIVE_PILOT_AUTHORIZATION_ENV, "").strip()
    if not env:
        raise LivePilotAuthorizationError(
            f"set {LIVE_PILOT_AUTHORIZATION_ENV} to a user authorization markdown path"
        )
    return env


def _resolve_authorization_path(path: str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate.resolve()


def validate_authorization(request: LivePilotRequest) -> None:
    """Fail-closed authorization gate — must pass before route preview or fetch."""
    auth_path = _resolve_authorization_path(request.authorization_evidence)
    if not auth_path.is_file():
        raise LivePilotAuthorizationError(
            f"authorization evidence missing: {request.authorization_evidence}"
        )

    auth_text = auth_path.read_text(encoding="utf-8")
    if "_user_authorization_" not in auth_path.name:
        raise LivePilotAuthorizationError(
            f"authorization evidence must be a *_user_authorization_* markdown file: {auth_path.name}"
        )
    if "Approved on" not in auth_text:
        raise LivePilotAuthorizationError("authorization evidence missing approval marker")

    if request.source_id in DISABLED_PILOT_SOURCE_IDS:
        raise LivePilotDisabledSourceError(
            f"source {request.source_id!r} is not authorized for Batch 2.75 live pilot"
        )

    triple = (request.source_id, request.data_domain, request.operation)
    if triple not in APPROVED_PILOT_REQUESTS:
        raise LivePilotAuthorizationError(
            f"request triple {triple!r} not in approved micro-pilot set"
        )

    if not request.raw_only:
        raise LivePilotAuthorizationError("first live pass requires raw_only=true")
    if request.write_target != "sandbox":
        raise LivePilotAuthorizationError("write_target must be sandbox")
    if request.allow_clean_write:
        raise LivePilotAuthorizationError("allow_clean_write must be false for default pilot")
    if request.max_rows <= 0 or request.max_rows > MAX_PILOT_ROW_CAP:
        raise LivePilotAuthorizationError(
            f"max_rows must be in 1..{MAX_PILOT_ROW_CAP}, got {request.max_rows}"
        )
    if not request.symbols_or_indicators:
        raise LivePilotAuthorizationError("symbols_or_indicators must be non-empty")

    envelope = (
        request.source_id,
        request.data_domain,
        request.operation,
        request.symbols_or_indicators,
        request.date_window,
        request.max_rows,
    )
    if envelope not in APPROVED_PILOT_REQUEST_ENVELOPES:
        raise LivePilotAuthorizationError(
            "request envelope does not exactly match approved micro-pilot authorization"
        )


def assert_pilot_ready_before_fetch(request: LivePilotRequest) -> None:
    """Authorization + disabled-source gate invoked before any network fetch."""
    validate_authorization(request)


def approved_pilot_requests() -> tuple[LivePilotRequest, ...]:
    """Three user-authorized micro-pilot requests; path from QMD_LIVE_PILOT_AUTHORIZATION."""
    auth = _default_authorization_evidence()
    return (
        LivePilotRequest(
            source_id="baostock",
            data_domain="cn_equity_daily_bar",
            operation="fetch_daily_bar",
            symbols_or_indicators=("sh.600519",),
            date_window="recent 5 trading days",
            max_rows=10,
            authorization_evidence=auth,
        ),
        LivePilotRequest(
            source_id="akshare",
            data_domain="cn_equity_daily_bar",
            operation="fetch_daily_bar_validation",
            symbols_or_indicators=("sh.600519",),
            date_window="recent 5 trading days",
            max_rows=10,
            authorization_evidence=auth,
        ),
        LivePilotRequest(
            source_id="akshare",
            data_domain="macro_supplementary",
            operation="fetch_macro_series",
            symbols_or_indicators=("DGS10",),
            date_window="recent 7 calendar days",
            max_rows=20,
            authorization_evidence=auth,
        ),
    )


def _pilot_request_to_dict(request: LivePilotRequest) -> dict[str, Any]:
    return {
        "source_id": request.source_id,
        "data_domain": request.data_domain,
        "operation": request.operation,
        "symbols_or_indicators": list(request.symbols_or_indicators),
        "date_window": request.date_window,
        "max_rows": request.max_rows,
        "dry_run": request.dry_run,
        "raw_only": request.raw_only,
        "write_target": request.write_target,
        "allow_clean_write": request.allow_clean_write,
        "authorization_evidence": request.authorization_evidence,
    }
