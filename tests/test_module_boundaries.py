"""Round2.6 模块边界契约：禁止 layer 直引 adapter 等跨层导入。"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from tests.contract_gate_support import PROJECT_ROOT, load_checker_module

CONTRACT_PATH = PROJECT_ROOT / "specs/contracts/module_boundary_contract.yaml"
LAYER_MODULES = (
    "layer1_axes",
    "layer2_sensors",
    "layer3_chains",
    "layer4_markets",
    "layer5_evidence",
)

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


def test_nonLayerModules_passModuleBoundaryScan() -> None:
    """覆盖范围：layer2–5 + 非 layer 模块（排除 layer1_axes）
    测试对象：check_paths 对 backend/app 子树
    目的/目标：S01 阶段非 layer1 模块须保持边界全绿
    验证点：除 layer1_axes 外扫描 violations == []
    失败含义：收紧契约后误伤非 layer 模块，或掩盖其它层违规
    """
    backend = PROJECT_ROOT / "backend" / "app"
    contract = load_contract()
    violations = check_paths(
        [p for p in backend.iterdir() if p.is_dir() and p.name != "layer1_axes"],
        contract,
    )
    assert violations == [], f"non-layer1 boundary violations: {violations}"


def test_layer1Axes_passesModuleBoundaryScan() -> None:
    """覆盖范围：layer1_axes 边界全绿（P1-14 GREEN）
    测试对象：ingestion.py · ingestion_evidence.py import 图
    目的/目标：P1-14 后 layer1 无 datasources.service 直连
    验证点：layer1_axes 扫描 violations == []
    失败含义：Layer 仍直连 DataSourceService，M-G1-03 接缝失效
    """
    layer1 = PROJECT_ROOT / "backend" / "app" / "layer1_axes"
    violations = check_paths([layer1])
    assert violations == [], f"layer1_axes boundary violations: {violations}"


def test_productionBackend_passesModuleBoundaryScan() -> None:
    """覆盖范围：当前 backend/app 全树扫描
    测试对象：check_paths([backend/app])
    目的/目标：P1-GATE 后全树边界须全绿
    验证点：violations == []
    失败含义：仓库内已有边界破坏，layer 与 adapter 耦合扩散
    """
    backend = PROJECT_ROOT / "backend" / "app"
    violations = check_paths([backend])
    assert violations == [], f"production boundary violations: {violations}"


def test_layerModules_forbidAdapterAndServiceImports() -> None:
    """覆盖范围：layer1–5 模块 must_not_import 规则
    测试对象：module_boundary_contract 各 layer 段
    目的/目标：五层业务模块契约上禁止依赖 datasources.adapters 与 datasources.service
    验证点：layer1_axes 至 layer5_evidence 的 forbidden 列表均含两项
    失败含义：层模块可直拉 adapter/service，架构分层与 M-G1-03 gate 失效
    """
    contract = load_contract()
    for layer in LAYER_MODULES:
        rules = (contract.get("modules") or {}).get(layer) or {}
        forbidden = rules.get("must_not_import") or []
        assert any("datasources.adapters" in str(r) for r in forbidden), layer
        assert any("datasources.service" in str(r) for r in forbidden), layer
