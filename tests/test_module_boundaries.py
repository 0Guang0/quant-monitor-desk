"""模块边界 checker 探测性单测（正式 tooling 锚点）。

全树 backend/app 扫描由 scripts/check_module_boundaries.py 承接（production_gate 已调用），
不在业务 pytest 重复跑 artifact-guard 全树扫描。
"""

from __future__ import annotations

from pathlib import Path

from tests.contract_gate_support import load_checker_module

_checker = load_checker_module()
check_file = _checker.check_file
load_contract = _checker.load_contract


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
