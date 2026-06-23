"""docs/specs 索引完整性对抗性审计测试。

覆盖范围：MIGRATION_MAP 与 authority_graph 对 docs/specs 权威文件的登记与引用有效性。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from tests.contract_gate_support import PROJECT_ROOT

SCRIPTS = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from check_docs_specs_indexed import (  # noqa: E402
    check_authority_graph_refs,
    check_migration_map_coverage,
    extract_migration_map_paths,
)

MIGRATION_MAP = PROJECT_ROOT / "MIGRATION_MAP.md"


def test_extractMigrationMapPaths_includesKnownEntry() -> None:
    """覆盖范围：MIGRATION_MAP 路径抽取器
    测试对象：extract_migration_map_paths
    目的/目标：表格内反引号包裹的 docs 路径应被正确解析
    验证点：paths 含 docs/START_HERE.md
    失败含义：地图解析漏路径，coverage 检查会系统性误报或漏报
    """
    paths = extract_migration_map_paths(MIGRATION_MAP)
    assert "docs/START_HERE.md" in paths


def test_migrationMapCoverage_coversUserInterventionPolicy() -> None:
    """覆盖范围：运维政策文档的 MIGRATION_MAP 登记
    测试对象：check_migration_map_coverage 对 user_intervention_policy
    目的/目标：loop 新增的 docs/ops/user_intervention_policy.md 不得处于未索引状态
    验证点：errors 中无该文件的 missing from MIGRATION_MAP 项（或 errors 为空）
    失败含义：关键运维政策成为导航黑洞，agent 无法从地图发现
    """
    errors = check_migration_map_coverage()
    policy = "docs/ops/user_intervention_policy.md"
    assert policy not in {e.split(":", 1)[-1].strip() for e in errors if "missing from MIGRATION_MAP" in e} or errors == []


def test_migrationMapCoverage_noStaleReferences() -> None:
    """覆盖范围：MIGRATION_MAP 陈旧引用检测
    测试对象：check_migration_map_coverage 的 stale 类错误
    目的/目标：地图登记的路径在磁盘上必须仍存在
    验证点：以 stale MIGRATION_MAP ref: 开头的 errors 为空
    失败含义：地图指向已删文件，读者按图索骥得到断链
    """
    errors = check_migration_map_coverage()
    stale = [e for e in errors if e.startswith("stale MIGRATION_MAP ref:")]
    assert stale == [], f"stale refs: {stale}"


def test_authorityGraphRefs_allExistOnDisk() -> None:
    """覆盖范围：authority_graph.yaml 引用有效性
    测试对象：check_authority_graph_refs
    目的/目标：模块路由图登记的 docs/specs 路径必须真实存在
    验证点：errors == []
    失败含义：路由图含幽灵文档，context_router 与 loop 维护会指向空路径
    """
    errors = check_authority_graph_refs()
    assert errors == [], f"authority graph broken refs: {errors}"


def test_migrationMapCoverage_returnsEmptyWhenComplete() -> None:
    """覆盖范围：docs/specs 全集 coverage 完整态
    测试对象：check_migration_map_coverage 的 missing 项
    目的/目标：当前仓库所有权威 docs/specs 文件均应出现在 MIGRATION_MAP
    验证点：含 missing from MIGRATION_MAP 的 errors 为空
    失败含义：仍有未登记权威文件，CI docs 索引 gate 应红灯
    """
    errors = check_migration_map_coverage()
    missing = [e for e in errors if "missing from MIGRATION_MAP" in e]
    assert missing == [], f"still missing from MIGRATION_MAP: {missing}"
