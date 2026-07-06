from __future__ import annotations

from dataclasses import replace
from pathlib import Path

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
