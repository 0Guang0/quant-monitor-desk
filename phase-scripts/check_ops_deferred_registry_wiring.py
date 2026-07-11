#!/usr/bin/env python3
"""Ops DbInspector deferred_item_mapping 接线盘点（阶段性 · 非业务 pytest）

功能：
  临时 DuckDB + apply_migrations 后跑 DbInspector.inspect()，核对 deferred_item_mapping
  非空、含约定 item_id，且每项有 evidence_fields。
  对应原 tests/test_ops_db_inspector.py::test_dbInspect_deferredItemMapping_nonEmpty。

业务价值：
  守住巡检 JSON 与 R3/R2.6 延期项对照；映射断档会导致 gate 审计追溯失败。

退役 / 清理时间（满足任一即可删本文件）：
  1. deferred registry 已移除并由正式 ledger SSOT + 自有 CI 检查取代；或
  2. DbInspector 不再产出 deferred_item_mapping。

运行：
  uv run python phase-scripts/check_ops_deferred_registry_wiring.py --strict
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db.migrate import apply_migrations  # noqa: E402
from backend.app.ops.db_inspector import DbInspector  # noqa: E402

REQUIRED_ITEM_IDS = frozenset(
    {
        "DB-R3-001",
        "DB-R3-002",
        "R3-PARTIAL-2",
        "R2.6-IMPL-8",
        "R3-EARLY-DB-INSPECT-CLI",
    }
)


def _init_db(db_path: Path) -> None:
    con = duckdb.connect(str(db_path))
    try:
        apply_migrations(con)
    finally:
        con.close()


def _run() -> list[str]:
    errors: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        db = root / "t.duckdb"
        _init_db(db)
        report = DbInspector(db, root).inspect()
        mapping = report.deferred_item_mapping
        if not mapping:
            errors.append("deferred_item_mapping is empty")
            return errors
        item_ids = {entry["item_id"] for entry in mapping}
        missing = REQUIRED_ITEM_IDS - item_ids
        if missing:
            errors.append(f"deferred_item_mapping missing item_ids: {sorted(missing)}")
        for entry in mapping:
            if not entry.get("evidence_fields"):
                errors.append(
                    f"{entry.get('item_id', '<unknown>')}: empty evidence_fields"
                )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="有违例时 exit 1（关账/人工门禁用）",
    )
    args = parser.parse_args(argv)
    errors = _run()
    if not errors:
        print("PASS: ops deferred registry wiring")
        return 0
    print("FAIL: ops deferred registry wiring")
    for err in errors:
        print(f"  - {err}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
