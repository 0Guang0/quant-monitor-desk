"""Round2.6 Phase B — DataSourceService import boundary contract tests."""

from __future__ import annotations

from tests.contract_gate_support import (
    ALLOWED_ADAPTER_FACTORY_PATHS,
    PROJECT_ROOT,
    SERVICE_CONTRACT,
    collect_imports,
    load_yaml,
    scan_package_for_create_adapter,
)

BACKEND_APP = PROJECT_ROOT / "backend" / "app"
RUNNERS = BACKEND_APP / "sync" / "runners.py"
CONCRETE_ADAPTER_PREFIX = "backend.app.datasources.adapters."


def _load_service_contract() -> dict:
    return load_yaml(SERVICE_CONTRACT)


def test_apiAndAgentCannotImportAdapterFactory() -> None:
    contract = _load_service_contract()
    forbidden_pkgs = contract.get("call_boundaries", {}).get("forbidden_direct_callers") or []
    violations: list[str] = []
    for pkg in forbidden_pkgs:
        pkg_path = pkg.replace("backend.app.", "")
        violations.extend(scan_package_for_create_adapter(pkg_path))
    assert violations == [], (
        "production modules must not import create_adapter directly: " + "; ".join(violations)
    )


def test_serviceBuildsRouteBeforeFetch() -> None:
    """Contract tracer: fetch gate order frozen in datasource_service_contract.yaml."""
    contract = _load_service_contract()
    steps = contract["public_methods"]["fetch"]["required_steps"]
    assert steps == [
        "load_source_registry",
        "load_capability_registry",
        "build_source_route_plan",
        "check_resource_guard",
        "create_adapter_internal_only",
        "call_adapter_fetch",
        "ensure_fetch_log_or_failure_event",
    ]


def test_serviceContract_declaresFetchGateOrder() -> None:
    test_serviceBuildsRouteBeforeFetch()


def test_forbiddenDirectCallers_includesSyncRunners_andScanIsContractDriven() -> None:
    contract = _load_service_contract()
    forbidden = contract.get("call_boundaries", {}).get("forbidden_direct_callers") or []
    assert "backend.app.sync.runners" in forbidden
    assert scan_package_for_create_adapter("sync/runners") == []


def test_createAdapterImports_onlyUnderTests() -> None:
    """create_adapter imports allowed only in datasources factory modules until Task 2 service."""
    violations: list[str] = []
    for py_file in BACKEND_APP.rglob("*.py"):
        if py_file in ALLOWED_ADAPTER_FACTORY_PATHS:
            continue
        imports = collect_imports(py_file)
        if "create_adapter" in imports or any(imp.endswith(".create_adapter") for imp in imports):
            rel = py_file.relative_to(PROJECT_ROOT)
            violations.append(str(rel))
    assert violations == [], f"create_adapter found outside allowed factory paths: {violations}"


def test_syncRunners_doesNotImportConcreteAdaptersOrFactory() -> None:
    imports = collect_imports(RUNNERS)
    assert "create_adapter" not in imports
    assert not any(imp.startswith(CONCRETE_ADAPTER_PREFIX) for imp in imports)
    assert not any(imp.endswith("Adapter") and "adapters" in imp for imp in imports)
