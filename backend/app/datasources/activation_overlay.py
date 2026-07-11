"""Activation overlay — 问开关（ADR-018 第一层 / data_sources.md §5.2.1）。

只回答：管理员是否允许已登记来源参与该领域/操作。
不做 license / platform / capability / ResourceGuard（属安检层）。

权威：docs/decisions/design/ADR-018-*.md · docs/modules/design/data_sources.md §5.2.1
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

# 复用 ERROR_CODE_GUIDE / route 语义；允许时不发明同义成功码。
_REASON_DISABLED = "DISABLED_SOURCE"


@dataclass(frozen=True, slots=True)
class ActivationDecision:
    """问开关最小对外结果：is_allowed · reason_code · overlay_revision。"""

    is_allowed: bool
    reason_code: str
    overlay_revision: str


def ask_activation(
    con: Any,
    *,
    source_id: str,
    data_domain: str,
    operation: str,
) -> ActivationDecision:
    """读最新未撤销 overlay；无 overlay 时回落 DB 基础 is_enabled（非内存对象）。"""
    overlay = con.execute(
        """
        SELECT enabled, revision
        FROM source_activation_overlay
        WHERE source_id = ?
          AND data_domain = ?
          AND operation = ?
          AND revoked_at IS NULL
        ORDER BY changed_at DESC
        LIMIT 1
        """,
        [source_id, data_domain, operation],
    ).fetchone()
    if overlay is not None:
        enabled, revision = bool(overlay[0]), str(overlay[1])
        return ActivationDecision(
            enabled, "" if enabled else _REASON_DISABLED, revision
        )

    row = con.execute(
        "SELECT is_enabled FROM source_registry WHERE source_id = ?",
        [source_id],
    ).fetchone()
    allowed = row is not None and bool(row[0])
    return ActivationDecision(
        allowed, "" if allowed else _REASON_DISABLED, ""
    )


def write_activation_overlay(
    con: Any,
    *,
    source_id: str,
    data_domain: str,
    operation: str,
    enabled: bool,
    reason: str,
    changed_by: str,
    sandbox: bool = False,
) -> str:
    """写入一条正规 overlay 记录；返回 revision。

    ``sandbox=True`` 时 reason 必须标明沙箱/测试用途（含 ``sandbox`` 字样），
    对齐 ADR-018：验收仅允许隔离根写标明用途的正规 overlay。
    """
    if not reason.strip():
        raise ValueError("activation overlay reason is required")
    if not changed_by.strip():
        raise ValueError("activation overlay changed_by is required")
    if sandbox and "sandbox" not in reason.casefold():
        raise ValueError("sandbox overlay reason must mark sandbox purpose")

    revision = f"ovr-{uuid.uuid4().hex}"
    overlay_id = f"ov-{uuid.uuid4().hex}"
    con.execute(
        """
        INSERT INTO source_activation_overlay (
            overlay_id, source_id, data_domain, operation, enabled,
            reason, changed_by, changed_at, revision
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            overlay_id,
            source_id,
            data_domain,
            operation,
            enabled,
            reason,
            changed_by,
            datetime.now(UTC),
            revision,
        ],
    )
    return revision
