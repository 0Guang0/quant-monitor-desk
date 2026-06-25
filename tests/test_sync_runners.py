"""Sync job runner wiring tests (B3F-BR / playbook §8.5).

覆盖范围：runner 类与 orchestrator 接线。
分片规划见 test_sync_orchestrator.test_backfillJob_largeRange_splitsIntoTasks。
"""

from __future__ import annotations

from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.sync.orchestrator import DataSyncOrchestrator, orchestrator_handler_registry
from backend.app.sync.runners import (
    BackfillShardRunner,
    IncrementalJobRunner,
    ReconcileJobRunner,
)


def test_syncRunners_orchestratorWiresRunnerAttributes(tmp_path) -> None:
    """覆盖范围：orchestrator 内部 runner 实例接线与 registry runner_attr 一致
    测试对象：DataSyncOrchestrator.__init__ · orchestrator_handler_registry
    目的/目标：三类已实现 job 的 runner 在编排器内可访问且与 registry 单源对齐
    验证点：_incremental/_backfill/_reconcile isinstance；registry runner_attr getattr 一致
    失败含义：runner 未接线或 registry 与实例分叉会导致运行期 AttributeError
    """
    db = tmp_path / "runners.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    orch = DataSyncOrchestrator(cm)
    registry = orchestrator_handler_registry()

    assert isinstance(orch._incremental, IncrementalJobRunner)
    assert isinstance(orch._backfill, BackfillShardRunner)
    assert isinstance(orch._reconcile, ReconcileJobRunner)

    for attr_name, expected_type in (
        ("_incremental", IncrementalJobRunner),
        ("_backfill", BackfillShardRunner),
        ("_reconcile", ReconcileJobRunner),
    ):
        row = next(r for r in registry.values() if r.runner_attr == attr_name)
        assert getattr(orch, row.runner_attr) is getattr(orch, attr_name)
        assert isinstance(getattr(orch, row.runner_attr), expected_type)
