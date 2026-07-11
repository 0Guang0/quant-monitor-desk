#!/usr/bin/env python3
"""早期 pytest 分层 / perf 门禁卫生扫描（阶段性 · 非业务 pytest）

功能：
  检查三件事，都不等于测生产业务行为：
  1）tests/slow_tier.py 的自动打标规则是否仍覆盖关键慢测（incremental e2e、编排重测、
     acceptance helper 全树扫描等）；
  2）pytest --collect-only 后 slow 与 quick 分层是否仍拉开（slow≥95，quick 明显更少）；
  3）可选：acceptance helper 脚本 strict 报告、以及 QMD_PERF_GATE=1 时的墙钟 profile。
  对应原 tests/test_pytest_slow_tier.py（meta-testing）。

业务价值：
  防止开发循环把重测重新塞进 quick，或 CI 墙钟门禁静默失效。
  按 completion-check TEST-EVIDENCE-GOVERNANCE：这是 meta-testing / tooling 卫生，
  不是生产 outcome，不得进 tests/ 业务套件，也不得单独当作产品功能关账证据。

退役 / 清理时间（满足任一即可删本文件）：
  1. slow 分层与 perf profile 已由正式 CI 门禁（pre-commit / GitHub Actions / production_gate）
     稳定承接，且本脚本无独立调用方；或
  2. tests/slow_tier.py 退役、改为 pytest 原生 marker 契约并由 CI 校验；或
  3. master 连续 4 周无「quick 墙钟回退 / slow 漏标」回流，且团队确认不再需要本扫描。

运行：
  uv run python phase-scripts/check_pytest_slow_tier_hygiene.py
  uv run python phase-scripts/check_pytest_slow_tier_hygiene.py --strict
  uv run python phase-scripts/check_pytest_slow_tier_hygiene.py --with-helper-budget
  QMD_PERF_GATE=1 uv run python phase-scripts/check_pytest_slow_tier_hygiene.py --with-perf-gate

guidelines 对齐：
  - testing-guidelines / completion-check 禁入：meta-testing → 不进业务 pytest
  - AGENTS.md → 阶段性流程放 phase-scripts，中文写明功能、价值、退役条件
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
_COLLECTED_RE = re.compile(r"^(\d+)(?:/\d+)? tests collected")


def _collected_count(stdout: str) -> int:
    for line in reversed(stdout.splitlines()):
        match = _COLLECTED_RE.match(line.strip())
        if match:
            return int(match.group(1))
    raise AssertionError(f"pytest collect summary missing from output:\n{stdout}")


def _check_slow_mark_rules() -> list[str]:
    from tests.slow_tier import is_slow_test

    errors: list[str] = []
    cases = (
        (
            PROJECT_ROOT / "tests" / "test_baostock_incremental_e2e.py",
            "test_baostockIncremental_repeatRun_noRowGrowth",
            True,
        ),
        (
            PROJECT_ROOT / "tests" / "test_sync_orchestrator.py",
            "test_backfillJob_secondShardGuardPause_preservesFirstShardOutcome",
            True,
        ),
        (
            PROJECT_ROOT / "tests" / "test_sync_orchestrator.py",
            "test_orchestrator_createJob_persistsDataSyncJob",
            False,
        ),
        (
            PROJECT_ROOT / "tests" / "test_sync_binding_executor.py",
            "test_bindingSyncExecutor_executeBinding_onlyOrchestrationPath",
            True,
        ),
        (
            PROJECT_ROOT / "tests" / "test_source_route_db_acceptance_matrix.py",
            "test_sourceRouteDbAcceptanceMatrix_dryRunClosure_passesWithoutLiveAuthorization",
            True,
        ),
    )
    for path, name, expect_slow in cases:
        got = is_slow_test(path, name)
        if got is not expect_slow:
            errors.append(f"is_slow_test({path.name}, {name})={got}, expect {expect_slow}")
    return errors


def _check_collection_split() -> list[str]:
    errors: list[str] = []
    slow_proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-m", "slow"],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if slow_proc.returncode != 0:
        return [f"slow collect failed: {slow_proc.stderr or slow_proc.stdout}"]
    slow_count = _collected_count(slow_proc.stdout)
    if slow_count < 95:
        errors.append(f"slow collected={slow_count}, expect >= 95")

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
    if all_proc.returncode != 0 or quick_proc.returncode != 0:
        return [
            "all/quick collect failed",
            all_proc.stderr or all_proc.stdout,
            quick_proc.stderr or quick_proc.stdout,
        ]
    all_count = _collected_count(all_proc.stdout)
    quick_count = _collected_count(quick_proc.stdout)
    if not (quick_count < all_count and quick_count <= all_count - 95):
        errors.append(
            f"quick={quick_count} all={all_count} slow={slow_count}; "
            "expect quick < all and quick <= all-95"
        )
    return errors


def _check_helper_strict() -> list[str]:
    from scripts.check_acceptance_helper_consumers import build_report

    report = build_report(PROJECT_ROOT)
    errors: list[str] = []
    if report.get("strict_status") != "PASS":
        errors.append(f"strict_status={report.get('strict_status')!r}")
    if report.get("product_runtime_count") != 0:
        errors.append(f"product_runtime_count={report.get('product_runtime_count')!r}")
    if report.get("seam_inventory_status") != "PASS":
        errors.append(f"seam_inventory_status={report.get('seam_inventory_status')!r}")
    return errors


def _check_helper_cli_budget() -> list[str]:
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
    errors: list[str] = []
    if proc.returncode != 0:
        errors.append(proc.stderr or proc.stdout or "helper CLI non-zero")
    if elapsed >= 12.0:
        errors.append(f"helper CLI elapsed={elapsed:.2f}s, expect < 12s")
    return errors


def _check_perf_gate() -> list[str]:
    if os.environ.get("QMD_PERF_GATE") != "1":
        return ["QMD_PERF_GATE!=1; skip --with-perf-gate or export QMD_PERF_GATE=1"]
    if os.environ.get("QMD_PERF_GATE_SUBPROCESS") == "1":
        return ["QMD_PERF_GATE_SUBPROCESS=1; refuse re-entry"]

    from scripts.perf_gate_profiles import (
        CI_PARALLEL_BUDGET_SEC,
        FULL_BUDGET_SEC,
        QUICK_BUDGET_SEC,
        run_profile,
    )

    errors: list[str] = []
    for profile, budget in (
        ("quick", QUICK_BUDGET_SEC),
        ("full", FULL_BUDGET_SEC),
        ("ci-parallel", CI_PARALLEL_BUDGET_SEC),
    ):
        elapsed = run_profile(profile, verbose=True)
        if elapsed >= budget:
            errors.append(f"profile {profile} elapsed={elapsed:.1f}s >= budget {budget}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="有失败时 exit 1")
    parser.add_argument(
        "--with-helper-budget",
        action="store_true",
        help="额外跑 acceptance helper CLI 墙钟预算",
    )
    parser.add_argument(
        "--with-perf-gate",
        action="store_true",
        help="额外跑 quick/full/ci-parallel 墙钟（需 QMD_PERF_GATE=1）",
    )
    args = parser.parse_args(argv)

    checks: list[tuple[str, list[str]]] = [
        ("slow_mark_rules", _check_slow_mark_rules()),
        ("collection_split", _check_collection_split()),
        ("helper_strict", _check_helper_strict()),
    ]
    if args.with_helper_budget:
        checks.append(("helper_cli_budget", _check_helper_cli_budget()))
    if args.with_perf_gate:
        checks.append(("perf_gate", _check_perf_gate()))

    failed = [(name, errs) for name, errs in checks if errs]
    if not failed:
        print("PASS: pytest slow-tier / helper hygiene")
        return 0

    print("FAIL: pytest slow-tier / helper hygiene")
    for name, errs in failed:
        print(f"  [{name}]")
        for err in errs:
            print(f"    - {err}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
