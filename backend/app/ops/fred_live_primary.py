"""FRED live primary closeout gate — Batch 3F SH-06 (sandbox only, fail-closed)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.app.config import PROJECT_ROOT
from backend.app.ops.fred_sandbox_pilot import FredPilotAuthorizationError, load_authorization_yaml

# SSOT path for Plan freeze + pytest (execute-evidence canonical copy)
FRED_LIVE_AUTHORIZATION_DEFAULT = (
    PROJECT_ROOT
    / ".trellis/tasks/round3-source-health-and-quality-runners/execute-evidence"
    / "fred_live_authorization_2026-06-25.yaml"
)


class FredLivePrimaryAuthorizationError(FredPilotAuthorizationError):
    """SH-06 authorization gate failure."""


def _resolve_path(path: str | Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate.resolve()


def validate_fred_live_authorization(
    authorization_path: str | Path,
    *,
    live_requested: bool,
) -> dict[str, Any]:
    """Fail-closed gate: live fetch requires present, valid authorization YAML."""
    resolved = _resolve_path(authorization_path)
    if not resolved.is_file():
        raise FredLivePrimaryAuthorizationError(
            f"authorization evidence missing: {authorization_path}"
        )
    payload = load_authorization_yaml(resolved)
    if payload.get("scope") != "fred_live_primary_sandbox_only":
        raise FredLivePrimaryAuthorizationError(
            "scope must be fred_live_primary_sandbox_only"
        )
    if payload.get("allow_production_clean_write"):
        raise FredLivePrimaryAuthorizationError("allow_production_clean_write must be false")
    if live_requested and payload.get("skip_live_fetch_default", True):
        raise FredLivePrimaryAuthorizationError(
            "live_requested but skip_live_fetch_default is true; explicit opt-in required"
        )
    return payload


def run_fred_live_primary_closeout(
    *,
    authorization_path: str | Path,
    skip_live_fetch: bool = True,
) -> dict[str, Any]:
    """Record SH-06 closeout metadata without production clean write."""
    auth = validate_fred_live_authorization(
        authorization_path, live_requested=not skip_live_fetch
    )
    return {
        "pilot_id": auth.get("pilot_id"),
        "source_id": auth.get("source_id"),
        "authorization_present": True,
        "skip_live_fetch": skip_live_fetch,
        "production_clean_write": False,
        "sandbox_only": True,
        "scope": auth.get("scope"),
    }
