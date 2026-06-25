#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Management Script.

Usage:
    python task.py create "<title>" [--slug <name>] [--assignee <dev>] [--priority P0|P1|P2|P3] [--parent <dir>] [--package <pkg>]
    python task.py add-context <dir> <file> <path> [reason] # Add jsonl entry
    python task.py validate <dir>              # Validate jsonl files
    python task.py validate-plan-freeze <dir>  # Plan freeze gate (complex tasks)
    python task.py validate-plan-phase <dir> <phase>  # Plan phase checkpoint (v2)
    python task.py validate-execute-handoff <dir>  # Execute §11 handoff gate
    python task.py validate-execute-boot <dir>  # Execute Phase 0 gate (E16 context-closure)
    python task.py validate-execute-step <dir> <step>  # Execute §8.x step gate
    python task.py suggest-implement-context <dir>  # Plan 5c manifest suggestions (E12)
    python task.py list-context <dir>          # List jsonl entries
    python task.py start <dir>                 # Set active task
    python task.py current [--source]          # Show active task
    python task.py finish                      # Clear active task
    python task.py set-branch <dir> <branch>   # Set git branch
    python task.py set-base-branch <dir> <branch>  # Set PR target branch
    python task.py set-scope <dir> <scope>     # Set scope for PR title
    python task.py archive <task-dir>          # Archive completed task
    python task.py list                        # List active tasks
    python task.py list-archive [month]        # List archived tasks
    python task.py add-subtask <parent-dir> <child-dir>     # Link child to parent
    python task.py remove-subtask <parent-dir> <child-dir>  # Unlink child from parent
    python task.py maintain [--fix]            # Loop repo maintenance (catalog + maps + graph gaps)
