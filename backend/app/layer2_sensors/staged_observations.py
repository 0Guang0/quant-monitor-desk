"""Shared observation staging prep for Layer 2 writers (L2-05)."""

from __future__ import annotations

from typing import Any


def prepare_staged_observations(
    observations: list[Any],
    *,
    as_of,
    asset_id: str,
) -> list[Any]:
    """Filter and assert observations match target asset/as_of before staging write."""
    from backend.app.layer2_sensors.observation_writer import (
        assert_observation_asset_match,
        filter_observations_for_as_of,
    )

    filtered = filter_observations_for_as_of(observations, as_of=as_of)
    for row in filtered:
        assert_observation_asset_match(row, asset_id=asset_id)
    return filtered
