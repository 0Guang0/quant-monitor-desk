"""全局执行规则文件存在性与任务 README 互引测试。

覆盖范围：Round 0 四份 GLOBAL_* 政策文件及 implementation_tasks/README 入口链接。
"""

from __future__ import annotations

import pytest

from tests.contract_gate_support import PROJECT_ROOT

REQUIRED_GLOBAL_FILES = [
    "docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md",
    "docs/implementation_tasks/GLOBAL_TESTING_POLICY.md",
    "docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md",
    "docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md",
]


@pytest.mark.parametrize("relative_path", REQUIRED_GLOBAL_FILES)
def test_globalRuleFile_exists_shouldBePresent(relative_path: str) -> None:
    """覆盖范围：Round 0 要求的四份全局规则文件
    测试对象：REQUIRED_GLOBAL_FILES 中 {relative_path}
    目的/目标：执行、测试、资源与任务模板政策文件必须存在且非空
    验证点：path.is_file() 且 read_text 去空白后长度 > 0
    失败含义：全局治理文档缺失，任务执行无统一约束可依
    """
    path = PROJECT_ROOT / relative_path
    assert path.is_file(), f"missing global rule file: {relative_path}"
    content = path.read_text(encoding="utf-8")
    assert len(content.strip()) > 0, f"empty global rule file: {relative_path}"


def test_implementationTasksReadme_referencesGlobalRules_shouldLinkExecutionOrder() -> None:
    """覆盖范围：implementation_tasks/README 与全局规则链接
    测试对象：docs/implementation_tasks/README.md
    目的/目标：任务入口 README 须引用 GLOBAL_EXECUTION_RULES 与 ROUND_0 脚手架任务
    验证点：readme 含 GLOBAL_EXECUTION_RULES.md 与 ROUND_0_PROJECT_SCAFFOLD
    失败含义：任务目录无法导向执行顺序与全局规则，onboarding 断档
    """
    readme = (PROJECT_ROOT / "docs/implementation_tasks/README.md").read_text(encoding="utf-8")
    assert "GLOBAL_EXECUTION_RULES.md" in readme
    assert "ROUND_0_PROJECT_SCAFFOLD" in readme
