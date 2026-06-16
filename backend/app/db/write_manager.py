"""Standard write entry: staging → ValidationGate → clean with audit."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

import duckdb
from backend.app.db.sql_identifiers import quote_ident
from backend.app.db.validation_gate import (
    StubValidationGate,
    ValidationGateError,
    ValidationRejected,
)

WriteStatus = Literal["SUCCESS", "FAILED"]


@dataclass(frozen=True)
class WriteRequest:
    run_id: str
    job_id: str
    target_table: str
    staging_table: str
    write_mode: str
    primary_keys: tuple[str, ...]
    validation_report_id: str
    source_used: str


@dataclass(frozen=True)
class WriteResult:
    write_id: str
    status: WriteStatus
    rows_inserted: int = 0
    rows_updated: int = 0
    error_message: str | None = None


class WriteManager:
    SUPPORTED_MODES = ("append_only", "upsert_by_pk")

    def __init__(self, conn_manager, gate=None) -> None:
        self.conn_manager = conn_manager
        self.gate = gate or StubValidationGate()

    def _validate_request(self, req: WriteRequest) -> None:
        quote_ident(req.target_table)
        quote_ident(req.staging_table)
        for col in req.primary_keys:
            quote_ident(col)

    def _validated_tables(self, req: WriteRequest) -> tuple[str, str, list[str]]:
        target = quote_ident(req.target_table)
        staging = quote_ident(req.staging_table)
        primary_keys = [quote_ident(col) for col in req.primary_keys]
        return target, staging, primary_keys

    def _count_pk_matches(
        self, con: duckdb.DuckDBPyConnection, target: str, staging: str, primary_keys: list[str]
    ) -> int:
        pk_join = " AND ".join(f"{target}.{col} = {staging}.{col}" for col in primary_keys)
        return con.execute(
            f"SELECT COUNT(*) FROM {target} WHERE EXISTS (SELECT 1 FROM {staging} WHERE {pk_join})"
        ).fetchone()[0]

    def _build_merge_sql(
        self, req: WriteRequest, target: str, staging: str, primary_keys: list[str]
    ) -> list[str]:
        if req.write_mode == "append_only":
            return [f"INSERT INTO {target} SELECT * FROM {staging}"]
        if req.write_mode == "upsert_by_pk":
            pk_join = " AND ".join(
                f"{target}.{col} = {staging}.{col}" for col in primary_keys
            )
            return [
                f"DELETE FROM {target} WHERE EXISTS (SELECT 1 FROM {staging} WHERE {pk_join})",
                f"INSERT INTO {target} SELECT * FROM {staging}",
            ]
        raise ValueError(f"unsupported write_mode: {req.write_mode}")

    def _write_audit(
        self,
        con,
        *,
        write_id: str,
        req: WriteRequest,
        started_at: datetime,
        status: str,
        rows_in_staging: int,
        rows_inserted: int,
        rows_updated: int,
        validation_status: str,
        error_message: str | None,
    ) -> None:
        con.execute(
            """
            INSERT INTO write_audit_log (
                write_id, run_id, job_id, target_table, staging_table, write_mode,
                primary_keys, rows_in_staging, rows_inserted, rows_updated,
                rows_deleted, rows_rejected, validation_status, source_used,
                started_at, finished_at, status, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                write_id,
                req.run_id,
                req.job_id,
                req.target_table,
                req.staging_table,
                req.write_mode,
                ",".join(req.primary_keys),
                rows_in_staging,
                rows_inserted,
                rows_updated,
                0,
                0,
                validation_status,
                req.source_used,
                started_at,
                datetime.now(UTC),
                status,
                error_message,
            ],
        )

    def _commit_audit_after_rollback(
        self,
        con: duckdb.DuckDBPyConnection,
        write_id: str,
        req: WriteRequest,
        started_at: datetime,
        rows_in_staging: int,
        validation_status: str,
        error_message: str,
        *,
        own_transaction: bool = True,
    ) -> WriteResult:
        """Persist FAILED audit after rolling back the data write."""
        audit_con = con
        close_audit = False
        if not own_transaction:
            audit_con = duckdb.connect(str(self.conn_manager.db_path))
            close_audit = True
        try:
            audit_con.execute("BEGIN")
            self._write_audit(
                audit_con,
                write_id=write_id,
                req=req,
                started_at=started_at,
                status="FAILED",
                rows_in_staging=rows_in_staging,
                rows_inserted=0,
                rows_updated=0,
                validation_status=validation_status,
                error_message=error_message,
            )
            audit_con.execute("COMMIT")
        finally:
            if close_audit:
                audit_con.close()
        return WriteResult(
            write_id=write_id,
            status="FAILED",
            error_message=error_message,
        )

    def _execute_write(
        self,
        con: duckdb.DuckDBPyConnection,
        req: WriteRequest,
        *,
        own_transaction: bool = True,
    ) -> WriteResult:
        write_id = str(uuid.uuid4())
        started_at = datetime.now(UTC)
        target, staging, primary_keys = self._validated_tables(req)
        rows_in_staging = con.execute(f"SELECT COUNT(*) FROM {staging}").fetchone()[0]

        if own_transaction:
            con.execute("BEGIN")

        try:
            self.gate.assert_can_write(req.validation_report_id, req.write_mode)

            before = con.execute(f"SELECT COUNT(*) FROM {target}").fetchone()[0]
            rows_updated = 0
            if req.write_mode == "upsert_by_pk":
                rows_updated = self._count_pk_matches(con, target, staging, primary_keys)

            for sql in self._build_merge_sql(req, target, staging, primary_keys):
                con.execute(sql)

            after = con.execute(f"SELECT COUNT(*) FROM {target}").fetchone()[0]
            rows_inserted = after - before

            self._write_audit(
                con,
                write_id=write_id,
                req=req,
                started_at=started_at,
                status="SUCCESS",
                rows_in_staging=rows_in_staging,
                rows_inserted=rows_inserted,
                rows_updated=rows_updated,
                validation_status="PASSED",
                error_message=None,
            )
            if own_transaction:
                con.execute("COMMIT")
            return WriteResult(
                write_id=write_id,
                status="SUCCESS",
                rows_inserted=rows_inserted,
                rows_updated=rows_updated,
            )
        except (ValidationRejected, ValidationGateError) as exc:
            if own_transaction:
                con.execute("ROLLBACK")
            return self._commit_audit_after_rollback(
                con,
                write_id,
                req,
                started_at,
                rows_in_staging,
                "FAILED",
                str(exc),
                own_transaction=own_transaction,
            )
        except duckdb.Error as exc:
            if own_transaction:
                con.execute("ROLLBACK")
            return self._commit_audit_after_rollback(
                con,
                write_id,
                req,
                started_at,
                rows_in_staging,
                "ERROR",
                str(exc),
                own_transaction=own_transaction,
            )
        except Exception:
            if own_transaction:
                con.execute("ROLLBACK")
            raise

    def write(
        self,
        req: WriteRequest,
        *,
        con: duckdb.DuckDBPyConnection | None = None,
        own_transaction: bool = True,
    ) -> WriteResult:
        if req.write_mode not in self.SUPPORTED_MODES:
            raise ValueError(f"unsupported write_mode: {req.write_mode}")
        self._validate_request(req)

        if con is not None:
            return self._execute_write(con, req, own_transaction=own_transaction)
        with self.conn_manager.writer() as writer_con:
            return self._execute_write(writer_con, req, own_transaction=own_transaction)
