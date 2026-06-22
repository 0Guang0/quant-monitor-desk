"""Cross-asset observation validation — no future data, staged-only."""

from __future__ import annotations

from datetime import date, datetime

from backend.app.layer2_sensors.models import CrossAssetObservation, CrossAssetRegistryEntry


class CrossAssetObservationError(ValueError):
    """Invalid observation for Layer 2 staged pipeline."""


def reject_future_observation(
    *,
    as_of: datetime,
    observation: CrossAssetObservation,
) -> None:
    """Enforce snapshot_lineage_contract no_future_data for all time boundaries."""
    if observation.trade_time > as_of:
        raise CrossAssetObservationError(
            f"future trade_time blocked for {observation.asset_id!r}: "
            f"trade_time {observation.trade_time!s} > snapshot as_of {as_of!s}"
        )
    visibility = observation.as_of_timestamp
    if visibility > as_of:
        raise CrossAssetObservationError(
            f"future input blocked for {observation.asset_id!r}: "
            f"as_of_timestamp {visibility!s} > snapshot as_of {as_of!s}"
        )
    if observation.fetch_time > as_of:
        raise CrossAssetObservationError(
            f"future fetch blocked for {observation.asset_id!r}: "
            f"fetch_time {observation.fetch_time!s} > snapshot as_of {as_of!s}"
        )


def filter_observations_for_as_of(
    *,
    as_of: datetime,
    trade_date: date,
    observations: list[CrossAssetObservation],
) -> list[CrossAssetObservation]:
    visible: list[CrossAssetObservation] = []
    wrong_date: list[CrossAssetObservation] = []
    for obs in observations:
        reject_future_observation(as_of=as_of, observation=obs)
        if obs.trade_time.date() != trade_date:
            wrong_date.append(obs)
            continue
        visible.append(obs)
    if wrong_date and visible:
        raise CrossAssetObservationError(
            f"mixed trade_date batch for {visible[0].asset_id!r}: "
            f"{len(wrong_date)} observations outside trade_date={trade_date}"
        )
    return visible


def assert_observation_asset_match(
    entry: CrossAssetRegistryEntry,
    observations: list[CrossAssetObservation],
) -> None:
    for obs in observations:
        if obs.asset_id != entry.asset_id:
            raise CrossAssetObservationError(
                f"observation asset_id {obs.asset_id!r} != registry {entry.asset_id!r}"
            )


def assert_staged_source(
    entry: CrossAssetRegistryEntry,
    observation: CrossAssetObservation,
) -> None:
    if entry.primary_source in ("none", ""):
        raise CrossAssetObservationError(
            f"asset {entry.asset_id!r} has no accepted primary_source"
        )
    if observation.source == "tdx_pytdx":
        raise CrossAssetObservationError(
            "tdx_pytdx cannot be used as production Layer 2 source on 019"
        )
