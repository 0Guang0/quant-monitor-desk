"""Verify config templates and eco defaults (Round 0 task 002)."""

from __future__ import annotations

from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_envExample_defaultProfileIsEco_shouldUseLowResourceMode() -> None:
    env_text = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")
    assert "QMD_RESOURCE_PROFILE=eco" in env_text
    for secret_key in ("QMT_PASSWORD=", "OPENAI_API_KEY=", "SMTP_PASSWORD="):
        assert secret_key in env_text
        line = next(line for line in env_text.splitlines() if line.startswith(secret_key))
        assert line.split("=", 1)[1] == "", f"secret placeholder must be empty: {secret_key}"


def test_resourceLimitsConfig_defaultProfileIsEco_shouldMatchContract() -> None:
    config_path = PROJECT_ROOT / "configs/resource_limits.yaml"
    contract_path = PROJECT_ROOT / "specs/contracts/resource_limits.yaml"
    with config_path.open(encoding="utf-8") as f:
        config = yaml.safe_load(f)
    with contract_path.open(encoding="utf-8") as f:
        contract = yaml.safe_load(f)
    assert config["default_profile"] == "eco"
    assert contract["default_profile"] == "eco"
    assert config["profiles"]["eco"]["max_threads"] == contract["profiles"]["eco"]["max_threads"]
