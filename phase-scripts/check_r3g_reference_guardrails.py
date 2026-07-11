#!/usr/bin/env python3
"""R3G 参考采纳护栏（阶段性 · 非业务 pytest）

功能：
  仅扫描 R3G-01/R3G-03 sandbox_clean_write 模块：禁止参考项目 import、
  交易 API def、OpenBB runtime 标记。全局扫描见
  scripts/check_reference_adoption_guardrails.py。

业务价值：
  Round3G 前守住 sandbox / limited-production 的 no-action 与审批边界，
  防止参考项目 AGPL/交易面渗入 R3G 模块。

退役 / 清理时间（满足任一即可删本文件）：
  1. R3G sandbox_clean_write 阶段关闭且模块已 promote/退役；或
  2. 本扫描已并入正式 scripts/check_reference_adoption_guardrails.py 并由
     production_gate 覆盖，无需独立 phase 入口。

运行：
  uv run python phase-scripts/check_r3g_reference_guardrails.py --strict
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.contract_gate_support import (  # noqa: E402
    FORBIDDEN_REFERENCE_IMPORT_ROOTS,
    FORBIDDEN_TRADING_DEF_NAMES,
    scan_forbidden_function_defs,
    scan_forbidden_import_roots,
)

_R3G01_MODULE_ROOT = PROJECT_ROOT / "backend/app/ops/sandbox_clean_write"
_R3G03_MODULE_ROOT = PROJECT_ROOT / "backend/app/ops/sandbox_clean_write"
_R3G03_FILES = (
    _R3G03_MODULE_ROOT / "approval_contract.py",
    _R3G03_MODULE_ROOT / "limited_production_entry.py",
    _R3G03_MODULE_ROOT / "rollback_plan.py",
)


def check_r3g01_no_reference_import(violations: list[str]) -> None:
    for item in scan_forbidden_import_roots(
        FORBIDDEN_REFERENCE_IMPORT_ROOTS,
        scan_roots=(_R3G01_MODULE_ROOT,),
    ):
        violations.append(f"r3g01 reference import: {item}")


def check_r3g01_no_trading_api(violations: list[str]) -> None:
    for item in scan_forbidden_function_defs(
        FORBIDDEN_TRADING_DEF_NAMES,
        roots=(_R3G01_MODULE_ROOT,),
    ):
        violations.append(f"r3g01 trading API: {item}")


def check_r3g01_openbb_architecture_only(violations: list[str]) -> None:
    if not _R3G01_MODULE_ROOT.is_dir():
        violations.append(f"missing module root: {_R3G01_MODULE_ROOT}")
        return
    text = "\n".join(
        p.read_text(encoding="utf-8")
        for p in _R3G01_MODULE_ROOT.rglob("*.py")
        if p.is_file()
    )
    for bad in ("openbb_platform/providers", "OBBject", "from openbb"):
        if bad in text:
            violations.append(f"r3g01 OpenBB runtime marker: {bad!r}")


def check_r3g03_no_reference_import(violations: list[str]) -> None:
    hits = scan_forbidden_import_roots(
        FORBIDDEN_REFERENCE_IMPORT_ROOTS,
        scan_roots=(_R3G03_MODULE_ROOT,),
    )
    r3g03_only = [
        v
        for v in hits
        if any(
            name in v
            for name in (
                "approval_contract",
                "limited_production_entry",
                "rollback_plan",
            )
        )
    ]
    for item in r3g03_only:
        violations.append(f"r3g03 reference import: {item}")


def check_r3g03_no_trading_api(violations: list[str]) -> None:
    for item in scan_forbidden_function_defs(
        FORBIDDEN_TRADING_DEF_NAMES,
        roots=_R3G03_FILES,
    ):
        violations.append(f"r3g03 trading API: {item}")


def check_r3g03_openbb_architecture_only(violations: list[str]) -> None:
    for path in _R3G03_FILES:
        if not path.is_file():
            violations.append(f"missing r3g03 file: {path.relative_to(PROJECT_ROOT)}")
            return
    text = "\n".join(path.read_text(encoding="utf-8") for path in _R3G03_FILES)
    for bad in ("openbb_platform/providers", "from openbb"):
        if bad in text:
            violations.append(f"r3g03 OpenBB runtime marker: {bad!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="有违例时 exit 1（关账/人工门禁用）",
    )
    args = parser.parse_args(argv)

    violations: list[str] = []
    check_r3g01_no_reference_import(violations)
    check_r3g01_no_trading_api(violations)
    check_r3g01_openbb_architecture_only(violations)
    check_r3g03_no_reference_import(violations)
    check_r3g03_no_trading_api(violations)
    check_r3g03_openbb_architecture_only(violations)

    if not violations:
        print("PASS: R3G reference adoption guardrails")
        return 0

    print("FAIL: R3G reference adoption guardrails")
    for item in violations:
        print(f"  - {item}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
