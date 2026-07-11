#!/usr/bin/env python3
"""build_test_adapter 默认 stub 端口冒烟（阶段性 · meta-testing）

功能：
  用临时 DuckDB + Batch B registry 验证 build_test_adapter 零配置即可 SUCCESS fetch。
  对应原 tests/test_adapter_skeletons.py::test_createTestAdapter_defaultStubFetchPort_success。

业务价值：
  守住测试辅助工厂可用性；该工厂断裂会导致大量集成测无法起步，但本身非生产业务契约。

退役 / 清理时间（满足任一即可删本文件）：
  1. create_test_adapter / build_test_adapter 已废止，测试统一走显式 StubFetchPort；或
  2. 团队确认不再需要独立 meta-testing 冒烟（由少数 fixture 自测覆盖）。

运行：
  uv run python phase-scripts/check_test_adapter_factory.py --strict
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

from backend.app.datasources.fetch_result import FetchRequest  # noqa: E402
from backend.app.datasources.source_registry import SourceRegistry  # noqa: E402
from backend.app.db.migrate import apply_migrations  # noqa: E402
from tests.service_path_support import build_test_adapter  # noqa: E402

FIXTURE_REGISTRY = PROJECT_ROOT / "tests/fixtures/source_registry_batch_b.yaml"


def check_default_stub_fetch_success(violations: list[str]) -> None:
    if not FIXTURE_REGISTRY.is_file():
        violations.append(f"missing fixture registry: {FIXTURE_REGISTRY}")
        return
    reg = SourceRegistry(FIXTURE_REGISTRY)
    reg.load()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data_root = root / "data"
        data_root.mkdir()
        db = root / "t.duckdb"
        con = duckdb.connect(str(db))
        try:
            apply_migrations(con)
            adapter = build_test_adapter("baostock", reg, data_root)
            req = FetchRequest(
                run_id="run-1",
                source_id="baostock",
                data_domain="cn_equity_daily_bar",
            )
            result = adapter.fetch(req, con=con)
            if result.status != "SUCCESS":
                violations.append(
                    f"build_test_adapter default stub fetch status={result.status!r}"
                )
        finally:
            con.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="有违例时 exit 1（关账/人工门禁用）",
    )
    args = parser.parse_args(argv)

    violations: list[str] = []
    check_default_stub_fetch_success(violations)

    if not violations:
        print("PASS: test adapter factory")
        return 0

    print("FAIL: test adapter factory")
    for item in violations:
        print(f"  - {item}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
