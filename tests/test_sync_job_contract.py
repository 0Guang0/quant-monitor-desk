"""M-G1-03 P1-08 — sync_job_contract parity and deferred error outcome."""

from __future__ import annotations

import pytest

from backend.app.sync.contract import (
    DEFERRED_JOB_TYPE_CODE,
    DEFERRED_OWNER,
    DEFERRED_PHASE,
    DOCS_ANCHOR_D2_P1_1,
    IMPLEMENTED_JOB_TYPES,
    RESERVED_JOB_TYPES,
    DeferredJobTypeError,
    load_sync_job_contract,
    raise_deferred_job_type,
)


def test_syncJobContract_fullLoad_inImplementedJobTypes() -> None:
    """覆盖范围：sync job 契约与 runtime 常量 parity（VR-SYNC-002 / SYNC-01）
    测试对象：specs/contracts/sync_job_contract.yaml · IMPLEMENTED_JOB_TYPES
    目的/目标：契约声明的已实现 job 类型须与模块常量一致；reserved 分离
    验证点：YAML implemented == IMPLEMENTED_JOB_TYPES；reserved 分离；full_load ∈ implemented
    失败含义：调用方或 CLI 无法从契约判断哪些 job 真正可跑，矩阵与代码漂移
    """
    contract = load_sync_job_contract()
    yaml_impl = frozenset(contract["implemented_job_types"])
    yaml_reserved = frozenset(contract.get("reserved_job_types") or [])
    assert "full_load" in yaml_impl
    assert "full_load" not in yaml_reserved
    assert yaml_impl == IMPLEMENTED_JOB_TYPES
    assert yaml_reserved == RESERVED_JOB_TYPES
    assert yaml_impl.isdisjoint(yaml_reserved)


def test_syncJobContract_deferredErrorYaml_parityWithRuntimeConstants() -> None:
    """覆盖范围：deferred_error 契约字段与 runtime 常量 parity（ZO-05/06）
    测试对象：sync_job_contract.yaml deferred_error · contract.py 常量
    目的/目标：owner/phase/code/docs_anchor 单源 YAML 与模块常量一致，防漂移
    验证点：load_sync_job_contract() deferred_error 各字段 == DEFERRED_* 常量
    失败含义：调用方或 registry 读到与 runtime 不一致的 deferred 元数据
    """
    deferred = load_sync_job_contract()["deferred_error"]
    assert deferred["code"] == DEFERRED_JOB_TYPE_CODE
    assert deferred["owner"] == DEFERRED_OWNER
    assert deferred["phase"] == DEFERRED_PHASE
    assert deferred["docs_anchor"] == DOCS_ANCHOR_D2_P1_1


def test_syncJobContract_deferredJobType_raisesStableOutcome() -> None:
    """覆盖范围：reserved job type 的 runtime deferred 错误 outcome
    测试对象：raise_deferred_job_type / DeferredJobTypeError
    目的/目标：调用 reserved job 时须抛出稳定 code/owner/phase/docs_anchor
    验证点：pytest.raises(DeferredJobTypeError)；各字段与契约常量一致
    失败含义：deferred 类型静默成功或错误元数据漂移，调用方无法 fail-closed
    """
    with pytest.raises(DeferredJobTypeError) as exc_info:
        raise_deferred_job_type(
            "historical_rebuild",
            entrypoint="DataSyncOrchestrator.run_historical_rebuild",
        )
    err = exc_info.value
    assert err.code == DEFERRED_JOB_TYPE_CODE
    assert err.job_type == "historical_rebuild"
    assert err.owner == DEFERRED_OWNER
    assert err.phase == DEFERRED_PHASE
    assert err.docs_anchor == DOCS_ANCHOR_D2_P1_1
    assert DOCS_ANCHOR_D2_P1_1 in str(err)
