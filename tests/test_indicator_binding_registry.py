"""M-G1-03 P1-02 — IndicatorBinding loader (§9.1 row schema)."""

from __future__ import annotations

import pytest

from tests._m_g1_03_red_stub import red_skip

pytestmark = pytest.mark.skip(reason="M-G1-03 RED: P1-02 indicator_binding loader (S01)")


def test_indicatorBinding_loader_matchesSection91Columns() -> None:
    """覆盖范围：indicator_binding_registry.yaml → IndicatorBinding frozen dataclass
    测试对象：backend.app.sync.indicator_binding.load_binding
    目的/目标：§9.1 列与 dataclass 1:1；未知 id → UnknownIndicatorError(CAPABILITY_MISSING)
    验证点：YAML 在 loader 边界校验；禁止裸 ValueError
    失败含义：Layer/ops 无法安全解析绑定矩阵
    """
    red_skip("S01", "P1-02")
