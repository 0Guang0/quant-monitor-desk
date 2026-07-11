#!/usr/bin/env python3
"""Batch 3F SH-07 no-false-close 阶段守卫（阶段性 · 非业务 pytest）

功能：
  调用 backend.app.ops.b3f_sh_registry_guard，确认 sidecar closeout 不得把
  AkShare / Eastmoney 等 validation 族 OPEN 行误标为 RESOLVED。
  对应原 tests/test_b3f_sh_hard_constraints.py（phase-guard / 早期关账闸）。

业务价值：
  Round3 Batch 3F hardening 期间防止审计 sidecar「假关账」把仍 OPEN 的 validation
  债行关掉。这是阶段关账卫生，不是日常业务 outcome。

退役 / 清理时间（满足任一即可删本文件；生产模块是否另票清理不在本脚本范围）：
  1. R3F-SH-07 / Batch 3F SH 债行已全部正式闭合或权威登记废止，且不再依赖
     b3f_sh_registry_guard 字面守卫；或
  2. 同等约束已并入正式 registry/ledger 校验（非硬编码 True 字典），并由 CI 正式门禁承接；或
  3. 权威 design / ADR 废止该 no-false-close sidecar 约定。

运行：
  uv run python phase-scripts/check_b3f_sh_no_false_close.py
  uv run python phase-scripts/check_b3f_sh_no_false_close.py --strict

guidelines 对齐：
  - completion-check TEST-EVIDENCE-GOVERNANCE：phase-guard → 不进业务 pytest
  - AGENTS.md → 阶段性流程放 phase-scripts，中文写明功能、价值、退役条件
"""

from __future__ import annotations

import argparse
import sys


def _run_checks() -> list[str]:
    from backend.app.ops.b3f_sh_registry_guard import (
        OPEN_VALIDATION_REGISTRY_ROWS,
        assert_sidecar_does_not_close_validation_rows,
        build_no_false_close_guard,
    )

    errors: list[str] = []
    guard = build_no_false_close_guard()
    if guard.get("does_not_close_R3-B2.75-REQ2-EM") is not True:
        errors.append("does_not_close_R3-B2.75-REQ2-EM is not True")
    if guard.get("does_not_close_R3-PROMPT14-AKSHARE-VAL-01") is not True:
        errors.append("does_not_close_R3-PROMPT14-AKSHARE-VAL-01 is not True")
    open_rows = frozenset(guard.get("registry_rows_must_remain_open") or ())
    if not OPEN_VALIDATION_REGISTRY_ROWS <= open_rows:
        errors.append(
            f"OPEN_VALIDATION_REGISTRY_ROWS not covered: "
            f"{sorted(OPEN_VALIDATION_REGISTRY_ROWS - open_rows)}"
        )
    try:
        assert_sidecar_does_not_close_validation_rows(guard)
    except AssertionError as exc:
        errors.append(f"happy-path guard rejected: {exc}")

    try:
        assert_sidecar_does_not_close_validation_rows(
            {"does_not_close_R3-B2.75-REQ2-EM": False}
        )
        errors.append("false-close closeout was not rejected")
    except AssertionError as exc:
        if "does_not_close_R3-B2.75-REQ2-EM" not in str(exc):
            errors.append(f"negative path wrong error: {exc}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="有失败时 exit 1")
    args = parser.parse_args(argv)

    errors = _run_checks()
    if not errors:
        print("PASS: B3F-SH no-false-close guard")
        return 0
    print("FAIL: B3F-SH no-false-close guard")
    for err in errors:
        print(f"  - {err}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
