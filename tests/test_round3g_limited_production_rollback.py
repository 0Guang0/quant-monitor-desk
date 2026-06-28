"""Round 3G R3G-03 limited production rollback 契约门禁。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.contract_gate_support import PROJECT_ROOT, load_yaml

CONTRACT = PROJECT_ROOT / "specs/contracts/sandbox_clean_write_contract.yaml"
R3G03_FIXTURES = PROJECT_ROOT / "tests/fixtures/sandbox_clean_write/r3g03"
APPROVAL_FIXTURE = R3G03_FIXTURES / "approval_minimal.yaml"
ROLLBACK_FIXTURE = R3G03_FIXTURES / "rollback_plan_minimal.json"


def _contract() -> dict:
    return load_yaml(CONTRACT)


def test_r3g03Contract_rollbackDryRunRequired() -> None:
    """覆盖范围：R3G-03 rollback 预演要求
    测试对象：r3g03_limited_entry.rollback_dry_run_required
    目的/目标：有限生产写前必须完成 rollback dry-run 证据
    验证点：rollback_dry_run_required 为 true
    失败含义：无 rollback 预演会导致生产写后无法证明可回滚
    """
    assert _contract()["r3g03_limited_entry"]["rollback_dry_run_required"] is True


def test_r3g03Contract_blocksMissingRollbackPlan() -> None:
    """覆盖范围：R3G-03 block_if 对缺失 rollback 计划的 fail-closed
    测试对象：r3g03_limited_entry.block_if
    目的/目标：缺 rollback 计划时必须拒绝 limited entry
    验证点：block_if 含 missing_rollback_plan 与 missing_before_proof
    失败含义：无 rollback 计划仍可能进入 limited production clean-write
    """
    block_if = set(_contract()["r3g03_limited_entry"]["block_if"])
    assert "missing_rollback_plan" in block_if
    assert "missing_before_proof" in block_if
    assert "missing_after_proof" in block_if


def test_r3g03Contract_listsRequiredQmdGates() -> None:
    """覆盖范围：R3G 全阶段 QMD 门禁清单
    测试对象：required_qmd_gates
    目的/目标：3G 路径必须经过 WriteManager 与 DbValidationGate 等 QMD 组件
    验证点：清单含 WriteManager 与 DbValidationGate
    失败含义：契约未冻结 QMD 门禁会导致 clean-write 绕过验证链
    """
    gates = set(_contract()["required_qmd_gates"])
    assert "WriteManager" in gates
    assert "DbValidationGate" in gates
    assert "SourceRoutePlanner" in gates


# --- RollbackPlan (9.3) ------------------------------------------------------


def test_RollbackPlan_buildsIdentifyOnlyDryRun() -> None:
    """覆盖范围：rollback dry-run identify-only
    测试对象：build_rollback_plan + dry_run_identify_affected_keys
    目的/目标：AC-06 rollback 仅识别 affected keys，不执行删除
    验证点：dry_run_only 与 identify_only 为 true
    失败含义：rollback 可能误删非目标 key
    """
    from backend.app.ops.sandbox_clean_write.approval_contract import load_approval_contract
    from backend.app.ops.sandbox_clean_write.rollback_plan import (
        build_rollback_plan,
        dry_run_identify_affected_keys,
    )

    contract = load_approval_contract(APPROVAL_FIXTURE)
    candidate = contract.source_candidates[0]
    plan = build_rollback_plan(contract, candidate)
    assert plan["dry_run_only"] is True
    assert plan["identify_only"] is True
    keys = dry_run_identify_affected_keys(plan)
    assert len(keys) == len(candidate.symbols)


def test_RollbackPlan_missingFile_blocks() -> None:
    """覆盖范围：block_if missing_rollback_plan
    测试对象：load_rollback_plan
    目的/目标：缺 rollback plan 文件时 fail-closed
    验证点：不存在路径抛 RollbackPlanError
    失败含义：无 rollback 计划仍可进入 promote
    """
    from backend.app.ops.sandbox_clean_write.rollback_plan import (
        RollbackPlanError,
        load_rollback_plan,
    )

    with pytest.raises(RollbackPlanError, match="missing_rollback_plan"):
        load_rollback_plan(PROJECT_ROOT / "nonexistent_rollback.json")


def test_RollbackPlan_nonTargetRowsUnchangedOnDryRunIdentify(tmp_path: Path) -> None:
    """覆盖范围：rollback identify-only 非目标 key 留存
    测试对象：dry_run_identify_affected_keys + promote dry_run
    目的/目标：识别 affected keys 不删除非目标行
    验证点：fixture DB 目标+非目标行 COUNT 在 identify 后不变
    失败含义：rollback 预演可能误删非批准 symbol 行
    """
    from backend.app.db.connection import ConnectionManager
    from backend.app.db.migrate import apply_migrations
    from backend.app.ops.sandbox_clean_write.approval_contract import load_approval_contract
    from backend.app.ops.sandbox_clean_write.rollback_plan import (
        build_rollback_plan,
        dry_run_identify_affected_keys,
    )

    db_path = PROJECT_ROOT / ".audit-sandbox/round3g/pytest/rollback_non_target.duckdb"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.is_file():
        db_path.unlink()
    cm = ConnectionManager(db_path)
    with cm.writer() as con:
        apply_migrations(con)
        con.execute("DELETE FROM security_bar_1d")
        con.execute(
            """
            INSERT INTO security_bar_1d (
                instrument_id, trade_date, open, high, low, close, pre_close, volume, amount,
                adjustment_type, source_used, batch_id, quality_flags, created_at
            ) VALUES
            ('sh.600000', '2026-05-01', 10.0, 10.0, 10.0, 10.0, NULL, NULL, NULL, 'none', 'test', 'b0', NULL, CURRENT_TIMESTAMP),
            ('sz.000001', '2026-05-01', 11.0, 11.0, 11.0, 11.0, NULL, NULL, NULL, 'none', 'test', 'b0', NULL, CURRENT_TIMESTAMP)
            """
        )
        before_count = con.execute("SELECT COUNT(*) FROM security_bar_1d").fetchone()[0]

    contract = load_approval_contract(APPROVAL_FIXTURE)
    candidate = contract.source_candidates[0]
    plan = build_rollback_plan(contract, candidate)
    keys = dry_run_identify_affected_keys(plan)
    assert len(keys) == 1

    with cm.reader() as con:
        after_count = con.execute("SELECT COUNT(*) FROM security_bar_1d").fetchone()[0]
    assert after_count == before_count == 2


def test_RollbackPlan_validateRejectsNonIdentifyOnly(tmp_path: Path) -> None:
    """覆盖范围：rollback overreach 停止条件
    测试对象：validate_rollback_plan identify_only
    目的/目标：identify_only=false 的 plan 不得通过校验
    验证点：篡改 identify_only 后抛错
    失败含义：rollback 可能执行真实删除
    """
    from backend.app.ops.sandbox_clean_write.approval_contract import load_approval_contract
    from backend.app.ops.sandbox_clean_write.rollback_plan import (
        RollbackPlanError,
        load_rollback_plan,
        validate_rollback_plan,
    )

    plan = json.loads(ROLLBACK_FIXTURE.read_text(encoding="utf-8"))
    plan["identify_only"] = False
    plan_path = tmp_path / "bad_rollback.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    contract = load_approval_contract(APPROVAL_FIXTURE)
    candidate = contract.source_candidates[0]
    with pytest.raises(RollbackPlanError, match="identify_only"):
        validate_rollback_plan(
            load_rollback_plan(plan_path),
            candidate=candidate,
            production_db_path=PROJECT_ROOT / plan["production_db_path"],
        )
