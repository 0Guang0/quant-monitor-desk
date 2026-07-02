"""Stable paths for archived planning artifacts (root cleanup @ 2026-07-02)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_repo_path_resolve():
    mod_path = PROJECT_ROOT / "scripts" / "repo_path_resolve.py"
    spec = importlib.util.spec_from_file_location("repo_path_resolve", mod_path)
    if spec is None or spec.loader is None:
        raise ImportError(mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_rpr = _load_repo_path_resolve()
ARCHIVE_LEGACY_IMPL = _rpr.ARCHIVE_LEGACY_IMPL
REPO_ROOT = _rpr.REPO_ROOT
ROUND3_BATCH_IMPLEMENTATION_MAP = _rpr.resolve_repo_path("ROUND3_BATCH_IMPLEMENTATION_MAP.md")
_IMPL_ROOT = PROJECT_ROOT / "docs/implementation_tasks"


def impl_task(*parts: str) -> Path:
    """Resolve docs/implementation_tasks path; ROUND_* packages live in legacy archive."""
    rel = Path(*parts)
    archived = ARCHIVE_LEGACY_IMPL / rel
    active = _IMPL_ROOT / rel
    if archived.exists():
        return archived
    return active


def repo_relative(relative: str) -> Path:
    """Resolve repo-relative path; routes archived ROUND_* task trees."""
    return _rpr.resolve_repo_path(relative)
