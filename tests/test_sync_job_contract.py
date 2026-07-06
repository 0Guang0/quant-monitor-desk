"""M-G1-03 P1-08 — sync_job_contract full_load implemented."""

from __future__ import annotations

from backend.app.sync.contract import IMPLEMENTED_JOB_TYPES, RESERVED_JOB_TYPES, load_sync_job_contract


def test_syncJobContract_fullLoad_inImplementedJobTypes() -> None:
    """覆盖范围：sync_job_contract.yaml job 类型登记
    测试对象：specs/contracts/sync_job_contract.yaml
    目的/目标：full_load ∈ implemented_job_types；无 reserved full_load
    验证点：契约与 runners/orchestrator 一致
    失败含义：FullLoad 仍为 defer 占位
    """
    contract = load_sync_job_contract()
    yaml_impl = frozenset(contract["implemented_job_types"])
    yaml_reserved = frozenset(contract.get("reserved_job_types") or [])
    assert "full_load" in yaml_impl
    assert "full_load" not in yaml_reserved
    assert yaml_impl == IMPLEMENTED_JOB_TYPES
    assert yaml_reserved == RESERVED_JOB_TYPES
    assert yaml_impl.isdisjoint(yaml_reserved)
