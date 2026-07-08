"""Design blueprint vs runtime mirror parity (artifact-gate)."""

from __future__ import annotations

import hashlib
from pathlib import Path

from scripts.promote_design_runtime import DIR_PAIRS, FILE_PAIRS

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative_files(root: Path) -> dict[str, str]:
    if not root.is_dir():
        return {}
    out: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            out[rel] = _sha256(path)
    return out


def test_designRuntimeParity_contractYamlFiles_matchDesignBlueprints() -> None:
    """覆盖范围：契约类 YAML 设计图与运行副本字节一致
    测试对象：FILE_PAIRS（resource_limits、source_conflict_rules）
    目的/目标：运行路径不得静默偏离 MIGRATION_MAP 索引的 design/ 设计图
    验证点：每对 design/runtime 文件存在且 SHA256 相同
    失败含义：有人只改了运行副本或 promote 未执行，R4 对照与运行时行为可能分裂
    """
    mismatches: list[str] = []
    for design_rel, runtime_rel in FILE_PAIRS:
        design = PROJECT_ROOT / design_rel
        runtime = PROJECT_ROOT / runtime_rel
        if not design.is_file():
            mismatches.append(f"missing design: {design_rel}")
            continue
        if not runtime.is_file():
            mismatches.append(f"missing runtime mirror: {runtime_rel}")
            continue
        if _sha256(design) != _sha256(runtime):
            mismatches.append(f"hash mismatch: {design_rel} != {runtime_rel}")
    assert not mismatches, ";\n".join(mismatches)


def test_designRuntimeParity_layer1AxisTree_matchesDesignBlueprint() -> None:
    """覆盖范围：五轴指标规格目录树 design/ 与运行副本一致
    测试对象：DIR_PAIRS（restructured_axes_v1_1）
    目的/目标：AxisSpecLoader 读取的运行树与封存设计图同步
    验证点：相对路径集合相同；同路径文件 SHA256 相同
    失败含义：五轴运行规格已漂移，Layer1 行为与导航地图设计不一致
    """
    design_rel, runtime_rel = DIR_PAIRS[0]
    design = PROJECT_ROOT / design_rel
    runtime = PROJECT_ROOT / runtime_rel
    design_files = _relative_files(design)
    runtime_files = _relative_files(runtime)
    assert design_files, f"design tree empty or missing: {design_rel}"
    assert runtime_files, f"runtime tree empty or missing: {runtime_rel}"
    only_design = set(design_files) - set(runtime_files)
    only_runtime = set(runtime_files) - set(design_files)
    hash_diffs = [
        rel
        for rel in sorted(set(design_files) & set(runtime_files))
        if design_files[rel] != runtime_files[rel]
    ]
    problems: list[str] = []
    if only_design:
        problems.append(f"only in design: {sorted(only_design)}")
    if only_runtime:
        problems.append(f"only in runtime: {sorted(only_runtime)}")
    if hash_diffs:
        problems.append(f"hash mismatch files: {hash_diffs}")
    assert not problems, ";\n".join(problems)
