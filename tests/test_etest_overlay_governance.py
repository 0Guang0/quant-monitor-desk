"""E-TEST 夹具治理 — G1-02 票 05：禁 patch 已加载对象作关账证据。"""

from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SERVICE_PATH_SUPPORT = _REPO / "tests" / "service_path_support.py"


def test_servicePathSupport_hasNoMonkeypatchEnableHelpers() -> None:
    """覆盖范围：E-TEST-01 service_path_support 启用夹具形态（ADR-018 / brief 3C）
    测试对象：tests/service_path_support.py 源码静态面
    目的/目标：关账证据不得再靠 object.__setattr__(is_enabled) 或强制 _platform_allows
    验证点：文件含 enable_source_route + write_activation_overlay；不含上述撬门字样
    失败含义：测试夹具仍用内存 OVERRIDE 冒充启用，无法证明正规 overlay 路径
    """
    text = _SERVICE_PATH_SUPPORT.read_text(encoding="utf-8")
    assert "def enable_source_route(" in text
    assert "write_activation_overlay" in text
    assert "object.__setattr__" not in text
    assert "monkeypatch.setattr(planner" not in text
    assert 'setattr(planner, "_platform_allows"' not in text
    assert "force_platform" not in text
