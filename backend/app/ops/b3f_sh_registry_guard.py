"""Batch 3F SH-07 — AkShare/Eastmoney no-false-close registry guard."""

from __future__ import annotations

from typing import Any

# SSOT: OPEN rows that sidecar evidence must not RESOLVED-close
OPEN_VALIDATION_REGISTRY_ROWS: frozenset[str] = frozenset(
    {"R3-B2.75-REQ2-EM", "R3-PROMPT14-AKSHARE-VAL-01"}
)


def build_no_false_close_guard() -> dict[str, Any]:
    """Return guard dict asserting validation-family rows stay OPEN."""
    return {
        "registry_rows_must_remain_open": sorted(OPEN_VALIDATION_REGISTRY_ROWS),
        "does_not_close_R3-B2.75-REQ2-EM": True,
        "does_not_close_R3-PROMPT14-AKSHARE-VAL-01": True,
        "validation_only_preserved": True,
        "sidecar_cannot_resolve_validation_rows": True,
    }


def assert_sidecar_does_not_close_validation_rows(closeout: dict[str, Any]) -> None:
    """Raise AssertionError if sidecar closeout falsely closes EM/AkShare rows."""
    guard = build_no_false_close_guard()
    for key, expected in guard.items():
        if key == "registry_rows_must_remain_open":
            continue
        if closeout.get(key) is not expected:
            raise AssertionError(f"{key} expected {expected!r}, got {closeout.get(key)!r}")
    for row_id in OPEN_VALIDATION_REGISTRY_ROWS:
        if row_id not in closeout.get("registry_rows_must_remain_open", []):
            raise AssertionError(f"{row_id} must remain in registry_rows_must_remain_open")
