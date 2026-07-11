#!/usr/bin/env python3
"""R3H resource_caps YAML↔port 常量 parity（阶段性 · 非业务 pytest）

功能：
  核对 source_capabilities.yaml resource_caps 与各 fetch_ports 模块 MAX_* 常量。
  对应原 test_r3h01_officialMacroCaps_matchRegistry /
  test_r3h02_marketCaps_matchRegistry / test_r3h02_cryptoCaps_matchRegistry。

业务价值：
  防止 registry 与 port 层 cap 权威分裂；cap overflow 行为测仍留各 adapters pytest。

退役 / 清理时间（满足任一即可删本文件）：
  1. caps SSOT 迁入稳定 scripts/production_gate 子步；或
  2. port 改为运行时只读 YAML caps、不再维护模块常量。

运行：
  uv run python phase-scripts/check_r3h_resource_caps_parity.py --strict
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

CAPS_PATH = PROJECT_ROOT / "specs/datasource_registry/source_capabilities.yaml"

# (source_id, yaml_key, port_attr, module_name)
CHECKS: tuple[tuple[str, str, str, str], ...] = (
    ("fred", "max_series", "MAX_SERIES", "fred_port"),
    ("fred", "max_rows_per_series", "MAX_ROWS_PER_SERIES", "fred_port"),
    ("fred", "max_window_days", "MAX_WINDOW_DAYS", "fred_port"),
    ("us_treasury", "max_tenors", "MAX_TENORS", "us_treasury_port"),
    ("us_treasury", "max_rows", "MAX_ROWS", "us_treasury_port"),
    ("sec_edgar", "max_ciks", "MAX_CIKS", "sec_edgar_port"),
    ("sec_edgar", "max_filings", "MAX_FILINGS", "sec_edgar_port"),
    ("cftc_cot", "max_markets", "MAX_MARKETS", "cftc_cot_port"),
    ("cftc_cot", "max_rows", "MAX_ROWS", "cftc_cot_port"),
    ("bis", "max_countries", "MAX_COUNTRIES", "bis_port"),
    ("world_bank", "max_indicators", "MAX_INDICATORS", "world_bank_port"),
    ("world_bank", "max_countries", "MAX_COUNTRIES", "world_bank_port"),
    ("alpha_vantage", "max_symbols", "MAX_SYMBOLS", "alpha_vantage_port"),
    ("alpha_vantage", "max_rows", "MAX_ROWS", "alpha_vantage_port"),
    ("alpha_vantage", "max_window_days", "MAX_WINDOW_DAYS", "alpha_vantage_port"),
    ("alpha_vantage", "max_option_strikes", "MAX_OPTION_STRIKES", "alpha_vantage_port"),
    ("stooq", "max_symbols", "MAX_SYMBOLS", "stooq_port"),
    ("stooq", "max_rows", "MAX_ROWS", "stooq_port"),
    ("stooq", "max_window_days", "MAX_WINDOW_DAYS", "stooq_port"),
    ("yahoo_finance", "max_symbols", "MAX_SYMBOLS", "yahoo_finance_port"),
    ("yahoo_finance", "max_window_days", "MAX_WINDOW_DAYS", "yahoo_finance_port"),
    ("deribit", "max_instruments", "MAX_INSTRUMENTS", "deribit_port"),
    ("deribit", "max_surface_rows", "MAX_SURFACE_ROWS", "deribit_port"),
    ("coingecko", "max_assets", "MAX_ASSETS", "coingecko_port"),
)


def _run() -> list[str]:
    errors: list[str] = []
    sources = (yaml.safe_load(CAPS_PATH.read_text(encoding="utf-8")) or {}).get(
        "sources"
    ) or {}
    for source_id, yaml_key, port_attr, module_name in CHECKS:
        caps = (sources.get(source_id) or {}).get("resource_caps") or {}
        if yaml_key not in caps:
            errors.append(f"{source_id}: missing resource_caps.{yaml_key}")
            continue
        mod = importlib.import_module(
            f"backend.app.datasources.fetch_ports.{module_name}"
        )
        runtime = getattr(mod, port_attr, None)
        if caps[yaml_key] != runtime:
            errors.append(
                f"{source_id}.{yaml_key}: yaml={caps[yaml_key]!r} "
                f"{module_name}.{port_attr}={runtime!r}"
            )
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
        print("PASS: R3H resource_caps parity")
        return 0
    print("FAIL: R3H resource_caps parity")
    for item in errors:
        print(f"  - {item}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
