"""Trellis Execute 协议 v2 校验器测试。

覆盖范围：validate_execute_step、validate_execute_handoff 与 _parse_executed_steps 的 RED/GREEN 证据门禁。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO / ".trellis" / "scripts"
sys.path.insert(0, str(_SCRIPTS))

from common.validate_execute_handoff import (  # noqa: E402
    _parse_executed_steps,
    validate_execute_handoff,
    validate_execute_step,
)


def _write_master(task_dir: Path, steps_done: list[str]) -> None:
    blocks = [f"### {step} step\n| 已执行 | [x] |\n" for step in steps_done]
    (task_dir / "MASTER.plan.md").write_text(
        "## 8. impl\n" + "\n".join(blocks) + "\n## 11. handoff\n- [x] done\n",
        encoding="utf-8",
    )


def _boot_artifacts(task_dir: Path, *, steps: list[str]) -> None:
    if not (task_dir / "task.json").is_file():
        (task_dir / "task.json").write_text(
            '{"meta":{"task_track":"simple"}}', encoding="utf-8"
        )
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
    """覆盖范围：单步 Execute RED 证据须含失败信号
    测试对象：validate_execute_step（8.1，RED 仅 all good）
    目的/目标：TDD RED 阶段必须留下 FAIL/ERROR 痕迹，禁止假 RED
    验证点：errors 中任一条含 FAIL/ERROR
    失败含义：无失败信号的 RED 会让 handoff 误判已走 TDD
    """
    ev = tmp_path / "research" / "execute-evidence"
    ev.mkdir(parents=True)
    (ev / "8.1-red.txt").write_text("all good\n", encoding="utf-8")
    (ev / "8.1-green.txt").write_text("passed\n", encoding="utf-8")
    errors = validate_execute_step(tmp_path, "8.1")
    assert any("FAIL/ERROR" in e for e in errors)


def test_validateExecuteStep_passesWithEvidence(tmp_path: Path) -> None:
    """覆盖范围：合规 RED/GREEN 证据的单步校验
    测试对象：validate_execute_step（8.1，含 ModuleNotFoundError 与 exit 码）
    目的/目标：标准 TDD 证据文件应零错误通过
    验证点：validate_execute_step(tmp_path, '8.1') == []
    失败含义：合法证据被拒会阻断 Execute 进度门禁
    """
    ev = tmp_path / "research" / "execute-evidence"
    ev.mkdir(parents=True)
    (ev / "8.1-red.txt").write_text("ModuleNotFoundError\nexit 1\n", encoding="utf-8")
    (ev / "8.1-green.txt").write_text("1 passed\nexit 0\n", encoding="utf-8")
    assert validate_execute_step(tmp_path, "8.1") == []


def test_validateExecuteHandoff_failsWithoutGitnexusSummary(tmp_path: Path) -> None:
    """覆盖范围：handoff 缺 gitnexus-execute-summary
    测试对象：validate_execute_handoff（仅 MASTER 已勾选 8.0）
    目的/目标：Execute handoff 必须要求 GitNexus 执行摘要
    验证点：errors 含 gitnexus-execute-summary
    失败含义：无摘要 handoff 会导致审计无法追溯影响面
    """
    _write_master(tmp_path, ["8.0"])
    errors = validate_execute_handoff(tmp_path, _REPO)
    assert any("gitnexus-execute-summary" in e for e in errors)


def test_validateExecuteHandoff_passesWithFullArtifacts(tmp_path: Path) -> None:
    """覆盖范围：完整 Execute 工件下的 handoff
    测试对象：validate_execute_handoff（MASTER + boot 工件 + 8.0/8.1 证据）
    目的/目标：simple 轨道任务齐备时应零错误 handoff
    验证点：errors == []
    失败含义：全量工件仍失败说明 handoff 规则回归
    """
    _write_master(tmp_path, ["8.0", "8.1"])
    _boot_artifacts(tmp_path, steps=["8.0", "8.1"])
    errors = validate_execute_handoff(tmp_path, _REPO)
    assert errors == []


def test_parseExecutedSteps_findsMarkedSteps() -> None:
    """覆盖范围：MASTER §8 已执行步骤解析
    测试对象：_parse_executed_steps
    目的/目标：仅 [x] 标记的步骤应进入已执行列表
    验证点：8.0 已勾选、8.1 未勾选时返回 ['8.0']
    失败含义：解析错误会导致 evidence 与 MASTER 勾选不一致
    """
    text = "### 8.0 x\n| 已执行 | [x] |\n\n### 8.1 y\n| 已执行 | [ ] |\n"
    assert _parse_executed_steps("## 8.\n" + text) == ["8.0"]


def test_validateExecuteHandoff_loopTaskRequiresEvidenceIndex(tmp_path: Path) -> None:
    """覆盖范围：complex 轨道 handoff 的 loop P3 证据链
    测试对象：validate_execute_handoff（task_track=complex，缺 evidence_index.json）
    目的/目标：仅有 context_pack/loop_manifest 不足，须 evidence_index
    验证点：errors 含 evidence_index
    失败含义：loop 单轨 handoff 缺口会导致 AC 证据无法机械索引
    """
    _write_master(tmp_path, ["8.0"])
    _boot_artifacts(tmp_path, steps=["8.0"])
    (tmp_path / "task.json").write_text(
        json.dumps({"meta": {"task_track": "complex"}, "status": "in_progress"}),
        encoding="utf-8",
    )
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
