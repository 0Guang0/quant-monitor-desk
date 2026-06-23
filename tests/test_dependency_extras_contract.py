"""Round2.6 可选依赖 extras 契约：默认安装不得夹带重型/代理包。"""

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
    """覆盖范围：pyproject 默认 dependencies 与契约 must_not_include
    测试对象：[project].dependencies 文本块
    目的/目标：最小安装不应默认拉上 QMT、浏览器自动化或外部 agent SDK
    验证点：契约列出的 must_not 项及 FORBIDDEN_DEFAULT_PATTERNS 均不在 deps_block 中
    失败含义：用户 pip install 即装重型/闭源依赖，违背 extras 分层策略
    """
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
    """覆盖范围：datasources extra 与默认依赖的隔离
    测试对象：default dependencies 与 datasources optional extra
    目的/目标：QMT 等数据源包只能显式 extra 安装，不能混进默认或 datasources 块
    验证点：must_not_include_by_default 各项不在 default_deps，且若定义了 datasources extra 也不含
    失败含义：数据源重型依赖被默认拉起，CI 与无 QMT 环境无法轻量运行
    """
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
    """覆盖范围：agent optional extra 默认关闭
    测试对象：dependency_extras_contract.yaml 的 agent 段与 pyproject
    目的/目标：agent 能力尚未就绪时不应定义可选 extra 或默认启用
    验证点：enabled_by_default 为 False；pyproject 中无 agent extra 块
    失败含义：agent 依赖被误开，默认环境承担未验收的 SDK 面
    """
    contract = _load_contract()
    assert contract["extras"]["agent"]["enabled_by_default"] is False
    agent_block = _optional_extra_block("agent")
    assert agent_block == "", "agent optional extra must not be defined in pyproject.toml yet"