"""

from __future__ import annotations

import argparse
import sys

from common.log import Colors, colored
from common.paths import (
    DIR_WORKFLOW,
    DIR_TASKS,
    FILE_TASK_JSON,
    get_repo_root,
    get_developer,
    get_tasks_dir,
    get_current_task,
)
from common.active_task import (
    clear_active_task,
    resolve_active_task,
    resolve_context_key,
    set_active_task,
)
from common.io import read_json, write_json
from common.task_utils import resolve_task_dir, run_task_hooks
from common.tasks import iter_active_tasks, children_progress

# Import command handlers from split modules (also re-exports for plan.py compatibility)
from common.task_store import (
    cmd_create,
    cmd_archive,
    cmd_set_branch,
    cmd_set_base_branch,
    cmd_set_scope,
    cmd_add_subtask,
    cmd_remove_subtask,
)
from common.task_context import (
    cmd_add_context,
    cmd_validate,
    cmd_list_context,
)
from common.validate_plan_freeze import (
    cmd_validate_plan_freeze,
    cmd_validate_plan_phase,
    validate_plan_freeze,
)
from common.execution_index import cmd_freeze_task_card, cmd_generate_manifests
from common.validate_execute_handoff import (
    cmd_validate_execute_handoff,
    cmd_validate_execute_step,
)
from common.validate_execute_boot import cmd_validate_execute_boot
from common.manifest_commands import cmd_suggest_implement_context


def cmd_maintain(args: argparse.Namespace) -> int:
    """Run loop_maintain.py (catalog + generated maps + authority_graph gaps)."""
    import subprocess

    repo_root = get_repo_root()
    cmd = [sys.executable, str(repo_root / "scripts" / "loop_maintain.py")]
    if args.fix:
        cmd.append("--fix")
    proc = subprocess.run(cmd, cwd=repo_root)
    return int(proc.returncode or 0)

def cmd_start(args: argparse.Namespace) -> int:
    """Set active task."""
    repo_root = get_repo_root()
    task_input = args.dir

    if not task_input:
        print(colored("Error: task directory or name required", Colors.RED))
        return 1

    # Resolve task directory (supports task name, relative path, or absolute path)
    full_path = resolve_task_dir(task_input, repo_root)

    if not full_path.is_dir():
        print(colored(f"Error: Task not found: {task_input}", Colors.RED))
        print("Hint: Use task name (e.g., 'my-task') or full path (e.g., '.trellis/tasks/01-31-my-task')")
        return 1

    task_json_path = full_path / FILE_TASK_JSON
    task_data = read_json(task_json_path) if task_json_path.is_file() else None
    if (full_path / "MASTER.plan.md").is_file() and task_data and task_data.get("status") == "planning":
        freeze_errors = validate_plan_freeze(full_path, repo_root)
        if freeze_errors:
            print(colored("Plan freeze validation failed (task.py start blocked):", Colors.RED))
            for err in freeze_errors:
                print(f"  - {err}")
            if not getattr(args, "force", False):
                print(colored("Fix plan artifacts or pass --force to override.", Colors.YELLOW))
                return 1
            print(colored("Continuing with --force", Colors.YELLOW))

    # Convert to relative path for storage
    try:
        task_dir = full_path.relative_to(repo_root).as_posix()
    except ValueError:
        task_dir = str(full_path)

    if not resolve_context_key():
        # Degraded mode: no session identity available.
        # Hook didn't inject TRELLIS_CONTEXT_ID (common on Windows + Claude Code,
        # --continue resume path, fork distribution, hooks disabled, etc.). Skip
        # per-session pointer write; AI continues based on conversation context.
        print(colored(
            "ℹ Session identity not available; active-task pointer not persisted "
            "this session (degraded mode). AI continues based on conversation context.",
            Colors.YELLOW,
        ))
        print(colored(
            "Hint: run inside an AI IDE/session that exposes session identity, "
            "or set TRELLIS_CONTEXT_ID before running task.py start.",
            Colors.YELLOW,
        ))

        # Still flip task.json status: planning → in_progress so downstream phases proceed.
        if task_json_path.is_file():
            data = read_json(task_json_path)
            if data and data.get("status") == "planning":
                data["status"] = "in_progress"
                if write_json(task_json_path, data):
                    print(colored("✓ Status: planning → in_progress (degraded)", Colors.GREEN))
            run_task_hooks("after_start", task_json_path, repo_root)
        return 0

    active = set_active_task(task_dir, repo_root)
    if active:
        print(colored(f"✓ Current task set to: {task_dir}", Colors.GREEN))
        print(f"Source: {active.source}")

        if task_json_path.is_file():
            data = read_json(task_json_path)
            if data and data.get("status") == "planning":
                data["status"] = "in_progress"
                if write_json(task_json_path, data):
                    print(colored("✓ Status: planning → in_progress", Colors.GREEN))

        print()
        print(colored("The hook will now inject context from this task's jsonl files.", Colors.BLUE))

        run_task_hooks("after_start", task_json_path, repo_root)
        return 0
    else:
        print(colored("Error: Failed to set current task", Colors.RED))
        return 1


def cmd_finish(args: argparse.Namespace) -> int:
    """Clear active task."""
    repo_root = get_repo_root()
    active = clear_active_task(repo_root)
    current = active.task_path

    if not current:
        print(colored("No current task set", Colors.YELLOW))
        return 0

    # Resolve task.json path before clearing
    task_json_path = repo_root / current / FILE_TASK_JSON

    print(colored(f"✓ Cleared current task (was: {current})", Colors.GREEN))
    print(f"Source: {active.source}")

    if task_json_path.is_file():
        run_task_hooks("after_finish", task_json_path, repo_root)
    return 0


def cmd_current(args: argparse.Namespace) -> int:
    """Show active task."""
    repo_root = get_repo_root()
    active = resolve_active_task(repo_root)

    if args.source:
        print(f"Current task: {active.task_path or '(none)'}")
        print(f"Source: {active.source}")
        if active.stale:
            print("State: stale")
        return 0 if active.task_path else 1

    if active.task_path:
        print(active.task_path)
        return 0

    return 1


# =============================================================================
# Command: list
# =============================================================================

def cmd_list(args: argparse.Namespace) -> int:
    """List active tasks."""
    repo_root = get_repo_root()
    tasks_dir = get_tasks_dir(repo_root)
    current_task = get_current_task(repo_root)
    developer = get_developer(repo_root)
    filter_mine = args.mine
    filter_status = args.status

    if filter_mine:
        if not developer:
            print(colored("Error: No developer set. Run init_developer.py first", Colors.RED), file=sys.stderr)
            return 1
        print(colored(f"My tasks (assignee: {developer}):", Colors.BLUE))
    else:
        print(colored("All active tasks:", Colors.BLUE))
    print()

    # Single pass: collect all tasks via shared iterator
    all_tasks = {t.dir_name: t for t in iter_active_tasks(tasks_dir)}
    all_statuses = {name: t.status for name, t in all_tasks.items()}

    # Display tasks hierarchically
    count = 0

    def _print_task(dir_name: str, indent: int = 0) -> None:
        nonlocal count
        t = all_tasks[dir_name]

        # Apply --mine filter
        if filter_mine and (t.assignee or "-") != developer:
            return

        # Apply --status filter
        if filter_status and t.status != filter_status:
            return

        relative_path = f"{DIR_WORKFLOW}/{DIR_TASKS}/{dir_name}"
        marker = ""
        if relative_path == current_task:
            marker = f" {colored('<- current', Colors.GREEN)}"

        # Children progress
        progress = children_progress(t.children, all_statuses)

        # Package tag
        pkg_tag = f" @{t.package}" if t.package else ""

        prefix = "  " * indent + "  - "

        if filter_mine:
            print(f"{prefix}{dir_name}/ ({t.status}){pkg_tag}{progress}{marker}")
        else:
            print(f"{prefix}{dir_name}/ ({t.status}){pkg_tag}{progress} [{colored(t.assignee or '-', Colors.CYAN)}]{marker}")
        count += 1

        # Print children indented
        for child_name in t.children:
            if child_name in all_tasks:
                _print_task(child_name, indent + 1)

    # Display only top-level tasks (those without a parent)
    for dir_name in sorted(all_tasks.keys()):
        if not all_tasks[dir_name].parent:
            _print_task(dir_name)

    if count == 0:
        if filter_mine:
            print("  (no tasks assigned to you)")
        else:
            print("  (no active tasks)")

    print()
    print(f"Total: {count} task(s)")
    return 0


# =============================================================================
# Command: list-archive
# =============================================================================

def cmd_list_archive(args: argparse.Namespace) -> int:
    """List archived tasks."""
    repo_root = get_repo_root()
    tasks_dir = get_tasks_dir(repo_root)
    archive_dir = tasks_dir / "archive"
    month = args.month

    print(colored("Archived tasks:", Colors.BLUE))
    print()

    if month:
        month_dir = archive_dir / month
        if month_dir.is_dir():
            print(f"[{month}]")
            for d in sorted(month_dir.iterdir()):
                if d.is_dir():
                    print(f"  - {d.name}/")
        else:
            print(f"  No archives for {month}")
    else:
        if archive_dir.is_dir():
            for month_dir in sorted(archive_dir.iterdir()):
                if month_dir.is_dir():
                    month_name = month_dir.name
                    count = sum(1 for d in month_dir.iterdir() if d.is_dir())
                    print(f"[{month_name}] - {count} task(s)")

    return 0


# =============================================================================
# Help
# =============================================================================

def show_usage() -> None:
    """Show usage help."""
    print("""Task Management Script

