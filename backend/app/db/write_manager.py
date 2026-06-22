"""Standard write entry: staging → ValidationGate → clean with audit."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import duckdb
from backend.app.db.failed_write_audit_sidecar import append_failed_write_audit
from backend.app.db.sql_identifiers import quote_ident
from backend.app.db.validation_gate import (
    ValidationGateError,
    ValidationRejected,
)
from backend.app.util.error_redaction import redact_error_message

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
    data_domain: str = ""
    partition_keys: tuple[str, ...] = ()
    conflict_report_id: str | None = None
    source_role: str = "primary"
    allow_partial_write: bool = False
    requested_by: str = "system"


@dataclass(frozen=True)
class WriteResult:
    write_id: str
    status: WriteStatus
    rows_inserted: int = 0
    rows_updated: int = 0
    error_message: str | None = None


class WriteManager:
    SUPPORTED_MODES = ("append_only", "upsert_by_pk")
    UNSUPPORTED_MODES = (
        "replace_partition",
        "manual_patch",
        "schema_migration",
    )
    MIN_STAGING_ROWS = 1

    def __init__(self, conn_manager, gate) -> None:
        if gate is None:
            raise ValueError(
                "WriteManager requires an explicit ValidationGate; "
                "use tests.db_helpers.create_test_write_manager() in tests"
            )
        self.conn_manager = conn_manager
        self.gate = gate

    def _validate_request(self, req: WriteRequest) -> None:
        quote_ident(req.target_table)
        quote_ident(req.staging_table)
        for col in req.primary_keys:
            quote_ident(col)
        if not (req.data_domain or "").strip():
            raise ValueError("WriteRequest.data_domain is required")
        if req.write_mode == "upsert_by_pk" and not req.primary_keys:
            raise ValueError("upsert_by_pk requires primary_keys")

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

    def _table_columns(self, con: duckdb.DuckDBPyConnection, table_name: str) -> list[str]:
        quoted = quote_ident(table_name)
        rows = con.execute(f"PRAGMA table_info({quoted})").fetchall()
        return [row[1] for row in rows]

    def _assert_staging_columns_match(
        self,
        con: duckdb.DuckDBPyConnection,
        req: WriteRequest,
        target: str,
        staging: str,
    ) -> list[str]:
        target_cols = self._table_columns(con, req.target_table)
        staging_cols = self._table_columns(con, req.staging_table)
        if target_cols != staging_cols:
            raise ValueError(
                f"column mismatch between {req.target_table!r} and "
                f"{req.staging_table!r}: target={target_cols!r} staging={staging_cols!r}"
            )
        return staging_cols

    def _assert_staging_pk_unique(
        self,
        con: duckdb.DuckDBPyConnection,
        staging: str,
        primary_keys: list[str],
    ) -> None:
        pk_list = ", ".join(primary_keys)
        dup_count = con.execute(
            f"""
            SELECT COUNT(*) FROM (
                SELECT {pk_list}, COUNT(*) AS c
                FROM {staging}
                GROUP BY {pk_list}
                HAVING COUNT(*) > 1
            )
            """
        ).fetchone()[0]
        if dup_count:
            raise ValueError("staging table contains duplicate primary keys")

    def _build_merge_sql(
        self,
        req: WriteRequest,
        target: str,
        staging: str,
        primary_keys: list[str],
        columns: list[str],
    ) -> list[str]:
        col_sql = ", ".join(quote_ident(col) for col in columns)
        if req.write_mode == "append_only":
            return [f"INSERT INTO {target} ({col_sql}) SELECT {col_sql} FROM {staging}"]
        if req.write_mode == "upsert_by_pk":
            pk_join = " AND ".join(f"{target}.{col} = {staging}.{col}" for col in primary_keys)
            return [
                f"DELETE FROM {target} WHERE EXISTS (SELECT 1 FROM {staging} WHERE {pk_join})",
                f"INSERT INTO {target} ({col_sql}) SELECT {col_sql} FROM {staging}",
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
        conflict_status: str | None = None,
    ) -> None:
        safe_message = redact_error_message(error_message) if error_message else None
        resolved_conflict = conflict_status or (
            "CHECKED"
            if req.conflict_report_id
            else ("NOT_APPLICABLE" if validation_status == "PASSED" else "SKIPPED")
        )
        con.execute(
            """
            INSERT INTO write_audit_log (
                write_id, run_id, job_id, target_table, staging_table, write_mode,
                primary_keys, partition_keys, rows_in_staging, rows_inserted,
                rows_updated, rows_deleted, rows_rejected, validation_status,
                conflict_status, source_used, source_role, source_switched,
                stale_reason, data_domain, conflict_report_id, requested_by,
                allow_partial_write, traceback_digest, started_at, finished_at,
                status, error_message
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            [
                write_id,
                req.run_id,
                req.job_id,
                req.target_table,
                req.staging_table,
                req.write_mode,
                ",".join(req.primary_keys),
                ",".join(req.partition_keys) if req.partition_keys else None,
                rows_in_staging,
                rows_inserted,
                rows_updated,
                0,
                0,
                validation_status,
                resolved_conflict,
                req.source_used,
                req.source_role,
                False,
                None,
                req.data_domain or None,
                req.conflict_report_id,
                req.requested_by,
                req.allow_partial_write,
                None,
                started_at,
                datetime.now(UTC),
                status,
                safe_message,
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
        audit_sidecar_root: Path | None = None,
    ) -> WriteResult:
        """Persist FAILED audit after rolling back the data write."""
        if own_transaction:
            con.execute("BEGIN")
            self._write_audit(
                con,
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
            con.execute("COMMIT")
        else:
            self._write_audit(
                con,
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
            if audit_sidecar_root is not None:
                append_failed_write_audit(
                    {
                        "write_id": write_id,
                        "run_id": req.run_id,
                        "job_id": req.job_id,
                        "target_table": req.target_table,
                        "staging_table": req.staging_table,
                        "write_mode": req.write_mode,
                        "validation_report_id": req.validation_report_id,
                        "validation_status": validation_status,
                        "status": "FAILED",
                        "error_message": redact_error_message(error_message),
                        "rows_in_staging": rows_in_staging,
                    },
                    data_root=audit_sidecar_root,
                )
        return WriteResult(
            write_id=write_id,
            status="FAILED",
            error_message=redact_error_message(error_message),
        )

    def _execute_write(
        self,
        con: duckdb.DuckDBPyConnection,
        req: WriteRequest,
        *,
        own_transaction: bool = True,
        audit_sidecar_root: Path | None = None,
    ) -> WriteResult:
        write_id = str(uuid.uuid4())
        started_at = datetime.now(UTC)
        target, staging, primary_keys = self._validated_tables(req)
        rows_in_staging = con.execute(f"SELECT COUNT(*) FROM {staging}").fetchone()[0]
        if rows_in_staging < self.MIN_STAGING_ROWS:
            raise ValueError(
                f"staging table {req.staging_table!r} has {rows_in_staging} rows; "
                f"minimum {self.MIN_STAGING_ROWS} required before clean write"
            )
        sidecar_root = audit_sidecar_root
        if not own_transaction and sidecar_root is None:
            from backend.app.config import DATA_ROOT

            sidecar_root = DATA_ROOT

        if own_transaction:
            con.execute("BEGIN")

        try:
            self.gate.assert_can_write(
                req.validation_report_id,
                req.write_mode,
                con=con,
            )

            before = con.execute(f"SELECT COUNT(*) FROM {target}").fetchone()[0]
            rows_updated = 0
            columns = self._assert_staging_columns_match(con, req, target, staging)
            if req.write_mode == "upsert_by_pk":
                self._assert_staging_pk_unique(con, staging, primary_keys)
                rows_updated = self._count_pk_matches(con, target, staging, primary_keys)

            for sql in self._build_merge_sql(req, target, staging, primary_keys, columns):
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
                audit_sidecar_root=sidecar_root,
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
                    own_transaction=True,
                )
            # own_transaction=False: aborted txn; caller ROLLBACKs. No extra audit con.
            return WriteResult(
                write_id=write_id,
                status="FAILED",
                error_message=redact_error_message(str(exc)),
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
        audit_sidecar_root: Path | None = None,
    ) -> WriteResult:
        if req.write_mode not in self.SUPPORTED_MODES:
            if req.write_mode in self.UNSUPPORTED_MODES:
                raise ValueError(
                    f"write_mode {req.write_mode!r} is defined in contract but not "
                    "implemented yet; use append_only or upsert_by_pk"
                )
            raise ValueError(f"unsupported write_mode: {req.write_mode}")
        self._validate_request(req)

        if con is not None:
            return self._execute_write(
                con,
                req,
                own_transaction=own_transaction,
                audit_sidecar_root=audit_sidecar_root,
            )
        with self.conn_manager.writer() as writer_con:
            return self._execute_write(
                writer_con,
                req,
                own_transaction=own_transaction,
                audit_sidecar_root=audit_sidecar_root,
            )
