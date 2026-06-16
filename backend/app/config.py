"""Application configuration loaded from environment and YAML."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = Path(os.getenv("QMD_DATA_ROOT", PROJECT_ROOT / "data"))
CONFIGS_ROOT = Path(os.getenv("QMD_CONFIGS_ROOT", PROJECT_ROOT / "configs"))

VALID_RESOURCE_PROFILES = frozenset({"eco", "normal", "batch"})


def get_resource_profile() -> str:
    profile = os.getenv("QMD_RESOURCE_PROFILE", "eco").strip().lower()
    if profile not in VALID_RESOURCE_PROFILES:
        raise ValueError(
            f"Invalid QMD_RESOURCE_PROFILE={profile!r}; "
            f"expected one of {sorted(VALID_RESOURCE_PROFILES)}"
        )
    return profile
