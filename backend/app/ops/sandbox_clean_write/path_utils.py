"""Shared path/time helpers for sandbox_clean_write orchestrators."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from backend.app.config import PROJECT_ROOT


def resolve_sandbox_path(path: Path | str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate.resolve()


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
