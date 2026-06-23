"""项目脚手架目录与 init_db 最小引导测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DIRS = [
    "backend/app/api",
    "backend/app/db",
    "backend/app/layer1_axes",
    "backend/app/layer3_chains",
    "backend/app/agents",
    "frontend/src",
    "scripts",
    "tests",
    "configs",
    "docs/architecture",
    "specs/schema",
    "specs/contracts",
]


@pytest.mark.parametrize("relative_dir", REQUIRED_DIRS)
def test_scaffoldDirectory_exists_shouldBePresent(relative_dir: str) -> None:
    """覆盖范围：Round 0 约定的仓库目录骨架
    测试对象：REQUIRED_DIRS 中 {relative_dir}
    目的/目标：后端分层、前端、脚本、测试与 specs 目录必须已创建
    验证点：(PROJECT_ROOT / relative_dir).is_dir()
    失败含义：脚手架缺目录，后续任务无约定落点
    """
    assert (PROJECT_ROOT / relative_dir).is_dir(), f"missing directory: {relative_dir}"


def test_migrationMap_exists_shouldGuideNavigation() -> None:
    """覆盖范围：根目录 MIGRATION_MAP.md 内容与结构
    测试对象：MIGRATION_MAP.md
    目的/目标：迁移地图应描述五层模型并指向架构文档与 MANIFEST
    验证点：含「五层模型」、docs/architecture 或 docs/modules、MANIFEST.json
    失败含义：导航地图空壳或缺关键锚点，文档迁移无法对照
    """
    content = (PROJECT_ROOT / "MIGRATION_MAP.md").read_text(encoding="utf-8")
    assert "五层模型" in content
    assert "docs/architecture/" in content or "docs/modules/" in content
    assert "MANIFEST.json" in content


def test_initDb_createsDuckDbDirectory(tmp_path, monkeypatch) -> None:
    """覆盖范围：scripts/init_db 初始化数据目录
    测试对象：init_db.main 与 DATA_ROOT
    目的/目标：init_db 应在 data_root 下创建 duckdb 子目录及 quant_monitor.duckdb
    验证点：duckdb/ 为目录；quant_monitor.duckdb 为文件
    失败含义：一键建库脚本失败，本地/CI 无法获得默认 DuckDB 路径
    """
    import scripts.init_db as init_db_mod

    data_root = tmp_path / "data"
    monkeypatch.setattr(init_db_mod, "DATA_ROOT", data_root)
    init_db_mod.main([])
    assert (data_root / "duckdb").is_dir()
    assert (data_root / "duckdb" / "quant_monitor.duckdb").is_file()
