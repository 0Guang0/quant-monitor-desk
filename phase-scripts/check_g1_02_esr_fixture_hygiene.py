#!/usr/bin/env python3
"""G1-02 阶段：ESR / 内存撬门 / 测试夹具卫生扫描（阶段性 · 非 pytest 业务套件）

功能：
  静态检查两件事，不跑业务行为：
  1）测试夹具 tests/service_path_support.py 是否仍含 object.__setattr__ / 强制 platform 等「内存 OVERRIDE」字样，
     以及是否仍提供 enable_source_route 正规入口（唯一公开名；禁止并列 build_sandbox_route_planner）；
  2）生产路径（ops 增量/验收、CLI 金路径）是否仍残留 enabled_source_registry、强制 _platform_allows、
     object.__setattr__(is_enabled)、以及任何 def enabled_*_source_registry 薄包装。
  对应原 pytest：test_etest_overlay_governance、test_g1_02_* 里的源码字符串断言。

业务价值：
  G1-02 迁移期防止「关账证据靠 patch 已加载对象」或「生产又抄回 ESR」。
  按 completion-check TEST-EVIDENCE-GOVERNANCE：这是 artifact-guard / phase-guard，
  不是生产 outcome 测试，不得进 tests/ 业务套件，也不得单独当作 R4/产品启用关账证据。

退役 / 清理时间（满足任一即可删本文件）：
  1. G1-02 全部票（含 4a/4b 生产 ESR 清零）关账完成，且正式 CI 已有等价门禁（pre-commit / production_gate 子步）；或
  2. 生产侧已无 ESR 旁路、夹具卫生由固定 CI 脚本接管，且 master 连续 2 周无本扫描告警回流；或
  3. ADR-018 两层启用链路被权威 design 废止并替换为新 SSOT（届时本扫描模式失效，应整文件删除而非改成业务测）。

运行：
  uv run python phase-scripts/check_g1_02_esr_fixture_hygiene.py
  uv run python phase-scripts/check_g1_02_esr_fixture_hygiene.py --strict

guidelines 对齐：
  - testing-guidelines §9 / completion-check 禁入：meta-testing、phase-guard → 不进业务 pytest
  - AGENTS.md → 阶段性流程放 phase-scripts，中文写明功能、价值、退役条件
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OPS = PROJECT_ROOT / "backend" / "app" / "ops"
CLI = PROJECT_ROOT / "backend" / "app" / "cli"
SERVICE_PATH_SUPPORT = PROJECT_ROOT / "tests" / "service_path_support.py"
DATA_COMMANDS = CLI / "data_commands.py"

PROD_ESR_PATHS = (
    OPS / "macro_incremental_common.py",
    OPS / "fred_incremental_run.py",
    OPS / "fred_incremental_watermark.py",
    OPS / "alpha_vantage_incremental_run.py",
    OPS / "bis_incremental_run.py",
    OPS / "cftc_incremental_run.py",
    OPS / "cninfo_incremental_run.py",
    OPS / "cninfo_incremental_watermark.py",
    OPS / "deribit_incremental_run.py",
    OPS / "deribit_incremental_watermark.py",
    OPS / "sec_edgar_incremental_run.py",
    OPS / "sec_edgar_incremental_watermark.py",
    OPS / "us_treasury_incremental_run.py",
    OPS / "world_bank_incremental_run.py",
    OPS / "source_route_db_acceptance.py",
    OPS / "source_route_db_acceptance_matrix.py",
    OPS / "matrix_live_handlers.py",
)

# 生产模块内禁止出现的旁路形态（字面 / 简单正则）
_ESR_REGEX = (
    re.compile(r"object\.__setattr__\([^)]*is_enabled"),
    re.compile(r"planner\._platform_allows\s*="),
    re.compile(r"def enabled_source_registry\s*\("),
    re.compile(r"def enabled_\w+_source_registry\s*\("),
)

_ESR_LITERALS = (
    "object.__setattr__(",
    "planner._platform_allows =",
    "def enabled_source_registry(",
)

_ENABLED_ALIAS_DEF = re.compile(r"def enabled_\w+_source_registry\s*\(")

_GOLD_MARKERS = (
    "enabled_source_registry",
    "object.__setattr__",
    "planner._platform_allows =",
)


def _fail(msg: str, violations: list[str]) -> None:
    violations.append(msg)


def check_fixture_hygiene(violations: list[str]) -> None:
    """E-TEST-01：夹具不得再用内存撬门作关账证据。"""
    if not SERVICE_PATH_SUPPORT.is_file():
        _fail(f"missing fixture file: {SERVICE_PATH_SUPPORT}", violations)
        return
    text = SERVICE_PATH_SUPPORT.read_text(encoding="utf-8")
    if "def enable_source_route(" not in text:
        _fail("service_path_support.py: missing enable_source_route", violations)
    if "def build_sandbox_route_planner(" in text:
        _fail(
            "service_path_support.py: build_sandbox_route_planner must be inlined into enable_source_route",
            violations,
        )
    for bad in (
        "object.__setattr__",
        "monkeypatch.setattr(planner",
        'setattr(planner, "_platform_allows"',
        "force_platform",
    ):
        if bad in text:
            _fail(f"service_path_support.py still contains banned seam: {bad!r}", violations)


def check_ops_esr_zero(violations: list[str]) -> None:
    """票 06 静态面：增量/验收生产模块无 ESR 旁路。"""
    activation = (
        PROJECT_ROOT / "backend" / "app" / "datasources" / "incremental_route_activation.py"
    )
    if activation.is_file():
        act = activation.read_text(encoding="utf-8")
        for bad in (
            "registry._sources",
            "registry._domain_roles",
            "capabilities._raw",
            "def build_sandbox_route_planner",
            "is_enabled=True",
        ):
            if bad in act:
                _fail(f"incremental_route_activation.py still contains {bad!r}", violations)
    common = OPS / "macro_incremental_common.py"
    if common.is_file():
        text = common.read_text(encoding="utf-8")
        if "def load_incremental_route_bundle(" not in text:
            _fail("macro_incremental_common.py: missing load_incremental_route_bundle", violations)
        for pat in _ESR_REGEX:
            if pat.search(text):
                _fail(
                    f"macro_incremental_common.py forbidden pattern: {pat.pattern}",
                    violations,
                )
    watermark = OPS / "fred_incremental_watermark.py"
    if watermark.is_file():
        wt = watermark.read_text(encoding="utf-8")
        if "def enabled_fred_source_registry" in wt:
            _fail("fred_incremental_watermark.py still defines enabled_fred_source_registry", violations)
    for path in PROD_ESR_PATHS:
        if not path.is_file():
            _fail(f"missing production path for scan: {path.relative_to(PROJECT_ROOT)}", violations)
            continue
        text = path.read_text(encoding="utf-8")
        for lit in _ESR_LITERALS:
            if lit in text:
                _fail(f"{path.relative_to(PROJECT_ROOT)}: contains {lit!r}", violations)
        if _ENABLED_ALIAS_DEF.search(text):
            _fail(
                f"{path.relative_to(PROJECT_ROOT)}: still defines enabled_*_source_registry",
                violations,
            )


def _gold_path_function_source() -> str:
    text = DATA_COMMANDS.read_text(encoding="utf-8")
    match = re.search(
        r"def _gold_path_backfill_route_preview\(.*?(?=\ndef [a-zA-Z_])",
        text,
        flags=re.DOTALL,
    )
    if match is None:
        return ""
    return match.group(0)


def check_gold_path_esr_zero(violations: list[str]) -> None:
    """票 07 静态面：金路径 fred/else 与 mootdx CLI 无 ESR。"""
    if not DATA_COMMANDS.is_file():
        _fail(f"missing {DATA_COMMANDS.relative_to(PROJECT_ROOT)}", violations)
        return
    body = _gold_path_function_source()
    if not body:
        _fail("_gold_path_backfill_route_preview missing in data_commands.py", violations)
        return
    for marker in _GOLD_MARKERS:
        if marker in body:
            _fail(f"gold path body still uses {marker!r}", violations)
    if "else:" not in body:
        _fail("gold path missing else branch (non-fred)", violations)
    else:
        fred_part, else_part = body.split("else:", 1)
        if "fred" not in fred_part:
            _fail("gold path fred branch marker missing", violations)
        for marker in _GOLD_MARKERS:
            if marker in fred_part:
                _fail(f"gold path fred branch still uses {marker!r}", violations)
            if marker in else_part:
                _fail(f"gold path else branch still uses {marker!r}", violations)
    full = DATA_COMMANDS.read_text(encoding="utf-8")
    if "mootdx" not in full:
        _fail("data_commands.py: mootdx reference missing", violations)
    if 'enabled_source_registry(source_id="mootdx"' in full:
        _fail("data_commands.py: mootdx still uses enabled_source_registry", violations)
    if "enabled_source_registry(source_id='mootdx'" in full:
        _fail("data_commands.py: mootdx still uses enabled_source_registry", violations)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="有违例时 exit 1（关账/人工门禁用）",
    )
    args = parser.parse_args(argv)

    violations: list[str] = []
    check_fixture_hygiene(violations)
    check_ops_esr_zero(violations)
    check_gold_path_esr_zero(violations)

    if not violations:
        print("G1-02 ESR/fixture hygiene: OK")
        return 0

    print("G1-02 ESR/fixture hygiene: VIOLATIONS")
    for item in violations:
        print(f"  - {item}")
    if args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
