"""Tests for Trellis Plan protocol v2 validators."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO / ".trellis" / "scripts"


def _load_plan_validate():
    path = _SCRIPTS / "common" / "validate_plan_freeze.py"
    spec = importlib.util.spec_from_file_location("validate_plan_freeze", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.path.insert(0, str(_SCRIPTS))
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.pop(0)
    return mod


plan_val = _load_plan_validate()


def _minimal_master(task_dir: Path) -> None:
    (task_dir / "MASTER.plan.md").write_text(
        "## 8.\n### 8.0\n| RED 命令 | x |\n| GREEN 命令 | x |\n"
        "| RED 证据 | x |\n| GREEN 证据 | x |\n| 已执行 | [ ] |\n",
        encoding="utf-8",
    )
    (task_dir / "AUDIT.plan.md").write_text("# audit\nno placeholders\n", encoding="utf-8")
    (task_dir / "implement.jsonl").write_text(
        '{"file": "MASTER.plan.md"}\n', encoding="utf-8"
    )
    freeze = task_dir / "plan.freeze.md"
    freeze.write_text("## 3.\n- [x] all done\n", encoding="utf-8")


def _plan_boot_artifacts(task_dir: Path) -> None:
    research = task_dir / "research"
    research.mkdir(parents=True, exist_ok=True)
    (research / "plan-boot.md").write_text("Phase P0 complete\n", encoding="utf-8")
    (research / "gitnexus-summary.md").write_text("# summary\n", encoding="utf-8")
    (research / "grill-me-session.md").write_text("# grill\n", encoding="utf-8")
    (research / "plan-skill-reads.jsonl").write_text(
        "\n".join(
            [
                '{"phase":"boot","skill":"trellis-plan"}',
                '{"phase":"P1","skill":"gitnexus-plan"}',
                '{"phase":"2a","skill":"trellis-brainstorm"}',
                '{"phase":"2b","skill":"spec-driven-development"}',
                '{"phase":"3","skill":"grill-me"}',
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
    errors = plan_val.validate_plan_freeze(tmp_path, _REPO)
    assert any("plan-boot" in e for e in errors)


def test_validatePlanFreeze_passesWithArtifacts(tmp_path: Path) -> None:
    _minimal_master(tmp_path)
    _plan_boot_artifacts(tmp_path)
    errors = plan_val.validate_plan_freeze(tmp_path, _REPO)
    assert errors == []


def test_validatePlanPhase_P1_requiresSummary(tmp_path: Path) -> None:
    research = tmp_path / "research"
    research.mkdir()
    (research / "plan-skill-reads.jsonl").write_text(
        '{"skill":"gitnexus-plan"}\n', encoding="utf-8"
    )
    errors = plan_val.validate_plan_phase(tmp_path, "P1", repo_root=_REPO)
    assert any("gitnexus-summary" in e for e in errors)


def test_validatePlanPhase_P1_passes(tmp_path: Path) -> None:
    research = tmp_path / "research"
    research.mkdir()
    (research / "gitnexus-summary.md").write_text("# ok\n", encoding="utf-8")
    (research / "plan-skill-reads.jsonl").write_text(
        '{"skill":"gitnexus-plan"}\n', encoding="utf-8"
    )
    assert plan_val.validate_plan_phase(tmp_path, "P1", repo_root=_REPO) == []


def test_validatePlanPhase_boot_requiresMarker(tmp_path: Path) -> None:
    research = tmp_path / "research"
    research.mkdir()
    (research / "plan-boot.md").write_text("incomplete\n", encoding="utf-8")
    (research / "plan-skill-reads.jsonl").write_text(
        '{"skill":"trellis-plan"}\n', encoding="utf-8"
    )
    errors = plan_val.validate_plan_phase(tmp_path, "boot", repo_root=_REPO)
    assert any("Phase P0 complete" in e for e in errors)


def test_loadPlanPaths_parsesPhases() -> None:
    cfg = plan_val._load_plan_paths(_REPO)
    assert "P1" in cfg.get("phases", {})
    assert "trellis-plan" in cfg.get("freeze_required_skills", [])
