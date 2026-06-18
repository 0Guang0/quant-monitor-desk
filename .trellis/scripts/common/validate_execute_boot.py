"""Validate Execute Phase 0 boot (E16/E17/E18)."""

from __future__ import annotations

from pathlib import Path

from .manifest_protocol import validate_execute_boot, validate_manifest_amend_chain


def validate_execute_boot_gate(task_dir: Path, repo_root: Path | None = None) -> list[str]:
    if repo_root is None:
        repo_root = task_dir
        while repo_root.name and not (repo_root / ".trellis").is_dir():
            if repo_root.parent == repo_root:
                break
            repo_root = repo_root.parent

    errors: list[str] = []
    validate_execute_boot(task_dir, errors)
    validate_manifest_amend_chain(task_dir, errors)
    return errors


def cmd_validate_execute_boot(args) -> int:
    from .log import Colors, colored
    from .paths import get_repo_root
    from .task_utils import resolve_task_dir

    repo_root = get_repo_root()
    task_dir = resolve_task_dir(args.dir, repo_root)
    if not task_dir.is_dir():
        print(colored(f"Error: task not found: {args.dir}", Colors.RED))
        return 1

    errors = validate_execute_boot_gate(task_dir, repo_root)
    if errors:
        print(colored("Execute boot validation FAILED:", Colors.RED))
        for err in errors:
            print(f"  - {err}")
        return 1

    print(colored("Execute boot validation passed", Colors.GREEN))
    return 0
