#!/usr/bin/env python3
"""参考采纳护栏兼容入口（阶段性 thin wrapper）

功能：
  依次调用 scripts/check_reference_adoption_guardrails.py（全局）与
  phase-scripts/check_r3g_reference_guardrails.py（R3G）。
  --strict 时任一失败则 exit non-zero，兼容旧命令路径。

业务价值：
  保留既有 phase-scripts 调用面，避免文档/脚本硬编码路径断裂。

退役 / 清理时间（满足任一即可删本文件）：
  1. 所有调用方已改用 scripts/ + phase-scripts/check_r3g_* 两个入口；或
  2. R3G phase 关闭且仅保留正式 scripts 全局扫描。

运行：
  uv run python phase-scripts/check_reference_adoption_guardrails.py --strict
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GLOBAL_SCRIPT = PROJECT_ROOT / "scripts" / "check_reference_adoption_guardrails.py"
R3G_SCRIPT = PROJECT_ROOT / "phase-scripts" / "check_r3g_reference_guardrails.py"


def _run(script: Path, *, strict: bool) -> int:
    cmd = [sys.executable, str(script)]
    if strict:
        cmd.append("--strict")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="有违例时 exit 1（关账/人工门禁用）",
    )
    args = parser.parse_args(argv)

    rc_global = _run(GLOBAL_SCRIPT, strict=args.strict)
    rc_r3g = _run(R3G_SCRIPT, strict=args.strict)
    if rc_global != 0 or rc_r3g != 0:
        if args.strict:
            return 1
        return 0
    print("PASS: reference adoption guardrails (wrapper: global + R3G)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
