"""Verify global execution rule files exist (Round 0 task 000)."""

from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_GLOBAL_FILES = [
    "docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md",
    "docs/implementation_tasks/GLOBAL_TESTING_POLICY.md",
    "docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md",
    "docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md",
]


@pytest.mark.parametrize("relative_path", REQUIRED_GLOBAL_FILES)
def test_globalRuleFile_exists_shouldBePresent(relative_path: str) -> None:
    path = PROJECT_ROOT / relative_path
    assert path.is_file(), f"missing global rule file: {relative_path}"
    content = path.read_text(encoding="utf-8")
    assert len(content.strip()) > 0, f"empty global rule file: {relative_path}"


def test_implementationTasksReadme_referencesGlobalRules_shouldLinkExecutionOrder() -> None:
    readme = (PROJECT_ROOT / "docs/implementation_tasks/README.md").read_text(encoding="utf-8")
    assert "GLOBAL_EXECUTION_RULES.md" in readme
    assert "ROUND_0_PROJECT_SCAFFOLD" in readme
