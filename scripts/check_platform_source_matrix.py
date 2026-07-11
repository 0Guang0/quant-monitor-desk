#!/usr/bin/env python3
"""platform_source_matrix.yaml QMT 条目静态核对（正式 scripts · production_gate 子步）

仅纯 YAML 断言：非 Windows 禁用；Windows 可配置但默认不启用。
plan_route 行为测仍留在 tests/test_platform_source_matrix.py。

运行：
  uv run python scripts/check_platform_source_matrix.py --strict
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.contract_gate_support import load_yaml  # noqa: E402

PLATFORM_MATRIX = PROJECT_ROOT / "specs/contracts/platform_source_matrix.yaml"


def check_qmt_xtdata_non_windows_disabled(violations: list[str]) -> None:
    matrix = load_yaml(PLATFORM_MATRIX)
    for platform in ("linux", "macos"):
        entry = matrix["platforms"][platform]["qmt_xtdata"]
        if entry.get("available_if_user_configured") is not False:
            violations.append(
                f"{platform}.qmt_xtdata.available_if_user_configured="
                f"{entry.get('available_if_user_configured')!r}"
            )
        if entry.get("default_enabled") is not False:
            violations.append(
                f"{platform}.qmt_xtdata.default_enabled={entry.get('default_enabled')!r}"
            )


def check_qmt_xtdata_windows_requires_auth(violations: list[str]) -> None:
    matrix = load_yaml(PLATFORM_MATRIX)
    entry = matrix["platforms"]["windows"]["qmt_xtdata"]
    if entry.get("available_if_user_configured") is not True:
        violations.append(
            f"windows.qmt_xtdata.available_if_user_configured="
            f"{entry.get('available_if_user_configured')!r}"
        )
    if entry.get("default_enabled") is not False:
        violations.append(
            f"windows.qmt_xtdata.default_enabled={entry.get('default_enabled')!r}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when violations are found",
    )
    args = parser.parse_args(argv)

    violations: list[str] = []
    check_qmt_xtdata_non_windows_disabled(violations)
    check_qmt_xtdata_windows_requires_auth(violations)

    if not violations:
        print("PASS: platform source matrix YAML")
        return 0

    print("FAIL: platform source matrix YAML")
    for item in violations:
        print(f"  - {item}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
