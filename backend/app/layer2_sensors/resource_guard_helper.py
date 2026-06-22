"""Shared ResourceGuard gate for Layer 2 batch-like operations."""

from __future__ import annotations

from backend.app.core.resource_guard import Decision, ResourceGuard


class ResourceGuardBlockedError(RuntimeError):
    """ResourceGuard blocked Layer 2 operation."""


def assert_resource_guard_allows(guard: ResourceGuard) -> None:
    decision, reason = guard.check()
    if decision in (Decision.PAUSE, Decision.HARD_STOP):
        raise ResourceGuardBlockedError(f"resource guard blocked: {decision.value} ({reason})")
