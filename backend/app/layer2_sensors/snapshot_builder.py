"""Build cross_asset_daily_snapshot rows with lineage (staged-only)."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import duckdb
from backend.app.core.resource_guard import ResourceGuard
from backend.app.db.connection import ConnectionManager
from backend.app.db.validation_gate import DbValidationGate
from backend.app.db.write_manager import WriteManager, WriteRequest
from backend.app.layer1_axes.lineage import guard_layer2_writeback
from backend.app.layer2_sensors.lineage import lineage_row_to_db_tuple
from backend.app.layer2_sensors.double_count_guard import (
    assert_model_eligible,
    quality_flags_for_registry_entry,
)
from backend.app.layer2_sensors.futures_roll import ContractLiquidity, FuturesRollHandler
from backend.app.layer2_sensors.lineage import Layer2LineageBuilder, Layer2LineageError
from backend.app.layer2_sensors.models import (
    CrossAssetDailySnapshot,
    CrossAssetObservation,
    CrossAssetRegistryEntry,
    Layer2LineageEnvelope,
    MainContractRollEvent,
)
from backend.app.layer2_sensors.clean_observation_reader import resolve_clean_db_key
from backend.app.layer2_sensors.observation import (
    CrossAssetObservationError,
    assert_observation_asset_match,
    assert_observation_source,
    filter_observations_for_as_of,
)
from backend.app.layer2_sensors.resource_guard_helper import assert_resource_guard_allows
from backend.app.layer2_sensors.schema_ddl import (
    AXIS_SNAPSHOT_LINEAGE_TABLE,
    ensure_layer2_staging_tables,
)


class CrossAssetSnapshotBuilder:
    """Build daily snapshots from staged observations under ResourceGuard."""

    def __init__(
        self,
        *,
        resource_guard: ResourceGuard | None = None,
        rule_version: str = "layer2_sensor_staged_v1",
        code_version: str = "layer2-staged-v1",
    ) -> None:
        self._guard = resource_guard or ResourceGuard()
        self._lineage_builder = Layer2LineageBuilder()
        self._roll_handler = FuturesRollHandler()
        self._rule_version = rule_version
        self._code_version = code_version

    def build_daily_snapshots(
        self,
        *,
        as_of: datetime,
        trade_date: date,
        registry_entry: CrossAssetRegistryEntry,
        observations: list[CrossAssetObservation],
        source_fetch_ids: tuple[str, ...],
        source_content_hashes: tuple[str, ...],
        upstream_snapshot_ids: tuple[str, ...] = (),
        is_incremental: bool = False,
        rebuild_reason: str | None = None,
        for_model: bool = False,
        roll_incumbent: ContractLiquidity | None = None,
        roll_challenger: ContractLiquidity | None = None,
    ) -> tuple[CrossAssetDailySnapshot, Layer2LineageEnvelope, MainContractRollEvent | None]:
        assert_resource_guard_allows(self._guard)

        if for_model:
            assert_model_eligible(registry_entry)

        assert_observation_asset_match(registry_entry, observations)
        visible = filter_observations_for_as_of(
            as_of=as_of,
            trade_date=trade_date,
            observations=observations,
        )
        if not visible:
            raise CrossAssetObservationError(
                f"no observations for {registry_entry.asset_id!r} on trade_date={trade_date}"
            )
        for obs in visible:
            assert_observation_source(registry_entry, obs)

        latest = max(visible, key=lambda o: o.trade_time)
        prev = _find_previous_close(visible, latest)
        pct_change = None
        if prev is not None and prev.close and latest.close:
            pct_change = (latest.close - prev.close) / prev.close

        roll_event: MainContractRollEvent | None = None
        active_contract = registry_entry.contract_code or ""
        if registry_entry.roll_rule and roll_incumbent and roll_challenger:
            roll_event = self._roll_handler.detect_roll(
                asset_id=registry_entry.asset_id,
                roll_date=trade_date,
                incumbent=roll_incumbent,
                challenger=roll_challenger,
                roll_rule=registry_entry.roll_rule,
            )
            if roll_event is not None:
                active_contract = roll_event.new_contract

        quality_flags = list(quality_flags_for_registry_entry(registry_entry))
        if latest.quality_flag:
            quality_flags.append(latest.quality_flag)

        hash_inputs = (
            registry_entry.asset_id,
            trade_date.isoformat(),
            *source_content_hashes,
            *(o.close for o in visible if o.close is not None),
        )
        param_hash = Layer2LineageBuilder.parameter_hash_for(
            rule_version=self._rule_version,
            inputs=tuple(str(x) for x in hash_inputs),
        )
        lineage_id = f"l2-lineage-{registry_entry.asset_id}-{trade_date.isoformat()}"
        window_start = min(o.trade_time for o in visible)
        window_end = max(o.as_of_timestamp for o in visible)

        lineage = self._lineage_builder.build(
            snapshot_id=lineage_id,
            snapshot_type="cross_asset_daily_snapshot",
            as_of=as_of,
            input_window_start=window_start,
            input_window_end=window_end,
            source_dataset_ids=(_lineage_source_dataset_id(registry_entry),),
            source_fetch_ids=source_fetch_ids,
            source_content_hashes=source_content_hashes,
            rule_version=self._rule_version,
            parameter_hash=param_hash,
            code_version=self._code_version,
            upstream_snapshot_ids=upstream_snapshot_ids,
            is_incremental=is_incremental,
            rebuild_reason=rebuild_reason,
        )

        snapshot = CrossAssetDailySnapshot(
            snapshot_id=f"l2-snap-{registry_entry.asset_id}-{trade_date.isoformat()}",
            asset_id=registry_entry.asset_id,
            trade_date=trade_date,
            close=latest.close,
            pct_change=pct_change,
            volume=latest.volume,
            amount=latest.amount,
            open_interest=latest.open_interest,
            level_label=_level_label(pct_change),
            change_label=_change_label(pct_change),
            quality_flags=tuple(quality_flags),
            source_used=latest.source,
            as_of_timestamp=as_of,
            lineage_snapshot_id=lineage.snapshot_id,
            active_contract=active_contract,
        )
        return snapshot, lineage, roll_event


def _lineage_source_dataset_id(registry_entry: CrossAssetRegistryEntry) -> str:
    if registry_entry.primary_source == "fred":
        db_key = resolve_clean_db_key(registry_entry.instrument_id)
        return f"fred:axis_observation:{db_key}"
    return f"staged:cross_asset_observation:{registry_entry.asset_id}"


def _find_previous_close(
    observations: list[CrossAssetObservation],
    latest: CrossAssetObservation,
) -> CrossAssetObservation | None:
    older = [o for o in observations if o.trade_time < latest.trade_time and o.close is not None]
    if not older:
        return None
    return max(older, key=lambda o: o.trade_time)


def _level_label(pct_change: float | None) -> str:
    if pct_change is None:
        return "unknown"
    if pct_change > 0.02:
        return "elevated"
    if pct_change < -0.02:
        return "depressed"
    return "neutral"


def _change_label(pct_change: float | None) -> str:
    if pct_change is None:
        return "no_prior"
    if pct_change > 0:
        return "up"
    if pct_change < 0:
        return "down"
    return "flat"


from backend.app.layer2_sensors.snapshot_writer import (  # noqa: E402
    Layer2SnapshotWriter,
    daily_snapshot_row_to_db_tuple,
)
