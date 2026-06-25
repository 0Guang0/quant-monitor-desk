"""Plan protocol version helpers (v3 MASTER legacy · v4 frozen task card + EXECUTION_INDEX)."""

from __future__ import annotations

import json
from pathlib import Path


def load_task_json(task_dir: Path) -> dict:
    path = task_dir / "task.json"
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def plan_protocol_version(task_dir: Path) -> str:
    """Return '4' (frozen card + index) or '3' (MASTER legacy)."""
    meta = load_task_json(task_dir).get("meta") or {}
    explicit = str(meta.get("plan_protocol_version", "")).strip()
    if explicit in ("3", "4"):
        return explicit
    if (task_dir / "EXECUTION_INDEX.md").is_file() and any(
        (task_dir / "frozen").glob("*.md")
    ):
        return "4"
    if (task_dir / "MASTER.plan.md").is_file():
        return "3"
    return "4"


def frozen_task_card_path(task_dir: Path) -> Path | None:
    frozen_dir = task_dir / "frozen"
    if not frozen_dir.is_dir():
        return None
    cards = sorted(frozen_dir.glob("*.md"))
    return cards[0] if cards else None


def execution_index_path(task_dir: Path) -> Path:
    return task_dir / "EXECUTION_INDEX.md"


def execute_ssot_path(task_dir: Path) -> Path | None:
    """Primary Execute human SSOT: frozen task card (v4) or MASTER (v3)."""
    if plan_protocol_version(task_dir) == "4":
        return frozen_task_card_path(task_dir)
    master = task_dir / "MASTER.plan.md"
    return master if master.is_file() else None


def execute_ssot_rel(task_dir: Path, repo_root: Path) -> str | None:
    path = execute_ssot_path(task_dir)
    if not path or not path.is_file():
        return None
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.relative_to(task_dir).as_posix()


def execution_index_rel(task_dir: Path, repo_root: Path) -> str | None:
    path = execution_index_path(task_dir)
    if not path.is_file():
        return None
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return "EXECUTION_INDEX.md"
