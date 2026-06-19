"""Round2.6 Phase B — module boundary contract tests."""

from __future__ import annotations

from pathlib import Path

import yaml
from tests.contract_gate_support import PROJECT_ROOT, load_checker_module

CONTRACT_PATH = PROJECT_ROOT / "specs/contracts/module_boundary_contract.yaml"

_checker = load_checker_module()
check_file = _checker.check_file
load_contract = _checker.load_contract
check_paths = _checker.check_paths


def test_moduleBoundaryContract_listsRequiredChecks() -> None:
    contract = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8")) or {}
    checks = contract.get("required_checks") or []
    assert "scripts/check_module_boundaries.py" in checks
    assert "tests/test_module_boundaries.py" in checks


def test_checkModuleBoundaries_detectsForbiddenImportFixture(tmp_path: Path) -> None:
    contract = load_contract()
    backend_app = tmp_path / "backend" / "app" / "api"
    backend_app.mkdir(parents=True)
    probe = backend_app / "violation_probe.py"
    probe.write_text(
        "from backend.app.datasources.adapters import create_adapter\n",
        encoding="utf-8",
    )
    violations = check_file(probe, contract)
    assert violations, f"expected forbidden import detection, got {violations}"


def test_productionBackend_passesModuleBoundaryScan() -> None:
    backend = PROJECT_ROOT / "backend" / "app"
    violations = check_paths([backend])
    assert violations == [], f"production boundary violations: {violations}"


def test_layerModules_forbidAdapterImports() -> None:
    contract = load_contract()
    for layer in (
        "layer1_axes",
        "layer2_sensors",
        "layer3_chains",
        "layer4_markets",
        "layer5_evidence",
    ):
        rules = (contract.get("modules") or {}).get(layer) or {}
        forbidden = rules.get("must_not_import") or []
        assert any("datasources.adapters" in str(r) for r in forbidden), layer
