"""Sync job runner wiring tests (B3F-BR / playbook §8.5).

覆盖范围：runner 类与 orchestrator 接线、backfill 分片规划。
"""

from __future__ import annotations

from datetime import date

from backend.app.sync.jobs import ECO_MAX_BACKFILL_DAYS_PER_TASK, plan_backfill_shards
from backend.app.sync.orchestrator import DataSyncOrchestrator
from backend.app.sync.runners import (
    BackfillShardRunner,
    IncrementalJobRunner,
    ReconcileJobRunner,
)


def test_syncRunners_backfillShardPlanner_respectsEcoMaxDays() -> None:
    """覆盖范围：backfill 分片规划上限
    测试对象：plan_backfill_shards
    目的/目标：回补任务按 ECO_MAX_BACKFILL_DAYS_PER_TASK 切分，避免单片过大
    验证点：每片天数 ≤ ECO_MAX_BACKFILL_DAYS_PER_TASK；跨度 200 天至少 3 片
    失败含义：分片失控会导致单任务超时或资源门禁误触发
    """
    start = date(2026, 1, 1)
    end = date(2026, 7, 19)
    shards = plan_backfill_shards(start, end)
    assert len(shards) >= 3
    for _task_id, shard_start, shard_end in shards:
        assert (shard_end - shard_start).days + 1 <= ECO_MAX_BACKFILL_DAYS_PER_TASK


def test_syncRunners_orchestratorWiresRunnerAttributes(tmp_path) -> None:
    """覆盖范围：orchestrator 内部 runner 实例接线
    测试对象：DataSyncOrchestrator.__init__
    目的/目标：三类已实现 job 的 runner 在编排器内可访问
    验证点：_incremental/_backfill/_reconcile 分别为 Incremental/Backfill/Reconcile runner
    失败含义：runner 未接线会导致 run_* 在运行期 AttributeError
    """
    from backend.app.db.connection import ConnectionManager
    from backend.app.db.migrate import apply_migrations

    db = tmp_path / "runners.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    orch = DataSyncOrchestrator(cm)

    assert isinstance(orch._incremental, IncrementalJobRunner)
    assert isinstance(orch._backfill, BackfillShardRunner)
    assert isinstance(orch._reconcile, ReconcileJobRunner)
