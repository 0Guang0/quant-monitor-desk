"""Plan protocol v4/v4.1 helpers; v3 is archive-only legacy."""

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
    """Return '4.1', '4' (frozen card + index), or '3' (legacy / simple default)."""
    meta = load_task_json(task_dir).get("meta") or {}
    explicit = str(meta.get("plan_protocol_version", "")).strip()
    if explicit == "3":
        return "3"
    if explicit == "4.1":
        return "4.1"
    if explicit == "4":
        return "4"
    if (task_dir / "EXECUTION_INDEX.md").is_file() and any(
        (task_dir / "frozen").glob("*.md")
    ):
        entry = task_dir / "research" / "00-EXECUTION-ENTRY.md"
        if entry.is_file():
            return "4.1"
        return "4"
    return "3"


def is_plan_protocol_v4(task_dir: Path) -> bool:
    return plan_protocol_version(task_dir) in ("4", "4.1")


def is_execution_bundle_v41(task_dir: Path) -> bool:
    return plan_protocol_version(task_dir) == "4.1"


def execution_entry_rel(task_dir: Path, repo_root: Path) -> str | None:
    """v4.1 Execute bundle entry path (repo-relative)."""
    meta = load_task_json(task_dir).get("meta") or {}
    rel = str(meta.get("execute_entry", "")).strip() or "research/00-EXECUTION-ENTRY.md"
    path = task_dir / rel
    if not path.is_file():
        return None
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return rel.replace("\\", "/")


def plan_freeze_required_before_start(task_dir: Path) -> bool:
    """Whether task.py start must pass validate_plan_freeze while status=planning."""
    from .task_archive import is_active_legacy_v3, is_archived_task

    if is_archived_task(task_dir):
        return False
    if is_plan_protocol_v4(task_dir) and (task_dir / "EXECUTION_INDEX.md").is_file():
        return True
    return is_active_legacy_v3(task_dir)


def frozen_task_card_path(task_dir: Path) -> Path | None:
    meta = load_task_json(task_dir).get("meta") or {}
    rel = str(meta.get("frozen_task_card", "")).strip()
    if rel:
        card = task_dir / rel.replace("\\", "/")
        if card.is_file():
            return card
    frozen_dir = task_dir / "frozen"
    if not frozen_dir.is_dir():
        return None
    cards = sorted(frozen_dir.glob("*.md"))
    return cards[0] if cards else None


def execution_index_path(task_dir: Path) -> Path:
    return task_dir / "EXECUTION_INDEX.md"


def execute_ssot_path(task_dir: Path) -> Path | None:
    """Primary Execute human SSOT: frozen task card (v4/v4.1)."""
    if is_plan_protocol_v4(task_dir):
        return frozen_task_card_path(task_dir)
    return None


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
