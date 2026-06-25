"""B3F-SH quality runners — R3F-SH-02 / SH-03."""

from __future__ import annotations

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
    orch = _orchestrator(tmp_path)
    result = orch.run_revision_audit(_reserved_job_spec("revision_audit", job_id="job-rev-audit"))
    assert result.status == "COMPLETED"


def test_b3fQualityRunners_dataQuality_notDeferred(tmp_path) -> None:
    """覆盖范围：data_quality job 非 defer 完成路径
    测试对象：DataSyncOrchestrator.run_data_quality
    目的/目标：R3F-SH-03 — data quality runner 闭包
    验证点：SyncJobResult.status == COMPLETED
    失败含义：job 仍 defer，Batch6 无法跑 data quality
    """
    orch = _orchestrator(tmp_path)
    result = orch.run_data_quality(_reserved_job_spec("data_quality", job_id="job-dq"))
    assert result.status == "COMPLETED"
