"""CLI run correlation helper tests."""

from __future__ import annotations

import re

from backend.app.cli.run_context import cli_requested_by, new_cli_run_id


def test_newCliRunId_usesPrefixAndCommandSlug() -> None:
    """覆盖范围：CLI 边界 run_id 格式
    测试对象：new_cli_run_id
    目的/目标：运维可用前缀+命令片段+随机后缀串联一次 CLI 调用
    验证点：匹配 p1-incremental-<12hex>
    失败含义：run_id 不可预测或不可与命令关联，审计链难串联
    """
    run_id = new_cli_run_id("incremental", prefix="p1")
    assert re.fullmatch(r"p1-incremental-[0-9a-f]{12}", run_id)


def test_cliRequestedBy_labelsQmdDataCommand() -> None:
    """覆盖范围：写入审计 requested_by 标签
    测试对象：cli_requested_by
    目的/目标：write_audit_log 能区分是哪条 qmd-data 子命令触发写入
    验证点：返回 qmd-data:data sync
    失败含义：审计里全是 orchestrator，无法从库表反查 CLI 入口
    """
    assert cli_requested_by("data sync") == "qmd-data:data sync"
