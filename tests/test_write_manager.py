"""WriteManager tests (Round 1 task 008)."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.db.validation_gate import (
    StubValidationGate,
    ValidationGateError,
    ValidationRejected,
)
from backend.app.db.write_manager import WriteManager, WriteRequest


def _setup(tmp_path: Path) -> ConnectionManager:
    db = tmp_path / "t.duckdb"
    con = duckdb.connect(str(db))
    apply_migrations(con)
    con.execute(
        "INSERT INTO stg_foundation_smoke VALUES ('AAPL','2026-06-15',195.0,'qmt','b1')"
    )
    con.close()
    return ConnectionManager(db)


def _req(mode: str = "append_only", report: str = "stub-pass-1") -> WriteRequest:
    return WriteRequest(
        run_id="r1",
        job_id="j1",
        target_table="security_bar_smoke_clean",
        staging_table="stg_foundation_smoke",
        write_mode=mode,
        primary_keys=("instrument_id", "trade_date"),
        validation_report_id=report,
        source_used="qmt",
    )


def test_assertCanWrite_stubPass_allowsWhileStubFailRejects() -> None:
    gate = StubValidationGate()
    gate.assert_can_write("stub-pass-001", "append_only")
    with pytest.raises(ValidationRejected):
        gate.assert_can_write("stub-fail-001", "append_only")


def test_assertCanWrite_unknownId_raisesGateError() -> None:
    with pytest.raises(ValidationGateError):
        StubValidationGate().assert_can_write("real-123", "append_only")


def test_write_invalidIdentifier_raisesBeforeWrite(tmp_path: Path) -> None:
    cm = _setup(tmp_path)
    bad = WriteRequest(
        run_id="r1",
        job_id="j1",
        target_table="file_registry; DROP TABLE write_audit_log; --",
        staging_table="stg_foundation_smoke",
        write_mode="append_only",
        primary_keys=("instrument_id", "trade_date"),
        validation_report_id="stub-pass-1",
        source_used="qmt",
    )
    with pytest.raises(ValueError, match="invalid SQL identifier"):
        WriteManager(cm).write(bad)


def test_write_appendOnlyStubPass_insertsAndAudits(tmp_path: Path) -> None:
    cm = _setup(tmp_path)
    with cm.writer() as w:
        w.execute(
            "CREATE TABLE security_bar_smoke_clean AS "
            "SELECT * FROM stg_foundation_smoke WHERE 1=0"
        )
    res = WriteManager(cm).write(_req())
    assert res.status == "SUCCESS"
    assert res.rows_inserted == 1
    with cm.reader() as r:
        assert r.execute("SELECT COUNT(*) FROM security_bar_smoke_clean").fetchone()[0] == 1
        audit = r.execute(
            "SELECT status, rows_inserted, rows_in_staging FROM write_audit_log WHERE write_id=?",
            [res.write_id],
        ).fetchone()
    assert audit == ("SUCCESS", 1, 1)


def test_write_stubFail_rollsBackAndAuditsFailed(tmp_path: Path) -> None:
    cm = _setup(tmp_path)
    with cm.writer() as w:
        w.execute(
            "CREATE TABLE security_bar_smoke_clean AS "
            "SELECT * FROM stg_foundation_smoke WHERE 1=0"
        )
    res = WriteManager(cm).write(_req(report="stub-fail-1"))
    assert res.status == "FAILED"
    with cm.reader() as r:
        assert r.execute("SELECT COUNT(*) FROM security_bar_smoke_clean").fetchone()[0] == 0
        cnt = r.execute(
            "SELECT COUNT(*) FROM write_audit_log WHERE status='FAILED'"
        ).fetchone()[0]
        assert cnt == 1


def test_write_gateError_rollsBackAndAuditsFailed(tmp_path: Path) -> None:
    cm = _setup(tmp_path)
    with cm.writer() as w:
        w.execute(
            "CREATE TABLE security_bar_smoke_clean AS "
            "SELECT * FROM stg_foundation_smoke WHERE 1=0"
        )
    res = WriteManager(cm).write(_req(report="real-report-1"))
    assert res.status == "FAILED"
    assert res.error_message
    with cm.reader() as r:
        assert r.execute("SELECT COUNT(*) FROM security_bar_smoke_clean").fetchone()[0] == 0
        audit = r.execute(
            "SELECT validation_status FROM write_audit_log WHERE write_id=?",
            [res.write_id],
        ).fetchone()[0]
        assert audit == "FAILED"


def test_write_sqlError_rollsBackAndAuditsError(tmp_path: Path) -> None:
    cm = _setup(tmp_path)
    res = WriteManager(cm).write(_req())
    assert res.status == "FAILED"
    assert res.error_message
    with cm.reader() as r:
        audit = r.execute(
            "SELECT validation_status, status FROM write_audit_log WHERE write_id=?",
            [res.write_id],
        ).fetchone()
        assert audit == ("ERROR", "FAILED")


def test_write_emptyStaging_insertsZeroRows(tmp_path: Path) -> None:
    cm = _setup(tmp_path)
    with cm.writer() as w:
        w.execute("DELETE FROM stg_foundation_smoke")
        w.execute(
            "CREATE TABLE security_bar_smoke_clean AS "
            "SELECT * FROM stg_foundation_smoke WHERE 1=0"
        )
    res = WriteManager(cm).write(_req())
    assert res.status == "SUCCESS"
    assert res.rows_inserted == 0
    with cm.reader() as r:
        assert r.execute("SELECT COUNT(*) FROM security_bar_smoke_clean").fetchone()[0] == 0


def test_write_unsupportedMode_raises(tmp_path: Path) -> None:
    cm = _setup(tmp_path)
    with pytest.raises(ValueError):
        WriteManager(cm).write(_req(mode="replace_partition"))


def test_write_upsertByPk_replacesExistingRow(tmp_path: Path) -> None:
    cm = _setup(tmp_path)
    with cm.writer() as w:
        w.execute("CREATE TABLE security_bar_smoke_clean AS SELECT * FROM stg_foundation_smoke")
        w.execute("UPDATE stg_foundation_smoke SET close=200.0")
    res = WriteManager(cm).write(_req(mode="upsert_by_pk"))
    assert res.status == "SUCCESS"
    assert res.rows_updated == 1
    assert res.rows_inserted == 0
    with cm.reader() as r:
        close = r.execute(
            "SELECT close FROM security_bar_smoke_clean WHERE instrument_id='AAPL'"
        ).fetchone()[0]
        assert close == 200.0
        assert r.execute("SELECT COUNT(*) FROM security_bar_smoke_clean").fetchone()[0] == 1
        audit = r.execute(
            "SELECT rows_updated, rows_inserted FROM write_audit_log WHERE write_id=?",
            [res.write_id],
        ).fetchone()
        assert audit == (1, 0)


def test_write_upsertByPk_pureNewRow_reportsZeroUpdated(tmp_path: Path) -> None:
    cm = _setup(tmp_path)
    with cm.writer() as w:
        w.execute(
            "CREATE TABLE security_bar_smoke_clean AS "
            "SELECT * FROM stg_foundation_smoke WHERE 1=0"
        )
        w.execute(
            "INSERT INTO security_bar_smoke_clean "
            "VALUES ('MSFT','2026-06-14',100.0,'qmt','b0')"
        )
        w.execute(
            "INSERT INTO security_bar_smoke_clean "
            "VALUES ('GOOG','2026-06-13',200.0,'qmt','b0')"
        )
        w.execute("DELETE FROM stg_foundation_smoke")
        w.execute(
            "INSERT INTO stg_foundation_smoke VALUES ('NVDA','2026-06-16',300.0,'qmt','b2')"
        )
    res = WriteManager(cm).write(_req(mode="upsert_by_pk"))
    assert res.status == "SUCCESS"
    assert res.rows_updated == 0
    assert res.rows_inserted == 1
    with cm.reader() as r:
        assert r.execute("SELECT COUNT(*) FROM security_bar_smoke_clean").fetchone()[0] == 3
        audit = r.execute(
            "SELECT rows_updated, rows_inserted FROM write_audit_log WHERE write_id=?",
            [res.write_id],
        ).fetchone()
        assert audit == (0, 1)


def test_write_upsertByPk_mixedNewAndExisting_reportsCorrectCounts(tmp_path: Path) -> None:
    cm = _setup(tmp_path)
    with cm.writer() as w:
        w.execute("CREATE TABLE security_bar_smoke_clean AS SELECT * FROM stg_foundation_smoke")
        w.execute(
            "INSERT INTO stg_foundation_smoke VALUES ('MSFT','2026-06-15',120.0,'qmt','b2')"
        )
        w.execute("UPDATE stg_foundation_smoke SET close=200.0 WHERE instrument_id='AAPL'")
    res = WriteManager(cm).write(_req(mode="upsert_by_pk"))
    assert res.status == "SUCCESS"
    assert res.rows_updated == 1
    assert res.rows_inserted == 1
    with cm.reader() as r:
        assert r.execute("SELECT COUNT(*) FROM security_bar_smoke_clean").fetchone()[0] == 2
        aapl_close = r.execute(
            "SELECT close FROM security_bar_smoke_clean WHERE instrument_id='AAPL'"
        ).fetchone()[0]
        assert aapl_close == 200.0


def test_write_ownTransactionFalse_stubFail_doesNotRollbackOuterTxn(tmp_path: Path) -> None:
    cm = _setup(tmp_path)
    with cm.writer() as w:
        w.execute(
            "CREATE TABLE security_bar_smoke_clean AS "
            "SELECT * FROM stg_foundation_smoke WHERE 1=0"
        )
        w.execute("BEGIN")
        w.execute("INSERT INTO stg_foundation_smoke VALUES ('MSFT','2026-06-16',120.0,'qmt','b2')")
        res = WriteManager(cm).write(_req(report="stub-fail-1"), con=w, own_transaction=False)
        assert res.status == "FAILED"
        audit_cnt = w.execute(
            "SELECT COUNT(*) FROM write_audit_log WHERE status='FAILED'"
        ).fetchone()[0]
        assert audit_cnt == 1
        # Outer transaction still active: staging insert from above remains visible.
        cnt = w.execute("SELECT COUNT(*) FROM stg_foundation_smoke").fetchone()[0]
        assert cnt == 2
        w.execute("ROLLBACK")


def test_assertCanWrite_unknownId_exposesReportId() -> None:
    with pytest.raises(ValidationGateError) as exc_info:
        StubValidationGate().assert_can_write("real-123", "append_only")
    assert exc_info.value.validation_report_id == "real-123"


def test_assertCanWrite_stubFail_exposesReportId() -> None:
    with pytest.raises(ValidationRejected) as exc_info:
        StubValidationGate().assert_can_write("stub-fail-001", "append_only")
    assert exc_info.value.validation_report_id == "stub-fail-001"
