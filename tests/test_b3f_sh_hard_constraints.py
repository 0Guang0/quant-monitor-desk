"""B3F-SH hard constraints — R3F-SH-07 no-false-close."""

from __future__ import annotations

from backend.app.ops.b3f_sh_registry_guard import (
    OPEN_VALIDATION_REGISTRY_ROWS,
    assert_sidecar_does_not_close_validation_rows,
    build_no_false_close_guard,
)


def test_b3fShHardConstraints_akshareNotClosedBySidecar() -> None:
    """覆盖范围：AkShare/Eastmoney OPEN 行 no-false-close 守卫
    测试对象：build_no_false_close_guard / assert_sidecar_does_not_close_validation_rows
    目的/目标：R3F-SH-07 — sidecar 不得 RESOLVED 关闭 REQ2-EM / AkShare validation
    验证点：does_not_close_* 为 True；OPEN 行集合含 R3-B2.75-REQ2-EM 与 AKSHARE-VAL-01
    失败含义：sidecar 可关 validation 族，违反 Batch 3F hardening §4
    """
    guard = build_no_false_close_guard()
    assert guard["does_not_close_R3-B2.75-REQ2-EM"] is True
    assert guard["does_not_close_R3-PROMPT14-AKSHARE-VAL-01"] is True
    assert OPEN_VALIDATION_REGISTRY_ROWS <= frozenset(guard["registry_rows_must_remain_open"])
    assert_sidecar_does_not_close_validation_rows(guard)
