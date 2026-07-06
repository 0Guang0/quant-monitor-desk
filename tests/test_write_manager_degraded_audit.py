from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from tests.db_helpers import (
    create_test_write_manager,
    empty_clean_table,
    setup_write_smoke_db,
    write_smoke_request,
)


def test_writeManager_degradedRequest_persistsSourceSwitchedAndFallbackReason(
    tmp_path: Path,
) -> None:
    """覆盖范围：degraded clean 写入请求的审计字段
    测试对象：WriteManager.write + WriteRequest source_switched/fallback_reason
    目的/目标：降级写入进入 clean 时必须在 write_audit_log 留下切源与原因证据
    验证点：audit.source_role=fallback；source_switched=True；stale_reason 写入 fallback_reason
    失败含义：降级 clean 审计被写成普通主源，后续验收和下游模型无法识别
    """
    cm = setup_write_smoke_db(tmp_path)
    with cm.writer() as writer:
        empty_clean_table(writer)
    request = replace(
        write_smoke_request(),
        source_role="fallback",
        source_switched=True,
        quality_flags=("SOURCE_FALLBACK_USED",),
        fallback_reason="primary_rate_limited",
    )

    result = create_test_write_manager(cm).write(request)

    assert result.status == "SUCCESS"
    with cm.reader() as reader:
        audit = reader.execute(
            """
            SELECT source_role, source_switched, stale_reason
            FROM write_audit_log
            WHERE write_id = ?
            """,
            [result.write_id],
        ).fetchone()
    assert audit == ("fallback", True, "primary_rate_limited")


def test_writeManager_validationSourceWithoutDegradedEvidence_rejectsCleanWrite(
    tmp_path: Path,
) -> None:
    """覆盖范围：validation 来源进入 clean 前的降级证据校验
    测试对象：WriteManager._validate_request validation source_role 分支
    目的/目标：未由 FallbackPolicy 授权并标注的 Validation 源不能写入 clean
    验证点：source_role=validation 但缺少切源、质量标记和原因时抛出 ValueError
    失败含义：旁路 Validation 源可能以普通 clean 写入，污染验收 DB 和下游读路径
    """
    cm = setup_write_smoke_db(tmp_path)
    with cm.writer() as writer:
        empty_clean_table(writer)
    request = replace(write_smoke_request(), source_role="validation")

    with pytest.raises(ValueError, match="source_switched=True"):
        create_test_write_manager(cm).write(request)


def test_writeManager_validationSourceWithDegradedEvidence_persistsAudit(
    tmp_path: Path,
) -> None:
    """覆盖范围：FallbackPolicy 授权的 validation 降级 clean 写入
    测试对象：WriteManager.write + WriteRequest validation/source_switched/quality_flags
    目的/目标：Validation 源只有携带完整降级元数据时才能写入并被审计
    验证点：写入成功；audit.source_role=validation；source_switched=True；stale_reason 写入授权原因
    失败含义：合法降级 Validation 源要么被误拒，要么进入 clean 后缺少可追踪审计证据
    """
    cm = setup_write_smoke_db(tmp_path)
    with cm.writer() as writer:
        empty_clean_table(writer)
    request = replace(
        write_smoke_request(),
        source_role="validation",
        source_switched=True,
        quality_flags=("VALIDATION_SOURCE_USED",),
        stale_reason="fallback_policy:primary_unavailable",
    )

    result = create_test_write_manager(cm).write(request)

    assert result.status == "SUCCESS"
    with cm.reader() as reader:
        audit = reader.execute(
            """
            SELECT source_role, source_switched, stale_reason
            FROM write_audit_log
            WHERE write_id = ?
            """,
            [result.write_id],
        ).fetchone()
    assert audit == ("validation", True, "fallback_policy:primary_unavailable")
