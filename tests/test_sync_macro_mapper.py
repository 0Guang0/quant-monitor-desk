"""M-G1-03 P1-06 — sync domain row mappers (pure functions)."""

from __future__ import annotations

import pytest

from tests._m_g1_03_red_stub import red_skip

pytestmark = pytest.mark.skip(reason="M-G1-03 RED: P1-06 mappers (S02)")


def test_syncMacroMapper_axisObservation_pureNoOrchestrator() -> None:
    """覆盖范围：macro_series → axis_observation mapper
    测试对象：backend.app.sync.mappers.*
    目的/目标：mapper 为纯函数；无 orchestrator/watermark 调用
    验证点：单测覆盖 macro→axis_observation 字段映射
    失败含义：mapper 与编排耦合，无法复用 BindingSyncExecutor
    """
    red_skip("S02", "P1-06")
