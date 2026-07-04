"""M-G1-03 P1-07 — FullLoadJobRunner §13.4.1."""

from __future__ import annotations

import pytest

from tests._m_g1_03_red_stub import red_skip

pytestmark = pytest.mark.skip(reason="M-G1-03 RED: P1-07 full load (S03)")


def test_syncFullLoad_runnerSection1341_noDeferredJobTypeError() -> None:
    """覆盖范围：FullLoad job runner
    测试对象：backend.app.sync.runners.FullLoadJobRunner
    目的/目标：§13.4.1 断点续跑；无 DeferredJobTypeError
    验证点：orchestrator 可调度 full_load
    失败含义：sync_job_contract reserved full_load 未消除
    """
    red_skip("S03", "P1-07")
