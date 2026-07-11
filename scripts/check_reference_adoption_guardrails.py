#!/usr/bin/env python3
"""参考采纳护栏 — 全局静态扫描（正式 scripts · production_gate 子步）

非 phase-script：覆盖 backend/scripts 范围的交易 API、自动登录、静默 fallback、
OpenBB runtime、调度钩子、agent 触发写、EasyXT 硬编码表名、compile+exec。
R3G01/R3G03 模块专项见 phase-scripts/check_r3g_reference_guardrails.py。

运行：
  uv run python scripts/check_reference_adoption_guardrails.py --strict
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.contract_gate_support import (  # noqa: E402
    FORBIDDEN_TRADING_DEF_NAMES,
    scan_file_for_forbidden_substrings,
    scan_forbidden_function_defs,
    scan_guardrail_roots_for_patterns,
    scan_strategy_exec_patterns,
)

GUARDRAILS = PROJECT_ROOT / "specs/contracts/reference_adoption_guardrails.yaml"


def _guardrails() -> dict:
    return yaml.safe_load(GUARDRAILS.read_text(encoding="utf-8")) or {}


def _forbidden_examples(category: str) -> tuple[str, ...]:
    block = (_guardrails().get("forbidden_adoption") or {}).get(category) or {}
    return tuple(block.get("examples") or [])


def _trading_substring_patterns() -> tuple[str, ...]:
    # ponytail: order/buy/sell via AST def scan; bare tokens false-positive in prose.
    skip = FORBIDDEN_TRADING_DEF_NAMES
    return tuple(p for p in _forbidden_examples("real_trading_or_order_api") if p not in skip)


def check_no_trading_api(violations: list[str]) -> None:
    hits = list(scan_guardrail_roots_for_patterns(_trading_substring_patterns()))
    hits.extend(scan_forbidden_function_defs(FORBIDDEN_TRADING_DEF_NAMES))
    for item in hits:
        violations.append(f"trading API: {item}")


def check_no_auto_login(violations: list[str]) -> None:
    patterns = _forbidden_examples("auto_login_or_captcha")
    for item in scan_guardrail_roots_for_patterns(patterns):
        violations.append(f"auto-login/captcha: {item}")


def check_no_silent_fallback(violations: list[str]) -> None:
    patterns = _forbidden_examples("silent_fallback")
    for item in scan_guardrail_roots_for_patterns(patterns):
        violations.append(f"silent-fallback: {item}")


def check_no_openbb_runtime(violations: list[str]) -> None:
    # Split literals so this scripts/ checker is not self-flagged by substring scan.
    openbb = "openbb"
    patterns = _forbidden_examples("copied_openbb_runtime_source") + (
        f"from {openbb}",
        f"import {openbb}",
    )
    for item in scan_guardrail_roots_for_patterns(patterns):
        violations.append(f"OpenBB runtime: {item}")


def check_no_jq2ptrade_scheduler_hook(violations: list[str]) -> None:
    patterns = _forbidden_examples("scheduler_or_execution_hook")
    for item in scan_guardrail_roots_for_patterns(patterns):
        violations.append(f"scheduler/exec hook: {item}")


def check_no_agent_triggered_write(violations: list[str]) -> None:
    patterns = _forbidden_examples("round3g_agent_triggered_write")
    for item in scan_guardrail_roots_for_patterns(patterns):
        violations.append(f"agent-triggered write: {item}")


def check_no_easyxt_hardcoded_table(violations: list[str]) -> None:
    paths = [PROJECT_ROOT / "backend/app/ops/data_health.py"]
    profiles = PROJECT_ROOT / "backend/app/ops/data_health_profiles"
    if profiles.is_dir():
        paths.extend(profiles.rglob("*.py"))
    for path in paths:
        if not path.is_file():
            continue
        hits = scan_file_for_forbidden_substrings(path, ("stock_daily",))
        if hits:
            violations.append(
                f"EasyXT hardcoded table: {path.relative_to(PROJECT_ROOT)}: {hits}"
            )


def check_no_compile_exec(violations: list[str]) -> None:
    for item in scan_strategy_exec_patterns():
        violations.append(f"strategy exec: {item}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when violations are found",
    )
    args = parser.parse_args(argv)

    violations: list[str] = []
    check_no_trading_api(violations)
    check_no_auto_login(violations)
    check_no_silent_fallback(violations)
    check_no_openbb_runtime(violations)
    check_no_jq2ptrade_scheduler_hook(violations)
    check_no_agent_triggered_write(violations)
    check_no_easyxt_hardcoded_table(violations)
    check_no_compile_exec(violations)

    if not violations:
        print("PASS: reference adoption guardrails (global)")
        return 0

    print("FAIL: reference adoption guardrails (global)")
    for item in violations:
        print(f"  - {item}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
