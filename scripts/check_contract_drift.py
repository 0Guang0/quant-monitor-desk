#!/usr/bin/env python3
"""ops/write 契约 YAML ↔ 运行时常量 parity（正式 scripts · production_gate 子步）

仅静态对账：ops_db_inspect_contract / write_contract 与代码常量一致。
loader fail-closed 与 reserved write 无副作用测仍留在
tests/test_contract_drift_ops_write.py。

运行：
  uv run python scripts/check_contract_drift.py --strict
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db.write_manager import WriteManager  # noqa: E402
from backend.app.ops.db_inspector import (  # noqa: E402
    DEFERRED_ITEM_MAPPING,
    FUTURE_PHASE_KEY_TABLES,
    KEY_TABLES,
    REQUIRED_TOP_LEVEL_FIELDS,
    _deferred_mapping_from_contract,
)

OPS_CONTRACT = PROJECT_ROOT / "specs/contracts/ops_db_inspect_contract.yaml"
WRITE_CONTRACT = PROJECT_ROOT / "specs/contracts/write_contract.yaml"


def _load_yaml(path: Path) -> dict:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def _run() -> list[str]:
    errors: list[str] = []
    ops = _load_yaml(OPS_CONTRACT)
    write = _load_yaml(WRITE_CONTRACT)

    contract_tables = tuple(ops["key_tables"])
    if KEY_TABLES != contract_tables:
        errors.append("KEY_TABLES != ops_db_inspect_contract.yaml key_tables")

    contract_future = frozenset(ops["future_phase_key_tables"])
    if FUTURE_PHASE_KEY_TABLES != contract_future:
        errors.append(
            "FUTURE_PHASE_KEY_TABLES != ops_db_inspect_contract.yaml "
            "future_phase_key_tables"
        )

    contract_fields = tuple(ops["required_output_fields"])
    if REQUIRED_TOP_LEVEL_FIELDS != contract_fields:
        errors.append(
            "REQUIRED_TOP_LEVEL_FIELDS != ops_db_inspect_contract.yaml "
            "required_output_fields"
        )

    expected_deferred = _deferred_mapping_from_contract(ops)
    if DEFERRED_ITEM_MAPPING != expected_deferred:
        errors.append(
            "DEFERRED_ITEM_MAPPING != ops_db_inspect_contract.yaml "
            "deferred_item_mapping"
        )

    if tuple(write["implemented_modes"]) != WriteManager.SUPPORTED_MODES:
        errors.append(
            "write_contract implemented_modes != WriteManager.SUPPORTED_MODES"
        )
    if tuple(write["reserved_modes"]) != WriteManager.UNSUPPORTED_MODES:
        errors.append(
            "write_contract reserved_modes != WriteManager.UNSUPPORTED_MODES"
        )

    implemented = tuple(write["implemented_modes"])
    reserved = tuple(write["reserved_modes"])
    enum_modes = tuple(write["write_request"]["fields"]["write_mode"])
    if enum_modes != implemented + reserved:
        errors.append(
            "write_request.write_mode enum != implemented_modes + reserved_modes"
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
        print("PASS: contract drift (ops/write YAML parity)")
        return 0
    print("FAIL: contract drift (ops/write YAML parity)")
    for item in errors:
        print(f"  - {item}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
