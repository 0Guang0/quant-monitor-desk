from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.check_acceptance_helper_consumers import build_report, collect_consumers

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_acceptanceHelperConsumers_reportListsKnownMigrationSubjects() -> None:
    """覆盖范围：旧验收 helper 消费者盘点
    测试对象：collect_consumers
    目的/目标：迁移前必须能看到旧 smoke、source-specific helper 和 test helper 的直接消费者
    验证点：报告包含 production_equivalent_smoke、tier_a_live_acceptance、live_incremental_support
    失败含义：迁移看不见旧入口消费者，后续删除或委托时容易漏掉活跃路径
    """
    hits = collect_consumers()
    targets = {hit.target for hit in hits}
    paths = {hit.path for hit in hits}

    assert "scripts/production_equivalent_smoke.py" in targets
    assert "backend/app/ops/tier_a_live_acceptance.py" in targets
    assert "tests/live_incremental_support.py" in targets
    assert "scripts/ci_perf_budget_artifact.py" in paths
    assert "backend/app/ops/tier_b_live_acceptance.py" in paths


def test_acceptanceHelperConsumers_reportIsAdvisoryByDefault() -> None:
    """覆盖范围：旧 helper 盘点脚本默认退出语义
    测试对象：scripts/check_acceptance_helper_consumers.py CLI
    目的/目标：当前任务只做 advisory deprecation，默认报告剩余消费者但不打断 CI
    验证点：returncode==0；status==WARN；consumer_count 大于 0
    失败含义：盘点脚本过早强制失败，会在替代路径完成前破坏现有工作流
    """
    result = subprocess.run(
        [sys.executable, "scripts/check_acceptance_helper_consumers.py", "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
        cwd=PROJECT_ROOT,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "WARN"
    assert payload["mode"] == "advisory_deprecation_inventory"
    assert payload["consumer_count"] > 0


def test_acceptanceHelperConsumers_strictModeFailsWhileConsumersRemain() -> None:
    """覆盖范围：旧 helper 盘点脚本严格模式
    测试对象：scripts/check_acceptance_helper_consumers.py --strict
    目的/目标：后续迁移完成时可以把盘点升级为 gate，当前仍能明确失败原因
    验证点：returncode==1；JSON 仍可解析并列出消费者
    失败含义：迁移完成后缺少可执行 gate，旧入口可能长期残留
    """
    result = subprocess.run(
        [
            sys.executable,
            "scripts/check_acceptance_helper_consumers.py",
            "--format",
            "json",
            "--strict",
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=PROJECT_ROOT,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["consumer_count"] > 0


def test_acceptanceHelperConsumers_reportExcludesDocsAndTaskPlans() -> None:
    """覆盖范围：旧 helper 盘点扫描范围
    测试对象：build_report
    目的/目标：迁移盘点只统计可执行 Python 消费者，不把文档和任务计划当活跃调用点
    验证点：所有 consumer path 都以 .py 结尾，且不在 task/ 目录下
    失败含义：报告混入说明文字会放大迁移范围，执行者无法判断真实代码消费者
    """
    report = build_report()

    for item in report["consumers"]:
        path = item["path"]
        assert path.endswith(".py")
        assert not path.startswith("task/")
