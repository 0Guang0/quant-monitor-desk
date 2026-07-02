"""Audit A9 / Repair close 校验器测试。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / ".trellis" / "scripts"))

from common.validate_audit_handoff import validate_audit_handoff, validate_repair_close  # noqa: E402

_DIM_REPORT = """\
## §维度裁决

**{verdict}**

---

## 计划内问题

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
{plan_in_row}

---

## 计划外发现

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| — | — | 无 | — | — | — | — |
"""

_LEDGER_HEAD = (
    "| ID | P | 维度 | 标题 | disposition | 绑定任务 | 依赖/承接 | 登记位置 |\n"
    "| --- | --- | --- | --- | --- | --- | --- | --- |\n"
)


def _write_ledger(task_dir: Path, row: str) -> None:
    path = task_dir / "research" / "audit-repair-ledger.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# Ledger\n\n{_LEDGER_HEAD}{row}\n", encoding="utf-8")


def _write_min_a9_task(
    task_dir: Path,
    ledger_row: str,
    *,
    a1_verdict: str = "FAIL",
    a1_plan_in: str = "| A1-P2-01 | P2 | A1 | t | a | f | v |",
) -> None:
    research = task_dir / "research"
    research.mkdir(parents=True)
    for n in range(1, 9):
        (research / f"audit-a{n}-report.md").write_text(
            _DIM_REPORT.format(
                verdict=a1_verdict if n == 1 else "PASS",
                plan_in_row=a1_plan_in if n == 1 else "| — | — | 无 | — | — | — | — |",
            ),
            encoding="utf-8",
        )
    (task_dir / "audit.report.md").write_text(
        f"# Audit\n\n## 4.1\n\n{_LEDGER_HEAD}{ledger_row}\n",
        encoding="utf-8",
    )
    _write_ledger(task_dir, ledger_row)
    matrix = {
        "dimensions": {
            f"A{n}": {"result": "pass", "evidence": f"research/audit-a{n}-report.md"}
            for n in range(1, 9)
        },
    }
    matrix["dimensions"]["A1"]["result"] = "fail" if a1_verdict == "FAIL" else "pass"
    (task_dir / "audit_matrix.json").write_text(json.dumps(matrix), encoding="utf-8")


def test_validateAuditHandoff_a9DeferredRow_ok(tmp_path: Path) -> None:
    """覆盖范围：validate_audit_handoff A9 阶段外置行。
    测试对象：validate_audit_handoff。
    目的/目标：阶段外置行含绑定任务与双登记路径时 A9 gate 通过。
    验证点：errors 为空。
    失败含义：A9 合法 ledger 被误拒，阻塞进入 Repair。"""
    row = (
        "| A1-P2-01 | P2 | A1 | t | 阶段外置 | R3H-08 | dep | "
        "docs/quality/待修复清单.md · PROJECT_IMPLEMENTATION_ROADMAP.md |"
    )
    _write_min_a9_task(tmp_path, row)
    assert validate_audit_handoff(tmp_path, _REPO) == []


def test_validateAuditHandoff_legacyBoilerplate_notScanned(tmp_path: Path) -> None:
    """覆盖范围：ledger 模板头含 NON-BLOCKING 字样。
    测试对象：validate_audit_handoff 行级扫描。
    目的/目标：说明性 legacy 文案不触发 forbidden 误报。
    验证点：待修复行合法时 errors 为空。
    失败含义：模板/注释误报导致 A9 无法过 gate。"""
    row = "| A1-P2-01 | P2 | A1 | t | 待修复 | — | — | — |"
    _write_min_a9_task(tmp_path, row)
    ledger = tmp_path / "research" / "audit-repair-ledger.md"
    ledger.write_text(
        ledger.read_text(encoding="utf-8") + "\n> legacy NON-BLOCKING 勿模仿\n",
        encoding="utf-8",
    )
    assert validate_audit_handoff(tmp_path, _REPO) == []


def test_validateRepairClose_rejectsPendingFix(tmp_path: Path) -> None:
    """覆盖范围：Repair 关账 disposition。
    测试对象：validate_repair_close。
    目的/目标：关账时拒绝残留 待修复。
    验证点：errors 非空且提及 待修复。
    失败含义：未修项可关账，违反无遗留。"""
    _write_ledger(tmp_path, "| A1-P2-01 | P2 | A1 | t | 待修复 | — | — | — |")
    errors = validate_repair_close(tmp_path, _REPO)
    assert errors and "待修复" in errors[0]


def test_validateRepairClose_acceptsFixed(tmp_path: Path) -> None:
    """覆盖范围：Repair 关账 disposition。
    测试对象：validate_repair_close。
    目的/目标：待修复→已修复 后关账 gate 通过。
    验证点：errors 为空。
    失败含义：合法关账 ledger 被误拒。"""
    _write_ledger(tmp_path, "| A1-P2-01 | P2 | A1 | t | 已修复 | — | pytest | ok |")
    assert validate_repair_close(tmp_path, _REPO) == []


def test_validateRepairClose_mData03SpotChecks_pass() -> None:
    """覆盖范围：M-DATA-03 D-05 validate_repair_close spot-checks。
    测试对象：validate_repair_close（真实任务目录）。
    目的/目标：关账 gate 除 disposition 外校验代码/证据锚点。
    验证点：m-data-03-tier-a-live errors 为空。
    失败含义：D-05 gate 仅扫 ledger，Repair 关账可假完成。"""
    task_dir = _REPO / ".trellis" / "tasks" / "m-data-03-tier-a-live"
    assert validate_repair_close(task_dir, _REPO) == []
