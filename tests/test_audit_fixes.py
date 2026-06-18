"""Regression tests for multi-dimension audit fixes."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import duckdb
import pytest
from backend.app.core.api_limits import clamp_agent_rows, clamp_page_size, load_api_limits
from backend.app.core.resource_guard import ResourceGuard
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.db.validation_gate import DbValidationGate
from backend.app.db.write_manager import WriteManager, WriteRequest
from backend.app.validators.data_quality import DataQualityRequest, DataQualityValidator


def _cm(tmp_path: Path) -> ConnectionManager:
    db = tmp_path / "audit.duckdb"
    cm = ConnectionManager(db, profile="eco")
    with cm.writer() as con:
        apply_migrations(con)
    return cm


def test_writeManager_defaultTransaction_withDbValidationGate_succeeds(tmp_path: Path) -> None:
    cm = _cm(tmp_path)
    with cm.writer() as con:
        con.execute(
            """
            CREATE TABLE stg_audit AS
            SELECT 'AAPL'::VARCHAR AS instrument_id, '2026-06-15'::VARCHAR AS trade_date,
                   100.0::DOUBLE AS close, 'qmt'::VARCHAR AS source_used,
                   'b1'::VARCHAR AS batch_id, 'qmt'::VARCHAR AS source_id
            """
        )
        con.execute(
            """
            CREATE TABLE clean_audit (
                instrument_id VARCHAR, trade_date VARCHAR, close DOUBLE,
                source_used VARCHAR, batch_id VARCHAR, source_id VARCHAR
            )
            """
        )
        quality = DataQualityValidator().validate_table(
            con,
            DataQualityRequest(
                run_id="run-audit",
                job_id="job-audit",
                data_domain="market_bar_1d",
                source_id="qmt_xtdata",
                staging_table="stg_audit",
                primary_keys=("instrument_id", "trade_date"),
                required_fields=("close", "source_used"),
                rule_set_id="p0_round_1",
            ),
            expected_columns=(
                "instrument_id",
                "trade_date",
                "close",
                "source_used",
                "batch_id",
                "source_id",
            ),
            timestamp_fields=("trade_date",),
        )
        result = WriteManager(cm, DbValidationGate(cm)).write(
            WriteRequest(
                run_id="run-audit",
                job_id="job-audit",
                target_table="clean_audit",
                staging_table="stg_audit",
                write_mode="append_only",
                primary_keys=("instrument_id", "trade_date"),
                validation_report_id=quality.validation_report_id,
                source_used="qmt_xtdata",
                data_domain="market_bar_1d",
            ),
            con=con,
            own_transaction=False,
        )
        clean_rows = con.execute("SELECT COUNT(*) FROM clean_audit").fetchone()[0]
        audit = con.execute(
            "SELECT source_role, data_domain, requested_by FROM write_audit_log"
        ).fetchone()

    assert result.status == "SUCCESS"
    assert clean_rows == 1
    assert audit == ("primary", "market_bar_1d", "system")


def test_writeManager_ownTransactionDefault_withDbValidationGate_succeeds(tmp_path: Path) -> None:
    cm = _cm(tmp_path)
    with cm.writer() as con:
        con.execute(
            """
            CREATE TABLE stg_audit_default AS
            SELECT 'MSFT'::VARCHAR AS instrument_id, '2026-06-16'::VARCHAR AS trade_date,
                   200.0::DOUBLE AS close, 'qmt'::VARCHAR AS source_used,
                   'b2'::VARCHAR AS batch_id, 'qmt'::VARCHAR AS source_id
            """
        )
        con.execute(
            """
            CREATE TABLE clean_audit_default (
                instrument_id VARCHAR, trade_date VARCHAR, close DOUBLE,
                source_used VARCHAR, batch_id VARCHAR, source_id VARCHAR
            )
            """
        )
        quality = DataQualityValidator().validate_table(
            con,
            DataQualityRequest(
                run_id="run-audit-default",
                job_id="job-audit-default",
                data_domain="market_bar_1d",
                source_id="qmt_xtdata",
                staging_table="stg_audit_default",
                primary_keys=("instrument_id", "trade_date"),
                required_fields=("close", "source_used"),
                rule_set_id="p0_round_1",
            ),
            expected_columns=(
                "instrument_id",
                "trade_date",
                "close",
                "source_used",
                "batch_id",
                "source_id",
            ),
            timestamp_fields=("trade_date",),
        )
        report_id = quality.validation_report_id

    result = WriteManager(cm, DbValidationGate(cm)).write(
        WriteRequest(
            run_id="run-audit-default",
            job_id="job-audit-default",
            target_table="clean_audit_default",
            staging_table="stg_audit_default",
            write_mode="append_only",
            primary_keys=("instrument_id", "trade_date"),
            validation_report_id=report_id,
            source_used="qmt_xtdata",
            data_domain="market_bar_1d",
        )
    )
    with cm.reader() as con:
        clean_rows = con.execute("SELECT COUNT(*) FROM clean_audit_default").fetchone()[0]
    assert result.status == "SUCCESS"
    assert clean_rows == 1


def test_syncJob_invalidStatus_rejectedByDbCheck(tmp_path: Path) -> None:
    cm = _cm(tmp_path)
    with cm.writer() as con, pytest.raises(duckdb.ConstraintException):
        con.execute("INSERT INTO data_sync_job (job_id, status) VALUES ('bad-job', 'BROKEN')")


def test_apiLimits_enforcesMaxPageSize() -> None:
    limits = load_api_limits()
    assert limits["max_page_size"] == 500
    assert clamp_page_size(999) == 500
    assert clamp_page_size(0) == limits["default_page_size"]
    rows, truncated = clamp_agent_rows(999)
    assert rows == 500
    assert truncated is True


def test_resourceGuard_reusesSnapshotWithinTtl(tmp_path: Path) -> None:
    guard = ResourceGuard()
    first = guard.snapshot(force_refresh=True)
    with patch.object(guard, "_compute_snapshot", wraps=guard._compute_snapshot) as compute:
        second = guard.snapshot()
        third = guard.snapshot(force_refresh=True)
    assert second is first
    assert third is not first
    assert compute.call_count == 1


def test_connection_lowMemoryForcesEcoThreads(tmp_path: Path, monkeypatch) -> None:
    db = tmp_path / "lowmem.duckdb"
    with duckdb.connect(str(db)) as con:
        apply_migrations(con)

    class _Mem:
        total = 6 * 1024 * 1024 * 1024
        available = 2 * 1024 * 1024 * 1024

    monkeypatch.setattr("backend.app.db.connection.psutil.virtual_memory", lambda: _Mem())
    cm = ConnectionManager(
        db,
        profile="eco",
        limits={"eco": {"duckdb_memory_max_mb": 1536, "max_threads": 2, "duckdb_temp_max_gb": 2}},
    )
    with cm.reader() as r:
        threads = int(r.execute("SELECT current_setting('threads')").fetchone()[0])
        mem = r.execute("SELECT current_setting('memory_limit')").fetchone()[0]
    assert threads == 1
    assert "732" in mem or "768" in mem or "767" in mem


def test_resourceGuard_largeCacheDir_completesWithinReasonableTime(tmp_path: Path) -> None:
    import time

    cache = tmp_path / "data" / "cache" / "many_files"
    cache.mkdir(parents=True)
    for i in range(500):
        (cache / f"f{i}.bin").write_bytes(b"x" * 64)

    import backend.app.core.resource_guard as rg_mod

    original = rg_mod.DATA_ROOT
    rg_mod.DATA_ROOT = tmp_path / "data"
    try:
        guard = ResourceGuard()
        start = time.perf_counter()
        decision, _ = guard.check()
        elapsed = time.perf_counter() - start
    finally:
        rg_mod.DATA_ROOT = original

    assert decision.value in {"OK", "WARN", "PAUSE", "HARD_STOP"}
    assert elapsed < 5.0
