#!/usr/bin/env python3
"""Fail if active tasks have MASTER.plan.md without legacy v3 waiver."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TASKS = REPO_ROOT / ".trellis" / "tasks"


def _legacy_v3_meta(meta: dict) -> bool:
    return str(meta.get("plan_protocol_version", "")).strip() == "3" or str(
        meta.get("manifest_protocol_version", "")
    ).strip() == "3"


def _legacy_master_waived(task_dir: Path) -> bool:
    master = task_dir / "MASTER.plan.md"
    if not master.is_file():
        return False
    parts = task_dir.resolve().parts
    try:
        i = parts.index("tasks")
        if i + 1 < len(parts) and parts[i + 1] == "archive":
            return True
    except ValueError:
        pass
    task_json = task_dir / "task.json"
    if not task_json.is_file():
        return False
    try:
        data = json.loads(task_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    meta = data.get("meta") or {}
    if not _legacy_v3_meta(meta):
        return False
    return str(data.get("status", "")) in ("in_progress", "planning")


def _under_audit_sandbox(path: Path) -> bool:
    return ".audit-sandbox" in path.resolve().parts


def check_active_master_tasks() -> list[str]:
    errors: list[str] = []
    if not TASKS.is_dir():
        return errors
    for master in TASKS.rglob("MASTER.plan.md"):
        if _under_audit_sandbox(master):
            continue
        rel = master.relative_to(TASKS).as_posix()
        if rel.startswith("archive/"):
            continue
        if _legacy_master_waived(master.parent):
            continue
        errors.append(
            f"active task still has MASTER.plan.md: .trellis/tasks/{rel} "
            "(migrate to v4 EXECUTION_INDEX+frozen or move to tasks/archive/)"
        )
    return errors


def main() -> int:
    errors = check_active_master_tasks()
    if errors:
        print("active MASTER task check FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print("OK: no active MASTER.plan.md under .trellis/tasks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
