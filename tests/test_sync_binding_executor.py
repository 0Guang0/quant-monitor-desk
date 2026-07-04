"""M-G1-03 P1-06′ — BindingSyncExecutor 唯一编排深度模块."""

from __future__ import annotations

import pytest

from tests._m_g1_03_red_stub import red_skip

pytestmark = pytest.mark.skip(reason="M-G1-03 RED: P1-06′ binding executor (S02)")


def test_bindingSyncExecutor_executeBinding_onlyOrchestrationPath() -> None:
    """覆盖范围：binding → SyncJobSpec → orchestrator 唯一路径
    测试对象：backend.app.sync.binding_executor.execute_binding
    目的/目标：删除 executor 则编排散落 ops+facade+scheduler（删除测试须失败）
    验证点：execute_binding 覆盖 watermark+mapper+orchestrator 序列
    失败含义：三处复制编排，与 AD-MG103-10 冲突
    """
    red_skip("S02", "P1-06′")


def test_bindingSyncExecutor_deletionTest_orchestrationNotInOps() -> None:
    """覆盖范围：删除测试 — 编排集中度
    测试对象：binding_executor vs ops/*_incremental_run
    目的/目标：禁止 facade/ops 内联 duplicate 编排
    验证点：mock 删除 executor 后 ops 路径无法完成 sync
    失败含义：浅层 pass-through 膨胀
    """
    red_skip("S02", "P1-06′")
