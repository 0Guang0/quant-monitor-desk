#!/usr/bin/env python3
"""Validate feature_verification_matrix.yaml consistency."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from loop_engineering_common import (
    FEATURE_MATRIX_PATH,
    REPO_ROOT,
    load_feature_matrix,
    load_test_catalog,
    path_exists,
)

NEGATIVE_TYPES = {"policy-negative", "negative-runtime", "registry-contract"}
SENSITIVE_KEYWORDS = (
    "production",
    "live",
    "security",
    "mutation",
    "write",
    "negative",
)


def _extract_section(text: str, header_prefix: str) -> str:
    lines = text.splitlines()
    start: int | None = None
    end = len(lines)
    prefix = f"## {header_prefix}"
    for i, line in enumerate(lines):
        stripped = line.strip()
        if start is None and stripped.startswith(prefix):
            start = i
            continue
        if start is not None and stripped.startswith("## ") and not stripped.startswith(prefix):
            end = i
            break
    if start is None:
        return ""
    return "\n".join(lines[start:end])


def _pytest_targets_exist(target: str) -> bool:
    norm = target.replace("\\", "/")
    if "::" in norm:
        module, func = norm.split("::", 1)
        path = REPO_ROOT / module
        if not path.is_file():
            return False
        return f"def {func}" in path.read_text(encoding="utf-8")
    return (REPO_ROOT / norm).is_file()


def _catalog_has_test(catalog: dict, target: str) -> bool:
    module = target.split("::", 1)[0].replace("\\", "/")
    return module in catalog


def _master_section9_10_tests() -> set[str]:
    tests: set[str] = set()
    tasks_root = REPO_ROOT / ".trellis/tasks"
    if not tasks_root.is_dir():
        return tests
    pattern = re.compile(r"tests/test_[a-zA-Z0-9_]+\.py")
    for master in tasks_root.rglob("MASTER.plan.md"):
        text = master.read_text(encoding="utf-8")
        scope = _extract_section(text, "9.") + "\n" + _extract_section(text, "10.")
        if not scope.strip():
            continue
        tests.update(pattern.findall(scope))
    return tests


def check_matrix() -> list[str]:
    errors: list[str] = []
    matrix = load_feature_matrix()
    features = matrix.get("features") or {}
    if not features:
        return ["feature_verification_matrix.yaml missing features"]

    catalog = load_test_catalog()
    for feature_id, feature in features.items():
        authorities = feature.get("authorities") or []
        for path in authorities:
            if not path_exists(str(path)):
                errors.append(f"{feature_id}: missing authority {path}")

        acceptance = feature.get("acceptance") or []
        if not acceptance:
            errors.append(f"{feature_id}: no acceptance criteria")
            continue

        for ac in acceptance:
            ac_id = ac.get("id", "<unknown>")
            tests = ac.get("tests") or []
            audit_check = ac.get("audit_check")
            if not tests and not audit_check:
                errors.append(f"{feature_id}/{ac_id}: requires tests or audit_check")
            for target in tests:
                if not _pytest_targets_exist(str(target)):
                    errors.append(f"{feature_id}/{ac_id}: missing test target {target}")
                if not _catalog_has_test(catalog, str(target)):
                    errors.append(f"{feature_id}/{ac_id}: test not in test_catalog: {target}")

            statement = str(ac.get("statement", "")).lower()
            vtype = str(ac.get("verification_type", ""))
            sensitive = any(k in statement for k in SENSITIVE_KEYWORDS)
            if sensitive and vtype not in NEGATIVE_TYPES and not audit_check:
                errors.append(
                    f"{feature_id}/{ac_id}: sensitive AC requires negative test or audit_check"
                )

    for module in _master_section9_10_tests():
        if module not in catalog:
            errors.append(f"MASTER §9/§10 references test not in test_catalog: {module}")

    return errors


def main() -> int:
    if not FEATURE_MATRIX_PATH.is_file():
        print(f"missing {FEATURE_MATRIX_PATH}", file=sys.stderr)
        return 1
    errors = check_matrix()
    if errors:
        print("verification matrix check FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print("OK: feature verification matrix")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