Usage:
  python task.py create <title>                     Create new task directory
  python task.py create <title> --package <pkg>     Create task for a specific package
  python task.py create <title> --parent <dir>      Create task as child of parent
  python task.py add-context <dir> <jsonl> <path> [reason]  Add entry to jsonl
  python task.py validate <dir>                     Validate jsonl files
  python task.py list-context <dir>                 List jsonl entries
  python task.py start <dir>                        Set active task
  python task.py current [--source]                 Show active task
  python task.py finish                             Clear active task
  python task.py set-branch <dir> <branch>          Set git branch
  python task.py set-base-branch <dir> <branch>     Set PR target branch
  python task.py set-scope <dir> <scope>            Set scope for PR title
  python task.py archive <task-dir>                 Archive completed task
  python task.py add-subtask <parent> <child>       Link child task to parent
  python task.py remove-subtask <parent> <child>    Unlink child from parent
  python task.py list [--mine] [--status <status>]  List tasks
  python task.py list-archive [YYYY-MM]             List archived tasks

Monorepo options:
  --package <pkg>      Package name (validated against config.yaml packages)

List options:
  --mine, -m           Show only tasks assigned to current developer
  --status, -s <s>     Filter by status (planning, in_progress, review, completed)

Examples:
  python task.py create "Add login feature" --slug add-login
  python task.py create "Add login feature" --slug add-login --package cli
  python task.py create "Child task" --slug child --parent .trellis/tasks/01-21-parent
  python task.py add-context <dir> implement .trellis/spec/cli/backend/auth.md "Auth guidelines"
  python task.py set-branch <dir> task/add-login
  python task.py start .trellis/tasks/01-21-add-login
  python task.py current --source
  python task.py finish
  python task.py archive add-login
  python task.py add-subtask parent-task child-task  # Link existing tasks
  python task.py remove-subtask parent-task child-task
  python task.py list                               # List all active tasks
  python task.py list --mine                        # List my tasks only
  python task.py list --mine --status in_progress   # List my in-progress tasks
