#!/usr/bin/env python3
"""Print loop engineering task status for active complex tasks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loop_engineering_common import REPO_ROOT, load_json, loop_required

TASKS = REPO_ROOT / ".trellis/tasks"
LOOP_FILES = ("context_pack.json", "loop_manifest.json", "evidence_index.json", "audit_matrix.json")


def _protocol_label(task_dir: Path) -> str:
    data = load_json(task_dir / "task.json") if (task_dir / "task.json").is_file() else {}
    meta = data.get("meta") or {}
    ver = str(meta.get("plan_protocol_version", "")).strip()
    if ver:
        return ver
    if (task_dir / "EXECUTION_INDEX.md").is_file() and any(
        (task_dir / "frozen").glob("*.md")
    ):
        return "4.1" if (task_dir / "research" / "00-EXECUTION-ENTRY.md").is_file() else "4"
    return "legacy"


def _row(task_dir: Path, *, strict: bool) -> tuple[str, str, str, str, str] | None:
    if not loop_required(task_dir):
        return None
    status = str(load_json(task_dir / "task.json").get("status", "unknown"))
    protocol = _protocol_label(task_dir)
    master = "yes" if (task_dir / "MASTER.plan.md").is_file() else "no"
    missing = [name for name in LOOP_FILES if not (task_dir / name).is_file()]
    blocker = f"missing {', '.join(missing)}" if missing else "none"
    return task_dir.name, status, protocol, master, blocker


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when loop-engineering tasks have missing loop artifacts",
    )
    args = parser.parse_args()
    rows: list[tuple[str, str, str, str, str]] = []
    if TASKS.is_dir():
        for task_json in sorted(TASKS.rglob("task.json")):
            if "archive" in task_json.parts:
                continue
            item = _row(task_json.parent, strict=args.check)
            if item:
                rows.append(item)
    print(f"{'Task':42} {'Status':18} {'Protocol':8} {'MASTER':6} Blocker")
    for name, status, protocol, master, blocker in rows:
        print(f"{name:42} {status:18} {protocol:8} {master:6} {blocker}")
    if args.check and any(blocker != "none" for _, _, blocker in rows):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
