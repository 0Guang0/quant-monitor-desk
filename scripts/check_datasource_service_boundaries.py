#!/usr/bin/env python3
"""DataSourceService 调用边界静态扫描（正式 scripts · production_gate 子步）

核对 datasource_service_contract：forbidden_direct_callers 包不得 import
create_adapter；契约 status=active；sync.runners 列入 forbidden 且扫描干净。

对应原 tests/test_datasource_service.py 中三条静态边界测。

运行：
  uv run python scripts/check_datasource_service_boundaries.py --strict
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.contract_gate_support import (  # noqa: E402
    SERVICE_CONTRACT,
    load_yaml,
    scan_package_for_create_adapter,
)


def check_api_and_agent_cannot_import_adapter_factory(violations: list[str]) -> None:
    contract = load_yaml(SERVICE_CONTRACT)
    forbidden_pkgs = contract.get("call_boundaries", {}).get("forbidden_direct_callers") or []
    for pkg in forbidden_pkgs:
        pkg_path = pkg.replace("backend.app.", "")
        hits = scan_package_for_create_adapter(pkg_path)
        for hit in hits:
            violations.append(f"forbidden create_adapter import: {hit}")


def check_datasource_service_contract_status_active(violations: list[str]) -> None:
    contract = load_yaml(SERVICE_CONTRACT)
    status = contract.get("status")
    if status != "active":
        violations.append(f"datasource_service_contract.status={status!r}, expect active")


def check_forbidden_direct_callers_includes_sync_runners(violations: list[str]) -> None:
    contract = load_yaml(SERVICE_CONTRACT)
    forbidden = contract.get("call_boundaries", {}).get("forbidden_direct_callers") or []
    if "backend.app.sync.runners" not in forbidden:
        violations.append("forbidden_direct_callers missing backend.app.sync.runners")
    hits = scan_package_for_create_adapter("sync/runners")
    for hit in hits:
        violations.append(f"sync/runners create_adapter: {hit}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when violations are found",
    )
    args = parser.parse_args(argv)

    violations: list[str] = []
    check_api_and_agent_cannot_import_adapter_factory(violations)
    check_datasource_service_contract_status_active(violations)
    check_forbidden_direct_callers_includes_sync_runners(violations)

    if not violations:
        print("PASS: datasource service boundaries")
        return 0

    print("FAIL: datasource service boundaries")
    for item in violations:
        print(f"  - {item}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
