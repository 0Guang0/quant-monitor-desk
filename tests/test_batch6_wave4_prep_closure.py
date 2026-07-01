"""Wave 4 prep hygiene closure tests (P0–P2 batch)."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _collect_node_id(node_id: str) -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", node_id, "--collect-only"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    combined = f"{proc.stdout}\n{proc.stderr}"
    assert proc.returncode == 0, (
        f"pytest --collect-only failed for {node_id!r}:\n{combined}"
    )

_LINEAGE_RUNTIME_STRONG = (
    "tests/test_layer3_snapshot_builder.py::test_layer3Snapshot_malformedBarElement_rejects",
    "tests/test_layer3_snapshot_builder.py::test_layer3Snapshot_deterministicRebuild_sameInputsSameHash",
    "tests/test_layer2_sensor_loader.py::test_layer2Snapshot_lineageVrMismatch_rejects",
    "tests/test_layer2_sensor_loader.py::test_layer2Snapshot_lineageIncludesFetchIdsAndHashes",
)


def test_r3yTestDepth_lineageClusterRuntimeStrongPresent() -> None:
    """覆盖范围：lineage 簇 runtime-strong 反证测试是否登记
    测试对象：R3Y-TEST-DEPTH-001 要求的 lineage 簇 pytest 锚点
    目的/目标：closed-claim 反证深度在 lineage 簇有可执行 runtime-strong 测
    验证点：四个锚定 test node id 对应的源文件与 def 名均存在
    失败含义：AUD-07 lineage 深度债未闭合，Wave 4 前 hygiene 回退
    """
    for node_id in _LINEAGE_RUNTIME_STRONG:
        rel_path, _, func_name = node_id.partition("::")
        path = PROJECT_ROOT / rel_path
        assert path.is_file(), f"missing {rel_path}"
        text = path.read_text(encoding="utf-8")
        assert f"def {func_name}" in text, f"missing {func_name} in {rel_path}"
        _collect_node_id(node_id)


def test_d3p12_c901WontFixAdrDocumentsHotPath() -> None:
    """覆盖范围：D3-P1-2 C901 债务的 ADR 闭包（非复杂度消除）
    测试对象：docs/decisions/ADR-003-c901-write-path-complexity.md
    目的/目标：复杂函数以 ADR wont-fix 闭合，非静默遗留；本测不证明 ruff C901 清零
    验证点：ADR 存在且点名 _validate_domain_roles 与 _execute_write
    失败含义：D3-P1-2 无文档化 disposition，审计无法判断是债还是决策
    """
    adr = PROJECT_ROOT / "docs/decisions/ADR-003-c901-write-path-complexity.md"
    text = adr.read_text(encoding="utf-8")
    assert "_validate_domain_roles" in text
    assert "_execute_write" in text
    assert "D3-P1-2" in text


def test_ciPerfBudgetArtifact_scriptDefinesClosurePaths() -> None:
    """覆盖范围：R3-B25-PERF-BUDGET-01 CI one-liner 脚本
    测试对象：scripts/ci_perf_budget_artifact.py
    目的/目标：权威 perf budget artifact 有固定隔离路径与 smoke 委托
    验证点：脚本存在；引用 production_equivalent_smoke 与 r3b275-audit 路径
    失败含义：CI nightly 无标准入口，perf budget 仍停留在口头 defer
    """
    script = PROJECT_ROOT / "scripts/ci_perf_budget_artifact.py"
    text = script.read_text(encoding="utf-8")
    assert "production_equivalent_smoke.py" in text
    assert "r3b275-audit" in text
    assert "production_equivalent_smoke_budget.json" in text


def test_ciPerfBudgetArtifact_moduleLoads() -> None:
    """覆盖范围：ci_perf_budget_artifact 可导入且 main 可调用
    测试对象：scripts/ci_perf_budget_artifact.main
    目的/目标：CI 包装脚本非死代码
    验证点：spec 加载成功；main 是可调用函数
    失败含义：登记了 CI 脚本但无法被 operator/CI 执行
    """
    script = PROJECT_ROOT / "scripts/ci_perf_budget_artifact.py"
    spec = importlib.util.spec_from_file_location("ci_perf_budget_artifact", script)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert callable(mod.main)
