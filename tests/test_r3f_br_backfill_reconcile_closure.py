"""R3F-BR-01..05 closure guards (Batch 3F.4 backfill/reconcile parity).

覆盖范围：backfill/reconcile parity、handler registry、R3-PARTIAL-4/5 关账链。
"""

from __future__ import annotations

from pathlib import Path

from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.sync.contract import (
    IMPLEMENTED_JOB_TYPES,
    RESERVED_JOB_TYPES,
    load_sync_job_contract,
)
from backend.app.sync.orchestrator import (
    ORCHESTRATOR_HANDLER_REGISTRY,
    DataSyncOrchestrator,
    orchestrator_handler_registry,
)
from backend.app.sync.runners import (
    BackfillShardRunner,
    IncrementalJobRunner,
    QualityJobRunner,
    ReconcileJobRunner,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLAYBOOK = (
    PROJECT_ROOT
    / "docs"
    / "implementation_tasks"
    / "ROUND_3_BATCH6_DATA_GOVERNANCE"
    / "BATCH_3F_BATCH6_DATA_GOVERNANCE"
    / "BATCH_3F_COORDINATOR_PLAYBOOK.md"
)
CONTEXT_CLOSURE = (
    PROJECT_ROOT
    / ".trellis"
    / "tasks"
    / "archive"
    / "2026-06"
    / "round3f-backfill-reconcile-parity"
    / "research"
    / "context-closure.md"
)
ADR_023 = PROJECT_ROOT / "docs" / "adr" / "ADR-023-layer5-conflict-review-path.md"
AUDIT_DEFERRED = PROJECT_ROOT / "docs" / "AUDIT_DEFERRED_REGISTRY.md"
UNRESOLVED = PROJECT_ROOT / "docs" / "UNRESOLVED_ISSUES_REGISTRY.md"
PLAYBOOK_85_SUBSET = (
    "tests/test_sync_orchestrator.py",
    "tests/test_sync_runners.py",
    "tests/test_r3f_br_backfill_reconcile_closure.py",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _orchestrator(tmp_path: Path) -> DataSyncOrchestrator:
    db = tmp_path / "br-closure.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    return DataSyncOrchestrator(cm)


def test_r3fBr01_backfillParity_registryDocumentsValidateWritePath() -> None:
    """覆盖范围：R3F-BR-01 / R3-PARTIAL-1 backfill parity 叙事
    测试对象：registry 与 test_sync_orchestrator backfill 测试族
    目的/目标：不得再声称 backfill 跳过 validator；须有 validate+write 证据
    验证点：registry 含 ADV-R3X-SYNC-002、validate+write；
    test_sync_orchestrator 含 severeConflict 测试
    失败含义：读者仍以为 backfill 可绕过校验写库
    """
    audit = _read(AUDIT_DEFERRED)
    unresolved = _read(UNRESOLVED)
    orch_tests = _read(PROJECT_ROOT / "tests" / "test_sync_orchestrator.py")

    assert "skips validator + clean write" not in audit
    assert "skips validator + clean write" not in unresolved
    for token in ("ADV-R3X-SYNC-002", "validate+write", "severe conflict"):
        assert token in audit
    assert (
        "test_backfillJob_severeConflict_blocksCleanWriteAndPersistsConflictReportId"
        in orch_tests
    )


def test_r3fBr02_reconcileRefetch_testsExistInAuditRemediation() -> None:
    """覆盖范围：R3F-BR-02 / R3-PARTIAL-3 reconcile re-fetch/compare closure
    测试对象：tests/test_audit_remediation.py reconcile 族
    目的/目标：reconcile 重拉后 match/mismatch/fetch-fail 三条路径有 pytest 锚点
    验证点：含 run_reconcile、RESOLVED_BY_REFETCH、MatchAdapter、StillDiffAdapter、FailFetchAdapter
    失败含义：reconcile 闭包无测试，R3-PARTIAL-3 无法 honest closeout
    """
    text = _read(PROJECT_ROOT / "tests" / "test_audit_remediation.py")

    for token in (
        "run_reconcile",
        "RESOLVED_BY_REFETCH",
        "MatchAdapter",
        "StillDiffAdapter",
        "FailFetchAdapter",
    ):
        assert token in text


def test_r3fBr03_r3Partial5_regressionGuard_noReopenInUnresolved() -> None:
    """覆盖范围：R3F-BR-03 / R3-PARTIAL-5 regression guard only
    测试对象：UNRESOLVED_ISSUES_REGISTRY.md
    目的/目标：B3V crash-window 已闭合，不得把 path A 重开为 DEFERRED 实现项
    验证点：UNRESOLVED 无 R3-PARTIAL-5 DEFERRED 行；handoff 文档指向 R3F-BR-03
    失败含义：已闭合项被重开，并行 slice 会重复实现 crash recovery
    """
    unresolved = _read(UNRESOLVED)
    handoff = PROJECT_ROOT / (
        ".trellis/tasks/archive/2026-06/round3v-sync-support-matrix-recovery/repair-evidence/"
        "sync-crash-window-runbook.md"
    )

    assert "| R3-PARTIAL-5          | DEFERRED" not in unresolved
    assert handoff.is_file()
    assert "R3F-BR-03" in handoff.read_text(encoding="utf-8")


def test_r3fBr04_orchestratorHandlerRegistry_coversContractMatrix(tmp_path) -> None:
    """覆盖范围：R3F-BR-04 / D7-P1-1 handler registry extraction
    测试对象：orchestrator_handler_registry / ORCHESTRATOR_HANDLER_REGISTRY / sync_job_contract.yaml
    目的/目标：已实现与保留 job 类型在 registry 有稳定 entrypoint 映射；runner_attr 可解析
    验证点：registry 覆盖 IMPLEMENTED+RESERVED+utility；YAML 单源；实例 getattr 接线
    失败含义：新 job 类型扩展仍耦合在 orchestrator 方法散落点
    """
    contract = load_sync_job_contract()
    yaml_impl = frozenset(contract["implemented_job_types"])
    yaml_reserved = frozenset(contract["reserved_job_types"])
    yaml_utility = frozenset(contract.get("utility_operations", ()))

    assert yaml_impl == IMPLEMENTED_JOB_TYPES
    assert yaml_reserved == RESERVED_JOB_TYPES
    assert yaml_impl.isdisjoint(yaml_reserved)
    assert yaml_utility == frozenset({"recover_stuck_writing_job"})

    registry = orchestrator_handler_registry()
    assert set(registry) >= set(IMPLEMENTED_JOB_TYPES) | set(RESERVED_JOB_TYPES) | yaml_utility
    assert registry is not ORCHESTRATOR_HANDLER_REGISTRY

    orch = _orchestrator(tmp_path)
    expected_runner_types = {
        "incremental": IncrementalJobRunner,
        "backfill": BackfillShardRunner,
        "reconcile": ReconcileJobRunner,
        "data_quality": QualityJobRunner,
        "revision_audit": QualityJobRunner,
    }
    for job_type in IMPLEMENTED_JOB_TYPES:
        row = registry[job_type]
        assert row.kind == "runner"
        assert row.runner_attr is not None
        assert hasattr(DataSyncOrchestrator, row.entrypoint)
        runner = getattr(orch, row.runner_attr)
        assert isinstance(runner, expected_runner_types[job_type])

    for job_type in RESERVED_JOB_TYPES:
        assert registry[job_type].kind == "deferred"

    utility = registry["recover_stuck_writing_job"]
    assert utility.kind == "utility"
    assert utility.runner_attr is None
    assert utility.entrypoint == "recover_stuck_writing_job"
    assert hasattr(orch, utility.entrypoint)


def test_r3fBr05_r3Partial4_adr023LinksRegistryDeferredRow() -> None:
    """覆盖范围：R3F-BR-05 / R3-PARTIAL-4 registry 关账 ADR 链
    测试对象：ADR-023 + UNRESOLVED R3-PARTIAL-4 行
    目的/目标：ADR 选定 manual-review queue 路径；registry 仍 honest DEFERRED 待主会话收口
    验证点：ADR-023 含 R3-PARTIAL-4；UNRESOLVED 含 R3-PARTIAL-4 DEFERRED；ADR 拒绝 instant UI
    失败含义：ADR 与 registry 脱节，Batch6 无法 honest 关账
    """
    adr = _read(ADR_023)
    unresolved = _read(UNRESOLVED)

    assert "R3-PARTIAL-4" in adr
    assert "R3-PARTIAL-4" in unresolved
    assert "| R3-PARTIAL-4" in unresolved
    assert "Instant severe queue UI" in adr
    assert "Round4 defer" in adr


def test_r3fBr06_playbookSection85_includesClosureModule() -> None:
    """覆盖范围：Playbook §8.5 子集与 closure 模块对齐（A1-PLAN-01）
    测试对象：BATCH_3F_COORDINATOR_PLAYBOOK.md §8.5 pytest 命令块
    目的/目标：仅跑 playbook 子集时 BR-01..05 registry 叙事 guard 不得静默回归
    验证点：§8.5 bash 块含三文件子集常量；与 MASTER §6 Tier A 一致
    失败含义：协调者按 playbook 跑测会漏掉 closure 守卫
    """
    playbook = _read(PLAYBOOK)
    section = playbook.split("### 8.5 B3F-BR")[1].split("### 8.6")[0]
    for path in PLAYBOOK_85_SUBSET:
        assert path in section


def test_r3fBr07_utilityRecoveryRow_documentsInContract() -> None:
    """覆盖范围：recover_stuck_writing_job utility 行契约登记（A1-PLAN-02 / A7-BR-O2）
    测试对象：sync_job_contract.yaml utility_operations + orchestrator registry
    目的/目标：ops recovery 入口在契约与 registry 双线 honest 登记，非 schedulable job_type
    验证点：YAML utility_operations 含 recover_stuck_writing_job；
    registry kind=utility；不在 job_types 调度矩阵
    失败含义：runbook 读者误以为 utility 行是标准 job type，或契约与 registry 分叉
    """
    contract = load_sync_job_contract()
    job_types = frozenset(contract["job_types"])
    utility_ops = frozenset(contract["utility_operations"])

    assert "recover_stuck_writing_job" in utility_ops
    assert "recover_stuck_writing_job" not in job_types
    assert "recover_stuck_writing_job" not in contract["implemented_job_types"]
    assert "recover_stuck_writing_job" not in contract["reserved_job_types"]

    row = orchestrator_handler_registry()["recover_stuck_writing_job"]
    assert row.kind == "utility"
    assert row.entrypoint == "recover_stuck_writing_job"


def test_r3fBr08_opsRegistryMatrix_a7BrClosureDocumented() -> None:
    """覆盖范围：A7-BR-O1..O4 运维/registry 矩阵 closure 文档（Repair）
    测试对象：research/context-closure.md A7 矩阵节
    目的/目标：运维面 WARN 在任务 closure 文档有 honest 登记，供 merge 后 RCA 引用
    验证点：context-closure 含 A7-BR-O1..O4 与 W-A3-01 ponytail 说明
    失败含义：A7 WARN 仅存在于审计 transcript，merge 后无 SSOT 可追溯
    """
    closure = _read(CONTEXT_CLOSURE)
    for token in (
        "A7-BR-O1",
        "A7-BR-O2",
        "A7-BR-O3",
        "A7-BR-O4",
        "W-A3-01",
        "quote_ident",
        "仅元数据",
        "ORCHESTRATOR_HANDLER_REGISTRY",
    ):
        assert token in closure
