"""Write clean axis_observation rows via WriteManager (Batch 2.5 Phase 4)."""

from __future__ import annotations

import uuid

import duckdb
from backend.app.db.connection import ConnectionManager
from backend.app.db.validation_gate import DbValidationGate
from backend.app.db.write_manager import WriteManager, WriteRequest, WriteResult
from backend.app.layer1_axes.observation_contract import AXIS_OBSERVATION_TABLE
from backend.app.layer1_axes.observation_mapper import observation_row_to_db_tuple


class Layer1ObservationWriter:
    """Persist validated observation staging rows to axis_observation."""

    def __init__(self, conn_manager: ConnectionManager) -> None:
        self._cm = conn_manager
        self._wm = WriteManager(conn_manager, DbValidationGate(conn_manager))

    def write_observations(
        self,
        *,
        rows: list[dict[str, object]],
        validation_report_id: str,
        run_id: str,
        job_id: str,
        source_used: str,
        data_domain: str = "layer1_axis_observation",
        con: duckdb.DuckDBPyConnection | None = None,
        own_transaction: bool = True,
    ) -> WriteResult:
        if not rows:
            raise ValueError("write_observations requires at least one row")
        if con is None:
            with self._cm.writer() as writer_con:
                return self._write_observations_on_connection(
                    writer_con,
                    rows=rows,
                    validation_report_id=validation_report_id,
                    run_id=run_id,
                    job_id=job_id,
                    source_used=source_used,
                    data_domain=data_domain,
                    own_transaction=own_transaction,
                )
        return self._write_observations_on_connection(
            con,
            rows=rows,
            validation_report_id=validation_report_id,
            run_id=run_id,
            job_id=job_id,
            source_used=source_used,
            data_domain=data_domain,
            own_transaction=own_transaction,
        )

    def _write_observations_on_connection(
        self,
        con: duckdb.DuckDBPyConnection,
        *,
        rows: list[dict[str, object]],
        validation_report_id: str,
        run_id: str,
        job_id: str,
        source_used: str,
        data_domain: str,
        own_transaction: bool,
    ) -> WriteResult:
        staging = f"stg_axis_obs_{uuid.uuid4().hex[:8]}"
        con.execute(f"CREATE TABLE {staging} AS SELECT * FROM {AXIS_OBSERVATION_TABLE} WHERE 1=0")
        for row in rows:
            con.execute(
                f"""
                INSERT INTO {staging} VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                observation_row_to_db_tuple(row),
            )
        req = WriteRequest(
            run_id=run_id,
            job_id=job_id,
            target_table=AXIS_OBSERVATION_TABLE,
            staging_table=staging,
            write_mode="append_only",
            primary_keys=("observation_id",),
            validation_report_id=validation_report_id,
            source_used=source_used,
            data_domain=data_domain,
        )
        return self._wm.write(req, con=con, own_transaction=own_transaction)
