"""Round2.6 Phase B — dependency extras contract tests."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXTRAS_CONTRACT = PROJECT_ROOT / "specs/contracts/dependency_extras_contract.yaml"
PYPROJECT = PROJECT_ROOT / "pyproject.toml"

FORBIDDEN_DEFAULT_PATTERNS = (
    r"\bqmt\b",
    r"\bxtquant\b",
    r"\bxqshare\b",
    r"browser_automation",
    r"external_agent_sdk",
)


def _load_contract() -> dict:
    return yaml.safe_load(EXTRAS_CONTRACT.read_text(encoding="utf-8")) or {}


def _default_dependencies_text() -> str:
    text = PYPROJECT.read_text(encoding="utf-8")
    match = re.search(r"dependencies\s*=\s*\[(.*?)\]", text, re.DOTALL)
    assert match, "pyproject.toml must declare [project] dependencies"
    return match.group(1)


def _optional_extra_block(extra_name: str) -> str:
    text = PYPROJECT.read_text(encoding="utf-8")
    pattern = rf"{extra_name}\s*=\s*\[(.*?)\]"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).lower() if match else ""


def test_defaultInstallHasNoQmtOrAgentExtras() -> None:
    contract = _load_contract()
    must_not = contract["extras"]["default"]["must_not_include"]
    deps_block = _default_dependencies_text().lower()
    for item in must_not:
        if re.search(rf"\b{re.escape(item.lower())}\b", deps_block):
            raise AssertionError(f"default dependencies must not include {item!r}")
    for pattern in FORBIDDEN_DEFAULT_PATTERNS:
        assert not re.search(pattern, deps_block), (
            f"forbidden pattern {pattern!r} found in default dependencies"
        )


def test_datasourcesExtra_doesNotIncludeQmtByDefault() -> None:
    contract = _load_contract()
    must_not = contract["extras"]["datasources"].get("must_not_include_by_default") or []
    default_deps = _default_dependencies_text().lower()
    datasources_extra = _optional_extra_block("datasources")
    for item in must_not:
        token = item.lower()
        assert token not in default_deps, f"{item!r} must not be in default dependencies"
        if datasources_extra:
            assert token not in datasources_extra, f"{item!r} must not be in datasources extra"


def test_agentExtra_disabledByDefault() -> None:
    contract = _load_contract()
    assert contract["extras"]["agent"]["enabled_by_default"] is False
    agent_block = _optional_extra_block("agent")
    assert agent_block == "", "agent optional extra must not be defined in pyproject.toml yet"
