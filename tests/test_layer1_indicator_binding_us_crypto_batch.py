"""M-G1-03 P2-02 S11 — US/crypto bar batch true chain."""

from __future__ import annotations

import pytest

from tests._m_g1_03_red_stub import red_skip

pytestmark = pytest.mark.skip(reason="M-G1-03 RED: S11 US/crypto batch")


def test_layer1IndicatorBinding_usCryptoBatch_alphaVantageDeribit_trueChain() -> None:
    """覆盖范围：us_equity_daily_bar · crypto_options_surface
    测试对象：alpha_vantage · deribit 绑定行
    目的/目标：批内真链；诚实 NULL 降级
    验证点：同库 lineage
    失败含义：单 ticker 代表整批
    """
    red_skip("S11", "P2-02 US/crypto")
