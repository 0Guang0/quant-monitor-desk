#!/usr/bin/env python3
"""Print loop engineering task status for active complex tasks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loop_engineering_common import REPO_ROOT, load_json, loop_engineering_enabled

TASKS = REPO_ROOT / ".trellis/tasks"
LOOP_FILES = ("context_pack.json", "loop_manifest.json", "evidence_index.json", "audit_matrix.json")


def _row(task_dir: Path, *, strict: bool) -> tuple[str, str, str] | None:
    if not (task_dir / "MASTER.plan.md").is_file():
        return None
    if strict and not loop_engineering_enabled(task_dir) and not (
        task_dir / "research/context-router-output.md"
    ).is_file():
        return None
    status = str(load_json(task_dir / "task.json").get("status", "unknown"))
    missing = [name for name in LOOP_FILES if not (task_dir / name).is_file()]
    blocker = f"missing {', '.join(missing)}" if missing else "none"
    return task_dir.name, status, blocker


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when loop-engineering tasks have missing loop artifacts",
    )
    args = parser.parse_args()
    rows: list[tuple[str, str, str]] = []
    if TASKS.is_dir():
        for task_json in sorted(TASKS.rglob("task.json")):
            if "archive" in task_json.parts:
                continue
            item = _row(task_json.parent, strict=args.check)
            if item:
                rows.append(item)
    print(f"{'Task':42} {'Status':18} Blocker")
    for name, status, blocker in rows:
        print(f"{name:42} {status:18} {blocker}")
    if args.check and any(blocker != "none" for _, _, blocker in rows):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
