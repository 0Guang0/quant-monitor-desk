"""M-G1-03 P1-08 — sync_job_contract full_load implemented."""

from __future__ import annotations

import pytest

from tests._m_g1_03_red_stub import red_skip

pytestmark = pytest.mark.skip(reason="M-G1-03 RED: P1-08 sync_job_contract (S03)")


def test_syncJobContract_fullLoad_inImplementedJobTypes() -> None:
    """覆盖范围：sync_job_contract.yaml job 类型登记
    测试对象：specs/contracts/sync_job_contract.yaml
    目的/目标：full_load ∈ implemented_job_types；无 reserved full_load
    验证点：契约与 runners/orchestrator 一致
    失败含义：FullLoad 仍为 defer 占位
    """
    red_skip("S03", "P1-08")
