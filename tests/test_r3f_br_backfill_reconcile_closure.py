"""R3F-BR-01..05 closure guards (Batch 3F.4 backfill/reconcile parity).

覆盖范围：backfill/reconcile parity、handler registry、R3-PARTIAL-4/5 关账链。
"""

from __future__ import annotations

from pathlib import Path

from backend.app.sync.contract import IMPLEMENTED_JOB_TYPES, RESERVED_JOB_TYPES
from backend.app.sync.orchestrator import (
    ORCHESTRATOR_HANDLER_REGISTRY,
    DataSyncOrchestrator,
    orchestrator_handler_registry,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ADR_023 = PROJECT_ROOT / "docs" / "adr" / "ADR-023-layer5-conflict-review-path.md"
AUDIT_DEFERRED = PROJECT_ROOT / "docs" / "AUDIT_DEFERRED_REGISTRY.md"
UNRESOLVED = PROJECT_ROOT / "docs" / "UNRESOLVED_ISSUES_REGISTRY.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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
    验证点：含 run_reconcile、RESOLVED_BY_REFETCH、StillDiffAdapter、FailFetchAdapter
    失败含义：reconcile 闭包无测试，R3-PARTIAL-3 无法 honest closeout
    """
    text = _read(PROJECT_ROOT / "tests" / "test_audit_remediation.py")

    for token in (
        "run_reconcile",
        "RESOLVED_BY_REFETCH",
        "StillDiffAdapter",
        "FailFetchAdapter",
        "MatchAdapter",
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
        ".trellis/tasks/round3v-sync-support-matrix-recovery/repair-evidence/"
        "sync-crash-window-runbook.md"
    )

    assert "| R3-PARTIAL-5          | DEFERRED" not in unresolved
    assert handoff.is_file()
    assert "R3F-BR-03" in handoff.read_text(encoding="utf-8")


def test_r3fBr04_orchestratorHandlerRegistry_coversContractMatrix() -> None:
    """覆盖范围：R3F-BR-04 / D7-P1-1 handler registry extraction
    测试对象：orchestrator_handler_registry / ORCHESTRATOR_HANDLER_REGISTRY
    目的/目标：已实现与保留 job 类型在 registry 有稳定 entrypoint 映射
    验证点：registry 覆盖 IMPLEMENTED+RESERVED；runner 行 runner_attr 非空且可解析
    失败含义：新 job 类型扩展仍耦合在 orchestrator 方法散落点
    """
    registry = orchestrator_handler_registry()
    assert set(registry) >= set(IMPLEMENTED_JOB_TYPES) | set(RESERVED_JOB_TYPES)
    assert registry is not ORCHESTRATOR_HANDLER_REGISTRY

    for job_type in IMPLEMENTED_JOB_TYPES:
        row = registry[job_type]
        assert row.kind == "runner"
        assert row.runner_attr is not None
        assert hasattr(DataSyncOrchestrator, row.entrypoint)

    for job_type in RESERVED_JOB_TYPES:
        assert registry[job_type].kind == "deferred"


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
