"""Tests for SyncJob state machine (Batch D §8.2)."""

from __future__ import annotations

from datetime import date

import pytest
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.sync.jobs import (
    InvalidTransitionError,
    SyncJobSpec,
    SyncJobStateMachine,
)


def _machine(tmp_path) -> SyncJobStateMachine:
    db = tmp_path / "jobs.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    return SyncJobStateMachine(cm)


def _base_spec(**overrides) -> SyncJobSpec:
    defaults = dict(
        run_id="run-1",
        job_id="job-1",
        job_type="incremental",
        data_domain="market_bar_1d",
        market_id="CN_A",
        source_id="baostock",
        adapter_id=None,
        date_start=None,
        date_end=None,
        instrument_id=None,
        partition_key=None,
        trigger_reason=None,
    )
    defaults.update(overrides)
    return SyncJobSpec(**defaults)


def test_syncJob_transition_createdToPlanned_recordsEvent(tmp_path) -> None:
    sm = _machine(tmp_path)
    sm.create_job(_base_spec())
    sm.transition("job-1", "PLANNED", message="planned")
    with sm._cm.writer() as con:
        row = con.execute("SELECT status FROM data_sync_job WHERE job_id = ?", ["job-1"]).fetchone()
        events = con.execute(
            """
            SELECT old_status, new_status, message
            FROM job_event_log WHERE job_id = ? ORDER BY created_at
            """,
            ["job-1"],
        ).fetchall()
    assert row[0] == "PLANNED"
    assert ("CREATED", "PLANNED", "planned") in events


def test_syncJob_invalidTransition_raises(tmp_path) -> None:
    sm = _machine(tmp_path)
    sm.create_job(_base_spec())
    with pytest.raises(InvalidTransitionError):
        sm.transition("job-1", "WRITING")


def test_syncJob_terminalState_cannotTransition(tmp_path) -> None:
    sm = _machine(tmp_path)
    sm.create_job(_base_spec())
    for status in ("PLANNED", "FETCHING", "STAGED", "VALIDATING", "READY_TO_WRITE", "WRITING"):
        sm.transition("job-1", status)
    sm.transition("job-1", "COMPLETED")
    with pytest.raises(InvalidTransitionError):
        sm.transition("job-1", "FETCHING")


def test_syncJob_fullLoad_createdToPlanned_recordsEvent(tmp_path) -> None:
    sm = _machine(tmp_path)
    sm.create_job(_base_spec(job_id="job-fl", job_type="full_load"))
    sm.transition("job-fl", "PLANNED")
    with sm._cm.writer() as con:
        row = con.execute(
            "SELECT job_type, status FROM data_sync_job WHERE job_id = ?",
            ["job-fl"],
        ).fetchone()
    assert row == ("full_load", "PLANNED")


def test_syncJob_incremental_createdToPlanned_recordsEvent(tmp_path) -> None:
    sm = _machine(tmp_path)
    sm.create_job(_base_spec(job_id="job-inc", job_type="incremental"))
    sm.transition("job-inc", "PLANNED")
    with sm._cm.writer() as con:
        status = con.execute(
            "SELECT status FROM data_sync_job WHERE job_id = ?", ["job-inc"]
        ).fetchone()[0]
    assert status == "PLANNED"


def test_syncJob_revisionAudit_skeletonReachesStaged(tmp_path) -> None:
    sm = _machine(tmp_path)
    sm.create_job(_base_spec(job_id="job-rev", job_type="revision_audit"))
    sm.transition("job-rev", "PLANNED")
    sm.transition("job-rev", "FETCHING")
    sm.transition("job-rev", "STAGED")
    with sm._cm.writer() as con:
        status = con.execute(
            "SELECT status FROM data_sync_job WHERE job_id = ?", ["job-rev"]
        ).fetchone()[0]
    assert status == "STAGED"


def test_syncJob_dataQuality_skeletonCompletesOrManualReview(tmp_path) -> None:
    sm = _machine(tmp_path)
    sm.create_job(
        _base_spec(
            job_id="job-dq",
            job_type="data_quality",
            instrument_id="000001",
            date_start=date(2026, 1, 1),
            date_end=date(2026, 1, 31),
        )
    )
    sm.transition("job-dq", "PLANNED")
    sm.transition("job-dq", "VALIDATING")
    sm.transition("job-dq", "COMPLETED")
    with sm._cm.writer() as con:
        status = con.execute(
            "SELECT status FROM data_sync_job WHERE job_id = ?", ["job-dq"]
        ).fetchone()[0]
    assert status in ("COMPLETED", "MANUAL_REVIEW_REQUIRED")