""")


# =============================================================================
# Main Entry
# =============================================================================

def main() -> int:
    """CLI entry point."""
    # Deprecation guard: `init-context` was removed in v0.5.0-beta.12.
    # Detect early so argparse doesn't mask the real reason with a generic
    # "invalid choice" error.
    if len(sys.argv) >= 2 and sys.argv[1] == "init-context":
        print(
            colored(
                "Error: `task.py init-context` was removed in v0.5.0-beta.12.",
                Colors.RED,
            ),
            file=sys.stderr,
        )
        print(
            "implement.jsonl / check.jsonl are now seeded on `task.py create` for",
            file=sys.stderr,
        )
        print(
            "sub-agent-capable platforms and curated by the AI during planning when needed.",
            file=sys.stderr,
        )
        print("See .trellis/workflow.md planning artifact guidance or run:", file=sys.stderr)
        print(
            "  python ./.trellis/scripts/get_context.py --mode phase --step 1",
            file=sys.stderr,
        )
        print(
            "Use `task.py add-context <dir> implement|check <path> <reason>` to append entries.",
            file=sys.stderr,
        )
        return 2

    parser = argparse.ArgumentParser(
        description="Task Management Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # create
    p_create = subparsers.add_parser("create", help="Create new task")
    p_create.add_argument("title", help="Task title")
    p_create.add_argument("--slug", "-s", help="Task slug")
    p_create.add_argument("--assignee", "-a", help="Assignee developer")
    p_create.add_argument("--priority", "-p", default="P2", help="Priority (P0-P3)")
    p_create.add_argument("--description", "-d", help="Task description")
    p_create.add_argument("--parent", help="Parent task directory (establishes subtask link)")
    p_create.add_argument("--package", help="Package name for monorepo projects")

    # add-context
    p_add = subparsers.add_parser("add-context", help="Add context entry")
    p_add.add_argument("dir", help="Task directory")
    p_add.add_argument("file", help="JSONL file (implement|check)")
    p_add.add_argument("path", help="File path to add")
    p_add.add_argument("reason", nargs="?", help="Reason for adding")

    # validate
    p_validate = subparsers.add_parser("validate", help="Validate context files")
    p_validate.add_argument("dir", help="Task directory")

    # list-context
    p_listctx = subparsers.add_parser("list-context", help="List context entries")
    p_listctx.add_argument("dir", help="Task directory")

    # validate-plan-freeze
    p_vfreeze = subparsers.add_parser(
        "validate-plan-freeze", help="Validate MASTER/AUDIT/plan.freeze before start"
    )
    p_vfreeze.add_argument("dir", help="Task directory")
    p_vfreeze.add_argument(
        "--force", action="store_true", help="Report errors but exit 0"
    )

    p_freeze_card = subparsers.add_parser(
        "freeze-task-card",
        help="Copy repo task card to frozen/ and regenerate jsonl manifests (v4)",
    )
    p_freeze_card.add_argument("dir", help="Task directory")
    p_freeze_card.add_argument(
        "--source",
        help="Repo-relative source task card path (default: task.json meta.source_task_card)",
    )

    p_gen_manifest = subparsers.add_parser(
        "generate-manifests",
        help="Regenerate implement/audit/check.jsonl from EXECUTION_INDEX.md (v4)",
    )
    p_gen_manifest.add_argument("dir", help="Task directory")

    # validate-plan-phase
    p_vphase = subparsers.add_parser(
        "validate-plan-phase",
        help="Validate one Plan phase checkpoint (protocol v2)",
    )
    p_vphase.add_argument("dir", help="Task directory")
    p_vphase.add_argument(
        "phase",
        help="Plan phase id: boot, 1a, 2a, 2b, 3, 3.5, 1b, 4, 5a, 5b, 5c, 5d",
    )

    # validate-execute-handoff
    p_vhandoff = subparsers.add_parser(
        "validate-execute-handoff", help="Validate Execute §11 handoff to Audit"
    )
    p_vhandoff.add_argument("dir", help="Task directory")

    # validate-execute-boot
    p_vboot = subparsers.add_parser(
        "validate-execute-boot", help="Validate Execute Phase 0 (E16 context-closure)"
    )
    p_vboot.add_argument("dir", help="Task directory")

    # suggest-implement-context
    p_suggest = subparsers.add_parser(
        "suggest-implement-context",
        help="Suggest missing implement.jsonl entries (Plan 5c, E12)",
    )
    p_suggest.add_argument("dir", help="Task directory")
    p_suggest.add_argument("--json", action="store_true", help="JSON output")

    # validate-execute-step
    p_vstep = subparsers.add_parser(
        "validate-execute-step",
        help="Validate one §8.x step RED/GREEN evidence (protocol v2)",
    )
    p_vstep.add_argument("dir", help="Task directory")
    p_vstep.add_argument("step", help="Step id e.g. 8.1")

    # start
    p_start = subparsers.add_parser("start", help="Set active task")
    p_start.add_argument("dir", help="Task directory")
    p_start.add_argument(
        "--force",
        action="store_true",
        help="Start despite plan freeze validation failures (complex tasks)",
    )

    # current
    p_current = subparsers.add_parser("current", help="Show active task")
    p_current.add_argument("--source", action="store_true",
                           help="Show active task source")

    # finish
    subparsers.add_parser("finish", help="Clear active task")

    # set-branch
    p_branch = subparsers.add_parser("set-branch", help="Set git branch")
    p_branch.add_argument("dir", help="Task directory")
    p_branch.add_argument("branch", help="Branch name")

    # set-base-branch
    p_base = subparsers.add_parser("set-base-branch", help="Set PR target branch")
    p_base.add_argument("dir", help="Task directory")
    p_base.add_argument("base_branch", help="Base branch name (PR target)")

    # set-scope
    p_scope = subparsers.add_parser("set-scope", help="Set scope")
    p_scope.add_argument("dir", help="Task directory")
    p_scope.add_argument("scope", help="Scope name")

    # archive
    p_archive = subparsers.add_parser("archive", help="Archive task")
    p_archive.add_argument("name", help="Task directory or name")
    p_archive.add_argument("--no-commit", action="store_true", help="Skip auto git commit after archive")

    # list
    p_list = subparsers.add_parser("list", help="List tasks")
    p_list.add_argument("--mine", "-m", action="store_true", help="My tasks only")
    p_list.add_argument("--status", "-s", help="Filter by status")

    # add-subtask
    p_addsub = subparsers.add_parser("add-subtask", help="Link child task to parent")
    p_addsub.add_argument("parent_dir", help="Parent task directory")
    p_addsub.add_argument("child_dir", help="Child task directory")

    # remove-subtask
    p_rmsub = subparsers.add_parser("remove-subtask", help="Unlink child task from parent")
    p_rmsub.add_argument("parent_dir", help="Parent task directory")
    p_rmsub.add_argument("child_dir", help="Child task directory")

    # list-archive
    p_listarch = subparsers.add_parser("list-archive", help="List archived tasks")
    p_listarch.add_argument("month", nargs="?", help="Month (YYYY-MM)")

    p_maintain = subparsers.add_parser(
        "maintain",
        help="Loop repo maintenance: test_catalog + generated maps + authority_graph gaps",
    )
    p_maintain.add_argument(
        "--fix",
        action="store_true",
        help="Write test_catalog.yaml and generated project/docs indexes",
    )

    args = parser.parse_args()

    if not args.command:
        show_usage()
        return 1

    commands = {
        "create": cmd_create,
        "add-context": cmd_add_context,
        "validate": cmd_validate,
        "validate-plan-freeze": cmd_validate_plan_freeze,
        "freeze-task-card": cmd_freeze_task_card,
        "generate-manifests": cmd_generate_manifests,
        "validate-plan-phase": cmd_validate_plan_phase,
        "validate-execute-handoff": cmd_validate_execute_handoff,
        "validate-execute-boot": cmd_validate_execute_boot,
        "validate-execute-step": cmd_validate_execute_step,
        "suggest-implement-context": cmd_suggest_implement_context,
        "list-context": cmd_list_context,
        "start": cmd_start,
        "current": cmd_current,
        "finish": cmd_finish,
        "set-branch": cmd_set_branch,
        "set-base-branch": cmd_set_base_branch,
        "set-scope": cmd_set_scope,
        "archive": cmd_archive,
        "add-subtask": cmd_add_subtask,
        "remove-subtask": cmd_remove_subtask,
        "list": cmd_list,
        "list-archive": cmd_list_archive,
        "maintain": cmd_maintain,
    }

    if args.command in commands:
        return commands[args.command](args)
    else:
        show_usage()
        return 1


if __name__ == "__main__":
    sys.exit(main())
