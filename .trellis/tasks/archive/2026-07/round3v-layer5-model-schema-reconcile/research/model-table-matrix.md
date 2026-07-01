# Research: L3/L4/L5 Model Table Matrix (MODEL-01)

- **Query**: WAVE0 §2 `MODEL-01` — designed / implemented / deferred 三列矩阵
- **Scope**: internal
- **Date**: 2026-06-28
- **SSOT 交叉**: 详表与 per-VR 摘要见 `l5-reconcile-matrix.md` §3；研究笔记见 `model-schema-table-reconcile.md`

## Findings

### 矩阵 legend

| 列                          | 含义                                            |
| --------------------------- | ----------------------------------------------- |
| **designed**                | module doc 和/或 `specs/schema/schema.sql` 列出 |
| **implemented (runtime)**   | Python 包 + staged pytest/fixtures              |
| **implemented (migration)** | DuckDB migration 已 apply                       |
| **deferred**                | 无 migration；显式 defer 或 Round 3F 归属       |

### Layer 汇总

| Layer | designed 表数                | migration                    | staged runtime             | 结论                                                  |
| ----- | ---------------------------- | ---------------------------- | -------------------------- | ----------------------------------------------------- |
| L1    | 7 `axis_*`                   | `011_layer1_tables` **DONE** | 部分                       | **唯一已迁移建模层**                                  |
| L3    | 8 `industry_chain_*`         | **无**                       | `layer3_chains/` + tests   | designed + staged；SSOT = module doc（非 schema.sql） |
| L4    | 6 `market_*`                 | **无**                       | `layer4_markets/` + tests  | 同上                                                  |
| L5    | 9（module）/ 2（schema.sql） | **无**                       | `layer5_evidence/` + tests | `security_bar_daily` vs `security_bar_1d` 命名漂移    |

### 命名漂移（须矩阵注明，禁止标 migrated）

| 文档/模块            | schema.sql        | 处置                                           |
| -------------------- | ----------------- | ---------------------------------------------- |
| `security_bar_daily` | `security_bar_1d` | **designed only**；不得标 implemented DB table |

### Migration 缺口 → Round 3F

- `industry_chain_*`、`market_*`、`instrument_registry`、`security_bar_1d`
- closure test 指针：`tests/test_migration_coverage.py`（inverse）+ migration 012+
- registry 提案：`research/registry_proposed_delta.yaml` → `R3-MODEL-L3L4-MIGRATION`

### 强制 pytest 指针（MODEL-02）

- `tests/test_migration_coverage.py` — 6 tests，断言 designed 建模表无 migration、L1 axis 011 覆盖
- 与 `docs/schema/MIGRATION_COVERAGE.md` L3/L4/L5 段一致

## Caveats / Not Found

- `specs/schema/schema.sql` **不含** L3/L4 表 — design SSOT 分裂（BLK-L5R-03）
- 完整逐表行见 `l5-reconcile-matrix.md` §3.1–§3.3
