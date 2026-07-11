#!/usr/bin/env python3
"""source_route_db_acceptance 契约 YAML ↔ 运行时常量 parity（正式 scripts · production_gate 子步）

仅静态对账：
  - required_report_fields ↔ REQUIRED_ACCEPTANCE_REPORT_FIELDS
  - AcceptanceReport.to_dict 覆盖 required 字段
  - documented_matrix_targets.count ↔ DOCUMENTED_SOURCE_MATRIX 长度
对应原 tests/test_source_route_db_acceptance_contract.py 中
test_sourceRouteDbAcceptance_contractFields_matchReportEnvelope（YAML↔常量）。

运行时 spine/CLI outcome 仍留在 tests/。

运行：
  uv run python scripts/check_source_route_db_acceptance_contract.py --strict
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.ops.source_route_db_acceptance import (  # noqa: E402
    REQUIRED_ACCEPTANCE_REPORT_FIELDS,
    AcceptanceReport,
    AcceptanceRequest,
)
from backend.app.ops.source_route_db_acceptance_matrix import (  # noqa: E402
    DOCUMENTED_SOURCE_MATRIX,
)

CONTRACT_PATH = PROJECT_ROOT / "specs/contracts/source_route_db_acceptance_contract.yaml"


def _run() -> list[str]:
    errors: list[str] = []
    contract = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    if not isinstance(contract, dict):
        return ["source_route_db_acceptance_contract.yaml is not a mapping"]

    required = tuple(contract.get("required_report_fields") or ())
    if required != REQUIRED_ACCEPTANCE_REPORT_FIELDS:
        errors.append(
            "required_report_fields != REQUIRED_ACCEPTANCE_REPORT_FIELDS "
            f"(yaml={len(required)} py={len(REQUIRED_ACCEPTANCE_REPORT_FIELDS)})"
        )

    request = AcceptanceRequest.from_target("macro_series:fred:fetch_macro_series")
    payload = AcceptanceReport.not_implemented(request).to_dict()
    missing = [field for field in required if field not in payload]
    if missing:
        errors.append(f"AcceptanceReport.to_dict missing fields: {missing}")

    documented = contract.get("documented_matrix_targets") or {}
    expected_count = documented.get("count")
    if expected_count is not None and int(expected_count) != len(DOCUMENTED_SOURCE_MATRIX):
        errors.append(
            f"documented_matrix_targets.count={expected_count} != "
            f"len(DOCUMENTED_SOURCE_MATRIX)={len(DOCUMENTED_SOURCE_MATRIX)}"
        )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    errors = _run()
    for item in errors:
        print(f"CONTRACT_VIOLATION: {item}")
    if not errors:
        print("check_source_route_db_acceptance_contract: PASS")
    return 1 if args.strict and errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
