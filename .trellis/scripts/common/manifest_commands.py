"""CLI commands for manifest protocol (suggest-implement-context)."""

from __future__ import annotations

import json
from pathlib import Path

from .manifest_protocol import suggest_implement_context


def cmd_suggest_implement_context(args) -> int:
    from .log import Colors, colored
    from .paths import get_repo_root
    from .task_utils import resolve_task_dir

    repo_root = get_repo_root()
    task_dir = resolve_task_dir(args.dir, repo_root)
    if not task_dir.is_dir():
        print(colored(f"Error: task not found: {args.dir}", Colors.RED))
        return 1

    suggestions = suggest_implement_context(task_dir, repo_root)
    if getattr(args, "json", False):
        print(json.dumps(suggestions, indent=2, ensure_ascii=False))
    else:
        if not suggestions:
            print(colored("No missing implement.jsonl entries suggested.", Colors.GREEN))
        else:
            print(colored(f"{len(suggestions)} suggested implement.jsonl entries:", Colors.YELLOW))
            for item in suggestions:
                print(f"  {item['file']}")
                print(f"    reason: {item['reason']}")
    return 0
