"""M-G1-03 P1-08 — sync_job_contract deferred error outcome.

静态 YAML↔常量 parity：
`uv run python scripts/check_sync_job_contract.py --strict`
（亦由 production_gate 调用）。
"""

from __future__ import annotations

import pytest

from backend.app.sync.contract import (
    DEFERRED_JOB_TYPE_CODE,
    DEFERRED_OWNER,
    DEFERRED_PHASE,
    DOCS_ANCHOR_D2_P1_1,
    DeferredJobTypeError,
    raise_deferred_job_type,
)


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
