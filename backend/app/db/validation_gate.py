"""ValidationGate implementations.

- ``StubValidationGate``: Round 1 test-only helper. **Must not** be the
  production default; ``WriteManager`` requires an explicit gate.
- ``DbValidationGate``: Round 2 Batch C production gate. It reads the
  persisted ``validation_report`` row and decides whether a write may
  proceed based on real DB state (no stubbed prefix behaviour).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import duckdb
    from backend.app.db.connection import ConnectionManager


class ValidationGateError(RuntimeError):
    """Unknown or invalid validation_report_id."""

    def __init__(self, message: str, *, validation_report_id: str) -> None:
        super().__init__(message)
        self.validation_report_id = validation_report_id


class ValidationRejected(RuntimeError):
    """Validation report indicates write must not proceed."""

    def __init__(self, message: str, *, validation_report_id: str) -> None:
        super().__init__(message)
        self.validation_report_id = validation_report_id


class StubValidationGate:
    """Test-only gate. Production must inject a real gate (e.g. DbValidationGate)."""

    def assert_can_write(self, validation_report_id: str, write_mode: str) -> None:
        if validation_report_id.startswith("stub-pass-"):
            return
        if validation_report_id.startswith("stub-fail-"):
            raise ValidationRejected(
                f"validation rejected: {validation_report_id}",
                validation_report_id=validation_report_id,
            )
        raise ValidationGateError(
            f"unknown validation_report_id: {validation_report_id}",
            validation_report_id=validation_report_id,
        )


class DbValidationGate:
    """Production ValidationGate backed by the ``validation_report`` table.

    Decision policy (MASTER §4.3):

    - report row missing            -> ValidationGateError (reject)
    - status == FAILED              -> ValidationRejected
    - can_write_clean == false      -> ValidationRejected
    - needs_manual_review == true   -> ValidationRejected
    - schema_hash_changed w/o approval -> ValidationRejected
    - status == PASSED  + can_write_clean + no review -> allow
    - status == WARNING + can_write_clean + no review -> allow (explicit policy)

    The gate opens its own read-only connection via the ConnectionManager reader
    pool; it does not participate in the WriteManager write transaction, which is
    intentional — validation reports are immutable once persisted.
    """

    _SCHEMA_APPROVED_MODES = frozenset({"manual_patch", "schema_migration"})
    _SYNTHETIC_QUALITY_MARKERS = frozenset(
        {"raw_file_registry_metadata_only", "synthetic_migrated_schema_only"}
    )

    def __init__(self, conn_manager: ConnectionManager) -> None:
        self.conn_manager = conn_manager

    def _fetch_report(
        self, validation_report_id: str, con=None
    ) -> tuple[str, bool, bool, str | None, str | None, str | None, str | None] | None:
        sql = """
            SELECT status, can_write_clean, needs_manual_review, run_id,
                   job_id, source_id, quality_flags
            FROM validation_report
            WHERE validation_report_id = ?
        """
        params = [validation_report_id]
        if con is not None:
            row = con.execute(sql, params).fetchone()
        else:
            with self.conn_manager.reader() as reader_con:
                row = reader_con.execute(sql, params).fetchone()
        if row is None:
            return None
        (
            status,
            can_write_clean,
            needs_manual_review,
            run_id,
            job_id,
            source_id,
            quality_flags,
        ) = row
        return (
            str(status),
            bool(can_write_clean),
            bool(needs_manual_review),
            (None if run_id is None else str(run_id)),
            (None if job_id is None else str(job_id)),
            (None if source_id is None else str(source_id)),
            (None if quality_flags is None else str(quality_flags)),
        )

    def _has_blocking_severe_conflicts(
        self,
        run_id: str,
        con=None,
        *,
        job_id: str | None = None,
    ) -> bool:
        sql = """
            SELECT COUNT(*)
            FROM source_conflict
            WHERE severity = 'severe'
              AND reconcile_status IN ('OPEN', 'UNRESOLVED')
        """
        params: list[str] = []
        if job_id:
            sql += " AND job_id = ?"
            params.append(job_id)
        else:
            sql += " AND run_id = ?"
            params.append(run_id)
        if con is not None:
            count = con.execute(sql, params).fetchone()[0]
        else:
            with self.conn_manager.reader() as reader_con:
                count = reader_con.execute(sql, params).fetchone()[0]
        return int(count) > 0

    def _quality_flags_include_schema_drift(self, quality_flags: str | None) -> bool:
        if not quality_flags:
            return False
        try:
            parsed = json.loads(quality_flags)
        except json.JSONDecodeError:
            return "SCHEMA_DRIFT" in quality_flags
        if isinstance(parsed, list):
            return "SCHEMA_DRIFT" in parsed
        return False

    def _quality_flags_block_clean_write(self, quality_flags: str | None) -> bool:
        if not quality_flags:
            return False
        lowered = quality_flags.lower()
        return any(marker in lowered for marker in self._SYNTHETIC_QUALITY_MARKERS)

    def _schema_hash_blocks_write(
        self,
        con,
        *,
        job_id: str | None,
        source_id: str | None,
        quality_flags: str | None,
        write_mode: str,
    ) -> bool:
        if write_mode in self._SCHEMA_APPROVED_MODES:
            return False
        if self._quality_flags_include_schema_drift(quality_flags):
            return True
        if not job_id or not source_id:
            return False
        current_row = con.execute(
            """
            SELECT schema_hash
            FROM fetch_log
            WHERE job_id = ?
            ORDER BY fetch_time DESC
            LIMIT 1
            """,
            [job_id],
        ).fetchone()
        if current_row is None or current_row[0] is None:
            return False
        current_hash = str(current_row[0])
        baseline_row = con.execute(
            """
            SELECT schema_hash
            FROM file_registry
            WHERE source = ? AND schema_hash IS NOT NULL
            ORDER BY fetch_time DESC
            LIMIT 1
            """,
            [source_id],
        ).fetchone()
        if baseline_row is None or baseline_row[0] is None:
            return False
        return current_hash != str(baseline_row[0])

    def _enforce_report(
        self,
        validation_report_id: str,
        *,
        status: str,
        can_write_clean: bool,
        needs_manual_review: bool,
        run_id: str | None,
        job_id: str | None,
        source_id: str | None,
        quality_flags: str | None,
        write_mode: str,
        con=None,
    ) -> None:
        if status == "FAILED":
            raise ValidationRejected(
                f"validation report {validation_report_id!r} status=FAILED",
                validation_report_id=validation_report_id,
            )
        if not can_write_clean:
            raise ValidationRejected(
                f"validation report {validation_report_id!r} can_write_clean=false",
                validation_report_id=validation_report_id,
            )
        if needs_manual_review:
            raise ValidationRejected(
                f"validation report {validation_report_id!r} needs_manual_review=true",
                validation_report_id=validation_report_id,
            )
        if self._quality_flags_block_clean_write(quality_flags):
            raise ValidationRejected(
                f"validation report {validation_report_id!r} is synthetic/staged-only; "
                "clean write blocked",
                validation_report_id=validation_report_id,
            )
        if run_id and self._has_blocking_severe_conflicts(run_id, con, job_id=job_id):
            raise ValidationRejected(
                f"validation report {validation_report_id!r} blocked by open severe "
                f"source_conflict for run_id={run_id!r}",
                validation_report_id=validation_report_id,
            )
        schema_con = con
        if schema_con is None:
            with self.conn_manager.reader() as reader_con:
                if self._schema_hash_blocks_write(
                    reader_con,
                    job_id=job_id,
                    source_id=source_id,
                    quality_flags=quality_flags,
                    write_mode=write_mode,
                ):
                    raise ValidationRejected(
                        f"validation report {validation_report_id!r} blocked by "
                        f"schema_hash_changed without approval",
                        validation_report_id=validation_report_id,
                    )
        elif self._schema_hash_blocks_write(
            schema_con,
            job_id=job_id,
            source_id=source_id,
            quality_flags=quality_flags,
            write_mode=write_mode,
        ):
            raise ValidationRejected(
                f"validation report {validation_report_id!r} blocked by "
                f"schema_hash_changed without approval",
                validation_report_id=validation_report_id,
            )

    def assert_can_write(self, validation_report_id: str, write_mode: str) -> str:
        report = self._fetch_report(validation_report_id)
        if report is None:
            raise ValidationGateError(
                f"unknown validation_report_id: {validation_report_id}",
                validation_report_id=validation_report_id,
            )
        (
            status,
            can_write_clean,
            needs_manual_review,
            run_id,
            job_id,
            source_id,
            quality_flags,
        ) = report
        self._enforce_report(
            validation_report_id,
            status=status,
            can_write_clean=can_write_clean,
            needs_manual_review=needs_manual_review,
            run_id=run_id,
            job_id=job_id,
            source_id=source_id,
            quality_flags=quality_flags,
            write_mode=write_mode,
        )
        return status

    def assert_can_write_with(
        self, con: duckdb.DuckDBPyConnection, validation_report_id: str, write_mode: str
    ) -> str:
        report = self._fetch_report(validation_report_id, con=con)
        if report is None:
            raise ValidationGateError(
                f"unknown validation_report_id: {validation_report_id}",
                validation_report_id=validation_report_id,
            )
        (
            status,
            can_write_clean,
            needs_manual_review,
            run_id,
            job_id,
            source_id,
            quality_flags,
        ) = report
        self._enforce_report(
            validation_report_id,
            status=status,
            can_write_clean=can_write_clean,
            needs_manual_review=needs_manual_review,
            run_id=run_id,
            job_id=job_id,
            source_id=source_id,
            quality_flags=quality_flags,
            write_mode=write_mode,
            con=con,
        )
        return str(status)
