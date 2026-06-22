"""Build cross_asset_daily_snapshot rows with lineage (staged-only)."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import duckdb
from backend.app.core.resource_guard import ResourceGuard
from backend.app.db.connection import ConnectionManager
from backend.app.db.validation_gate import DbValidationGate
from backend.app.db.write_manager import WriteManager, WriteRequest
from backend.app.layer1_axes.lineage import guard_layer2_writeback, lineage_row_to_db_tuple
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
from backend.app.layer2_sensors.observation import (
    CrossAssetObservationError,
    assert_observation_asset_match,
    assert_staged_source,
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
            assert_staged_source(registry_entry, obs)

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
            source_dataset_ids=(f"staged:cross_asset_observation:{registry_entry.asset_id}",),
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


def daily_snapshot_row_to_db_tuple(row: CrossAssetDailySnapshot) -> list:
    return [
        row.snapshot_id,
        row.asset_id,
        row.trade_date,
        row.close,
        row.pct_change,
        row.volume,
        row.amount,
        row.open_interest,
        row.level_label,
        row.change_label,
        ",".join(row.quality_flags),
        row.source_used,
        row.as_of_timestamp,
        datetime.now(UTC),
        row.lineage_snapshot_id,
        row.active_contract,
    ]


def layer2_lineage_to_axis_tuple(lineage: Layer2LineageEnvelope) -> list:
    """Map Layer2 envelope to axis_snapshot_lineage row shape."""
    from backend.app.layer1_axes.models import LineageEnvelope

    axis_env = LineageEnvelope(
        snapshot_id=lineage.snapshot_id,
        snapshot_type=lineage.snapshot_type,
        layer_id=lineage.layer_id,
        as_of_timestamp=lineage.as_of_timestamp,
        generated_at=lineage.generated_at,
        input_data_window_start=lineage.input_data_window_start,
        input_data_window_end=lineage.input_data_window_end,
        source_dataset_ids=lineage.source_dataset_ids,
        source_fetch_ids=lineage.source_fetch_ids,
        source_content_hashes=lineage.source_content_hashes,
        rule_version=lineage.rule_version,
        code_version=lineage.code_version,
        parameter_hash=lineage.parameter_hash,
        resource_profile=lineage.resource_profile,
        upstream_snapshot_ids=lineage.upstream_snapshot_ids,
        is_incremental=lineage.is_incremental,
        rebuild_reason=lineage.rebuild_reason,
    )
    return lineage_row_to_db_tuple(axis_env)


class Layer2SnapshotWriter:
    """Write Layer 2 snapshots via staging → DbValidationGate → WriteManager."""

    def __init__(self, conn_manager: ConnectionManager) -> None:
        self._cm = conn_manager
        self._wm = WriteManager(conn_manager, DbValidationGate(conn_manager))

    def write_daily_snapshot(
        self,
        *,
        snapshot: CrossAssetDailySnapshot,
        lineage: Layer2LineageEnvelope,
        validation_report_id: str,
        roll_event: MainContractRollEvent | None = None,
        run_id: str = "layer2-staged-run",
        job_id: str = "layer2-staged-job",
        source_used: str = "layer2_staged_fixture",
        data_domain: str = "layer2_cross_asset_daily",
        con: duckdb.DuckDBPyConnection | None = None,
        own_transaction: bool = True,
    ):
        from backend.app.layer2_sensors.roll_writer import Layer2RollEventWriter

        guard_layer2_writeback(target_table="cross_asset_daily_snapshot", layer_id="layer2")
        # axis_snapshot_lineage: shared audit table; layer_id=layer2 rows permitted.
        if lineage.layer_id != "layer2":
            raise Layer2LineageError("layer2 writer requires layer_id=layer2")

        if con is None:
            with self._cm.writer() as writer_con:
                ensure_layer2_staging_tables(writer_con)
                return self._write_on_connection(
                    writer_con,
                    snapshot=snapshot,
                    lineage=lineage,
                    roll_event=roll_event,
                    validation_report_id=validation_report_id,
                    run_id=run_id,
                    job_id=job_id,
                    source_used=source_used,
                    data_domain=data_domain,
                    roll_writer=Layer2RollEventWriter(self._cm),
                    own_transaction=own_transaction,
                )
        ensure_layer2_staging_tables(con)
        return self._write_on_connection(
            con,
            snapshot=snapshot,
            lineage=lineage,
            roll_event=roll_event,
            validation_report_id=validation_report_id,
            run_id=run_id,
            job_id=job_id,
            source_used=source_used,
            data_domain=data_domain,
            roll_writer=Layer2RollEventWriter(self._cm),
            own_transaction=own_transaction,
        )

    def _write_on_connection(
        self,
        con: duckdb.DuckDBPyConnection,
        *,
        snapshot: CrossAssetDailySnapshot,
        lineage: Layer2LineageEnvelope,
        roll_event: MainContractRollEvent | None,
        validation_report_id: str,
        run_id: str,
        job_id: str,
        source_used: str,
        data_domain: str,
        roll_writer,
        own_transaction: bool,
    ):
        if roll_event is not None:
            roll_writer.write_roll_event(
                roll_event,
                validation_report_id=validation_report_id,
                con=con,
                own_transaction=False,
            )

        staging_snap = f"stg_l2_snap_{uuid.uuid4().hex[:8]}"
        con.execute(
            f"CREATE TABLE {staging_snap} AS SELECT * FROM cross_asset_daily_snapshot WHERE 1=0"
        )
        con.execute(
            f"INSERT INTO {staging_snap} VALUES ({','.join(['?'] * 16)})",
            daily_snapshot_row_to_db_tuple(snapshot),
        )
        snap_req = WriteRequest(
            run_id=run_id,
            job_id=job_id,
            target_table="cross_asset_daily_snapshot",
            staging_table=staging_snap,
            write_mode="upsert_by_pk",
            primary_keys=("snapshot_id",),
            validation_report_id=validation_report_id,
            source_used=source_used,
            data_domain=data_domain,
        )
        snap_result = self._wm.write(snap_req, con=con, own_transaction=False)

        staging_lin = f"stg_l2_lin_{uuid.uuid4().hex[:8]}"
        con.execute(
            f"CREATE TABLE {staging_lin} AS SELECT * FROM {AXIS_SNAPSHOT_LINEAGE_TABLE} WHERE 1=0"
        )
        con.execute(
            f"INSERT INTO {staging_lin} VALUES ({','.join(['?'] * 17)})",
            layer2_lineage_to_axis_tuple(lineage),
        )
        lin_req = WriteRequest(
            run_id=run_id,
            job_id=job_id,
            target_table=AXIS_SNAPSHOT_LINEAGE_TABLE,
            staging_table=staging_lin,
            write_mode="upsert_by_pk",
            primary_keys=("snapshot_id",),
            validation_report_id=validation_report_id,
            source_used=source_used,
            data_domain=data_domain,
        )
        lin_result = self._wm.write(lin_req, con=con, own_transaction=own_transaction)
        return snap_result, lin_result
