"""资源限制运行时配置契约测试。

覆盖范围：configs/resource_limits.yaml 相对 specs/contracts 的一致性。
"""

from __future__ import annotations

from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


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
