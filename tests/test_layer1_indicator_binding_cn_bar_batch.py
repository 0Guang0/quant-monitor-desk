"""M-G1-03 P2-02 S10 — CN equity bar batch true chain."""

from __future__ import annotations

import pytest

from tests._m_g1_03_red_stub import red_skip

pytestmark = pytest.mark.skip(reason="M-G1-03 RED: S10 CN bar batch")


def test_layer1IndicatorBinding_cnBarBatch_baostockMootdx_trueChain() -> None:
    """覆盖范围：cn_equity_daily_bar · baostock/mootdx
    测试对象：矩阵 CN bar 绑定行
    目的/目标：真链落库；与 M-DATA-03 clean 输入衔接
    验证点：axis_observation 可断言
    失败含义：仅 staged 单样本冒充整批
    """
    red_skip("S10", "P2-02 CN bar")
