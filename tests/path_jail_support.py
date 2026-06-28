"""Paths guaranteed outside PROJECT_ROOT for path-jail pytest (ponytail: one helper)."""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

from backend.app.config import PROJECT_ROOT


def path_outside_project_root(*, suffix: str = "outside") -> Path:
    """Return a fresh directory outside the repo tree (basetemp-safe)."""
    project = PROJECT_ROOT.resolve()
    root = Path(tempfile.gettempdir()).resolve() / f"qmd-outside-{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    if root.is_relative_to(project):
        raise RuntimeError(f"temp dir {root} unexpectedly under project {project}")
    return root / suffix
