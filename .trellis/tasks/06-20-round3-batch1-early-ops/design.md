# Design — Round 3 Batch 1

见 `MASTER.plan.md` §4–§6。

- 架构：`backend/app/ops/db_inspector.py` 纯函数/类 + `scripts/qmd_ops.py` argparse 薄包装
- 数据流：CLI args → DbInspector.inspect() → JSON/text report → stdout
- DB 访问：仅 `ConnectionManager(db_path).reader()` 或等价 `duckdb.connect(..., read_only=True)`
- 契约：`specs/contracts/ops_db_inspect_contract.yaml` + `docs/ops/db_inspect_cli.md` Phase A
