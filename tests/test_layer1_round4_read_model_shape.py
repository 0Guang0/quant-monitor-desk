"""M-G1-03 P2-10 — Round4 read model column shape (no HTTP)."""

from __future__ import annotations

import pytest

from tests._m_g1_03_red_stub import red_skip

pytestmark = pytest.mark.skip(reason="M-G1-03 RED: P2-10 read model shape (S13)")


def test_layer1Round4ReadModel_axisFeatureSnapshot_columnsSubset() -> None:
    """覆盖范围：Round4 读模型字段形状
    测试对象：axis_feature_snapshot · axis_indicator_profile 列
    目的/目标：对齐 layer1_global_regime_panel.md §6.4–6.5
    验证点：列名+类型子集；本票无 REST
    失败含义：Round4 读模型与契约分叉
    """
    red_skip("S13", "P2-10")
