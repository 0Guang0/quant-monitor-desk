"""Archive + legacy v3 path helpers (active code uses v4 only)."""

from __future__ import annotations

from pathlib import Path

LEGACY_V3_MSG = (
    "plan freeze/handoff requires protocol v4/v4.1 (EXECUTION_INDEX.md + frozen/); "
    "legacy MASTER tasks must live under .trellis/tasks/archive/"
)


def is_archived_task(task_dir: Path) -> bool:
    try:
        parts = task_dir.resolve().parts
        i = parts.index("tasks")
        return i + 1 < len(parts) and parts[i + 1] == "archive"
    except ValueError:
        return False


def has_task_plan_artifacts(task_dir: Path) -> bool:
    if (task_dir / "task.json").is_file():
        return True
    if (task_dir / "MASTER.plan.md").is_file():
        return True
    if (task_dir / "EXECUTION_INDEX.md").is_file():
        return True
    frozen = task_dir / "frozen"
    return frozen.is_dir() and any(frozen.glob("*.md"))


def is_legacy_v3_meta(meta: dict) -> bool:
    """Explicit v3 marker (plan or manifest protocol field)."""
    return str(meta.get("plan_protocol_version", "")).strip() == "3" or str(
        meta.get("manifest_protocol_version", "")
    ).strip() == "3"


def legacy_master_waived(task_dir: Path) -> bool:
    """Active MASTER allowed for explicit legacy v3 while planning or in_progress."""
    if is_archived_task(task_dir):
        return True
    if not (task_dir / "MASTER.plan.md").is_file():
        return False
    from .plan_protocol import load_task_json

    data = load_task_json(task_dir)
    meta = data.get("meta") or {}
    if not is_legacy_v3_meta(meta):
        return False
    return str(data.get("status", "")) in ("in_progress", "planning")


def is_active_legacy_v3(task_dir: Path) -> bool:
    if is_archived_task(task_dir):
        return False
    from .plan_protocol import is_plan_protocol_v4, load_task_json

    if is_plan_protocol_v4(task_dir):
        return False
    if (task_dir / "MASTER.plan.md").is_file():
        return True
    return is_legacy_v3_meta(load_task_json(task_dir).get("meta") or {})


def legacy_handoff_allowed(task_dir: Path) -> bool:
    """In-progress explicit v3 with MASTER may still handoff until migrated."""
    if not (task_dir / "MASTER.plan.md").is_file():
        return False
    if is_archived_task(task_dir):
        return True
    from .plan_protocol import load_task_json

    data = load_task_json(task_dir)
    return (
        is_legacy_v3_meta(data.get("meta") or {})
        and str(data.get("status", "")) == "in_progress"
    )


def legacy_freeze_error() -> str:
    return LEGACY_V3_MSG


def legacy_handoff_error() -> str:
    return LEGACY_V3_MSG
