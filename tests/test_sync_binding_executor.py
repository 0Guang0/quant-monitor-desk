"""M-G1-03 P1-06′ — BindingSyncExecutor 唯一编排深度模块."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.sync import binding_executor as be
from backend.app.sync.binding_executor import execute_binding
from backend.app.sync.indicator_binding import load_binding
from backend.app.sync.jobs import SyncJobResult
from backend.app.sync.orchestrator import DataSyncOrchestrator
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

    orch = DataSyncOrchestrator(cm)
    mock_service = MagicMock()
    expected = SyncJobResult(job_id="job-mock", status="COMPLETED")
    orch.run_incremental = MagicMock(return_value=expected)  # type: ignore[method-assign]

    live = execute_binding(
        binding,
        "incremental",
        dry_run=False,
        orchestrator=orch,
        datasource_service=mock_service,
    )
    assert live is expected
    orch.run_incremental.assert_called_once()
    call_kwargs = orch.run_incremental.call_args
    assert call_kwargs.kwargs["datasource_service"] is mock_service
    assert call_kwargs.args[0].instrument_id == "ENV-E1-DGS10"
    assert call_kwargs.args[0].data_domain == "macro_series"


def test_bindingSyncExecutor_deletionTest_orchestrationNotInOps() -> None:
    """覆盖范围：删除测试 — 编排集中度
    测试对象：binding_executor vs ops/*_incremental_run
    目的/目标：禁止 facade/ops 内联 duplicate 编排
    验证点：mock 删除 executor 后 ops 路径无法完成 sync
    失败含义：浅层 pass-through 膨胀
    """
    repo = Path(__file__).resolve().parents[1]
    executor_src = (repo / "backend/app/sync/binding_executor.py").read_text(encoding="utf-8")
    assert "def execute_binding" in executor_src
    assert "read_watermark" in executor_src
    assert "run_incremental" in executor_src

    facade = repo / "backend/app/sync/layer1_sync_facade.py"
    if facade.is_file():
        assert "run_incremental" not in facade.read_text(encoding="utf-8")

    binding = load_binding("ENV-E1-DGS10")
    saved = be.execute_binding
    try:
        del be.execute_binding
        with pytest.raises(AttributeError):
            be.execute_binding(binding, "incremental", dry_run=True)
    finally:
        be.execute_binding = saved


def test_fredIncrementalRun_delegatesToExecuteBinding_notInlineOrchestration() -> None:
    """覆盖范围：fred ops 薄绑定 — 无内联 orchestration
    测试对象：backend.app.ops.fred_incremental_run 模块源码
    目的/目标：run_fred_macro_incremental 经 execute_binding，禁止 orch.run_incremental
    验证点：含 execute_binding；不含 orch.run_incremental / run_incremental(
    失败含义：ops 仍复制编排，P1-11 LOC 未下降
    """
    import inspect

    from backend.app.ops import fred_incremental_run as fred_mod

    source = inspect.getsource(fred_mod)
    assert "execute_binding" in source
    assert "orch.run_incremental" not in source
    assert "run_incremental(" not in source
    assert len(source.splitlines()) < 310
