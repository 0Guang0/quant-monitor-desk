#!/usr/bin/env python3
"""staged_evidence 公开面不得绕过 WriteManager（阶段性 · 非业务 pytest）

功能：
  检查 staged_evidence.__all__ 仅含常量，且 backend/app 生产代码不得
  import register_staged_file_registry_rows。对应原
  tests/test_raw_store.py::test_stagedEvidence_publicApiCannotBypassWriteManager
  （artifact-guard / implementation snapshot）。

业务价值：
  防止 staging 旁路再次变成公开 API，绕过 WriteManager 审计写路径。

退役 / 清理时间（满足任一即可删本文件）：
  1. staged 写路径仅经 WriteManager 的运行时 fail-closed 测已覆盖且稳定 1 个发布周期；或
  2. staged_evidence 模块退役 / 合并进正式 storage 面，本扫描模式失效。

运行：
  uv run python phase-scripts/check_staged_evidence_public_api.py --strict
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _run() -> list[str]:
    import backend.app.storage.staged_evidence as staged_mod

    errors: list[str] = []
    expected = (
        "STAGED_EVIDENCE_PHASE",
        "STAGED_FILE_REGISTRY_PARSE_STATUS",
        "STAGED_FILE_REGISTRY_QUALITY",
    )
    if staged_mod.__all__ != expected:
        errors.append(f"__all__={staged_mod.__all__!r}, expect {expected}")
    forbidden = "register_staged_file_registry_rows"
    if hasattr(staged_mod, forbidden):
        errors.append(f"public symbol still present: {forbidden}")
    backend_root = PROJECT_ROOT / "backend" / "app"
    for py in backend_root.rglob("*.py"):
        if py.name == "staged_evidence.py":
            continue
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and "staged_evidence" in node.module:
                for alias in node.names:
                    if alias.name == forbidden:
                        errors.append(f"{py.relative_to(PROJECT_ROOT)}: imports {forbidden}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    errors = _run()
    if not errors:
        print("PASS: staged_evidence public API hygiene")
        return 0
    print("FAIL: staged_evidence public API hygiene")
    for err in errors:
        print(f"  - {err}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
