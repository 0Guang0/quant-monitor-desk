"""参考采纳护栏 — 仅保留正式运行时行为锚点。

静态扫描（交易 API / OpenBB / EasyXT 等）已迁至
phase-scripts/check_reference_adoption_guardrails.py（artifact-guard，非业务 pytest）。
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from backend.app.ops.sandbox_clean_write.approval_contract import (
    ApprovalContractError,
    validate_approval_contract,
)
from tests.contract_gate_support import PROJECT_ROOT


def test_r3g03LimitedProduction_noAgentTriggeredWriteMarker() -> None:
    """覆盖范围：R3G-03 agent 触发写拒绝（行为测）
    测试对象：validate_approval_contract no_agent_triggered_write
    目的/目标：no_agent_triggered_write=false 时 fail-closed
    验证点：篡改 approval 后抛 agent_triggered_write_path
    失败含义：agent 可替代用户 approval 触发生产写
    """
    raw = yaml.safe_load(
        (
            PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g03/approval_minimal.yaml"
        ).read_text(encoding="utf-8")
    )
    raw["no_agent_triggered_write"] = False
    with tempfile.TemporaryDirectory() as tmp:
        approval_path = Path(tmp) / "approval.yaml"
        audit_path = Path(tmp) / "audit.json"
        audit_path.write_text(
            (
                PROJECT_ROOT
                / "tests/fixtures/sandbox_clean_write/r3g03/audit_decision_allow.json"
            ).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        raw["audit_decision_file"] = str(audit_path)
        approval_path.write_text(yaml.dump(raw), encoding="utf-8")
        with pytest.raises(ApprovalContractError, match="agent_triggered_write_path"):
            validate_approval_contract(approval_path, audit_path)
