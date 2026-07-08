"""Guard tests for pytest slow-tier and perf profile contracts."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

from scripts.check_acceptance_helper_consumers import build_report
from scripts.perf_gate_profiles import (
    CI_PARALLEL_BUDGET_SEC,
    FULL_BUDGET_SEC,
    QUICK_BUDGET_SEC,
    run_profile,
)
from tests.slow_tier import is_slow_test

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_COLLECTED_RE = re.compile(r"^(\d+)(?:/\d+)? tests collected")


def _require_perf_gate() -> None:
    if os.environ.get("QMD_PERF_GATE") != "1":
        pytest.skip("perf wall-clock gate opt-in via QMD_PERF_GATE=1")
    if os.environ.get("QMD_PERF_GATE_SUBPROCESS") == "1":
        pytest.skip("perf gate subprocess must not re-enter wall-clock tests")


def _collected_count(stdout: str) -> int:
    for line in reversed(stdout.splitlines()):
        match = _COLLECTED_RE.match(line.strip())
        if match:
            return int(match.group(1))
    raise AssertionError(f"pytest collect summary missing from output:\n{stdout}")


def test_slowTier_autoMarksIncrementalE2eModules() -> None:
    """覆盖范围：slow_tier SSOT 对 incremental e2e 模块的自动标记规则
    测试对象：is_slow_test
    目的/目标：P1 分层须覆盖全部 *_incremental_e2e.py replay 路径
    验证点：baostock incremental e2e 模块内代表测试被判定为 slow
    失败含义：quick profile 仍会跑全量 replay E2E，开发循环无收益
    """
    path = PROJECT_ROOT / "tests" / "test_baostock_incremental_e2e.py"
    assert is_slow_test(path, "test_baostockIncremental_repeatRun_noRowGrowth")


def test_slowTier_autoMarksOrchestratorHeavyIntegrationKeepsFastUnit() -> None:
    """覆盖范围：编排器重集成测按名称标 slow，快测仍留 quick profile
    测试对象：is_slow_test
    目的/目标：墙钟 >3s 的 backfill/reconcile 不得进入 quick，create_job 等快测须保留
    验证点：backfill 分片 guard 测为 slow；createJob 测非 slow
    失败含义：整文件标 slow 或漏标重测，quick 仍 ~300s+ 或失去编排回归
    """
    path = PROJECT_ROOT / "tests" / "test_sync_orchestrator.py"
    assert is_slow_test(path, "test_backfillJob_secondShardGuardPause_preservesFirstShardOutcome")
    assert not is_slow_test(path, "test_orchestrator_createJob_persistsDataSyncJob")


def test_slowTier_autoMarksMetaGuardAndBindingExecutor() -> None:
    """覆盖范围：meta guard 与 binding executor 的 slow 分层
    测试对象：is_slow_test
    目的/目标：subprocess collect-only 与全树扫描不得进入 quick profile
    验证点：slowTier collect guard、buildReportStrict、binding executor 为 slow
    失败含义：quick 仍承担 ~8s meta 开销或 orchestration 重测
    """
    assert is_slow_test(
        PROJECT_ROOT / "tests" / "test_pytest_slow_tier.py",
        "test_slowTier_collection_excludesSlowFromQuickProfile",
    )
    assert is_slow_test(
        PROJECT_ROOT / "tests" / "test_pytest_slow_tier.py",
        "test_checkAcceptanceHelperConsumers_buildReportStrictPass",
    )
    assert is_slow_test(
        PROJECT_ROOT / "tests" / "test_sync_binding_executor.py",
        "test_bindingSyncExecutor_executeBinding_onlyOrchestrationPath",
    )


def test_slowTier_autoMarksAcceptanceHelperConsumerGate() -> None:
    """覆盖范围：P0 离群 subprocess 门禁的 slow 分层
    测试对象：is_slow_test
    目的/目标：全仓扫描门禁不得进入 quick profile
    验证点：acceptanceHelperConsumers strict 测试被判定为 slow
    失败含义：quick CI 仍承担 ~18s 全树扫描，分层失效
    """
    path = PROJECT_ROOT / "tests" / "test_source_route_db_acceptance_matrix.py"
    assert is_slow_test(path, "test_acceptanceHelperConsumers_strictMode_hasZeroProductRuntimeConsumers")


def test_slowTier_collection_excludesSlowFromQuickProfile() -> None:
    """覆盖范围：pytest collection 后 slow 标记数量
    测试对象：pytest --collect-only + slow 关键字
    目的/目标：P1 guard — quick profile 须排除足够多慢测（≥95）
    验证点：collect-only 中 slow 标记数 ≥ 95；quick 选择数 < 全量
    失败含义：slow 自动打标未生效或覆盖不足，quick/full 无差异
    """
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-m", "slow"],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert _collected_count(proc.stdout) >= 95

    all_proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only"],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    quick_proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-m",
            "not slow and not network",
        ],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert all_proc.returncode == 0 and quick_proc.returncode == 0
    all_count = _collected_count(all_proc.stdout)
    quick_count = _collected_count(quick_proc.stdout)
    assert quick_count < all_count
    assert quick_count <= 1435


def test_checkAcceptanceHelperConsumers_buildReportStrictPass() -> None:
    """覆盖范围：P2 脚本预过滤后 strict 报告语义不变
    测试对象：build_report
    目的/目标：needle 预过滤不得漏报 product_runtime consumer
    验证点：strict_status PASS；product_runtime_count == 0；seam_inventory PASS
    失败含义：扫描优化破坏门禁语义，migration 回归 silent
    """
    report = build_report(PROJECT_ROOT)
    assert report["strict_status"] == "PASS"
    assert report["product_runtime_count"] == 0
    assert report["seam_inventory_status"] == "PASS"


@pytest.mark.perf
def test_checkAcceptanceHelperConsumers_cliCompletesWithinBudget() -> None:
    """覆盖范围：P2 脚本 CLI 墙钟预算
    测试对象：scripts/check_acceptance_helper_consumers.py subprocess
    目的/目标：预过滤 + 单次调用后全树扫描须在 12s 内完成（原 ~18s 双调用）
    验证点：returncode 0；elapsed < 12s
    失败含义：consumer 扫描回退为不可接受的 CI 开销
    """
    started = time.perf_counter()
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/check_acceptance_helper_consumers.py",
            "--strict",
            "--strict-seam-inventory",
            "--format",
            "json",
        ],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    elapsed = time.perf_counter() - started
    assert proc.returncode == 0, proc.stderr
    assert elapsed < 12.0


@pytest.mark.perf
@pytest.mark.perf_gate
def test_perfGate_quickProfile_completesWithinBudget() -> None:
    """覆盖范围：quick profile 全套件墙钟预算（P5 / Slice B）
    测试对象：pytest -m "not slow and not network and not perf_gate"
    目的/目标：pre-commit quick 须在 180s 内完成，防分层失效回归
    验证点：QMD_PERF_GATE=1 时 subprocess exit 0 且 elapsed < 180s
    失败含义：开发循环 quick 超时，commit 频繁失败或跳过测试
    """
    _require_perf_gate()
    elapsed = run_profile("quick", verbose=True)
    assert elapsed < QUICK_BUDGET_SEC


@pytest.mark.perf
@pytest.mark.perf_gate
def test_perfGate_fullProfile_completesWithinBudget() -> None:
    """覆盖范围：full profile 串行全套件墙钟预算（P5 / Slice B）
    测试对象：pytest -q -m "not perf_gate"（同 npm run test:full 口径）
    目的/目标：本地/合并前 full 须在 300s 内完成
    验证点：QMD_PERF_GATE=1 时 subprocess exit 0 且 elapsed < 300s
    失败含义：全量回归超时，CI 或 pre-push 无法稳定关账
    """
    _require_perf_gate()
    elapsed = run_profile("full", verbose=True)
    assert elapsed < FULL_BUDGET_SEC


@pytest.mark.perf
@pytest.mark.perf_gate
def test_perfGate_ciParallelFullProfile_completesWithinBudget() -> None:
    """覆盖范围：CI parallel full 墙钟预算（P5 / Slice B）
    测试对象：pytest -q -n auto -m "not perf_gate"（同 .github/workflows/ci.yml backend）
    目的/目标：Linux CI xdist 全量须在 240s 内完成（较串行 300s 留并行余量）
    验证点：QMD_PERF_GATE=1 时 subprocess exit 0 且 elapsed < 240s
    失败含义：CI backend job 墙钟回归，合并队列阻塞
    """
    _require_perf_gate()
    elapsed = run_profile("ci-parallel", verbose=True)
    assert elapsed < CI_PARALLEL_BUDGET_SEC
