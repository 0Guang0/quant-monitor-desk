#!/usr/bin/env python3
"""Static import boundary checker for Round2.6 module_boundary_contract.yaml."""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = PROJECT_ROOT / "specs/contracts/module_boundary_contract.yaml"
BACKEND_APP = PROJECT_ROOT / "backend" / "app"


def load_contract() -> dict:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8")) or {}


def module_prefix_for_path(py_path: Path) -> str | None:
    parts = py_path.parts
    for idx, part in enumerate(parts):
        if part == "app" and idx > 0 and parts[idx - 1] == "backend" and idx + 1 < len(parts):
            return parts[idx + 1]
    try:
        rel = py_path.relative_to(BACKEND_APP)
    except ValueError:
        return None
    return rel.parts[0] if rel.parts else None


def collect_imports(py_path: Path) -> set[str]:
    try:
        tree = ast.parse(py_path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        raise SyntaxError(f"BOUNDARY_CHECK_ABORTED: {py_path}: {exc}") from exc
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def normalize_forbidden(rule: str) -> str:
    return rule.split()[0].strip()


def check_file(py_path: Path, contract: dict) -> list[str]:
    module_key = module_prefix_for_path(py_path)
    if module_key is None:
        return []
    rules = (contract.get("modules") or {}).get(module_key) or {}
    forbidden = [normalize_forbidden(r) for r in rules.get("must_not_import") or []]
    if not forbidden:
        return []

    imports = collect_imports(py_path)
    violations: list[str] = []
    try:
        rel = py_path.relative_to(PROJECT_ROOT)
    except ValueError:
        rel = py_path
    for rule in forbidden:
        for imp in imports:
            if imp == rule or imp.startswith(rule + "."):
                violations.append(f"{rel}: forbidden import {imp!r} (rule {rule!r})")
    return violations


def check_paths(paths: list[Path], contract: dict | None = None) -> list[str]:
    contract = contract or load_contract()
    violations: list[str] = []
    for path in paths:
        try:
            if path.is_dir():
                for py_file in path.rglob("*.py"):
                    violations.extend(check_file(py_file, contract))
            elif path.suffix == ".py":
                violations.extend(check_file(path, contract))
        except SyntaxError as exc:
            violations.append(str(exc))
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check backend module import boundaries")
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional paths to scan (default: backend/app)",
    )
    args = parser.parse_args(argv)
    targets = [Path(p) for p in args.paths] if args.paths else [BACKEND_APP]
    contract = load_contract()
    violations = check_paths(targets, contract)
    if violations:
        print("Module boundary violations:")
        for v in violations:
            print(f"  - {v}")
        return 1
    print("Module boundary check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
