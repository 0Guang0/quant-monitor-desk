"""Resolve repo-relative paths after 2026-07-02 root / implementation_tasks archive."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_LEGACY_IMPL = (
    REPO_ROOT / "docs/implementation_tasks/archive/legacy-pre-module-v2-20260702"
)
_IMPL_ROOT = REPO_ROOT / "docs/implementation_tasks"

_ARCHIVED_IMPL_SINGLE_FILES = frozenset(
    {
        "PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md",
        "ROUND3_EARLY_CLOSE_PLAN.md",
        "BATCH_FOLDER_REHOME_PLAN.md",
    }
)

_ROOT_ARCHIVED_FILES = frozenset(
    {
        "ROUND3_BATCH_IMPLEMENTATION_MAP.md",
    }
)


def _is_archived_impl_suffix(suffix: str) -> bool:
    return suffix.startswith("ROUND_") or suffix in _ARCHIVED_IMPL_SINGLE_FILES


def resolve_repo_path(relative: str) -> Path:
    """Resolve repo-relative path; routes archived ROUND_* task trees."""
    rel = relative.replace("\\", "/")
    if rel in _ROOT_ARCHIVED_FILES:
        archived = ARCHIVE_LEGACY_IMPL / rel
        if archived.is_file():
            return archived
    if rel.startswith("docs/implementation_tasks/"):
        suffix = rel.removeprefix("docs/implementation_tasks/")
        if _is_archived_impl_suffix(suffix):
            archived = ARCHIVE_LEGACY_IMPL / suffix
            if archived.exists():
                return archived
    return REPO_ROOT / rel


def repo_path_exists(relative: str) -> bool:
    path = resolve_repo_path(relative)
    return path.is_file() or path.is_dir()
