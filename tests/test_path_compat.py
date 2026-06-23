"""Windows 超长路径兼容（extended path）读写测试。"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from backend.app.storage.path_compat import (
    is_file,
    needs_extended_path,
    to_extended_path,
    write_bytes,
)


def test_needsExtendedPath_shortPath_false(tmp_path: Path) -> None:
    """覆盖范围：常规短路径不需 extended 前缀
    测试对象：needs_extended_path
    目的/目标：未超 MAX_PATH 的 tmp_path 应返回 False
    验证点：needs_extended_path(tmp_path) is False（仅 Windows）
    失败含义：短路径误走 extended 长路径前缀，非 Windows 或浅目录行为异常
    """
    if os.name != "nt":
        pytest.skip("Windows-only")
    assert needs_extended_path(tmp_path) is False


def test_toExtendedPath_longPath_writesReadable(tmp_path: Path) -> None:
    """覆盖范围：深目录超长文件名读写
    测试对象：needs_extended_path、write_bytes、is_file、to_extended_path
    目的/目标：复现 audit-sandbox 级深路径后仍能写入并读回
    验证点：目标路径 needs_extended_path 为真；write 后 is_file；read_bytes == b"ok"
    失败含义：Windows 长路径下原始文件 API 失败，layer1 取证类测试会随机挂
    """
    if os.name != "nt":
        pytest.skip("Windows-only")
    # Mirror deep basetemp evidence layout (~275 chars) that broke phase3/4 tests.
    deep = (
        tmp_path
        / ".audit-sandbox"
        / "pytest-9agent-restored-targeted"
        / "test_layer1Ingestion_phase3_taskEvidenceArtifacts0"
        / "evidence"
        / ".phase3-micro-fetch-sandbox"
        / "data"
        / "raw"
        / "akshare"
        / "macro_supplementary"
        / "2024-06-15"
    )
    from backend.app.storage.path_compat import mkdir_parents

    mkdir_parents(deep, exist_ok=True)
    target = deep / ("a" * 64 + ".json")
    assert needs_extended_path(target)
    write_bytes(target, b"ok")
    assert is_file(target)
    assert to_extended_path(target).read_bytes() == b"ok"
