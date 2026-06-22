#!/usr/bin/env python3
"""Validate contract_coverage.yaml against specs/contracts and test catalog."""

from __future__ import annotations

import sys
from pathlib import Path

from loop_engineering_common import (
    CONTRACT_COVERAGE_PATH,
    REPO_ROOT,
    load_contract_coverage,
    load_test_catalog,
    path_exists,
)

CONTRACTS_DIR = REPO_ROOT / "specs/contracts"
NEGATIVE_TYPES = {"policy-contract", "negative-runtime", "policy-negative"}


def _target_exists(target: str) -> bool:
    norm = target.replace("\\", "/")
    if "::" in norm:
        module, func = norm.split("::", 1)
        path = REPO_ROOT / module
        if not path.is_file():
            return False
        return f"def {func}" in path.read_text(encoding="utf-8")
    return (REPO_ROOT / norm).is_file()


def _has_negative_test(tests: list[str], catalog: dict) -> bool:
    for target in tests:
        module = target.split("::", 1)[0]
        entry = catalog.get(module) or {}
        vtype = str(entry.get("type", ""))
        if vtype in NEGATIVE_TYPES:
            return True
        text = f"{entry.get('purpose', '')} {entry.get('failure_meaning', '')}".lower()
        if any(token in text for token in ("must not", "blocks", "fail-closed", "rejects")):
            return True
    return False


def _coverage_entries(raw: dict) -> dict:
    contracts = raw.get("contracts")
    if isinstance(contracts, dict):
        return contracts
    return {k: v for k, v in raw.items() if k not in {"version", "description"}}


def check_coverage() -> list[str]:
    errors: list[str] = []
    coverage = _coverage_entries(load_contract_coverage())
    catalog = load_test_catalog()

    contract_files = sorted(p.name for p in CONTRACTS_DIR.glob("*.yaml"))
    for contract_file in contract_files:
        rel = f"specs/contracts/{contract_file}"
        entry = coverage.get(rel)
        if not entry:
            errors.append(f"missing coverage entry or waiver: {rel}")
            continue
        if entry.get("waiver"):
            continue
        requirements = entry.get("requirements") or {}
        if not requirements:
            errors.append(f"{rel}: empty requirements and no waiver")
            continue
        for req_id, req in requirements.items():
            tests = req.get("tests") or []
            audit_check = req.get("audit_check")
            if not tests and not audit_check:
                errors.append(f"{rel}/{req_id}: requires tests or audit_check")
            for target in tests:
                if not _target_exists(str(target)):
                    errors.append(f"{rel}/{req_id}: missing test target {target}")
                module = str(target).split("::", 1)[0]
                if module not in catalog:
                    errors.append(f"{rel}/{req_id}: test not in catalog: {module}")
            if req.get("negative_required") and tests and not _has_negative_test(
                [str(t) for t in tests], catalog
            ):
                errors.append(
                    f"{rel}/{req_id}: negative_required but no negative/policy test registered"
                )

    for rel in coverage:
        if not rel.startswith("specs/contracts/"):
            errors.append(f"coverage key must be under specs/contracts/: {rel}")
        elif not path_exists(rel):
            errors.append(f"coverage references missing contract file: {rel}")

    return errors


def main() -> int:
    if not CONTRACT_COVERAGE_PATH.is_file():
        print(f"missing {CONTRACT_COVERAGE_PATH}", file=sys.stderr)
        return 1
    errors = check_coverage()
    if errors:
        print("contract coverage check FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print("OK: contract coverage matrix")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
