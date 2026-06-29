"""task_archive 与单轨门禁边界测试。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO / ".trellis" / "scripts"
sys.path.insert(0, str(_SCRIPTS))

from common.task_archive import (  # noqa: E402
    is_archived_task,
    legacy_handoff_allowed,
)
from common.validate_plan_freeze import validate_plan_freeze  # noqa: E402
from common.validate_execute_handoff import validate_execute_handoff  # noqa: E402


def test_isArchivedTask_requiresTasksArchiveSegment(tmp_path: Path) -> None:
    """覆盖范围：归档路径判定
    测试对象：is_archived_task
    目的/目标：仅 .trellis/tasks/archive/ 下为真，slug 含 archive 不算
    验证点：tasks/archive/x 真；tasks/my-archive-fix 假
    失败含义：误跳过活跃任务门禁
    """
    assert is_archived_task(_REPO / ".trellis" / "tasks" / "archive" / "2026-06" / "x")
    assert not is_archived_task(tmp_path / "my-archive-fix")


def test_validatePlanFreeze_rejectsOrphanMaster(tmp_path: Path) -> None:
    """覆盖范围：无 task.json 但有 MASTER 的目录
    测试对象：validate_plan_freeze
    目的/目标：不得静默通过
    验证点：errors 含 missing task.json
    失败含义：孤儿 MASTER 目录绕过单轨
    """
    (tmp_path / "MASTER.plan.md").write_text("## 8.\n", encoding="utf-8")
    errors = validate_plan_freeze(tmp_path, _REPO)
    assert any("missing task.json" in e for e in errors)


def test_legacyHandoffAllowed_inProgressV3(tmp_path: Path) -> None:
    """覆盖范围：legacy handoff 白名单
    测试对象：legacy_handoff_allowed
    目的/目标：in_progress + plan_protocol_version 3 + MASTER 允许 shim
    验证点：返回 True
    失败含义：在途 v3 无法 handoff
    """
    (tmp_path / "task.json").write_text(
        json.dumps({"meta": {"plan_protocol_version": "3"}, "status": "in_progress"}),
        encoding="utf-8",
    )
    (tmp_path / "MASTER.plan.md").write_text("# m\n", encoding="utf-8")
    assert legacy_handoff_allowed(tmp_path)


def test_validateExecuteHandoff_rejectsOrphanMaster(tmp_path: Path) -> None:
    """覆盖范围：无 task.json 但有 MASTER 的 handoff
    测试对象：validate_execute_handoff
    目的/目标：孤儿 MASTER 不得假绿 handoff
    验证点：errors 含 missing task.json
    失败含义：handoff 静默通过会放过半成品目录
    """
    (tmp_path / "MASTER.plan.md").write_text("## 8.\n", encoding="utf-8")
    errors = validate_execute_handoff(tmp_path, _REPO)
    assert any("missing task.json" in e for e in errors)


def test_extractPlanAcIds_readsExecutionIndex(tmp_path: Path) -> None:
    """覆盖范围：EXECUTION_INDEX §2 AC 提取
    测试对象：extract_plan_ac_ids
    目的/目标：loop 证据链以 INDEX §2 为 SSOT（非 MASTER 别名）
    验证点：返回 AC-1
    失败含义：AC 提取回退错误会导致 evidence_index 漂移
    """
    import sys

    sys.path.insert(0, str(_REPO / "scripts"))
    from loop_engineering_common import extract_plan_ac_ids

    (tmp_path / "EXECUTION_INDEX.md").write_text(
        "## 2. AC\n| AC-1 | tests/test_x.py | pass |\n", encoding="utf-8"
    )
    assert "AC-1" in extract_plan_ac_ids(tmp_path)


def test_validateExecuteHandoff_skipsArchivedLegacy(tmp_path: Path) -> None:
    """覆盖范围：归档 handoff 只读跳过
    测试对象：validate_execute_handoff（路径含 tasks/archive/）
    目的/目标：归档任务 handoff 不阻断
    验证点：errors == []
    失败含义：只读归档被误伤
    """
    archive = tmp_path / "tasks" / "archive" / "2026-06" / "legacy"
    archive.mkdir(parents=True)
    (archive / "MASTER.plan.md").write_text("## 8.\n", encoding="utf-8")
    assert validate_execute_handoff(archive, _REPO) == []
