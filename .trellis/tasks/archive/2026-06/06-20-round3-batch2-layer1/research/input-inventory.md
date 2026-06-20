# Input Inventory — 06-20-round3-batch2-layer1 (P0i)

> 2026-06-20 · 文档宇宙审计 · 三层追溯：`README.md` → `MIGRATION_MAP.md` → `ROUND3_BATCH_IMPLEMENTATION_MAP.md` → 任务卡 §3

## 1. 任务卡展开

| 来源          | 路径                                                                      | 状态      |
| ------------- | ------------------------------------------------------------------------- | --------- |
| 017           | `ROUND_3_MODELING_LAYERS/017_implement_layer1_axis_loader.md`             | in-repo   |
| 018           | `ROUND_3_MODELING_LAYERS/018_implement_layer1_interpretation_snapshot.md` | in-repo   |
| Round 3 入口  | `ROUND_3_MODELING_LAYERS/README.md`                                       | in-repo   |
| Lineage alias | `ROUND3_EARLY_CLOSE_PLAN.md`                                              | in-repo   |
| GLOBAL×4      | `GLOBAL_*.md`                                                             | in-repo   |
| 批次地图      | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §3–4.2                               | in-repo   |
| 项目地图      | `MIGRATION_MAP.md` §6 Layer 1 行                                          | in-repo   |
| 三层模型      | `README.md` §上下文三层追溯                                               | in-repo   |
| Plan 桥       | `TASK_INPUT_CONTEXT_INDEX.md`                                             | in-repo   |
| v3 ledger     | `research/integration-ledger.md`                                          | Plan 产出 |

### 017 §3 输入展开

- `docs/modules/layer1_global_regime_panel.md`
- `specs/contracts/layer1_axis_contract.yaml`
- `specs/layer1_axes/restructured_axes_v1_1/README.md` + 五轴 `*_indicator_spec.yaml` + `common_axis_rules.md`
- GLOBAL + `runtime_versions.md` + `staged_acceptance_policy.md`
- `specs/contracts/snapshot_lineage_contract.yaml`

### 018 §3 输入展开

- `layer1_global_regime_panel.md`（特征/解释流程 §7–10）
- GLOBAL + runtime + staged acceptance
- `snapshot_lineage_contract.yaml`

### Batch 2 bundle 追加（§4.2）

- `docs/modules/duckdb_and_parquet.md`
- `specs/schema/schema.sql`（对照；axis 表待 migration）
- `docs/adr/ADR-0003-layer1-standardization-only.md`

## 2. 六类关键信息覆盖

| 类别         | 必须覆盖                            | 已定位路径                                                      | 缺口                                 |
| ------------ | ----------------------------------- | --------------------------------------------------------------- | ------------------------------------ |
| decision     | D-09 Layer1 标准化                  | `PENDING_USER_DECISIONS.md`, ADR-0003                           | 无                                   |
| rule         | GLOBAL + WriteManager               | `GLOBAL_*`, `write_manager.md`                                  | 无                                   |
| architecture | Layer1 模块 + DuckDB                | `layer1_global_regime_panel.md`, `duckdb_and_parquet.md`        | axis 表 migration 待建               |
| business     | 五轴语义 + 禁止动作                 | axis specs + `layer1_axis_contract.yaml` forbidden_output_terms | 无                                   |
| contract     | axis + lineage                      | `layer1_axis_contract.yaml`, `snapshot_lineage_contract.yaml`   | 无                                   |
| wiring       | write_manager, data_quality lineage | `write_manager.py`, `data_quality.py`, migration 008            | `layer1_axes/` 除 `__init__.py` 待建 |

## 3. 交叉引用闭包（1-hop）

| 自                               | 引用                                      | 状态                     |
| -------------------------------- | ----------------------------------------- | ------------------------ |
| `layer1_axis_contract.yaml`      | `layer1_global_regime_panel.md` authority | required                 |
| `017` 任务卡                     | `layer1_axes/restructured_axes_v1_1/**`   | required                 |
| `MIGRATION_MAP.md`               | `backend/app/layer1_axes/`                | required                 |
| `snapshot_lineage_contract.yaml` | `validation_report` lineage fields        | required — migration 008 |
| `ROUND3_EARLY_CLOSE_PLAN.md`     | lineage consumers                         | required                 |
| Batch 1 audit                    | Batch 2 gate                              | required                 |

## 4. missing-in-repo（Execute 将创建）

| 路径                                              | 说明                          |
| ------------------------------------------------- | ----------------------------- |
| `backend/app/layer1_axes/axis_loader.py`          | 017 核心                      |
| `backend/app/layer1_axes/feature_engine.py`       | 018                           |
| `backend/app/layer1_axes/interpretation.py`       | 018                           |
| `backend/app/layer1_axes/models.py`               | 可选 dataclasses              |
| `backend/app/layer1_axes/lineage.py`              | lineage 打包 helper           |
| `backend/app/db/migrations/011_layer1_tables.sql` | axis registry + snapshot 表   |
| `tests/test_layer1_axis_loader.py`                | 017 测试                      |
| `tests/test_layer1_interpretation.py`             | 018 + lineage 测试            |
| `ROUND_3_MODELING_LAYERS/DECISIONS.md`            | 不存在 — 用 GLOBAL + ADR 代替 |

## 5. 门禁

- [x] 任务来源 + §3 输入已展开
- [x] 六类关键信息均有路径
- [x] 与 `original-plan-trace.md` 一致

`P0i complete`
