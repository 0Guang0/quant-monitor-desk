"""Tests for Trellis Plan protocol v2 validators."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO / ".trellis" / "scripts"
sys.path.insert(0, str(_SCRIPTS))

from common.validate_plan_freeze import (  # noqa: E402
    _load_plan_paths,
    validate_plan_freeze,
    validate_plan_phase,
)


def _minimal_master(task_dir: Path) -> None:
    task_card = (
        "015_implement_data_quality_validator.md + 016_implement_source_conflict_validator.md"
    )
    (task_dir / "MASTER.plan.md").write_text(
        f"## 0.\n原计划任务: {task_card}\n"
        "## 1.\n### 1.3 原计划归并\n"
        "## 8.\n### 8.0\n| RED 命令 | x |\n| GREEN 命令 | x |\n"
        "| RED 证据 | x |\n| GREEN 证据 | x |\n| 已执行 | [ ] |\n",
        encoding="utf-8",
    )
    (task_dir / "AUDIT.plan.md").write_text("# audit\nno placeholders\n", encoding="utf-8")
    dq_task = (
        "docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/"
        "015_implement_data_quality_validator.md"
    )
    sc_task = (
        "docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/"
        "016_implement_source_conflict_validator.md"
    )
    impl_lines = [
        '{"file": "MASTER.plan.md"}',
        '{"file": "docs/implementation_tasks/README.md"}',
        '{"file": "docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md"}',
        '{"file": "docs/implementation_tasks/GLOBAL_TESTING_POLICY.md"}',
        '{"file": "docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md"}',
        '{"file": "docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md"}',
        f'{{"file": "{dq_task}"}}',
        f'{{"file": "{sc_task}"}}',
    ]
    (task_dir / "implement.jsonl").write_text("\n".join(impl_lines) + "\n", encoding="utf-8")
    freeze = task_dir / "plan.freeze.md"
    freeze.write_text("## 3.\n### 3.0b 原计划包门禁\n- [x] all done\n", encoding="utf-8")


def _plan_boot_artifacts(task_dir: Path) -> None:
    research = task_dir / "research"
    research.mkdir(parents=True, exist_ok=True)
    (research / "plan-boot.md").write_text("原计划已读\nPhase P0 complete\n", encoding="utf-8")
    (research / "project-overview.md").write_text("# overview\n", encoding="utf-8")
    (research / "original-plan-trace.md").write_text(
        "# Original Plan Trace\n## 任务卡清单\n015\n016\n", encoding="utf-8"
    )
    (research / "gitnexus-summary.md").write_text("# summary\n", encoding="utf-8")
    (research / "grill-me-session.md").write_text("# grill\n", encoding="utf-8")
    (research / "plan-skill-reads.jsonl").write_text(
        "\n".join(
            [
                '{"phase":"boot","skill":"trellis-plan"}',
                '{"phase":"1a","skill":"gitnexus-plan-1a"}',
                '{"phase":"1b","skill":"gitnexus-plan-1b"}',
                '{"phase":"2a","skill":"trellis-brainstorm"}',
                '{"phase":"2b","skill":"spec-driven-development"}',
                '{"phase":"3","skill":"grill-me"}',
                '{"phase":"3.5","skill":"to-issues"}',
                '{"phase":"5a","skill":"planning-and-task-breakdown"}',
                '{"phase":"5b","skill":"writing-plans"}',
                '{"phase":"5c","skill":"trellis-before-dev"}',
                '{"phase":"5d","skill":"doubt-driven-development"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (task_dir / "prd.md").write_text("# prd\n", encoding="utf-8")


def test_validatePlanFreeze_failsWithoutBoot(tmp_path: Path) -> None:
    _minimal_master(tmp_path)
    errors = validate_plan_freeze(tmp_path, _REPO)
    assert any("plan-boot" in e for e in errors)


def test_validatePlanFreeze_failsWithoutOriginalPlanTrace(tmp_path: Path) -> None:
    _minimal_master(tmp_path)
    research = tmp_path / "research"
    research.mkdir()
    (research / "plan-boot.md").write_text("Phase P0 complete\n", encoding="utf-8")
    (research / "project-overview.md").write_text("# ov\n", encoding="utf-8")
    (research / "gitnexus-summary.md").write_text("# gnx\n", encoding="utf-8")
    (research / "plan-skill-reads.jsonl").write_text('{"skill":"trellis-plan"}\n', encoding="utf-8")
    errors = validate_plan_freeze(tmp_path, _REPO)
    assert any("original-plan-trace" in e for e in errors)


def test_validatePlanFreeze_doesNotRequireGlobalOriginalTaskRulesInImplementJsonl(tmp_path: Path) -> None:
    _minimal_master(tmp_path)
    (tmp_path / "implement.jsonl").write_text('{"file": "MASTER.plan.md"}\n', encoding="utf-8")
    _plan_boot_artifacts(tmp_path)
    errors = validate_plan_freeze(tmp_path, _REPO)
    assert not any("GLOBAL_EXECUTION_RULES" in e for e in errors)


def test_validatePlanFreeze_passesWithArtifacts(tmp_path: Path) -> None:
    _minimal_master(tmp_path)
    _plan_boot_artifacts(tmp_path)
    errors = validate_plan_freeze(tmp_path, _REPO)
    assert errors == []


def test_validatePlanPhase_1b_requiresSummary(tmp_path: Path) -> None:
    research = tmp_path / "research"
    research.mkdir()
    (research / "plan-skill-reads.jsonl").write_text(
        '{"skill":"gitnexus-plan-1b"}\n', encoding="utf-8"
    )
    errors = validate_plan_phase(tmp_path, "1b", repo_root=_REPO)
    assert any("gitnexus-summary" in e for e in errors)


def test_validatePlanPhase_1b_passes(tmp_path: Path) -> None:
    research = tmp_path / "research"
    research.mkdir()
    (research / "gitnexus-summary.md").write_text("# ok\n", encoding="utf-8")
    (research / "plan-skill-reads.jsonl").write_text(
        '{"skill":"gitnexus-plan-1b"}\n', encoding="utf-8"
    )
    assert validate_plan_phase(tmp_path, "1b", repo_root=_REPO) == []


def test_validatePlanPhase_boot_requiresMarker(tmp_path: Path) -> None:
    research = tmp_path / "research"
    research.mkdir()
    (research / "plan-boot.md").write_text("incomplete\n", encoding="utf-8")
    (research / "plan-skill-reads.jsonl").write_text('{"skill":"trellis-plan"}\n', encoding="utf-8")
    errors = validate_plan_phase(tmp_path, "boot", repo_root=_REPO)
    assert any("Phase P0 complete" in e for e in errors)


def test_loadPlanPaths_parsesPhases() -> None:
    cfg = _load_plan_paths(_REPO)
    assert "1a" in cfg.get("phases", {})
    assert "1b" in cfg.get("phases", {})
    assert "gitnexus-plan-1a" in cfg.get("freeze_required_skills", [])
    assert "gitnexus-plan-1b" in cfg.get("freeze_required_skills", [])
