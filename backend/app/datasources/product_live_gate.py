"""Product live env gate (R3H-08 S08-BOOT · ADR-008).

Fail-closed switch for env-gated product live fetch. Rehearsal/pilot paths must not
substitute for this gate. Upgrade path: per-tier policy in live_tier_router.py.
"""

from __future__ import annotations

import os

from backend.app.core.resource_guard import Decision, ResourceGuard

PRODUCT_LIVE_FETCH_ENV = "QMD_ALLOW_LIVE_FETCH"


class ProductLiveGateError(RuntimeError):
    """Product live fetch rejected by env gate."""

    def __init__(self, message: str, *, code: str = "LIVE_FETCH_REJECTED") -> None:
        super().__init__(message)
        self.code = code


def is_product_live_fetch_allowed() -> bool:
    """Return True when documented product-live env opt-in is present."""
    raw = os.environ.get(PRODUCT_LIVE_FETCH_ENV, "")
    return str(raw).strip().lower() in {"1", "true", "yes"}


def assert_product_live_allowed(*, source_id: str, operation: str = "fetch") -> None:
    """Raise ProductLiveGateError when product live is not env-authorized."""
    if is_product_live_fetch_allowed():
        return
    raise ProductLiveGateError(
        (
            f"product live {operation} rejected for {source_id!r}: "
            f"{PRODUCT_LIVE_FETCH_ENV} not set to opt-in value"
        ),
        code="LIVE_FETCH_REJECTED",
    )


def gate_live_fetch_port(*, source_id: str, operation: str = "fetch") -> None:
    """ADR-008 fail-closed chain: env opt-in + ResourceGuard before live port use."""
    assert_product_live_allowed(source_id=source_id, operation=operation)
    decision, reason = ResourceGuard().check()
    if decision in (Decision.PAUSE, Decision.HARD_STOP):
        raise ProductLiveGateError(
            (
                f"product live {operation} blocked for {source_id!r}: "
                f"resource guard {decision.value}"
                + (f" ({reason})" if reason else "")
            ),
            code="RESOURCE_GUARD_PAUSED",
        )
