"""Write clean cross_asset_observation rows via WriteManager (staged-only)."""

from __future__ import annotations

import uuid
from datetime import date, datetime

import duckdb
from backend.app.core.resource_guard import ResourceGuard
from backend.app.db.connection import ConnectionManager
from backend.app.db.validation_gate import DbValidationGate
from backend.app.db.write_manager import WriteManager, WriteRequest, WriteResult
from backend.app.layer1_axes.lineage import guard_layer2_writeback
from backend.app.layer2_sensors.double_count_guard import DoubleCountGuardError
from backend.app.layer2_sensors.models import CrossAssetObservation, CrossAssetRegistryEntry
from backend.app.layer2_sensors.observation import (
    assert_observation_asset_match,
    assert_staged_source,
    filter_observations_for_as_of,
)
from backend.app.layer2_sensors.resource_guard_helper import assert_resource_guard_allows
from backend.app.layer2_sensors.schema_ddl import ensure_layer2_staging_tables

CROSS_ASSET_OBSERVATION_TABLE = "cross_asset_observation"


def observation_row_to_db_tuple(obs: CrossAssetObservation) -> list:
    return [
        obs.asset_id,
        obs.trade_time,
        obs.market,
        obs.asset_type,
        obs.open,
        obs.high,
        obs.low,
        obs.close,
        obs.pre_close,
        obs.volume,
        obs.amount,
        obs.open_interest,
        obs.source,
        obs.as_of_timestamp,
        obs.fetch_time,
        obs.quality_flag,
    ]


class Layer2ObservationWriter:
    """Persist validated Layer 2 observations to cross_asset_observation."""

    def __init__(
        self,
        conn_manager: ConnectionManager,
        *,
        resource_guard: ResourceGuard | None = None,
    ) -> None:
        self._cm = conn_manager
        self._wm = WriteManager(conn_manager, DbValidationGate(conn_manager))
        self._guard = resource_guard or ResourceGuard()

    def write_observations(
        self,
        *,
        registry_entry: CrossAssetRegistryEntry,
        as_of: datetime,
        trade_date: date,
        observations: list[CrossAssetObservation],
        validation_report_id: str,
        display_only_write: bool = True,
        run_id: str = "layer2-staged-run",
        job_id: str = "layer2-staged-job",
        source_used: str = "layer2_staged_fixture",
        data_domain: str = "layer2_cross_asset_observation",
        con: duckdb.DuckDBPyConnection | None = None,
        own_transaction: bool = True,
    ) -> WriteResult:
        if not observations:
            raise ValueError("write_observations requires at least one observation")
        if registry_entry.is_axis_input and not display_only_write:
            raise DoubleCountGuardError(
                f"axis-input asset {registry_entry.asset_id!r} requires display_only_write=True"
            )

        assert_resource_guard_allows(self._guard)
        assert_observation_asset_match(registry_entry, observations)
        visible = filter_observations_for_as_of(
            as_of=as_of,
            trade_date=trade_date,
            observations=observations,
        )
        if not visible:
            raise ValueError(f"no observations on trade_date {trade_date}")
        for obs in visible:
            assert_staged_source(registry_entry, obs)

        guard_layer2_writeback(target_table=CROSS_ASSET_OBSERVATION_TABLE, layer_id="layer2")

        if con is None:
            with self._cm.writer() as writer_con:
                ensure_layer2_staging_tables(writer_con)
                return self._write_on_connection(
                    writer_con,
                    rows=visible,
                    validation_report_id=validation_report_id,
                    run_id=run_id,
                    job_id=job_id,
                    source_used=source_used,
                    data_domain=data_domain,
                    own_transaction=own_transaction,
                )
        ensure_layer2_staging_tables(con)
        return self._write_on_connection(
            con,
            rows=visible,
            validation_report_id=validation_report_id,
            run_id=run_id,
            job_id=job_id,
            source_used=source_used,
            data_domain=data_domain,
            own_transaction=own_transaction,
        )

    def _write_on_connection(
        self,
        con: duckdb.DuckDBPyConnection,
        *,
        rows: list[CrossAssetObservation],
        validation_report_id: str,
        run_id: str,
        job_id: str,
        source_used: str,
        data_domain: str,
        own_transaction: bool,
    ) -> WriteResult:
        staging = f"stg_l2_obs_{uuid.uuid4().hex[:8]}"
        con.execute(
            f"CREATE TABLE {staging} AS SELECT * FROM {CROSS_ASSET_OBSERVATION_TABLE} WHERE 1=0"
        )
        for row in rows:
            con.execute(
                f"INSERT INTO {staging} VALUES ({','.join(['?'] * 16)})",
                observation_row_to_db_tuple(row),
            )
        req = WriteRequest(
            run_id=run_id,
            job_id=job_id,
            target_table=CROSS_ASSET_OBSERVATION_TABLE,
            staging_table=staging,
            write_mode="upsert_by_pk",
            primary_keys=("asset_id", "trade_time", "source"),
            validation_report_id=validation_report_id,
            source_used=source_used,
            data_domain=data_domain,
        )
        return self._wm.write(req, con=con, own_transaction=own_transaction)
