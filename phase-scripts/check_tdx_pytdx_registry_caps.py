#!/usr/bin/env python3
"""tdx_pytdx registry caps / 默认禁用 YAML 盘点（阶段性 · 非业务 pytest）

功能：
  1）source_capabilities.yaml resource_caps 与 port 常量一致；
  2）source_registry.yaml tdx_pytdx enabled_by_default=False 且 validation_only=True。
  对应原 test_tdxPytdx_capsMatchTaskCard 与 disabledByDefault 的 YAML 半边。
  build_route_matrix 行为测仍留 tests/test_tdx_pytdx_port.py。

业务价值：
  防止 registry 与 R3FR-03 cap SSOT 分叉，或 TDX 默认可被 production 选中。

退役 / 清理时间（满足任一即可删本文件）：
  1. tdx_pytdx caps/默认策略迁入稳定 scripts/production_gate 子步；或
  2. TDX 源退役且无替代 registry 行。

运行：
  uv run python phase-scripts/check_tdx_pytdx_registry_caps.py --strict
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.datasources.fetch_ports.tdx_pytdx_port import (  # noqa: E402
    EQUITY_INDEX_MAX_ROWS,
    MAX_NETWORK_CALLS,
    SECURITY_LIST_MAX_ROWS,
)


def _run() -> list[str]:
    errors: list[str] = []
    caps_path = PROJECT_ROOT / "specs/datasource_registry/source_capabilities.yaml"
    caps = (
        (yaml.safe_load(caps_path.read_text(encoding="utf-8")) or {})
        .get("sources", {})
        .get("tdx_pytdx", {})
        .get("resource_caps")
        or {}
    )
    if not (
        caps.get("security_list_max_rows")
        == SECURITY_LIST_MAX_ROWS
        == 20
    ):
        errors.append(
            f"security_list_max_rows caps={caps.get('security_list_max_rows')!r} "
            f"runtime={SECURITY_LIST_MAX_ROWS!r}"
        )
    if not (
        caps.get("equity_daily_bar_max_symbols")
        == EQUITY_INDEX_MAX_ROWS
        == 3
    ):
        errors.append(
            f"equity_daily_bar_max_symbols caps={caps.get('equity_daily_bar_max_symbols')!r} "
            f"runtime={EQUITY_INDEX_MAX_ROWS!r}"
        )
    if caps.get("index_daily_bar_max_symbols") != 3:
        errors.append(
            f"index_daily_bar_max_symbols={caps.get('index_daily_bar_max_symbols')!r}"
        )
    if not (caps.get("max_network_calls") == MAX_NETWORK_CALLS == 5):
        errors.append(
            f"max_network_calls caps={caps.get('max_network_calls')!r} "
            f"runtime={MAX_NETWORK_CALLS!r}"
        )
    if caps.get("minute_bars_enabled") is not False:
        errors.append(f"minute_bars_enabled={caps.get('minute_bars_enabled')!r}")
    if caps.get("full_market_scan_enabled") is not False:
        errors.append(
            f"full_market_scan_enabled={caps.get('full_market_scan_enabled')!r}"
        )

    registry_path = PROJECT_ROOT / "specs/datasource_registry/source_registry.yaml"
    entry = next(
        s
        for s in (yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {})[
            "sources"
        ]
        if s["source_id"] == "tdx_pytdx"
    )
    if entry.get("enabled_by_default") is not False:
        errors.append(f"tdx_pytdx.enabled_by_default={entry.get('enabled_by_default')!r}")
    if entry.get("validation_only") is not True:
        errors.append(f"tdx_pytdx.validation_only={entry.get('validation_only')!r}")
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
        print("PASS: tdx_pytdx registry caps")
        return 0
    print("FAIL: tdx_pytdx registry caps")
    for item in errors:
        print(f"  - {item}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
