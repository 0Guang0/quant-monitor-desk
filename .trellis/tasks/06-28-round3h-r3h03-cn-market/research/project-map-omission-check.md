# Project Map Omission Check — R3H-03

> `check_docs_specs_indexed.py` Plan 门禁 · 2026-06-28

## 检查范围

本任务触及：`backend/app/datasources/**`、`specs/datasource_registry/**`、`specs/contracts/**`、`tests/test_cn_market_adapters.py`（计划新增）。

## 结论

- 活卡 §2 QMD 列表路径均存在于仓库（`MIGRATION_MAP.md` / `docs/generated/docs_specs_index.generated.md` 可索引）。
- 新增 `tests/test_cn_market_adapters.py` — Execute §9.0 后须 `loop_maintain.py --fix` 登记 catalog。
- `backend/app/datasources/auth/` — 新包；Execute 后须核对 `authority_graph.yaml` mapping。

**omission-check: PASS**（Plan 阶段无新增未索引 docs/specs 路径）
