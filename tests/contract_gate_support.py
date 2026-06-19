"""Shared helpers for Round2.6 Phase B contract-gate tests."""

from __future__ import annotations

import ast
import importlib.util
import os
import platform
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_REGISTRY = PROJECT_ROOT / "specs/datasource_registry/source_registry.yaml"
SOURCE_CAPABILITIES = PROJECT_ROOT / "specs/datasource_registry/source_capabilities.yaml"
PLATFORM_MATRIX = PROJECT_ROOT / "specs/contracts/platform_source_matrix.yaml"
SERVICE_CONTRACT = PROJECT_ROOT / "specs/contracts/datasource_service_contract.yaml"
BACKEND_APP = PROJECT_ROOT / "backend" / "app"

FORBIDDEN_ADAPTER_FACTORY_IMPORTS = (
    "backend.app.datasources.adapters",
    "backend.app.datasources.adapters.create_adapter",
    "create_adapter",
)

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


def capability_declared(
    capabilities: dict[str, Any], source_id: str, data_domain: str
) -> bool:
    entry = (capabilities.get("sources") or {}).get(source_id) or {}
    return data_domain in (entry.get("domains") or {})


@dataclass
class SourceRouteCandidate:
    source_id: str
    role: str
    enabled: bool
    allowed_domain: str
    capability_declared: bool
    disabled_reason: str | None = None
    skip_reason: str | None = None


@dataclass
class SourceRoutePlan:
    route_plan_id: str
    run_id: str
    job_id: str
    data_domain: str
    operation: str
    route_status: str
    selected_source_id: str | None
    candidates: list[SourceRouteCandidate] = field(default_factory=list)
    quality_flags: list[str] = field(default_factory=list)
    created_at: str = "2026-06-19T00:00:00+00:00"


def _source_registry_entry(registry: dict[str, Any], source_id: str) -> dict[str, Any] | None:
    for source in registry.get("sources") or []:
        if source["source_id"] == source_id:
            return source
    return None


def _source_enabled(source_id: str, registry: dict[str, Any]) -> tuple[bool, str | None]:
    entry = _source_registry_entry(registry, source_id)
    if entry is None:
        return False, "source_not_in_registry"
    if not entry.get("enabled_by_default"):
        return False, "source_disabled_by_default"
    return True, None


def _platform_allows(source_id: str, matrix: dict[str, Any]) -> tuple[bool, str | None]:
    key = platform_key()
    entry = ((matrix.get("platforms") or {}).get(key) or {}).get(source_id) or {}
    if not entry:
        return False, f"platform_matrix_missing:{key}:{source_id}"
    if source_id == "qmt_xtdata" and not entry.get("available_if_user_configured", False):
        return False, "qmt_xtdata_not_available_on_this_platform"
    if source_id == "qmt_xqshare":
        for env_name in entry.get("requires_env") or []:
            if not os.environ.get(env_name):
                return False, f"missing_env:{env_name}"
        if not entry.get("default_enabled", False):
            return False, "user_authorization_required"
    if not entry.get("default_enabled", False) and entry.get("requires_user_confirmation"):
        return False, "user_authorization_required"
    return bool(entry.get("available_if_user_configured", False)), None


class ContractSourceRoutePlanner:
    """Minimal contract planner for Phase B — not production code."""

    def __init__(self) -> None:
        self._registry = load_yaml(SOURCE_REGISTRY)
        self._matrix = load_yaml(PLATFORM_MATRIX)
        self._capabilities = load_yaml(SOURCE_CAPABILITIES)

    def plan(
        self,
        *,
        data_domain: str,
        operation: str,
        run_id: str = "contract-gate-run",
        job_id: str = "contract-gate-job",
        use_fallback: bool = False,
        extra_candidates: list[tuple[str, str]] | None = None,
    ) -> SourceRoutePlan:
        domain_roles = (self._registry.get("domain_roles") or {}).get(data_domain) or {}
        ordered: list[tuple[str, str]] = []
        if domain_roles.get("primary"):
            ordered.append((domain_roles["primary"], "Primary"))
        for vid in domain_roles.get("validation") or []:
            ordered.append((vid, "Validation"))
        if use_fallback:
            for fid in domain_roles.get("fallback_policy") or []:
                ordered.append((fid, "FallbackPolicy"))
        if extra_candidates:
            ordered.extend(extra_candidates)

        candidates: list[SourceRouteCandidate] = []
        selected: str | None = None
        quality_flags: list[str] = []
        route_status = "NO_AVAILABLE_SOURCE"

        for source_id, role in ordered:
            cap_ok = capability_declared(self._capabilities, source_id, data_domain)
            plat_ok, plat_reason = _platform_allows(source_id, self._matrix)
            reg_ok, reg_reason = _source_enabled(source_id, self._registry)
            disabled_reason = None
            skip_reason = None

            if not cap_ok:
                disabled_reason = "capability_missing"
            elif not plat_ok:
                disabled_reason = plat_reason
            elif not reg_ok:
                disabled_reason = reg_reason
            else:
                disabled_reason = None

            skip_reason = disabled_reason
            schedulable = disabled_reason is None

            candidates.append(
                SourceRouteCandidate(
                    source_id=source_id,
                    role=role,
                    enabled=schedulable,
                    allowed_domain=data_domain,
                    capability_declared=cap_ok,
                    disabled_reason=disabled_reason,
                    skip_reason=skip_reason,
                )
            )
            if schedulable and selected is None:
                selected = source_id
                route_status = "READY"
                if role == "FallbackPolicy":
                    quality_flags.append("SOURCE_FALLBACK_USED")

        if route_status != "READY":
            selected = None
            if any(c.source_id == "qmt_xtdata" and c.skip_reason for c in candidates):
                route_status = "DISABLED_SOURCE"
            elif any(c.skip_reason == "capability_missing" for c in candidates):
                route_status = "CAPABILITY_MISSING"

        return SourceRoutePlan(
            route_plan_id="contract-gate-plan",
            run_id=run_id,
            job_id=job_id,
            data_domain=data_domain,
            operation=operation,
            route_status=route_status,
            selected_source_id=selected,
            candidates=candidates,
            quality_flags=quality_flags,
        )
