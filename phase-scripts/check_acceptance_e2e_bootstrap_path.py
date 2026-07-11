#!/usr/bin/env python3
"""acceptance_e2e_bootstrap 路径契约（阶段性 · 非业务 pytest）

功能：
  核对 tests.acceptance_e2e_bootstrap.acceptance_db_path 仍落在
  sandbox_root/duckdb/quant_monitor.duckdb（ADR-015 布局）。
  对应原 tests/test_acceptance_e2e_bootstrap.py（meta：SUT 是 test helper）。

业务价值：
  防止 live e2e harness 与 isolation 脚本对 acceptance DuckDB 路径漂移。

退役 / 清理时间（满足任一即可删本文件）：
  1. acceptance_e2e_bootstrap helper 退役，正式入口只用 ops.ACCEPTANCE_DUCKDB_NAME；或
  2. 本检查已并入正式 scripts/check_* + production_gate。

运行：
  uv run python phase-scripts/check_acceptance_e2e_bootstrap_path.py
  uv run python phase-scripts/check_acceptance_e2e_bootstrap_path.py --strict
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.acceptance_e2e_bootstrap import ACCEPTANCE_DUCKDB_NAME, acceptance_db_path


def _run() -> list[str]:
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="qmd-e2e-bootstrap-") as raw:
        sandbox = Path(raw) / "acceptance-sandbox"
        expected = sandbox / "duckdb" / ACCEPTANCE_DUCKDB_NAME
        got = acceptance_db_path(sandbox)
        if got != expected:
            errors.append(f"acceptance_db_path={got} expected={expected}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    errors = _run()
    for item in errors:
        print(f"BOOTSTRAP_PATH: {item}")
    if not errors:
        print("check_acceptance_e2e_bootstrap_path: PASS")
    return 1 if args.strict and errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
