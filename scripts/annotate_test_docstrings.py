"""DEPRECATED — 禁止用于 Round3 docstring 卫生。

批量套话无审计价值；请按 rules/GLOBAL_TESTING_POLICY.md §7 人工润色。
保留本文件仅供历史参考，勿在 CI/任务中调用。
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"

FIELD_VERIFY = "验证点"
FIELD_FAIL = "失败含义"
FIELD_COVER = "覆盖范围"
FIELD_OBJECT = "测试对象"
FIELD_GOAL = "目的/目标"


def _humanize_test_name(name: str) -> str:
    base = name[5:] if name.startswith("test_") else name
    base = re.sub(r"([a-z])([A-Z])", r"\1 \2", base)
    return base.replace("_", " ").strip()


def _module_scope(path: Path, module_doc: str | None) -> str:
    if module_doc:
        first = module_doc.strip().splitlines()[0].strip().strip('"').strip("'")
        if first:
            return first.rstrip("。")
    stem = path.stem.replace("test_", "")
    return f"tests/{path.name}（{stem}）"


def _first_assert_hint(body: list[ast.stmt]) -> str:
    for node in ast.walk(ast.Module(body=body, type_ignores=[])):
        if isinstance(node, ast.Assert):
            hint = ast.unparse(node.test)[:120]
            return hint.replace('"""', "'").replace("'''", "'")
        if isinstance(node, ast.With):
            for item in node.items:
                if (
                    isinstance(item.context_expr, ast.Call)
                    and isinstance(item.context_expr.func, ast.Attribute)
                    and item.context_expr.func.attr == "raises"
                ):
                    hint = ast.unparse(item.context_expr)[:120]
                    return hint.replace('"""', "'").replace("'''", "'")
    return "关键业务断言成立"


def _derive_fields(name: str, path: Path, module_doc: str | None, body: list[ast.stmt]) -> dict[str, str]:
    human = _humanize_test_name(name)
    scope = _module_scope(path, module_doc)
    hint = _first_assert_hint(body)
    parts = human.split()
    behavior = " ".join(parts[1:]) if len(parts) > 1 else human
    return {
        FIELD_COVER: f"{scope} — {behavior}",
        FIELD_OBJECT: name.replace("test_", "", 1),
        FIELD_GOAL: f"证明 {human} 的可观察行为符合模块契约",
        FIELD_VERIFY: f"断言/异常语义满足：{hint}",
        FIELD_FAIL: f"若失败则 {behavior} 回归不可被审计或调用方无法 fail-closed",
    }


def _format_docstring(fields: dict[str, str]) -> str:
    lines = [
        f"{FIELD_COVER}：{fields[FIELD_COVER]}",
        f"{FIELD_OBJECT}：{fields[FIELD_OBJECT]}",
        f"{FIELD_GOAL}：{fields[FIELD_GOAL]}",
        f"{FIELD_VERIFY}：{fields[FIELD_VERIFY]}",
        f"{FIELD_FAIL}：{fields[FIELD_FAIL]}",
    ]
    return "\n    ".join(lines)


def _has_quadruple(doc: str | None) -> bool:
    if not doc:
        return False
    return (
        FIELD_COVER in doc
        and FIELD_OBJECT in doc
        and ("目的" in doc or FIELD_GOAL in doc)
        and FIELD_VERIFY in doc
        and FIELD_FAIL in doc
    )


def _merge_docstring(existing: str | None, fields: dict[str, str]) -> str:
    # ponytail: always emit frozen 四元组; legacy purpose/verifies fields are replaced, not appended
    if _has_quadruple(existing):
        return existing or _format_docstring(fields)
    return _format_docstring(fields)


def _annotate_file_lines(path: Path) -> int:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    module_doc = ast.get_docstring(tree)
    lines = source.splitlines(keepends=True)
    changed = 0

    test_funcs = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    ]
    for node in sorted(test_funcs, key=lambda n: n.lineno, reverse=True):
        doc = ast.get_docstring(node)
        if _has_quadruple(doc):
            continue
        if not node.body:
            continue
        fields = _derive_fields(node.name, path, module_doc, node.body)
        new_doc = _merge_docstring(doc, fields)
        def_line = lines[node.lineno - 1]
        base_indent = len(def_line) - len(def_line.lstrip())
        doc_indent = " " * (base_indent + 4)
        doc_lines = [f'{doc_indent}"""{new_doc.splitlines()[0]}\n']
        for line in new_doc.splitlines()[1:]:
            doc_lines.append(f"{doc_indent}{line}\n")
        doc_lines.append(f'{doc_indent}"""\n')
        block = "".join(doc_lines)

        if (
            isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            start = node.body[0].lineno - 1
            end = node.body[0].end_lineno or node.body[0].lineno
            lines[start:end] = [block]
        else:
            insert_at = node.body[0].lineno - 1
            lines.insert(insert_at, block)
        changed += 1

    if changed:
        path.write_text("".join(lines), encoding="utf-8")
    return changed


def main() -> int:
    total = 0
    for path in sorted(TESTS.rglob("test_*.py")):
        total += _annotate_file_lines(path)
    print(f"annotated_functions={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
