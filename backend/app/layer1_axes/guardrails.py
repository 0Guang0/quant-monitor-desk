"""Axis engineering guardrails — forbidden substitutes and shadow constraints."""

from __future__ import annotations

from backend.app.layer1_axes.models import AxisEngineeringGuardrail, AxisIndicatorDefinition


class GuardrailViolationError(ValueError):
    """Engineering guardrail blocked an operation."""


class AxisEngineeringGuardrailValidator:
    """Validates substitute usage and shadow diagnostic constraints."""

    def __init__(self, guardrails: tuple[AxisEngineeringGuardrail, ...]) -> None:
        by_axis = {g.axis_id: g for g in guardrails}
        self._guardrails = by_axis

    def reject_forbidden_substitute(
        self,
        indicator: AxisIndicatorDefinition,
        *,
        substitute_id: str,
    ) -> None:
        blocked = set(indicator.forbidden_substitutes)
        axis_guard = self._guardrails.get(indicator.axis_id)
        if axis_guard:
            blocked.update(axis_guard.forbidden_terms)
        if substitute_id in blocked:
            raise GuardrailViolationError(
                f"forbidden substitute {substitute_id!r} for indicator {indicator.indicator_id!r}"
            )

    @staticmethod
    def assert_shadow_diagnostics_allowed(indicator: AxisIndicatorDefinition) -> None:
        if not indicator.is_shadow:
            return
        role = indicator.role_notes.lower()
        if indicator.module == "shadow_diagnostics":
            if "no_takeover" not in role and not indicator.diagnostic_only:
                raise GuardrailViolationError(
                    f"shadow indicator {indicator.indicator_id!r} missing no_takeover constraint"
                )

    @staticmethod
    def assert_shadow_outside_group_has_diagnostic_only(indicator: AxisIndicatorDefinition) -> None:
        if not indicator.is_shadow:
            return
        if indicator.module == "shadow_diagnostics":
            return
        if not indicator.diagnostic_only:
            raise GuardrailViolationError(
                f"shadow indicator {indicator.indicator_id!r} outside shadow_diagnostics "
                "requires diagnostic_only=true"
            )
