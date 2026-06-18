"""Tests for DbValidationGate (Batch C §8.2).

DbValidationGate reads the persisted validation_report row and decides whether
WriteManager may proceed. It must NOT be a stub: decisions come from real DB state.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.db.validation_gate import (
    DbValidationGate,
    ValidationGateError,
    ValidationRejected,
)


def _setup(tmp_path: Path) -> ConnectionManager:
    db = tmp_path / "gate.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    return cm


def _insert_report(
    cm: ConnectionManager,
    report_id: str,
    *,
    status: str,
    can_write_clean: bool,
    needs_manual_review: bool,
    checked_rows: int = 1,
    failed_rows: int = 0,
    warning_rows: int = 0,
    run_id: str = "r1",
) -> None:
    with cm.writer() as con:
        con.execute(
            """
            INSERT INTO validation_report (
                validation_report_id, run_id, data_domain, source_id,
                status, checked_rows, failed_rows, warning_rows,
                can_write_clean, needs_manual_review
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                report_id,
                run_id,
                "market_bar_1d",
                "qmt",
                status,
                checked_rows,
                failed_rows,
                warning_rows,
                can_write_clean,
                needs_manual_review,
            ],
        )


def test_missingReport_raisesGateError(tmp_path: Path) -> None:
    cm = _setup(tmp_path)
    gate = DbValidationGate(cm)
    with pytest.raises(ValidationGateError) as exc:
        gate.assert_can_write("does-not-exist", "append_only")
    assert exc.value.validation_report_id == "does-not-exist"


def test_failedReport_rejected(tmp_path: Path) -> None:
    cm = _setup(tmp_path)
    _insert_report(
        cm,
        "vr-failed",
        status="FAILED",
        can_write_clean=False,
        needs_manual_review=True,
        failed_rows=1,
    )
    gate = DbValidationGate(cm)
    with pytest.raises(ValidationRejected) as exc:
        gate.assert_can_write("vr-failed", "append_only")
    assert exc.value.validation_report_id == "vr-failed"


def test_canWriteCleanFalse_rejected(tmp_path: Path) -> None:
    """Even a non-FAILED report with can_write_clean=false must reject."""
    cm = _setup(tmp_path)
    _insert_report(
        cm,
        "vr-no-write",
        status="WARNING",
        can_write_clean=False,
        needs_manual_review=False,
    )
    gate = DbValidationGate(cm)
    with pytest.raises(ValidationRejected):
        gate.assert_can_write("vr-no-write", "append_only")


def test_needsManualReviewTrue_rejected(tmp_path: Path) -> None:
    """needs_manual_review=true must reject regardless of status."""
    cm = _setup(tmp_path)
    _insert_report(
        cm,
        "vr-review",
        status="WARNING",
        can_write_clean=True,
        needs_manual_review=True,
    )
    gate = DbValidationGate(cm)
    with pytest.raises(ValidationRejected):
        gate.assert_can_write("vr-review", "append_only")


def test_passedReport_canWriteCleanTrue_allows(tmp_path: Path) -> None:
    cm = _setup(tmp_path)
    _insert_report(
        cm,
        "vr-pass",
        status="PASSED",
        can_write_clean=True,
        needs_manual_review=False,
    )
    gate = DbValidationGate(cm)
    status = gate.assert_can_write("vr-pass", "append_only")
    assert status == "PASSED"


def test_warningReport_canWriteTrue_noReview_allows(tmp_path: Path) -> None:
    """Explicit WARNING policy: allow only if can_write_clean=true AND no review."""
    cm = _setup(tmp_path)
    _insert_report(
        cm,
        "vr-warn-ok",
        status="WARNING",
        can_write_clean=True,
        needs_manual_review=False,
        warning_rows=2,
    )
    gate = DbValidationGate(cm)
    status = gate.assert_can_write("vr-warn-ok", "upsert_by_pk")
    assert status == "WARNING"


def test_openSevereConflict_rejectsEvenWhenReportPassed(tmp_path: Path) -> None:
    cm = _setup(tmp_path)
    _insert_report(
        cm,
        "vr-conflict",
        status="PASSED",
        can_write_clean=True,
        needs_manual_review=False,
        run_id="run-blocked",
    )
    with cm.writer() as con:
        con.execute(
            """
            INSERT INTO source_conflict (
                conflict_id, run_id, job_id, data_domain, field_name,
                primary_source, competing_source, severity, reconcile_status,
                manual_review_required
            ) VALUES (
                'c1', 'run-blocked', 'j1', 'market_bar_1d', 'close',
                'qmt', 'baostock', 'severe', 'OPEN', false
            )
            """
        )
    gate = DbValidationGate(cm)
    with pytest.raises(ValidationRejected, match="severe"):
        gate.assert_can_write("vr-conflict", "append_only")


def test_warningReport_canWriteFalse_rejected(tmp_path: Path) -> None:
    cm = _setup(tmp_path)
    _insert_report(
        cm,
        "vr-warn-no",
        status="WARNING",
        can_write_clean=False,
        needs_manual_review=False,
    )
    gate = DbValidationGate(cm)
    with pytest.raises(ValidationRejected):
        gate.assert_can_write("vr-warn-no", "append_only")


def test_dbValidationGate_isNotStubBehavior(tmp_path: Path) -> None:
    """Production gate must query DB; stub-pass/stub-fail prefixes must not short-circuit."""
    cm = _setup(tmp_path)
    gate = DbValidationGate(cm)
    # stub-style ids that StubValidationGate would pass must be unknown to DbValidationGate.
    with pytest.raises(ValidationGateError):
        gate.assert_can_write("stub-pass-1", "append_only")
    _insert_report(
        cm,
        "stub-pass-1",
        status="PASSED",
        can_write_clean=True,
        needs_manual_review=False,
    )
    # Now that a real row exists, the same id must be allowed.
    gate.assert_can_write("stub-pass-1", "append_only")


def test_dbValidationGate_writeManagerIntegration_rejectsFailed(tmp_path: Path) -> None:
    """WriteManager injected with DbValidationGate must honor DB state."""
    from backend.app.db.write_manager import WriteManager, WriteRequest

    cm = _setup(tmp_path)
    with cm.writer() as con:
        con.execute("CREATE TABLE target_clean AS SELECT * FROM stg_foundation_smoke WHERE 1=0")
        con.execute(
            "INSERT INTO stg_foundation_smoke VALUES ('AAPL','2026-06-15',195.0,'qmt','b1')"
        )
    _insert_report(
        cm,
        "vr-fail-2",
        status="FAILED",
        can_write_clean=False,
        needs_manual_review=True,
        failed_rows=1,
    )
    wm = WriteManager(cm, DbValidationGate(cm))
    req = WriteRequest(
        run_id="r1",
        job_id="j1",
        target_table="target_clean",
        staging_table="stg_foundation_smoke",
        write_mode="append_only",
        primary_keys=("instrument_id", "trade_date"),
        validation_report_id="vr-fail-2",
        source_used="qmt",
    )
    res = wm.write(req)
    assert res.status == "FAILED"
    with cm.reader() as r:
        assert r.execute("SELECT COUNT(*) FROM target_clean").fetchone()[0] == 0
