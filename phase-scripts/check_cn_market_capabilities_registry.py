#!/usr/bin/env python3
"""CN 市场十源 capabilities 终态登记盘点（阶段性 · 非业务 pytest）

功能：
  核对 source_capabilities.yaml 中 R3H-03 十源均为 READY_WITH_EVIDENCE，
  且 replay_fixture_path / fetch_port_path 非空。
  对应原 tests/test_cn_market_adapters.py::test_baostock_registry_readyWithEvidenceStatus。

业务价值：
  防止 CN 源回退到 proposed-disabled 占位；port/layer smoke 仍留 pytest。

退役 / 清理时间（满足任一即可删本文件）：
  1. CN 十源 registry 终态由稳定 scripts/production_gate 子步承接；或
  2. R3H-03 源集合退役/合并后无对应 capabilities 行。

运行：
  uv run python phase-scripts/check_cn_market_capabilities_registry.py --strict
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CAPS_PATH = PROJECT_ROOT / "specs/datasource_registry/source_capabilities.yaml"

R3H03_CN_SOURCES: tuple[str, ...] = (
    "baostock",
    "cninfo",
    "akshare",
    "tdx_pytdx",
    "mootdx",
    "eastmoney",
    "sina_finance",
    "ths_ifind",
    "qmt_xtdata",
    "qmt_xqshare",
)


def _run() -> list[str]:
    errors: list[str] = []
    sources = (yaml.safe_load(CAPS_PATH.read_text(encoding="utf-8")) or {}).get(
        "sources"
    ) or {}
    for source_id in R3H03_CN_SOURCES:
        entry = sources.get(source_id) or {}
        if entry.get("status") != "READY_WITH_EVIDENCE":
            errors.append(f"{source_id}: status={entry.get('status')!r}")
        if not entry.get("replay_fixture_path"):
            errors.append(f"{source_id}: missing replay_fixture_path")
        if not entry.get("fetch_port_path"):
            errors.append(f"{source_id}: missing fetch_port_path")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when violations are found",
    )
    args = parser.parse_args(argv)
    errors = _run()
    if not errors:
        print("PASS: CN market capabilities registry")
        return 0
    print("FAIL: CN market capabilities registry")
    for item in errors:
        print(f"  - {item}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
