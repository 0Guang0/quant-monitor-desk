"""M-G1-03 P2-02 S08 — macro/policy source batch true chain."""

from __future__ import annotations

import pytest

from tests._m_g1_03_red_stub import red_skip

pytestmark = pytest.mark.skip(reason="M-G1-03 RED: S08 macro/policy batch")


def test_layer1IndicatorBinding_macroBatch_fredTreasuryBisWorldBank_trueChain() -> None:
    """覆盖范围：矩阵 primary_source ∈ {fred, us_treasury, bis, world_bank}
    测试对象：批内 indicator_id 真链 sync→clean→axis_observation
    目的/目标：同库 lineage 可断言；禁止 seed
    验证点：隔离库 e2e；非 tmp seed
    失败含义：macro 批次未达 G1 R4 真链要求
    """
    red_skip("S08", "P2-02 macro")
