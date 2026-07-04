"""M-G1-03 P2-08 — Layer1 feature engine publish-day deltas."""

from __future__ import annotations

import pytest

from tests._m_g1_03_red_stub import red_skip

pytestmark = pytest.mark.skip(reason="M-G1-03 RED: P2-08 feature engine (S13)")


def test_layer1FeatureEngine_publishDayDelta_zScore_stateBucket() -> None:
    """覆盖范围：特征引擎输出
    测试对象：backend.app.layer1_axes.feature_engine
    目的/目标：publish 日 delta · z/分位/state_bucket；诚实 NULL
    验证点：quality_flags 与 layer1_axis_contract 一致
    失败含义：seed 或伪造特征冒充真链
    """
    red_skip("S13", "P2-08")
