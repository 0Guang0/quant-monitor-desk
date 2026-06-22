"""对抗性审计：docs/specs 是否被 MIGRATION_MAP 与 authority_graph 索引。

覆盖范围：MIGRATION_MAP 全量索引、authority_graph 引用有效性。
测试对象：scripts/check_docs_specs_indexed.py。
目的：防止设计/契约文件成为导航黑洞。
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
    """覆盖：extract_migration_map_paths。
    对象：MIGRATION_MAP.md 中已登记的 docs/START_HERE.md。
    目的：路径抽取必须能识别表格内反引号路径。
    """
    paths = extract_migration_map_paths(MIGRATION_MAP)
    assert "docs/START_HERE.md" in paths


def test_migrationMapCoverage_coversUserInterventionPolicy() -> None:
    """覆盖：check_migration_map_coverage。
    对象：docs/ops/user_intervention_policy.md（loop 新增运维政策）。
    目的：MIGRATION_MAP 必须登记每一个 docs/specs 权威文件。
    """
    errors = check_migration_map_coverage()
    policy = "docs/ops/user_intervention_policy.md"
    assert policy not in {e.split(":", 1)[-1].strip() for e in errors if "missing from MIGRATION_MAP" in e} or errors == []


def test_migrationMapCoverage_noStaleReferences() -> None:
    """覆盖：check_migration_map_coverage stale 检测。
    对象：MIGRATION_MAP 登记路径与磁盘一致性。
    目的：地图不得引用已删除文件。
    """
    errors = check_migration_map_coverage()
    stale = [e for e in errors if e.startswith("stale MIGRATION_MAP ref:")]
    assert stale == [], f"stale refs: {stale}"


def test_authorityGraphRefs_allExistOnDisk() -> None:
    """覆盖：check_authority_graph_refs。
    对象：specs/context/authority_graph.yaml 登记路径。
    目的：模块路由图不得指向幽灵文档。
    """
    errors = check_authority_graph_refs()
    assert errors == [], f"authority graph broken refs: {errors}"


def test_migrationMapCoverage_returnsEmptyWhenComplete() -> None:
    """覆盖：check_migration_map_coverage 完整态。
    对象：当前仓库 docs/specs 全集。
    目的：修复后 CI gate 应无 missing 项（回归守门）。
    """
    errors = check_migration_map_coverage()
    missing = [e for e in errors if "missing from MIGRATION_MAP" in e]
    assert missing == [], f"still missing from MIGRATION_MAP: {missing}"
