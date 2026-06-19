"""Repair-package API security contract alignment tests."""

from __future__ import annotations

from pathlib import Path

import yaml
from backend.app.core.api_limits import load_api_limits

PROJECT_ROOT = Path(__file__).resolve().parents[1]
API_SECURITY = PROJECT_ROOT / "specs/contracts/api_security_contract.yaml"
RESOURCE_LIMITS_SPEC = PROJECT_ROOT / "specs/contracts/resource_limits.yaml"
RESOURCE_LIMITS_CFG = PROJECT_ROOT / "configs/resource_limits.yaml"


def _query_budget(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("query_budget") or data.get("api_limits") or {}


def test_apiSecurityContract_isSingleAuthorityForQueryBudget() -> None:
    limits = load_api_limits()
    budget = _query_budget(API_SECURITY)
    assert limits["default_page_size"] == int(budget["default_page_size"])
    assert limits["max_page_size"] == int(budget["max_page_size_absolute"])
    assert limits["agent_max_rows"] == int(budget["agent_tool_max_rows"])


def test_resourceLimitsApiLimits_matchApiSecurityContract() -> None:
    spec = yaml.safe_load(RESOURCE_LIMITS_SPEC.read_text(encoding="utf-8")) or {}
    cfg = yaml.safe_load(RESOURCE_LIMITS_CFG.read_text(encoding="utf-8")) or {}
    budget = _query_budget(API_SECURITY)
    expected_max = int(budget["max_page_size_absolute"])
    assert spec["api_limits"]["authority"] == "specs/contracts/api_security_contract.yaml"
    assert int(spec["api_limits"]["max_page_size"]) == expected_max
    assert int(cfg["api_limits"]["max_page_size"]) == expected_max
