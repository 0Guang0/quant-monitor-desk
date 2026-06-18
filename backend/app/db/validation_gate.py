"""ValidationGate implementations.

- ``StubValidationGate``: Round 1 test-only helper. **Must not** be the
  production default; ``WriteManager`` requires an explicit gate.
- ``DbValidationGate``: Round 2 Batch C production gate. It reads the
  persisted ``validation_report`` row and decides whether a write may
  proceed based on real DB state (no stubbed prefix behaviour).
"""

from __future__ import annotations

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
    - status == PASSED  + can_write_clean + no review -> allow
    - status == WARNING + can_write_clean + no review -> allow (explicit policy)

    The gate opens its own read-only connection via the ConnectionManager reader
    pool; it does not participate in the WriteManager write transaction, which is
    intentional — validation reports are immutable once persisted.
    """

    def __init__(self, conn_manager: ConnectionManager) -> None:
        self.conn_manager = conn_manager

    def _fetch_report(
        self, validation_report_id: str
    ) -> tuple[str, bool, bool, str | None] | None:
        with self.conn_manager.reader() as con:
            row = con.execute(
                """
                SELECT status, can_write_clean, needs_manual_review, run_id
                FROM validation_report
                WHERE validation_report_id = ?
                """,
                [validation_report_id],
            ).fetchone()
        if row is None:
            return None
        status, can_write_clean, needs_manual_review, run_id = row
        return str(status), bool(can_write_clean), bool(needs_manual_review), (
            None if run_id is None else str(run_id)
        )

    def _has_blocking_severe_conflicts(self, run_id: str, con=None) -> bool:
        sql = """
            SELECT COUNT(*)
            FROM source_conflict
            WHERE run_id = ?
              AND severity = 'severe'
              AND reconcile_status IN ('OPEN', 'UNRESOLVED')
        """
        params = [run_id]
        if con is not None:
            count = con.execute(sql, params).fetchone()[0]
        else:
            with self.conn_manager.reader() as reader_con:
                count = reader_con.execute(sql, params).fetchone()[0]
        return int(count) > 0

    def _enforce_report(
        self,
        validation_report_id: str,
        *,
        status: str,
        can_write_clean: bool,
        needs_manual_review: bool,
        run_id: str | None,
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
        if run_id and self._has_blocking_severe_conflicts(run_id, con):
            raise ValidationRejected(
                f"validation report {validation_report_id!r} blocked by open severe "
                f"source_conflict for run_id={run_id!r}",
                validation_report_id=validation_report_id,
            )

    def assert_can_write(self, validation_report_id: str, write_mode: str) -> str:
        report = self._fetch_report(validation_report_id)
        if report is None:
            raise ValidationGateError(
                f"unknown validation_report_id: {validation_report_id}",
                validation_report_id=validation_report_id,
            )
        status, can_write_clean, needs_manual_review, run_id = report
        self._enforce_report(
            validation_report_id,
            status=status,
            can_write_clean=can_write_clean,
            needs_manual_review=needs_manual_review,
            run_id=run_id,
        )
        return status

    def assert_can_write_with(
        self, con: duckdb.DuckDBPyConnection, validation_report_id: str, write_mode: str
    ) -> str:
        row = con.execute(
            """
            SELECT status, can_write_clean, needs_manual_review, run_id
            FROM validation_report
            WHERE validation_report_id = ?
            """,
            [validation_report_id],
        ).fetchone()
        if row is None:
            raise ValidationGateError(
                f"unknown validation_report_id: {validation_report_id}",
                validation_report_id=validation_report_id,
            )
        status, can_write_clean, needs_manual_review, run_id = row
        run_id_str = None if run_id is None else str(run_id)
        if run_id_str and self._has_blocking_severe_conflicts(run_id_str, con):
            raise ValidationRejected(
                f"validation report {validation_report_id!r} blocked by open severe "
                f"source_conflict for run_id={run_id_str!r}",
                validation_report_id=validation_report_id,
            )
        self._enforce_report(
            validation_report_id,
            status=str(status),
            can_write_clean=bool(can_write_clean),
            needs_manual_review=bool(needs_manual_review),
            run_id=run_id_str,
            con=con,
        )
        return str(status)
