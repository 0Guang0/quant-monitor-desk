"""Application configuration loaded from environment and YAML."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_dotenv_if_present() -> None:
    """Load PROJECT_ROOT/.env into os.environ without overriding existing vars."""
    env_path = PROJECT_ROOT / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = value.strip().strip('"').strip("'")


_load_dotenv_if_present()


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
