# Original Plan Trace — 06-20-round3-batch2-layer1

## Round / Batch

- **Round:** 3 — Modeling Layers
- **Batch:** 2 — Layer 1 base (`017` + `018` + `R3-EARLY-LINEAGE-CONSUMERS`)
- **权威批次索引:** `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §3 Batch 2、§4.2

## 任务卡清单（NNN → 路径）

| ID                           | 路径                                                                                                | 类型               |
| ---------------------------- | --------------------------------------------------------------------------------------------------- | ------------------ |
| `017`                        | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/017_implement_layer1_axis_loader.md`             | 正式任务卡         |
| `018`                        | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018_implement_layer1_interpretation_snapshot.md` | 正式任务卡         |
| `R3-EARLY-LINEAGE-CONSUMERS` | `docs/implementation_tasks/ROUND3_EARLY_CLOSE_PLAN.md`（Layer snapshot lineage consumers 行）       | 别名 / early close |

## AC 映射（任务卡预期结果 → MASTER §2）

| 任务卡预期                                                                          | MASTER AC                         |
| ----------------------------------------------------------------------------------- | --------------------------------- |
| 017 §1：加载五轴 spec，初始化 `axis_registry` / `axis_indicator_registry` / profile | AC-017-1..4                       |
| 017 §9：禁止 FORBIDDEN 进入观测                                                     | AC-017-3                          |
| 017 §15：统一 lineage 字段；no-future-data                                          | AC-LINEAGE-1, AC-018-4            |
| 018 §1：生成 `axis_feature_snapshot` 与 `axis_interpretation_snapshot`              | AC-018-1..3                       |
| 018 §9：`z/percentile`、`INSUFFICIENT_HISTORY`、禁止动作语义                        | AC-018-2, AC-018-3                |
| early close：lineage consumers 依赖 `validation_report.rule_version`                | AC-LINEAGE-1..3                   |
| BATCH_MAP：Layer 1 specs 加载、快照生成、lineage 可追溯、语义测试                   | AC-017-_, AC-018-_, AC-LINEAGE-\* |

## 输入文件已读（specs / architecture）

| 路径                                                                                                | 类别         | manifest                                                      |
| --------------------------------------------------------------------------------------------------- | ------------ | ------------------------------------------------------------- |
| `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/017_implement_layer1_axis_loader.md`             | 任务卡       | Plan only                                                     |
| `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018_implement_layer1_interpretation_snapshot.md` | 任务卡       | Plan only                                                     |
| `docs/modules/layer1_global_regime_panel.md`                                                        | 模块设计     | **Execute must-read**（表结构 §6、计算流程 §8、测试清单 §13） |
| `specs/contracts/layer1_axis_contract.yaml`                                                         | 契约         | **Execute must-read**                                         |
| `specs/layer1_axes/restructured_axes_v1_1/**`                                                       | domain spec  | **Execute must-read**（五轴 YAML + engineering rules）        |
| `specs/contracts/snapshot_lineage_contract.yaml`                                                    | 契约         | **Execute must-read**                                         |
| `docs/adr/ADR-0003-layer1-standardization-only.md`                                                  | ADR          | 可总结（D-09 inline）                                         |
| `docs/modules/duckdb_and_parquet.md`                                                                | 架构         | 可总结 + pointer（Layer 1 表归属）                            |
| `docs/implementation_tasks/ROUND3_EARLY_CLOSE_PLAN.md`                                              | early plan   | 可总结（lineage consumer 范围）                               |
| `configs/layer1_axes.yml`                                                                           | 运行配置     | **Execute must-read**                                         |
| `backend/app/layer1_axes/__init__.py`                                                               | 接线（占位） | inherited — 扩展                                              |
| `backend/app/db/write_manager.py`                                                                   | 接线         | **Execute must-read**（快照写入边界）                         |
| `backend/app/validators/data_quality.py`                                                            | 接线         | pointer（`rule_version` / fetch lineage 来源）                |
| `backend/app/db/migrations/008_lineage_version_fields.sql`                                          | migration    | 可总结（lineage 前置已闭合）                                  |
| `backend/app/db/migrations/`（新 `011_layer1_tables.sql`）                                          | Execute 新建 | deferred → §8.1                                               |
| `tests/test_layer1_axis_loader.py`                                                                  | Execute 新建 | deferred                                                      |
| `tests/test_layer1_interpretation.py`                                                               | Execute 新建 | deferred                                                      |
| `.trellis/tasks/archive/2026-06/06-20-round3-batch1-early-ops/audit.report.md`                      | 前置 gate    | pointer（Batch 1 PASS）                                       |

## 路径纠偏（任务卡路径与仓库不一致）

| 任务卡                                | 仓库实际                                                  |
| ------------------------------------- | --------------------------------------------------------- |
| `backend/layers/layer1/*.py`          | `backend/app/layer1_axes/*.py` per `MIGRATION_MAP.md` §6  |
| `axis_indicator_profile` 表名         | 设计文档 §6.5 与任务卡「profile」一致                     |
| `specs/schema/schema.sql` 无 axis DDL | 以 `layer1_global_regime_panel.md` §6 + 新 migration 为准 |

## 已过滤 / 本批排除

| 来源                                   | 原因                                                  |
| -------------------------------------- | ----------------------------------------------------- |
| Layer 1 API（`fastapi_routes.md` §11） | Round 4 `024`                                         |
| `Layer1AxisFetcher` 全量生产抓取       | 超出 017/018；本批用 fixture observation 驱动快照测试 |
| `019`–`023`                            | Batch 3–5                                             |
| Migration 008 CHECK 约束               | Batch 6 `A9-P*`                                       |
| `docs/ops/db_inspect_cli.md`           | Batch 1 已闭合                                        |
