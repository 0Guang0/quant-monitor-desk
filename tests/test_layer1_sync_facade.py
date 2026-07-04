"""M-G1-03 P1-13 — layer1 sync_indicator facade seam."""

from __future__ import annotations

import pytest

from tests._m_g1_03_red_stub import red_skip

pytestmark = pytest.mark.skip(reason="M-G1-03 RED: P1-13 sync facade (S05)")


def test_layer1SyncFacade_syncIndicator_thinWrapperOnly() -> None:
    """覆盖范围：Layer 对外 sync 接缝
    测试对象：backend.app.sync.layer1_sync_facade.sync_indicator
    目的/目标：load_binding + execute_binding；禁止膨胀为新 orchestrator
    验证点：返回 SyncJobResult；无源专属逻辑
    失败含义：Layer 须直接懂 SyncJobSpec（违反 AD-MG103-10）
    """
    red_skip("S05", "P1-13")
