"""Trellis Execute handoff 校验器测试（v4.1 代码优先；legacy 仍验 txt 证据）。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO / ".trellis" / "scripts"
sys.path.insert(0, str(_SCRIPTS))

from common.validate_execute_handoff import (  # noqa: E402
    _parse_v4_executed_steps,
    validate_execute_handoff,
    validate_execute_step,
)


def _write_v4_task(task_dir: Path, steps_done: list[str], *, complex_track: bool = False) -> None:
    track = "complex" if complex_track else "simple"
    (task_dir / "task.json").write_text(
        json.dumps({"meta": {"plan_protocol_version": "4", "task_track": track}}),
        encoding="utf-8",
    )
    (task_dir / "EXECUTION_INDEX.md").write_text(
        "P0i：索引完整\n## 1. 步骤与证据\n| Step | RED | GREEN |\n",
        encoding="utf-8",
    )
    frozen = task_dir / "frozen"
    frozen.mkdir(exist_ok=True)
    blocks = [f"### {step} step\n| 已执行 | [x] |\n" for step in steps_done]
    (frozen / "card.md").write_text("## 9. 实现步骤\n" + "\n".join(blocks), encoding="utf-8")


def _legacy_boot_artifacts(task_dir: Path, *, steps: list[str]) -> None:
    research = task_dir / "research"
    research.mkdir(parents=True, exist_ok=True)
    (research / "context-closure.md").write_text(
        "upstream wiring closure verified\n", encoding="utf-8"
    )
    (research / "gitnexus-execute-summary.md").write_text("# gnx\n", encoding="utf-8")
    (research / "batch-b-execute-evidence.md").write_text("# ev\n", encoding="utf-8")
    (research / "execute-skill-evaluation.md").write_text(
        "refs execute-skill-reads.jsonl\n", encoding="utf-8"
    )
    reads = research / "execute-skill-reads.jsonl"
    reads.write_text(
        "\n".join(
            [
                '{"phase":"boot","skill":"trellis-execute"}',
                '{"phase":"boot","skill":"test-driven-development"}',
                '{"phase":"boot","skill":"incremental-implementation"}',
                '{"phase":"boot","skill":"karpathy-guidelines"}',
                '{"phase":"boot","skill":"testing-guidelines"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    ev = research / "execute-evidence"
    ev.mkdir(exist_ok=True)
    for step in steps:
        (ev / f"{step}-red.txt").write_text(
            "exit 4\nERROR: ModuleNotFoundError\n", encoding="utf-8"
        )
        (ev / f"{step}-green.txt").write_text("8 passed\nexit 0\n", encoding="utf-8")


def test_validateExecuteStep_requiresFailSignal(tmp_path: Path) -> None:
    """覆盖范围：legacy 单步 RED 证据须含失败信号
    测试对象：validate_execute_step（8.1，RED 仅 all good）
    目的/目标：legacy handoff 仍要求 TDD RED txt 含 FAIL/ERROR
    验证点：errors 中任一条含 FAIL/ERROR
    失败含义：无失败信号的 RED 会让 legacy handoff 误判已走 TDD
    """
    ev = tmp_path / "research" / "execute-evidence"
    ev.mkdir(parents=True)
    (ev / "8.1-red.txt").write_text("all good\n", encoding="utf-8")
    (ev / "8.1-green.txt").write_text("passed\n", encoding="utf-8")
    errors = validate_execute_step(tmp_path, "8.1")
    assert any("FAIL/ERROR" in e for e in errors)


def test_validateExecuteStep_passesWithEvidence(tmp_path: Path) -> None:
    """覆盖范围：legacy 合规 RED/GREEN txt
    测试对象：validate_execute_step（8.1）
    目的/目标：legacy 证据文件应零错误通过
    验证点：validate_execute_step(tmp_path, '8.1') == []
    失败含义：legacy 合法证据被拒会阻断 handoff
    """
    ev = tmp_path / "research" / "execute-evidence"
    ev.mkdir(parents=True)
    (ev / "8.1-red.txt").write_text("ModuleNotFoundError\nexit 1\n", encoding="utf-8")
    (ev / "8.1-green.txt").write_text("1 passed\nexit 0\n", encoding="utf-8")
    assert validate_execute_step(tmp_path, "8.1") == []


def test_validateExecuteHandoff_v41PassesWithFrozenMarkedSteps(tmp_path: Path) -> None:
    """覆盖范围：v4.1 handoff 仅要求 frozen [x]
    测试对象：validate_execute_handoff（4.1 + frozen 9.0 [x]）
    目的/目标：v4.1 不要求 txt/jsonl/summary 工件
    验证点：errors == []
    失败含义：v4.1 仍强制 prose 证据会阻断代码优先 handoff
    """
    (tmp_path / "task.json").write_text(
        json.dumps(
            {
                "meta": {
                    "plan_protocol_version": "4.1",
                    "execute_entry": "research/00-EXECUTION-ENTRY.md",
                    "task_track": "simple",
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "EXECUTION_INDEX.md").write_text(
        "P0i：索引完整\n## 3.\n| path | manifest | audience |\n| x | must-read | execute |\n",
        encoding="utf-8",
    )
    frozen = tmp_path / "frozen"
    frozen.mkdir()
    (frozen / "card.md").write_text(
        "## 9. 实现步骤\n### 9.0 boot\n| 已执行 | [x] |\n",
        encoding="utf-8",
    )
    assert validate_execute_handoff(tmp_path, _REPO) == []


def test_validateExecuteHandoff_v41FailsWithoutMarkedSteps(tmp_path: Path) -> None:
    """覆盖范围：v4.1 handoff 无 [x] 步
    测试对象：validate_execute_handoff（4.1，frozen 全未勾）
    目的/目标：handoff 须至少一步已执行标记
    验证点：errors 含 executed steps
    失败含义：空 handoff 会误交 Audit
    """
    (tmp_path / "task.json").write_text(
        json.dumps({"meta": {"plan_protocol_version": "4.1", "task_track": "simple"}}),
        encoding="utf-8",
    )
    (tmp_path / "EXECUTION_INDEX.md").write_text("## 1.\n", encoding="utf-8")
    frozen = tmp_path / "frozen"
    frozen.mkdir()
    (frozen / "card.md").write_text(
        "## 9.\n### 9.0 boot\n| 已执行 | [ ] |\n",
        encoding="utf-8",
    )
    errors = validate_execute_handoff(tmp_path, _REPO)
    assert any("executed steps" in e for e in errors)


def test_validateExecuteHandoff_legacyRequiresGitnexusSummary(tmp_path: Path) -> None:
    """覆盖范围：legacy v4 handoff 仍要 gitnexus summary
    测试对象：validate_execute_handoff（v4 + 9.0 证据，无 summary）
    目的/目标：非 4.1 任务保持旧门禁
    验证点：errors 含 gitnexus-execute-summary
    失败含义：legacy 路径被误放宽
    """
    _write_v4_task(tmp_path, ["9.0"])
    ev = tmp_path / "research" / "execute-evidence"
    ev.mkdir(parents=True)
    (ev / "9.0-red.txt").write_text("ERROR\n", encoding="utf-8")
    (ev / "9.0-green.txt").write_text("passed\n", encoding="utf-8")
    errors = validate_execute_handoff(tmp_path, _REPO)
    assert any("gitnexus-execute-summary" in e for e in errors)


def test_validateExecuteHandoff_legacyPassesWithFullArtifacts(tmp_path: Path) -> None:
    """覆盖范围：legacy v4 完整工件 handoff
    测试对象：validate_execute_handoff（v4 + boot 工件 + 9.0/9.1 证据）
    目的/目标：legacy 齐备时应零错误
    验证点：errors == []
    失败含义：legacy handoff 回归
    """
    _write_v4_task(tmp_path, ["9.0", "9.1"])
    _legacy_boot_artifacts(tmp_path, steps=["9.0", "9.1"])
    assert validate_execute_handoff(tmp_path, _REPO) == []


def test_validateExecuteHandoff_rejectsLegacyMasterOnly(tmp_path: Path) -> None:
    """覆盖范围：活跃 v3 planning 任务 handoff 拒绝
    测试对象：validate_execute_handoff（MASTER + task.json planning v3）
    目的/目标：planning legacy 不得 handoff
    验证点：errors 含 v4/archive 要求
    失败含义：planning legacy 可 handoff 会破坏单轨
    """
    (tmp_path / "task.json").write_text(
        json.dumps({"meta": {"plan_protocol_version": "3", "task_track": "simple"}}),
        encoding="utf-8",
    )
    (tmp_path / "MASTER.plan.md").write_text("## 8.\n", encoding="utf-8")
    errors = validate_execute_handoff(tmp_path, _REPO)
    assert any("v4" in e.lower() or "archive" in e.lower() for e in errors)


def test_validateExecuteHandoff_loopTaskRequiresEvidenceIndex(tmp_path: Path) -> None:
    """覆盖范围：v4.1 complex 轨道 loop handoff
    测试对象：validate_execute_handoff（4.1 complex，缺 evidence_index）
    目的/目标：loop 单轨仍须 evidence_index
    验证点：errors 含 evidence_index
    失败含义：loop handoff 缺口会导致 AC 无法机械索引
    """
    (tmp_path / "task.json").write_text(
        json.dumps(
            {
                "meta": {
                    "plan_protocol_version": "4.1",
                    "task_track": "complex",
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "EXECUTION_INDEX.md").write_text("## 1.\n### 9.0 x\n| 已执行 | [x] |\n", encoding="utf-8")
    frozen = tmp_path / "frozen"
    frozen.mkdir()
    (frozen / "card.md").write_text("## 9.\n### 9.0 x\n| 已执行 | [x] |\n", encoding="utf-8")
    (tmp_path / "context_pack.json").write_text(
        json.dumps({"source_authorities": [], "tests": [], "modules": []}),
        encoding="utf-8",
    )
    (tmp_path / "loop_manifest.json").write_text(
        json.dumps({"acs": [], "modules": []}),
        encoding="utf-8",
    )
    errors = validate_execute_handoff(tmp_path, _REPO)
    assert any("evidence_index" in e for e in errors)


def test_parseV4ExecutedSteps_findsMarkedSteps() -> None:
    """覆盖范围：frozen §9 已执行解析
    测试对象：_parse_v4_executed_steps
    目的/目标：仅 [x] 的 9.x 进入解析列表
    验证点：9.0 勾选、9.1 未勾选 → ['9.0']
    失败含义：步骤与 handoff 脱节
    """
    text = "## 9.\n### 9.0 x\n| 已执行 | [x] |\n\n### 9.1 y\n| 已执行 | [ ] |\n"
    assert _parse_v4_executed_steps(text) == ["9.0"]
