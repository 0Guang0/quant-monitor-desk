"""Double-count guard — Layer 1 axis inputs are display/reference only in Layer 2."""

from __future__ import annotations

from backend.app.layer2_sensors.models import CrossAssetRegistryEntry

LAYER1_AXIS_INPUT_GUARD = "layer1_axis_input_display_only"
NO_ACCEPTED_CHANNEL_GUARD = "no_accepted_channel"


class DoubleCountGuardError(ValueError):
    """Layer 2 attempted to re-count a Layer 1 axis input."""


def validate_registry_double_count_rules(entries: list[CrossAssetRegistryEntry]) -> None:
    """Validate registry annotations for axis-input assets."""
    for entry in entries:
        if entry.is_axis_input:
            if not entry.display_only:
                raise DoubleCountGuardError(
                    f"asset {entry.asset_id!r}: is_axis_input=true requires display_only=true"
                )
            if entry.eligible_for_model:
                raise DoubleCountGuardError(
                    f"asset {entry.asset_id!r}: Layer 1 axis inputs must not be eligible_for_model"
                )
            if entry.double_count_guard != LAYER1_AXIS_INPUT_GUARD:
                raise DoubleCountGuardError(
                    f"asset {entry.asset_id!r}: axis input must use "
                    f"double_count_guard={LAYER1_AXIS_INPUT_GUARD!r}"
                )
        if entry.double_count_guard == NO_ACCEPTED_CHANNEL_GUARD:
            if entry.eligible_for_model:
                raise DoubleCountGuardError(
                    f"asset {entry.asset_id!r}: NO_ACCEPTED_CHANNEL assets cannot be model-eligible"
                )


def assert_model_eligible(entry: CrossAssetRegistryEntry) -> None:
    """Block model aggregation for display-only / axis-input assets."""
    if entry.is_axis_input or entry.display_only:
        raise DoubleCountGuardError(
            f"asset {entry.asset_id!r} is Layer 1 axis display/reference only; "
            "cannot participate in Layer 2 model aggregation"
        )
    if not entry.eligible_for_model:
        raise DoubleCountGuardError(
            f"asset {entry.asset_id!r} is not eligible_for_model in cross_asset_registry"
        )
    if entry.double_count_guard == NO_ACCEPTED_CHANNEL_GUARD:
        raise DoubleCountGuardError(
            f"asset {entry.asset_id!r} has no accepted channel (NO_ACCEPTED_CHANNEL)"
        )


def quality_flags_for_registry_entry(entry: CrossAssetRegistryEntry) -> tuple[str, ...]:
    flags: list[str] = []
    if entry.double_count_guard == NO_ACCEPTED_CHANNEL_GUARD:
        flags.append("NO_ACCEPTED_CHANNEL")
    if entry.is_axis_input:
        flags.append("LAYER1_AXIS_INPUT_DISPLAY_ONLY")
    return tuple(flags)
