"""全局执行规则文件存在性测试。

覆盖范围：根目录 rules/ 下全局治理政策文件。
"""

from __future__ import annotations

import pytest

from tests.contract_gate_support import PROJECT_ROOT

REQUIRED_GLOBAL_FILES = [
    "rules/GLOBAL_EXECUTION_RULES.md",
    "rules/GLOBAL_TESTING_POLICY.md",
    "rules/GLOBAL_RESOURCE_LIMITS.md",
    "rules/GLOBAL_RULES.md",
]


@pytest.mark.parametrize("relative_path", REQUIRED_GLOBAL_FILES)
def test_globalRuleFile_exists_shouldBePresent(relative_path: str) -> None:
    """覆盖范围：根 rules/ 目录要求的全局规则文件
    测试对象：REQUIRED_GLOBAL_FILES 中 {relative_path}
    目的/目标：执行、测试、资源与总规则政策文件必须存在且非空
    验证点：path.is_file() 且 read_text 去空白后长度 > 0
    失败含义：全局治理文档缺失，任务执行无统一约束可依
    """
    path = PROJECT_ROOT / relative_path
    assert path.is_file(), f"missing global rule file: {relative_path}"
    content = path.read_text(encoding="utf-8")
    assert len(content.strip()) > 0, f"empty global rule file: {relative_path}"


def test_globalRulesIndex_referencesExecutionBoundaries_shouldAnchorGovernance() -> None:
    """覆盖范围：rules/GLOBAL_RULES.md 作为治理入口
    测试对象：rules/GLOBAL_RULES.md
    目的/目标：总规则文件须包含执行边界等核心约束关键词
    验证点：readme 含「执行边界」与「DuckDBWriteManager」
    失败含义：rules/ 治理入口无法导向执行约束，onboarding 断档
    """
    rules = (PROJECT_ROOT / "rules/GLOBAL_RULES.md").read_text(encoding="utf-8")
    assert "执行边界" in rules
    assert "DuckDBWriteManager" in rules
