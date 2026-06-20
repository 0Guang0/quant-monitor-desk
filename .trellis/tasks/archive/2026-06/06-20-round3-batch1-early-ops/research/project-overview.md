# Project Overview — Round 3 Batch 1 (≤1 page)

> 基于三层追溯（`research/three-layer-trace.md`）更新；非抢先草稿。

## 当前状态

- **Gates:** Round 2.6 Contract + Routing Service Gate archived PASS；`R2.6-IMPL-7`（prod-equiv smoke）已 RESOLVED。
- **Round 3 entry:** `BLOCK-R3-001` CLEAR；本批为 `ROUND3_BATCH_IMPLEMENTATION_MAP.md` Batch 1。
- **Data reality:** `data/` 仅 `duckdb/quant_monitor.duckdb` + `.gitkeep`（`DB-R3-001`）；smoke 用隔离 `.audit-sandbox`。
- **Code gap:** `backend/app/ops/`、`scripts/qmd_ops.py`、`tests/test_ops_db_inspector.py` 尚不存在。

## Batch 1 范围（八项 ID）

| ID                          | 性质                                                         |
| --------------------------- | ------------------------------------------------------------ |
| `R3-EARLY-DB-INSPECT-CLI`   | **主实现** — 冻结设计 Phase A                                |
| `DB-R3-001/002`             | 由 inspect CLI 输出关闭                                      |
| `DOC-R3-001/002`            | docs-only 修补                                               |
| `R3-PARTIAL-2`              | fixture E2E 已有；`run_full_load` 不存在 — Plan 须 reconcile |
| `R3-EARLY-PROD-SCALE-BENCH` | 可能重跑 smoke + 证据；`R2.6-IMPL-7` 已闭环                  |
| `R2.6-IMPL-8`               | 保持禁用 + 文档；不 live 验证                                |

**排除:** `017`–`023` Layer 建模。

## 实现目录（MIGRATION_MAP §6）

`backend/app/ops/db_inspector.py` ← `ConnectionManager.reader()`（`read_only=True`）  
`scripts/qmd_ops.py` — transitional 薄包装  
`tests/test_ops_db_inspector.py` — 语义 + 无 mutation

## 安全不变量（设计层冻结）

- 无 migration / writer / 网络 / QMT / 自由 SQL
- `deferred_item_mapping` 输出对接 registry 关闭证据
