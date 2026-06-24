"""Layer 2 snapshot writer (L2-04 extract from snapshot_builder)."""

from __future__ import annotations

import uuid

import duckdb

from backend.app.db.connection import ConnectionManager
from backend.app.db.validation_gate import DbValidationGate
from backend.app.db.write_manager import WriteManager, WriteRequest
from backend.app.layer1_axes.lineage import guard_layer2_writeback
from backend.app.layer2_sensors.lineage import (
    Layer2LineageError,
    Layer2LineageEnvelope,
    assert_lineage_matches_validation_report,
    lineage_row_to_db_tuple,
    load_validation_report_provenance,
)
from backend.app.layer2_sensors.models import CrossAssetDailySnapshot, MainContractRollEvent
from backend.app.layer2_sensors.schema_ddl import AXIS_SNAPSHOT_LINEAGE_TABLE, ensure_layer2_staging_tables


def daily_snapshot_row_to_db_tuple(row: CrossAssetDailySnapshot) -> list:
    from datetime import UTC, datetime

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

        vr_fetch_ids, vr_content_hashes = load_validation_report_provenance(
            con, validation_report_id
        )
        assert_lineage_matches_validation_report(
            lineage,
            validation_report_id=validation_report_id,
            vr_fetch_ids=vr_fetch_ids,
            vr_content_hashes=vr_content_hashes,
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
            lineage_row_to_db_tuple(lineage),
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
