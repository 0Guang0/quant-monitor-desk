#!/usr/bin/env python3
"""task-01.5 S3/S4 关账用仓库禁词扫描（阶段性 · 非 pytest）

功能：
  在 backend / specs / tests / scripts 里用 ripgrep 检查是否仍残留已退役的沙箱段名
  （m-data-03 / M-DATA-03 / M_DATA_03 等，不区分大小写）与旧 harness 名
  （tier_a_live_acceptance、test_tierA 前缀）。
  供 task-01.5 CP-2 关账时人工或流水线执行，不是 operator 业务行为验收。

业务价值：
  防止新人/Agent 从代码或契约抄到已删除的沙箱路径或旧 harness 入口，避免双轨 SSOT。
  对齐 testing-guidelines：artifact-guard 不进 pytest，避免改文档/改名就误伤业务测试套件。

退役 / 清理时间（满足任一即删本文件）：
  1. task-01.5 Phase F 关账完成（B12/S6 + AUD-F-01/02 已闭合），且 master 连续 2 周无禁词回流；或
  2. 同类检查已并入正式 CI 门禁（pre-commit / GitHub Actions）且本脚本无独立调用方。

运行：
  uv run python phase-scripts/check_task015_s3_s4_rg_compliance.py --strict

guidelines 对齐：
  - testing-guidelines §Exclude noisy tests / artifact-guard → 不进 pytest
  - AGENTS.md → 阶段性流程放 phase-scripts，并写明退役条件
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SCAN_ROOTS = ("backend", "specs", "tests", "scripts")

# inventory 脚本用 base64 登记退役符号供扫描器读取（见该文件 ponytail 注释）
ALLOWLIST_RELATIVE = frozenset(
    {
        "scripts/check_acceptance_helper_consumers.py",
    }
)

RETIRED_PATTERNS: tuple[tuple[str, bool], ...] = (
    (r"m[-_]data[-_]03", True),
    ("tier_a_live_acceptance", False),
    ("test_tierA", False),
)


def _rg_hits(pattern: str, *, ignore_case: bool = False) -> list[str]:
    hits: list[str] = []
    cmd_base = ["rg", "-l"]
    if ignore_case:
        cmd_base.append("-i")
    for root in SCAN_ROOTS:
        proc = subprocess.run(
            [*cmd_base, pattern, str(PROJECT_ROOT / root)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode not in (0, 1):
            raise RuntimeError(proc.stderr or proc.stdout or f"rg failed for {pattern!r}")
        hits.extend(line.strip() for line in proc.stdout.splitlines() if line.strip())
    allowed = {str(PROJECT_ROOT / rel) for rel in ALLOWLIST_RELATIVE}
    return sorted({h for h in hits if h not in allowed})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="有命中时 exit 1（关账/CI 用）",
    )
    args = parser.parse_args(argv)

    violations: dict[str, list[str]] = {}
    for pattern, ignore_case in RETIRED_PATTERNS:
        hits = _rg_hits(pattern, ignore_case=ignore_case)
        if hits:
            label = f"{pattern!r}{' (ignore-case)' if ignore_case else ''}"
            violations[label] = hits

    if violations:
        print("task-01.5 S3/S4 rg compliance: FAIL", file=sys.stderr)
        for pattern, paths in violations.items():
            print(f"  pattern {pattern!r}:", file=sys.stderr)
            for path in paths:
                print(f"    - {path}", file=sys.stderr)
        return 1 if args.strict else 0

    print("task-01.5 S3/S4 rg compliance: PASS (no hits outside allowlist)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
