"""Tests for Trellis Execute protocol v2 validators."""

from __future__ import annotations

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
    (research / "execute-boot.md").write_text(
        "Phase 0 complete\nimplement.jsonl read in full\n", encoding="utf-8"
    )
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
    (ev / "8.0-boot-reads.txt").write_text("MASTER.plan.md | boot read entry\n", encoding="utf-8")
    for step in steps:
        (ev / f"{step}-red.txt").write_text(
            "exit 4\nERROR: ModuleNotFoundError\n", encoding="utf-8"
        )
        (ev / f"{step}-green.txt").write_text("8 passed\nexit 0\n", encoding="utf-8")


def test_validateExecuteStep_requiresFailSignal(tmp_path: Path) -> None:
    ev = tmp_path / "research" / "execute-evidence"
    ev.mkdir(parents=True)
    (ev / "8.1-red.txt").write_text("all good\n", encoding="utf-8")
    (ev / "8.1-green.txt").write_text("passed\n", encoding="utf-8")
    errors = validate_execute_step(tmp_path, "8.1")
    assert any("FAIL/ERROR" in e for e in errors)


def test_validateExecuteStep_passesWithEvidence(tmp_path: Path) -> None:
    ev = tmp_path / "research" / "execute-evidence"
    ev.mkdir(parents=True)
    (ev / "8.1-red.txt").write_text("ModuleNotFoundError\nexit 1\n", encoding="utf-8")
    (ev / "8.1-green.txt").write_text("1 passed\nexit 0\n", encoding="utf-8")
    assert validate_execute_step(tmp_path, "8.1") == []


def test_validateExecuteHandoff_failsWithoutBoot(tmp_path: Path) -> None:
    _write_master(tmp_path, ["8.0"])
    errors = validate_execute_handoff(tmp_path, _REPO)
    assert any("execute-boot" in e for e in errors)


def test_validateExecuteHandoff_passesWithFullArtifacts(tmp_path: Path) -> None:
    _write_master(tmp_path, ["8.0", "8.1"])
    _boot_artifacts(tmp_path, steps=["8.0", "8.1"])
    errors = validate_execute_handoff(tmp_path, _REPO)
    assert errors == []


def test_parseExecutedSteps_findsMarkedSteps() -> None:
    text = "### 8.0 x\n| 已执行 | [x] |\n\n### 8.1 y\n| 已执行 | [ ] |\n"
    assert _parse_executed_steps("## 8.\n" + text) == ["8.0"]


def test_validateExecuteHandoff_loopTaskRequiresEvidenceIndex(tmp_path: Path) -> None:
    """覆盖：validate_execute_handoff loop P3 门禁。
    对象：task_track=complex 且缺 evidence_index.json 的任务。
    目的：Execute handoff 必须校验 loop 证据链，不能只有 context_pack。
    """
    import json

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
