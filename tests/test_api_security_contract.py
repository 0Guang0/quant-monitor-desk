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


def test_loadApiLimits_queryBudgetNotOverriddenByLowerPriorityYaml(tmp_path, monkeypatch) -> None:
    import backend.app.core.api_limits as mod

    security = tmp_path / "api_security_contract.yaml"
    contract = tmp_path / "resource_limits_spec.yaml"
    configs_root = tmp_path / "configs"
    configs_root.mkdir()
    config = configs_root / "resource_limits.yaml"

    security.write_text(
        "query_budget:\n"
        "  default_page_size: 50\n"
        "  max_page_size_absolute: 500\n"
        "  frontend_table_default_page_size: 50\n"
        "  agent_tool_max_rows: 500\n",
        encoding="utf-8",
    )
    override_block = (
        "api_limits:\n"
        "  default_page_size: 999\n"
        "  max_page_size: 9999\n"
        "  agent_default_rows: 999\n"
        "  agent_max_rows: 9999\n"
        "  custom_limit: 42\n"
    )
    contract.write_text(override_block, encoding="utf-8")
    config.write_text(override_block, encoding="utf-8")

    monkeypatch.setattr(mod, "API_SECURITY_PATH", security)
    monkeypatch.setattr(mod, "CONTRACT_PATH", contract)
    monkeypatch.setattr(mod, "CONFIGS_ROOT", configs_root)

    limits = mod.load_api_limits()
    assert limits["default_page_size"] == 50
    assert limits["max_page_size"] == 500
    assert limits["agent_default_rows"] == 50
    assert limits["agent_max_rows"] == 500
    assert limits["custom_limit"] == 42
