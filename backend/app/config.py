"""Application configuration loaded from environment and YAML."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _path_env(name: str, default: Path) -> Path:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return Path(raw).expanduser()


DATA_ROOT = _path_env("QMD_DATA_ROOT", PROJECT_ROOT / "data")
CONFIGS_ROOT = _path_env("QMD_CONFIGS_ROOT", PROJECT_ROOT / "configs")

VALID_RESOURCE_PROFILES = frozenset({"eco", "normal", "batch"})


def get_resource_profile() -> str:
    profile = os.getenv("QMD_RESOURCE_PROFILE", "eco").strip().lower()
    if profile not in VALID_RESOURCE_PROFILES:
        raise ValueError(
            f"Invalid QMD_RESOURCE_PROFILE={profile!r}; "
            f"expected one of {sorted(VALID_RESOURCE_PROFILES)}"
        )
    return profile
