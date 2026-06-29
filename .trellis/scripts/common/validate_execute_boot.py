"""Validate Execute Phase 0 boot (E16/E18)."""

from __future__ import annotations

from pathlib import Path

from .manifest_protocol import validate_execute_boot, validate_manifest_amend_chain
from .plan_protocol import is_plan_protocol_v4
from .task_archive import is_active_legacy_v3, is_archived_task, legacy_handoff_error


def validate_execute_boot_gate(task_dir: Path, repo_root: Path | None = None) -> list[str]:
    from .paths import get_repo_root

    if repo_root is None:
        repo_root = get_repo_root()

    if is_archived_task(task_dir):
        return []
    if is_active_legacy_v3(task_dir) and not is_plan_protocol_v4(task_dir):
        return [legacy_handoff_error()]
    if not is_plan_protocol_v4(task_dir):
        return []

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
