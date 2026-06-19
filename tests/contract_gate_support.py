"""Shared helpers for Round2.6 Phase B contract-gate tests."""

from __future__ import annotations

import ast
import importlib.util
import platform
import re
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SERVICE_CONTRACT = PROJECT_ROOT / "specs/contracts/datasource_service_contract.yaml"
BACKEND_APP = PROJECT_ROOT / "backend" / "app"

ALLOWED_ADAPTER_FACTORY_PATHS = {
    PROJECT_ROOT / "backend" / "app" / "datasources" / "adapters" / "__init__.py",
    PROJECT_ROOT / "backend" / "app" / "datasources" / "__init__.py",
    PROJECT_ROOT / "backend" / "app" / "datasources" / "service.py",
}


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_checker_module():
    spec = importlib.util.spec_from_file_location(
        "check_module_boundaries",
        PROJECT_ROOT / "scripts" / "check_module_boundaries.py",
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def collect_imports(py_path: Path) -> set[str]:
    tree = ast.parse(py_path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
            for alias in node.names:
                imports.add(f"{node.module}.{alias.name}")
    return imports


def scan_package_for_create_adapter(relative_pkg: str) -> list[str]:
    pkg_root = BACKEND_APP / relative_pkg.replace(".", "/")
    if not pkg_root.is_dir():
        return []
    violations: list[str] = []
    for py_file in pkg_root.rglob("*.py"):
        if py_file in ALLOWED_ADAPTER_FACTORY_PATHS:
            continue
        imports = collect_imports(py_file)
        if "create_adapter" in imports or any(imp.endswith(".create_adapter") for imp in imports):
            rel = py_file.relative_to(PROJECT_ROOT)
            violations.append(f"{rel}: imports adapter factory")
    return violations


def scan_file_for_forbidden_substrings(py_path: Path, patterns: tuple[str, ...]) -> list[str]:
    text = py_path.read_text(encoding="utf-8")
    lowered = text.lower()
    hits: list[str] = []
    for pattern in patterns:
        token = pattern.lower()
        if re.search(rf"\b{re.escape(token)}\b", lowered):
            hits.append(pattern)
    return hits


def scan_backend_python_for_patterns(
    patterns: tuple[str, ...],
    *,
    root: Path | None = None,
) -> list[str]:
    root = root or BACKEND_APP
    violations: list[str] = []
    for py_file in root.rglob("*.py"):
        if "tests" in py_file.parts:
            continue
        hits = scan_file_for_forbidden_substrings(py_file, patterns)
        if hits:
            rel = py_file.relative_to(PROJECT_ROOT)
            violations.append(f"{rel}: forbidden pattern(s) {hits}")
    return violations


def platform_key() -> str:
    plat = platform.system().lower()
    if plat == "windows":
        return "windows"
    if plat == "darwin":
        return "macos"
    return "linux"
