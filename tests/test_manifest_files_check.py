"""MANIFEST.json 文件存在性对抗性审计测试。

覆盖范围：MANIFEST.json 登记路径在磁盘上必须存在。
"""

from __future__ import annotations

import sys
from pathlib import Path

from tests.contract_gate_support import PROJECT_ROOT

SCRIPTS = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from check_manifest_files import check_manifest  # noqa: E402

MANIFEST = PROJECT_ROOT / "MANIFEST.json"


def test_checkManifest_allListedFilesExist() -> None:
    """覆盖范围：MANIFEST.json 全集存在性
    测试对象：check_manifest 全量 errors
    目的/目标：MANIFEST 与真实文件树一致，无幽灵登记项
    验证点：errors 为空
    失败含义：README/MANIFEST 与真实文件树不一致，文档闭合不可信
    """
    errors = check_manifest(MANIFEST)
    assert errors == [], f"manifest gaps: {errors}"
