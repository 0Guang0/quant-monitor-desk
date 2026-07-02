"""docs/INDEX.md 导航链接完整性与关键入口登记测试。"""

from __future__ import annotations

import re

from tests.contract_gate_support import PROJECT_ROOT
from tests.repo_paths import repo_relative

INDEX_PATH = PROJECT_ROOT / "docs/INDEX.md"
LINK_PATTERN = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def _is_external(link: str) -> bool:
    lowered = link.lower()
    return (
        lowered.startswith("http://")
        or lowered.startswith("https://")
        or lowered.startswith("mailto:")
        or link.startswith("#")
    )


def test_docsIndex_linksArchitectureAndTasks_shouldBeNavigable() -> None:
    """覆盖范围：INDEX.md 核心文档入口
    测试对象：docs/INDEX.md 文本内容
    目的/目标：索引须链到项目概览、任务 README 与全局执行规则
    验证点：含 00_project_overview.md、implementation_tasks/README.md、GLOBAL_EXECUTION_RULES.md
    失败含义：新人无法从索引进入架构与任务体系，导航断链
    """
    index = INDEX_PATH.read_text(encoding="utf-8")
    assert "00_project_overview.md" in index
    assert "implementation_tasks/README.md" in index
    assert "GLOBAL_EXECUTION_RULES.md" in index


def test_docsIndex_linksMigrationMap_shouldCrossReferenceRootMap() -> None:
    """覆盖范围：INDEX 与根目录 MIGRATION_MAP 互引
    测试对象：docs/INDEX.md
    目的/目标：文档索引应指向仓库根 MIGRATION_MAP 作为迁移导航
    验证点：索引文本含 MIGRATION_MAP.md
    失败含义：文档树与迁移地图脱节，找不到权威路径对照
    """
    index = INDEX_PATH.read_text(encoding="utf-8")
    assert "MIGRATION_MAP.md" in index


def test_docsIndex_relativeLinks_resolveToExistingFiles() -> None:
    """覆盖范围：INDEX.md 全部相对链接可达性
    测试对象：INDEX 内 markdown 链接解析结果
    目的/目标：站内相对链接必须指向磁盘上真实存在的文件
    验证点：遍历非外链、非锚点链接，broken 列表为空
    失败含义：索引展示可点链接但目标缺失，文档导航产生 404 式断链
    """
    index = INDEX_PATH.read_text(encoding="utf-8")
    broken: list[str] = []
    for match in LINK_PATTERN.finditer(index):
        link = match.group(1).strip()
        if not link or _is_external(link):
            continue
        path_part = link.split("#", 1)[0]
        if not path_part:
            continue
        if path_part.startswith("../"):
            target = (INDEX_PATH.parent / path_part).resolve()
        else:
            target = repo_relative(f"docs/{path_part}")
        if not target.exists():
            broken.append(link)
    assert not broken, f"broken INDEX.md links: {broken}"
