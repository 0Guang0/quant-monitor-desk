"""全库测试函数五字段 docstring 门禁。

规范：rules/GLOBAL_TESTING_POLICY.md §7
Layer1 参考模板：test_layer1Observation_fetchFailure_blocksCleanWrite、
test_layer1MicroIngestion_phase3DoesNotWriteCleanAxisObservation
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

TESTS_ROOT = Path(__file__).resolve().parent
REQUIRED_LITERAL = ("覆盖范围", "测试对象", "验证点", "失败含义")
PURPOSE_LABELS = ("目的/目标", "目的：", "目的:")


def _has_purpose_field(doc: str) -> bool:
    return any(label in doc for label in PURPOSE_LABELS)


def _missing_fields(doc: str) -> list[str]:
    missing = [field for field in REQUIRED_LITERAL if field not in doc]
    if not _has_purpose_field(doc):
        missing.append("目的/目标")
    return missing


def _iter_test_functions(path: Path) -> list[tuple[str, str | None]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: list[tuple[str, str | None]] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            out.append((node.name, ast.get_docstring(node)))
    return out


def _collect_gaps() -> list[str]:
    gaps: list[str] = []
    for path in sorted(TESTS_ROOT.rglob("test_*.py")):
        if path.name == "test_docstring_quadruple_coverage.py":
            continue
        for name, doc in _iter_test_functions(path):
            if not doc:
                gaps.append(f"{path.relative_to(TESTS_ROOT)}::{name} missing docstring")
                continue
            missing = _missing_fields(doc)
            if missing:
                gaps.append(
                    f"{path.relative_to(TESTS_ROOT)}::{name} missing fields: {', '.join(missing)}"
                )
    return gaps


def test_docstringQuadruple_allPytestFunctionsDocumented() -> None:
    """覆盖范围：全库每条 test_* 是否具备完整五字段 docstring
    测试对象：tests/**/test_*.py 中全部 test_* 函数（本文件除外）
    目的/目标：防止只写「目的」漏「目的/目标」标签，或缺验证点/失败含义
    验证点：_collect_gaps() 返回空列表
    失败含义：测试自描述不完整，全扫 agent 无法以 docstring 追溯意图与覆盖
    """
    gaps = _collect_gaps()
    assert not gaps, "docstring quadruple gaps:\n" + "\n".join(gaps[:40])


def test_docstringQuadruple_testCountMatchesVerifyField() -> None:
    """覆盖范围：「验证点」出现次数与 test_* 定义数的粗检
    测试对象：tests 目录下全部 test_*.py 源文件
    目的/目标：整文件漏扫时验证点行数会明显少于函数数，作二次兜底
    验证点：全库「验证点」出现次数 >= test_* 定义数
    失败含义：批量漏改时门禁可能只绿一半，卫生债无声回流
    """
    test_count = 0
    verify_count = 0
    for path in TESTS_ROOT.rglob("test_*.py"):
        if path.name == "test_docstring_quadruple_coverage.py":
            continue
        text = path.read_text(encoding="utf-8")
        test_count += len(re.findall(r"^def test_", text, re.M))
        verify_count += text.count("验证点")
    assert verify_count >= test_count


def test_docstringQuadruple_goldSampleFirstTestComplete() -> None:
    """覆盖范围：唯一金样文件首条 test_* 是否五字段齐全（防止金样自身缺项带偏全库）
    测试对象：tests/test_layer3_snapshot_builder.py::test_layer3Snapshot_buildsFromStagedLoaderAndL5_success
    目的/目标：金样第一条必须含「目的/目标」标签，供人工与 agent 对照
    验证点：该函数 docstring 经 _missing_fields 检查为空；且含「目的/目标」字面
    失败含义：金样缺项会导致 R1–R7 全扫再次照抄错误模板
    """
    path = TESTS_ROOT / "test_layer3_snapshot_builder.py"
    for name, doc in _iter_test_functions(path):
        if name == "test_layer3Snapshot_buildsFromStagedLoaderAndL5_success":
            assert doc, "gold sample first test missing docstring"
            assert not _missing_fields(doc), f"gold sample incomplete: {_missing_fields(doc)}"
            assert "目的/目标" in doc
            return
    pytest.fail("gold sample first test not found")
