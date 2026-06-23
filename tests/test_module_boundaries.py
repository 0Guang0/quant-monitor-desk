"""Round2.6 模块边界契约：禁止 layer 直引 adapter 等跨层导入。"""

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
    """覆盖范围：module_boundary_contract.yaml 登记项
    测试对象：required_checks 列表
    目的/目标：契约须点名边界检查脚本与对应测试模块
    验证点：含 scripts/check_module_boundaries.py 与 tests/test_module_boundaries.py
    失败含义：CI 无法从契约找到守门脚本，边界违规可能漏检
    """
    contract = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8")) or {}
    checks = contract.get("required_checks") or []
    assert "scripts/check_module_boundaries.py" in checks
    assert "tests/test_module_boundaries.py" in checks


def test_checkModuleBoundaries_detectsForbiddenImportFixture(tmp_path: Path) -> None:
    """覆盖范围：单文件违规导入探测
    测试对象：check_file 对伪造 api 层探针
    目的/目标：api 层直接 import datasources.adapters 应被检出
    验证点：violation_probe.py 触发非空 violations
    失败含义：边界扫描器对明显违规无感，生产代码可悄悄跨层
    """
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
    """覆盖范围：当前 backend/app 全树扫描
    测试对象：check_paths([backend/app])
    目的/目标：已合并生产代码不得存在契约禁止的跨模块导入
    验证点：violations == []
    失败含义：仓库内已有边界破坏，layer 与 adapter 耦合扩散
    """
    backend = PROJECT_ROOT / "backend" / "app"
    violations = check_paths([backend])
    assert violations == [], f"production boundary violations: {violations}"


def test_layerModules_forbidAdapterImports() -> None:
    """覆盖范围：layer1–5 模块 must_not_import 规则
    测试对象：module_boundary_contract 各 layer 段
    目的/目标：五层业务模块契约上禁止依赖 datasources.adapters
    验证点：layer1_axes 至 layer5_evidence 的 forbidden 列表均含 datasources.adapters
    失败含义：层模块可直拉 adapter，架构分层与 Batch B gate 失效
    """
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
