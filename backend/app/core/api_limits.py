"""API and pagination limits from resource contract."""

from __future__ import annotations

import yaml
from backend.app.config import PROJECT_ROOT

CONFIGS_ROOT = PROJECT_ROOT / "configs"
CONTRACT_PATH = PROJECT_ROOT / "specs/contracts/resource_limits.yaml"


def load_api_limits() -> dict[str, int]:
    """Load api_limits with contract fallback for missing config keys."""
    config_path = CONFIGS_ROOT / "resource_limits.yaml"
    with config_path.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    with CONTRACT_PATH.open(encoding="utf-8") as f:
        contract = yaml.safe_load(f) or {}
    limits = dict(contract.get("api_limits", {}))
    limits.update(cfg.get("api_limits", {}))
    return {key: int(value) for key, value in limits.items()}


def clamp_page_size(page_size: int) -> int:
    limits = load_api_limits()
    default = limits.get("default_page_size", 100)
    maximum = limits.get("max_page_size", 500)
    if page_size <= 0:
        return default
    return min(page_size, maximum)


def clamp_agent_rows(rows: int) -> tuple[int, bool]:
    limits = load_api_limits()
    default = limits.get("agent_default_rows", 100)
    maximum = limits.get("agent_max_rows", 500)
    if rows <= 0:
        return default, False
    if rows > maximum:
        return maximum, True
    return rows, False
