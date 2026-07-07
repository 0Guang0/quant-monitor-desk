"""B3F-SH quality runners — R3F-SH-02 / SH-03."""

from __future__ import annotations

from datetime import date

import pytest
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.sync.jobs import SyncJobSpec
from backend.app.sync.orchestrator import DataSyncOrchestrator


def _reserved_job_spec(job_type: str, *, job_id: str = "job-b3f-reserved") -> SyncJobSpec:
    return SyncJobSpec(
        run_id="run-b3f-reserved",
        job_id=job_id,
        job_type=job_type,
        data_domain="macro_series",
        market_id="GLOBAL",
        source_id="fred",
        adapter_id=None,
        date_start=None,
        date_end=None,
        instrument_id=None,
        partition_key=None,
        trigger_reason=None,
    )


def _orchestrator(tmp_path) -> DataSyncOrchestrator:
    db = tmp_path / "b3f-quality.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    return DataSyncOrchestrator(cm)


def test_b3fQualityRunners_revisionAudit_notDeferred(tmp_path) -> None:
    """覆盖范围：revision_audit job 非 defer 完成路径
    测试对象：DataSyncOrchestrator.run_revision_audit
    目的/目标：R3F-SH-02 — revision audit runner 闭包
    验证点：SyncJobResult.status == COMPLETED
    失败含义：job 仍 defer，Batch6 无法跑 revision audit
    """
    from datetime import date

    from tests.fred_macro_incremental_support import insert_axis_observation

    orch = _orchestrator(tmp_path)
    with orch._cm.writer() as con:
        insert_axis_observation(
            con,
            observation_id="obs-rev-b3f",
            indicator_id="DGS10",
            obs_date=date(2026, 6, 10),
        )
    result = orch.run_revision_audit(
        SyncJobSpec(
            run_id="run-b3f-reserved",
            job_id="job-rev-audit",
            job_type="revision_audit",
            data_domain="macro_series",
            market_id="GLOBAL",
            source_id="fred",
            adapter_id=None,
            date_start=None,
            date_end=None,
            instrument_id="DGS10",
            partition_key=None,
            trigger_reason=None,
        )
    )
    assert result.status == "COMPLETED"
    assert result.message == "revision audit complete"
    with orch._cm.reader() as con:
        events = con.execute(
            "SELECT event_type, message FROM job_event_log WHERE job_id = ? ORDER BY created_at",
            ["job-rev-audit"],
        ).fetchall()
    assert len(events) >= 2
    assert any("revision audit" in (msg or "").lower() for _, msg in events)


def test_b3fQualityRunners_dataQuality_notDeferred(tmp_path) -> None:
    """覆盖范围：data_quality job 非 defer 完成路径
    测试对象：DataSyncOrchestrator.run_data_quality
    目的/目标：R3F-SH-03 — data quality runner 闭包
    验证点：SyncJobResult.status == COMPLETED
    失败含义：job 仍 defer，Batch6 无法跑 data quality
    """
    orch = _orchestrator(tmp_path)
    with orch._cm.writer() as con:
        con.execute(
            """
            INSERT INTO security_bar_1d (
                instrument_id, trade_date, adjustment_type, close, source_used, batch_id
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            ["000001", "2026-01-15", "none", 10.0, "baostock", "b1"],
        )
    result = orch.run_data_quality(
        SyncJobSpec(
            run_id="run-b3f-reserved",
            job_id="job-dq",
            job_type="data_quality",
            data_domain="market_bar_1d",
            market_id="CN_A",
            source_id="baostock",
            adapter_id=None,
            date_start=None,
            date_end=None,
            instrument_id="000001",
            partition_key=None,
            trigger_reason=None,
        )
    )
    assert result.status == "COMPLETED"
    assert result.message == "data quality complete"
    with orch._cm.reader() as con:
        events = con.execute(
            "SELECT event_type, message FROM job_event_log WHERE job_id = ? ORDER BY created_at",
            ["job-dq"],
        ).fetchall()
    assert len(events) >= 2
    assert any("data quality" in (msg or "").lower() for _, msg in events)


def test_b3fQualityRunners_fullLoad_notDeferred(tmp_path, monkeypatch) -> None:
    """覆盖范围：full_load job 非 defer 完成路径（M-G1-03 S03）
    测试对象：DataSyncOrchestrator.run_full_load
    目的/目标：FullLoad runner 与 dq/ra 同为可调度 job
    验证点：SyncJobResult.status == COMPLETED
    失败含义：full_load 仍 defer，Batch6 FullLoad 矩阵未闭包
    """
    from backend.app.core.resource_guard import Decision, ResourceGuard
    from tests.support.sync_adapters import FullLoadCountAdapter

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    orch = _orchestrator(tmp_path)
    spec = SyncJobSpec(
        run_id="run-b3f-fl",
        job_id="job-fl",
        job_type="full_load",
        data_domain="market_bar_1d",
        market_id="CN_A",
        source_id="baostock",
        adapter_id=None,
        date_start=date(2026, 1, 1),
        date_end=date(2026, 1, 15),
        instrument_id=None,
        partition_key=None,
        trigger_reason="cold_start",
    )
    results = orch.run_full_load(
        spec,
        adapter=FullLoadCountAdapter(),
        clean_table=FullLoadCountAdapter.CLEAN,
    )
    assert results[-1].status == "COMPLETED"
