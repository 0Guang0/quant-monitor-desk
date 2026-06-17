"""Validate complex-task plan freeze before ``task.py start``."""

from __future__ import annotations

import json
import re
from pathlib import Path


def _extract_section(text: str, header_prefix: str) -> str:
    """Return markdown from ``## {header_prefix}...`` until next ``## ``."""
    lines = text.splitlines()
    start: int | None = None
    end = len(lines)
    prefix = f"## {header_prefix}"
    for i, line in enumerate(lines):
        stripped = line.strip()
        if start is None and stripped.startswith(prefix):
            start = i
            continue
        if start is not None and stripped.startswith("## ") and not stripped.startswith(prefix):
            end = i
            break
    if start is None:
        return ""
    return "\n".join(lines[start:end])


def _first_jsonl_file(jsonl_path: Path) -> str | None:
    try:
        for line in jsonl_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            path = item.get("file") or item.get("path")
            if path:
                return str(path)
    except (json.JSONDecodeError, OSError):
        return None
    return None


def validate_plan_freeze(task_dir: Path, repo_root: Path) -> list[str]:
    """Return validation errors; empty list means pass."""
    _ = repo_root
    errors: list[str] = []
    master = task_dir / "MASTER.plan.md"
    if not master.is_file():
        return errors

    text = master.read_text(encoding="utf-8")
    placeholders = re.findall(r"\{\{[^}]+\}\}", text)
    if placeholders:
        uniq = sorted(set(placeholders))[:8]
        errors.append(f"MASTER.plan.md unresolved placeholders: {uniq}")

    section8 = _extract_section(text, "8.")
    if section8:
        legacy = "TDD 全文" in section8 or "legacy-execute-evidence" in text
        if not legacy:
            for label in ("RED 命令", "GREEN 命令", "RED 证据", "GREEN 证据"):
                if label not in section8:
                    errors.append(f"MASTER §8 missing column: {label}")
            test_defs = re.findall(r"def test_\w+", section8)
            if len(test_defs) > 2:
                errors.append(
                    f"MASTER §8 embeds {len(test_defs)} test functions; "
                    "move bodies to research/ (max 2 tracer examples in MASTER)"
                )
        else:
            if not list(task_dir.glob("research/*evidence*.md")):
                errors.append(
                    "Legacy MASTER §8 (TDD 全文): require research/*evidence*.md for Execute"
                )

    impl_jsonl = task_dir / "implement.jsonl"
    if impl_jsonl.is_file():
        first = _first_jsonl_file(impl_jsonl)
        if first and "MASTER.plan" not in first.replace("\\", "/"):
            errors.append(
                f"implement.jsonl first entry must be MASTER.plan.md (got {first!r})"
            )

    audit = task_dir / "AUDIT.plan.md"
    if audit.is_file():
        audit_text = audit.read_text(encoding="utf-8")
        if re.search(r"\{\{[^}]+\}\}", audit_text):
            errors.append("AUDIT.plan.md has unresolved {{placeholders}}")

    freeze = task_dir / "plan.freeze.md"
    if not freeze.is_file():
        errors.append("plan.freeze.md missing (required when MASTER.plan.md exists)")
    else:
        sec3 = _extract_section(freeze.read_text(encoding="utf-8"), "3.")
        if sec3 and re.search(r"- \[ \]", sec3):
            errors.append("plan.freeze.md §3 has unchecked items")

    return errors


def cmd_validate_plan_freeze(args) -> int:
    from .log import Colors, colored
    from .paths import get_repo_root
    from .task_utils import resolve_task_dir

    repo_root = get_repo_root()
    task_dir = resolve_task_dir(args.dir, repo_root)
    if not task_dir.is_dir():
        print(colored(f"Error: task not found: {args.dir}", Colors.RED))
        return 1

    errors = validate_plan_freeze(task_dir, repo_root)
    if errors:
        print(colored("Plan freeze validation FAILED:", Colors.RED))
        for err in errors:
            print(f"  - {err}")
        if getattr(args, "force", False):
            print(colored("Continuing due to --force", Colors.YELLOW))
            return 0
        return 1

    print(colored("Plan freeze validation passed", Colors.GREEN))
    return 0
