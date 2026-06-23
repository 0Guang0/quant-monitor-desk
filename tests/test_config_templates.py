"""Round 0 任务 002 — 配置模板与 eco 默认档位契约测试。

覆盖范围：.env.example 与 configs/resource_limits.yaml 相对 specs/contracts 的一致性。
"""

from __future__ import annotations

from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_envExample_defaultProfileIsEco_shouldUseLowResourceMode() -> None:
    """覆盖范围：.env.example 默认资源档位与密钥占位符
    测试对象：项目根 .env.example
    目的/目标：新环境默认 eco 低资源模式；敏感项仅占位、值为空
    验证点：含 QMD_RESOURCE_PROFILE=eco；QMT_PASSWORD 等密钥行值为空字符串
    失败含义：默认高资源或预填密钥会误导部署与安全审计
    """
    env_text = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")
    assert "QMD_RESOURCE_PROFILE=eco" in env_text
    for secret_key in ("QMT_PASSWORD=", "OPENAI_API_KEY=", "SMTP_PASSWORD="):
        assert secret_key in env_text
        line = next(line for line in env_text.splitlines() if line.startswith(secret_key))
        assert line.split("=", 1)[1] == "", f"secret placeholder must be empty: {secret_key}"


def test_resourceLimitsConfig_defaultProfileIsEco_shouldMatchContract() -> None:
    """覆盖范围：configs/resource_limits.yaml 与契约文件对齐
    测试对象：configs/resource_limits.yaml、specs/contracts/resource_limits.yaml
    目的/目标：运行时配置与 machine-readable 契约的 default_profile 及 eco 线程上限一致
    验证点：两侧 default_profile 均为 eco；profiles.eco.max_threads 相等
    失败含义：配置与契约分叉会导致 CI 契约门禁与运行时不一致
    """
    config_path = PROJECT_ROOT / "configs/resource_limits.yaml"
    contract_path = PROJECT_ROOT / "specs/contracts/resource_limits.yaml"
    with config_path.open(encoding="utf-8") as f:
        config = yaml.safe_load(f)
    with contract_path.open(encoding="utf-8") as f:
        contract = yaml.safe_load(f)
    assert config["default_profile"] == "eco"
    assert contract["default_profile"] == "eco"
    assert config["profiles"]["eco"]["max_threads"] == contract["profiles"]["eco"]["max_threads"]
