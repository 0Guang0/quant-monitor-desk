"""API and pagination limits from resource contract."""

from __future__ import annotations

import yaml
from backend.app.config import PROJECT_ROOT

CONFIGS_ROOT = PROJECT_ROOT / "configs"
CONTRACT_PATH = PROJECT_ROOT / "specs/contracts/resource_limits.yaml"
API_SECURITY_PATH = PROJECT_ROOT / "specs/contracts/api_security_contract.yaml"


def _int_api_limit_value(key: str, value: object) -> int | None:
    if key == "authority" or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    return None


def _query_budget_from_api_security() -> dict[str, int]:
    with API_SECURITY_PATH.open(encoding="utf-8") as f:
        security = yaml.safe_load(f) or {}
    budget = security.get("query_budget") or {}
    default_page = int(budget["default_page_size"])
    return {
        "default_page_size": default_page,
        "max_page_size": int(budget["max_page_size_absolute"]),
        "agent_default_rows": int(budget.get("frontend_table_default_page_size", default_page)),
        "agent_max_rows": int(budget["agent_tool_max_rows"]),
    }


QUERY_BUDGET_KEYS = frozenset(
    {"default_page_size", "max_page_size", "agent_default_rows", "agent_max_rows"}
)


def load_api_limits() -> dict[str, int]:
    """Load api_limits; query budget authority is api_security_contract.yaml."""
    limits = _query_budget_from_api_security()

    with CONTRACT_PATH.open(encoding="utf-8") as f:
        contract = yaml.safe_load(f) or {}
    for key, value in (contract.get("api_limits") or {}).items():
        if key in QUERY_BUDGET_KEYS:
            continue
        parsed = _int_api_limit_value(key, value)
        if parsed is not None:
            limits[key] = parsed

    config_path = CONFIGS_ROOT / "resource_limits.yaml"
    with config_path.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    for key, value in (cfg.get("api_limits") or {}).items():
        if key in QUERY_BUDGET_KEYS:
            continue
        parsed = _int_api_limit_value(key, value)
        if parsed is not None:
            limits[key] = parsed

    return limits


def clamp_page_size(page_size: int) -> int:
    limits = load_api_limits()
    default = limits.get("default_page_size", 200)
    maximum = limits.get("max_page_size", 1000)
    if page_size <= 0:
        return default
    return min(page_size, maximum)


def clamp_agent_rows(rows: int) -> tuple[int, bool]:
    limits = load_api_limits()
    default = limits.get("agent_default_rows", 200)
    maximum = limits.get("agent_max_rows", 1000)
    if rows <= 0:
        return default, False
    if rows > maximum:
        return maximum, True
    return rows, False
