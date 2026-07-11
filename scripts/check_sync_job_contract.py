#!/usr/bin/env python3
"""sync_job_contract.yaml ↔ runtime 常量 parity（正式 scripts · production_gate 子步）

仅静态对账：implemented/reserved job types 与 deferred_error 元数据。
reserved job 抛错 outcome 仍留 tests/test_sync_job_contract.py。

运行：
  uv run python scripts/check_sync_job_contract.py --strict
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.sync.contract import (  # noqa: E402
    DEFERRED_JOB_TYPE_CODE,
    DEFERRED_OWNER,
    DEFERRED_PHASE,
    DOCS_ANCHOR_D2_P1_1,
    IMPLEMENTED_JOB_TYPES,
    RESERVED_JOB_TYPES,
    load_sync_job_contract,
)


def _run() -> list[str]:
    errors: list[str] = []
    contract = load_sync_job_contract()
    yaml_impl = frozenset(contract["implemented_job_types"])
    yaml_reserved = frozenset(contract.get("reserved_job_types") or [])
    if "full_load" not in yaml_impl:
        errors.append("full_load missing from implemented_job_types")
    if "full_load" in yaml_reserved:
        errors.append("full_load must not be in reserved_job_types")
    if yaml_impl != IMPLEMENTED_JOB_TYPES:
        errors.append(
            f"implemented_job_types drift yaml={sorted(yaml_impl)} "
            f"runtime={sorted(IMPLEMENTED_JOB_TYPES)}"
        )
    if yaml_reserved != RESERVED_JOB_TYPES:
        errors.append(
            f"reserved_job_types drift yaml={sorted(yaml_reserved)} "
            f"runtime={sorted(RESERVED_JOB_TYPES)}"
        )
    if not yaml_impl.isdisjoint(yaml_reserved):
        errors.append(f"implemented∩reserved={sorted(yaml_impl & yaml_reserved)}")

    deferred = contract["deferred_error"]
    checks = [
        ("code", DEFERRED_JOB_TYPE_CODE),
        ("owner", DEFERRED_OWNER),
        ("phase", DEFERRED_PHASE),
        ("docs_anchor", DOCS_ANCHOR_D2_P1_1),
    ]
    for key, expected in checks:
        if deferred.get(key) != expected:
            errors.append(
                f"deferred_error.{key}={deferred.get(key)!r} expected={expected!r}"
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
        print("PASS: sync_job_contract parity")
        return 0
    print("FAIL: sync_job_contract parity")
    for item in errors:
        print(f"  - {item}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
