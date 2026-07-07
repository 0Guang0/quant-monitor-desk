"""M-G1-03 P1-06′ — BindingSyncExecutor 唯一编排深度模块."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.sync.binding_executor import execute_binding
from backend.app.sync.indicator_binding import load_binding
from backend.app.sync.jobs import SyncJobResult
from tests.fred_macro_incremental_support import insert_axis_observation


def _cm(tmp_path: Path) -> ConnectionManager:
    cm = ConnectionManager(db_path=tmp_path / "exec.duckdb")
    with cm.writer() as con:
        apply_migrations(con)
    return cm


def test_bindingSyncExecutor_executeBinding_onlyOrchestrationPath(tmp_path) -> None:
    """覆盖范围：binding → SyncJobSpec → orchestrator 唯一路径
    测试对象：backend.app.sync.binding_executor.execute_binding
    目的/目标：删除 executor 则编排散落 ops+facade+scheduler（删除测试须失败）
    验证点：execute_binding 覆盖 watermark+mapper+orchestrator 序列
    失败含义：三处复制编排，与 AD-MG103-10 冲突
    """
    binding = load_binding("ENV-E1-DGS10")
    cm = _cm(tmp_path)
    with cm.writer() as con:
        insert_axis_observation(
            con,
            observation_id="obs-env-dgs10",
            indicator_id="ENV-E1-DGS10",
            obs_date=date(2026, 6, 10),
        )

    dry = execute_binding(binding, "incremental", dry_run=True, connection_manager=cm)
    assert dry.status == "SKIPPED"
    assert "2026-06-10" in (dry.message or "")
    assert "2026-06-11" in (dry.message or "")

    expected = SyncJobResult(job_id="job-mock", status="COMPLETED")

    class ProbeOrchestrator:
        def __init__(self) -> None:
            self.spec = None
            self.datasource_service = None

        def run_incremental(self, spec, *, datasource_service=None, **_kwargs):
            self.spec = spec
            self.datasource_service = datasource_service
            return expected

    orch = ProbeOrchestrator()
    datasource_service = object()

    live = execute_binding(
        binding,
        "incremental",
        dry_run=False,
        connection_manager=cm,
        orchestrator=orch,
        datasource_service=datasource_service,
    )
    assert live is expected
    assert orch.datasource_service is datasource_service
    assert orch.spec.instrument_id == "ENV-E1-DGS10"
    assert orch.spec.data_domain == "macro_series"
