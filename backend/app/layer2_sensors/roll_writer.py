"""Persist explicit futures roll events via WriteManager."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import duckdb
from backend.app.db.connection import ConnectionManager
from backend.app.db.validation_gate import DbValidationGate
from backend.app.db.write_manager import WriteManager, WriteRequest, WriteResult
from backend.app.layer2_sensors.models import MainContractRollEvent


def roll_event_row_to_db_tuple(event: MainContractRollEvent) -> list:
    roll_id = f"roll-{event.asset_id}-{event.roll_date.isoformat()}-{event.new_contract}"
    return [
        roll_id,
        event.asset_id,
        event.roll_event,
        event.old_contract,
        event.new_contract,
        event.roll_reason,
        event.roll_date,
        event.volume_old,
        event.volume_new,
        event.open_interest_old,
        event.open_interest_new,
        datetime.now(UTC),
    ]


class Layer2RollEventWriter:
    """Write cross_asset_roll_event rows — explicit roll, no silent switch."""

    def __init__(self, conn_manager: ConnectionManager) -> None:
        self._cm = conn_manager
        self._wm = WriteManager(conn_manager, DbValidationGate(conn_manager))

    def write_roll_event(
        self,
        event: MainContractRollEvent,
        *,
        validation_report_id: str,
        con: duckdb.DuckDBPyConnection | None = None,
        own_transaction: bool = True,
    ) -> WriteResult:
        if not event.roll_event:
            raise ValueError("refusing to write roll_event=false; silent switch forbidden")
        if con is None:
            with self._cm.writer() as writer_con:
                return self._write_on_connection(
                    writer_con,
                    event=event,
                    validation_report_id=validation_report_id,
                    own_transaction=own_transaction,
                )
        return self._write_on_connection(
            con,
            event=event,
            validation_report_id=validation_report_id,
            own_transaction=own_transaction,
        )

    def _write_on_connection(
        self,
        con: duckdb.DuckDBPyConnection,
        *,
        event: MainContractRollEvent,
        validation_report_id: str,
        own_transaction: bool,
    ) -> WriteResult:
        staging = f"stg_l2_roll_{uuid.uuid4().hex[:8]}"
        con.execute(f"CREATE TABLE {staging} AS SELECT * FROM cross_asset_roll_event WHERE 1=0")
        con.execute(
            f"INSERT INTO {staging} VALUES ({','.join(['?'] * 12)})",
            roll_event_row_to_db_tuple(event),
        )
        req = WriteRequest(
            run_id="layer2-staged-run",
            job_id="layer2-roll-event",
            target_table="cross_asset_roll_event",
            staging_table=staging,
            write_mode="upsert_by_pk",
            primary_keys=("roll_id",),
            validation_report_id=validation_report_id,
            source_used="layer2_staged_fixture",
            data_domain="layer2_cross_asset_roll",
        )
        return self._wm.write(req, con=con, own_transaction=own_transaction)
