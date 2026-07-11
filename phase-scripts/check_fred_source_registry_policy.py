#!/usr/bin/env python3
"""FRED registry 默认禁用策略盘点（阶段性 · 非业务 pytest）

功能：
  核对 source_registry.yaml / source_capabilities.yaml 中 fred 行：
  enabled_by_default=False，且 capability 操作无 production_default=True。
  对应原 tests/test_fred_source_registry.py::test_fredRegistry_disabledByDefault_notProductionLive。

业务价值：
  防止 registry 漂移把 FRED 默认可当 production-live 源；series cap 运行时测仍留 pytest。

退役 / 清理时间（满足任一即可删本文件）：
  1. FRED 正式 production-live 关账且 registry 策略改由稳定 scripts/production_gate 子步承接；或
  2. fred 源从 registry 移除且无替代默认启用路径。

运行：
  uv run python phase-scripts/check_fred_source_registry_policy.py --strict
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.contract_gate_support import load_yaml  # noqa: E402

SOURCE_REGISTRY = PROJECT_ROOT / "specs/datasource_registry/source_registry.yaml"
SOURCE_CAPABILITIES = PROJECT_ROOT / "specs/datasource_registry/source_capabilities.yaml"


def _run() -> list[str]:
    errors: list[str] = []
    registry = load_yaml(SOURCE_REGISTRY)
    entry = next(
        (s for s in (registry.get("sources") or []) if s.get("source_id") == "fred"),
        None,
    )
    if entry is None:
        return ["fred source_id missing from source_registry.yaml"]
    if entry.get("enabled_by_default") is not False:
        errors.append(f"fred.enabled_by_default={entry.get('enabled_by_default')!r}")
    if "macro_series" not in (entry.get("allowed_domains") or []):
        errors.append("fred.allowed_domains missing macro_series")

    capabilities = load_yaml(SOURCE_CAPABILITIES)
    cap = (capabilities.get("sources") or {}).get("fred") or {}
    status = cap.get("status")
    if status not in {
        "sandbox_candidate",
        "proposed_disabled_source",
        "READY_WITH_EVIDENCE",
    }:
        errors.append(f"fred capability status unexpected: {status!r}")
    for domain_cfg in (cap.get("domains") or {}).values():
        for op in (domain_cfg.get("operations") or {}).values():
            if op.get("production_default") is True:
                errors.append("fred operation has production_default=True")
            if op.get("enabled_by_default") is not False:
                errors.append(
                    f"fred operation enabled_by_default={op.get('enabled_by_default')!r}"
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
        print("PASS: fred source registry policy")
        return 0
    print("FAIL: fred source registry policy")
    for item in errors:
        print(f"  - {item}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
