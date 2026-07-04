"""M-G1-03 P1-16 — sync scheduler §13.6 profiles."""

from __future__ import annotations

import pytest

from tests._m_g1_03_red_stub import red_skip

pytestmark = pytest.mark.skip(reason="M-G1-03 RED: P1-16 scheduler (S06)")


def test_syncScheduler_profileExpandsRegistryToExecuteBinding() -> None:
    """覆盖范围：内置 scheduler + sync_scheduler_profiles.yaml
    测试对象：backend.app.sync.scheduler.run_profile
    目的/目标：profile job 经 registry 展开为 execute_binding；非硬编码 series
    验证点：scheduler run --profile daily_close 登记 data_cli_contract
    失败含义：分散 crontab 或绕过 binding executor
    """
    red_skip("S06", "P1-16")
