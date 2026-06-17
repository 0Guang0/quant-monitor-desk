"""Validate Execute handoff to Audit (§11 DoD)."""

from __future__ import annotations

import re
from pathlib import Path


def validate_execute_handoff(task_dir: Path) -> list[str]:
    errors: list[str] = []
    master = task_dir / "MASTER.plan.md"
    if not master.is_file():
        return errors

    evidence_md = list(task_dir.glob("research/*evidence*.md"))
    evidence_dir = task_dir / "research" / "execute-evidence"
    if not evidence_md and not evidence_dir.is_dir():
        errors.append(
            "Missing Execute evidence: research/*evidence*.md or research/execute-evidence/"
        )

    skill_eval = task_dir / "research" / "execute-skill-evaluation.md"
    if not skill_eval.is_file():
        errors.append("Missing research/execute-skill-evaluation.md (§12 skill evaluation)")

    text = master.read_text(encoding="utf-8")
    sec12_match = re.search(r"## 12\.[\s\S]*?(?=\n## |\Z)", text)
    if sec12_match:
        sec12 = sec12_match.group(0)
        for skill in (
            "test-driven-development",
            "incremental-implementation",
            "trellis-implement",
        ):
            row = re.search(rf"\|\s*{re.escape(skill)}\s*\|[^\n]+\|", sec12)
            if row and "[x]" not in row.group(0) and "不用" not in row.group(0):
                if "| 必做 |" in row.group(0) or "|必做|" in row.group(0):
                    errors.append(f"MASTER §12 '{skill}' 必做行未勾选 [x]")

    sec11 = re.search(r"## 11\.[\s\S]*?(?=\n## |\Z)", text)
    if sec11 and re.search(r"- \[ \]", sec11.group(0)):
        errors.append("MASTER §11 DoD has unchecked items")

    return errors


def cmd_validate_execute_handoff(args) -> int:
    from .log import Colors, colored
    from .paths import get_repo_root
    from .task_utils import resolve_task_dir

    repo_root = get_repo_root()
    task_dir = resolve_task_dir(args.dir, repo_root)
    if not task_dir.is_dir():
        print(colored(f"Error: task not found: {args.dir}", Colors.RED))
        return 1

    errors = validate_execute_handoff(task_dir)
    if errors:
        print(colored("Execute handoff validation FAILED:", Colors.RED))
        for err in errors:
            print(f"  - {err}")
        return 1

    print(colored("Execute handoff validation passed", Colors.GREEN))
    return 0
