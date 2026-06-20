# Input Inventory — 06-20-round3-batch2-5-layer1-obs-ingest (P0i)

> 2026-06-20 · 文档宇宙审计 · 追溯链：`README.md` → `MIGRATION_MAP.md` → `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §4.2 → `018A` §5

## 1. 任务来源展开

| 来源             | 路径                                                                  | 状态                                    |
| ---------------- | --------------------------------------------------------------------- | --------------------------------------- |
| Batch map alias  | `R3-B2.5-L1-OBS-INGEST`                                               | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §3 |
| 正式 alias 文件  | `ROUND_3_MODELING_LAYERS/018A_layer1_observation_ingestion_bridge.md` | in-repo                                 |
| Round 3 入口     | `ROUND_3_MODELING_LAYERS/README.md`                                   | in-repo（`017`→`018`→`018A`→`019`）     |
| 上游 Batch 2     | `017` + `018` 任务卡                                                  | in-repo · archived PASS                 |
| GLOBAL×4         | `GLOBAL_*.md`                                                         | in-repo                                 |
| Plan 桥          | `TASK_INPUT_CONTEXT_INDEX.md` §4/§6                                   | in-repo                                 |
| 共享 Plan 上下文 | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §4.1（12 项）                    | in-repo                                 |
| Batch 2.5 bundle | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §4.2                             | in-repo                                 |
| 项目地图         | `MIGRATION_MAP.md`                                                    | in-repo                                 |
| 前置 Trellis     | `06-20-round3-batch2-layer1/audit.report.md`                          | archived PASS                           |

### 018A §5.1–5.5 输入展开（与 §4.2 bundle 对齐）

- **§5.1 协议（10）：** README, MIGRATION_MAP, ROUND3 map, TASK_INPUT_CONTEXT_INDEX, complex-task-planning-protocol, GLOBAL×3, staged_acceptance, PENDING_USER_DECISIONS
- **§5.2 架构/模块/ops/ADR（24）：** `03_runtime_flows`, `04_data_architecture`, `module_boundary_matrix`, layer1/data_sources/capability/route/service/orchestrator/validation/write/duckdb/local_file_system, ops×5, decisions×2, adr×2
- **§5.3 契约/schema/migration（22）：** schema.sql, migrations 004–006/008/010/011, datasource registries×2, contracts×12
- **§5.4 历史任务/registry（18）：** Round2 011–016, Round2.6 016A–016F, gaps, DECISIONS, AUDIT/UNRESOLVED/RESOLVED registries
- **§5.5 代码（23）：** config, db×3, resource_guard, storage×3, datasources×7, sync×4, validators×2, layer1_axes/\*, ops db_inspector, scripts×3

## 2. 六类关键信息覆盖

| 类别         | 必须覆盖                                               | 已定位路径                                                           | 缺口                                            |
| ------------ | ------------------------------------------------------ | -------------------------------------------------------------------- | ----------------------------------------------- |
| decision     | 数据源角色、摄取授权、D-01..D-12                       | `PENDING_USER_DECISIONS.md`, ADR-0005, Round2 DECISIONS              | 无决策重开风险                                  |
| rule         | GLOBAL + eco-mode + staged acceptance                  | `GLOBAL_*`, `resource_limits.yaml`, `staged_acceptance_policy.md`    | 无                                              |
| architecture | 摄取主链、模块边界、数据分区                           | `03_runtime_flows`, `04_data_architecture`, `module_boundary_matrix` | 无                                              |
| business     | Layer1 indicator → observation → snapshot trace        | `layer1_global_regime_panel.md`, `018A` §3                           | 摄取桥代码未建                                  |
| contract     | route/service/write/lineage/quality/conflict           | `source_route_contract.yaml` 等 §5.3 清单                            | `schema.sql` 滞后于 migration 011               |
| wiring       | DataSourceService, WriteManager, pipeline, layer1_axes | `service.py`, `write_manager.py`, `pipeline.py`, `layer1_axes/`      | `ingestion.py` 缺失；Layer1 无 production fetch |

## 3. 交叉引用闭包（1-hop）

| 自                                     | 引用                                         | 状态                                       |
| -------------------------------------- | -------------------------------------------- | ------------------------------------------ |
| `018A` §8 Phase 0                      | Batch 2 表/lineage/no-future-data PASS       | required — Batch 2 audit PASS              |
| `module_boundary_matrix`               | Layer 模块不得直调 adapter factory           | required — Execute 静态边界检查            |
| `datasource_service_contract.yaml`     | 仅 DataSourceService 可调 `create_adapter`   | required — `service.py:190`                |
| `write_contract.yaml`                  | clean write 经 WriteManager                  | required                                   |
| `snapshot_lineage_contract.yaml`       | `source_fetch_ids` + `source_content_hashes` | required — Batch 2 lineage 已实现          |
| `ops_db_inspect_contract.yaml`         | Phase 1/4 只读 inspect 字段                  | required — Batch 1 db_inspector            |
| `ROUND3_BATCH_IMPLEMENTATION_MAP` §4.2 | 与 `018A` §5 路径集合                        | required — 已对齐（见 omission-check）     |
| Batch 2 `017`/`018`                    | fixture observation 驱动快照                 | inherited — 本批替换为受控真实/staged 路径 |

## 4. missing-in-repo（Plan/Execute 将创建或补齐）

| 路径                                            | 说明                                                    |
| ----------------------------------------------- | ------------------------------------------------------- |
| `backend/app/layer1_axes/ingestion.py`          | 摄取编排（候选）                                        |
| `backend/app/layer1_axes/observation_writer.py` | 可选；须经 WriteManager                                 |
| `tests/test_layer1_observation_ingestion.py`    | Phase 2–4 语义测试                                      |
| `tests/test_layer1_ingestion_gates.py`          | Phase 0 gate 测试                                       |
| `execute-evidence/phase0_*.md` 等               | 018A §11 证据工件                                       |
| `specs/schema/schema.sql` axis DDL              | **滞后** — Phase 0 须记录为 BLOCKER 或 scoped sync 任务 |
| `ROUND_3_MODELING_LAYERS/DECISIONS.md`          | 不存在 — 用 GLOBAL + ADR 代替                           |

## 5. 门禁

- [x] 任务来源 + 018A §5 输入已展开
- [x] 六类关键信息均有路径
- [x] 与 `original-plan-trace.md` 一致
- [x] 与 `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §4.2 bundle 一致

`P0i complete`
