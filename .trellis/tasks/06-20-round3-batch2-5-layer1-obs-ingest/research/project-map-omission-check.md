# Project Map Omission Check — 06-20-round3-batch2-5-layer1-obs-ingest

> Plan P0 冻结前回查 `MIGRATION_MAP.md` vs `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §4.2 vs `018A` §5  
> 日期：2026-06-20

## 1. 核对方法

1. 以 `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §4.2 Batch 2.5 bundle 为**计划输入全集**。
2. 以 `018A_layer1_observation_ingestion_bridge.md` §5 为**任务卡声明全集**（应 ⊇ 或 = §4.2）。
3. 在 `MIGRATION_MAP.md` 中查找：任务索引、§6 模块映射、契约索引、实现目录。
4. 标记：已覆盖 / 仅在 batch map / 仅在 018A / 遗漏 / 需回写 MASTER。

## 2. MIGRATION_MAP 已覆盖项

| 主题                                | MIGRATION_MAP 位置     | Batch 2.5 需要 | 结论                                      |
| ----------------------------------- | ---------------------- | -------------- | ----------------------------------------- |
| 018A 任务文件                       | §5 任务索引 L244       | 是             | OK                                        |
| Layer 1 模块                        | §6 五层模型 Layer 1 行 | 是             | OK（实现目录 `backend/app/layer1_axes/`） |
| 数据源 registry/adapter             | §6 数据源行            | 是             | OK                                        |
| Source Capability / Route / Service | §6 三行                | 是             | OK                                        |
| 数据同步 orchestrator               | §6 行                  | 是             | OK                                        |
| 数据质量与冲突                      | §6 行                  | 是             | OK                                        |
| WriteManager                        | §6 行                  | 是             | OK                                        |
| DuckDB / Parquet / 数据架构         | §6 + §7                | 是             | OK                                        |
| QMD Ops DB Inspect                  | §6 专行                | Phase 1/4      | OK（Batch 1 已实现）                      |
| ADR-001 摄取/写事务边界             | §6 WriteManager 规则列 | Phase 4        | OK                                        |
| runtime_flow / resource_limits      | §6 ResourceGuard 行    | Phase 2–3      | OK                                        |

## 3. 在 batch map / 018A 中但 MIGRATION_MAP §6 未单独成行的路径

以下路径在 §4.2 / 018A §5 中为 **Plan 必读**，由相邻模块行或 §7 旧设计映射覆盖，**不视为地图遗漏**，但须在 MASTER Source Context Index 显式列出：

| 路径                                                 | 归类依据                | MASTER 处理         |
| ---------------------------------------------------- | ----------------------- | ------------------- |
| `docs/architecture/03_runtime_flows.md`              | §7 运行链路             | must-read           |
| `docs/architecture/module_boundary_matrix.md`        | §6 目录结构与模块边界   | must-read           |
| `docs/modules/local_file_system.md`                  | §6 Raw Store 邻域       | summarize + pointer |
| `docs/ops/data_sync_quick_reference.md`              | §6 orchestrator 规则列  | summarize           |
| `docs/ops/data_sync_command_matrix.md`               | 同上                    | summarize           |
| `docs/ops/privacy_data_flow.md`                      | §6 通知与报告 / privacy | summarize           |
| `docs/ops/lock_and_concurrency_policy.md`            | §6 WriteManager 规则列  | summarize           |
| `docs/adr/ADR-0001-use-duckdb-local-first.md`        | §7 数据架构             | summarize           |
| `docs/adr/ADR-0003-layer1-standardization-only.md`   | §6 Layer 1 规则列       | summarize           |
| `specs/contracts/platform_source_matrix.yaml`        | §6 QMT 可选源           | pointer             |
| `specs/contracts/reference_adoption_guardrails.yaml` | 全局边界                | filtered-out        |
| Round 2 `011`–`016` 与 Round 2.6 `016A`–`016F`       | §5 Round 2/2.6 任务索引 | Plan trace only     |

## 4. 真实遗漏 / 不一致（须写入 MASTER §2 或 Phase 0 gate）

| ID       | 发现                                                                                                         | 严重度 | 建议处理                                                                                   |
| -------- | ------------------------------------------------------------------------------------------------------------ | ------ | ------------------------------------------------------------------------------------------ |
| **O-01** | `MIGRATION_MAP.md` §6 Layer 1 行仅列 `017`/`018`，**未列 `018A`**                                            | 低     | Plan 在 MASTER §0/§1.3 补 018A；可选 docs 维护 PR 更新地图任务索引                         |
| **O-02** | `specs/schema/schema.sql` **无** `axis_observation` 等 Layer 1 表，但 migration `011_layer1_tables.sql` 已建 | **中** | Execute Phase 0 gate 记为 BLOCKER 或窄 scope schema sync；禁止 silent 假设 schema.sql 权威 |
| **O-03** | `MIGRATION_MAP.md` 未索引 `backend/app/db/validation_gate.py`                                                | 低     | MASTER §6 接线表补行（Phase 4 clean write 前置）                                           |
| **O-04** | `MIGRATION_MAP.md` 未索引 `backend/app/sync/runners.py`（018A §5.5 / §7.1 候选）                             | 低     | MASTER §6 候选接线；Plan 4 阶段决定 ingestion.py vs runners 窄扩展                         |
| **O-05** | `TASK_INPUT_CONTEXT_INDEX.md` §6 已列 Layer 1 ingestion bridge 主题入口                                      | —      | 已覆盖，无动作                                                                             |
| **O-06** | Batch 2 Trellis 路径在 INDEX 中写「当前执行前」但未列 archived 路径                                          | 低     | MASTER predecessor_tasks 指向 `archive/.../06-20-round3-batch2-layer1`                     |

## 5. docs/specs 非实现边界复检

- [x] 本批允许实现目录：`backend/app/layer1_axes/`、`backend/app/sync/`（窄扩展）、`tests/`、可选 `scripts/`（须 MASTER 批准）
- [x] 禁止：`docs/`、`specs/` 下落运行时代码
- [x] 禁止：Layer 1 模块 import `create_adapter`

## 6. 结论（2026-06-20 自检修补后）

| ID   | 处置                                                                              |
| ---- | --------------------------------------------------------------------------------- |
| O-01 | **已修复** — `MIGRATION_MAP.md` §6 补 `018A` 与 Layer 1 observation bridge 行     |
| O-02 | **已写入 MASTER** — AC-P0-2；Execute Phase 0 gate                                 |
| O-03 | **已修复** — `MIGRATION_MAP.md` WriteManager 行补 `validation_gate.py`；MASTER §4 |
| O-04 | **已写入 MASTER** — §4 `sync/runners.py` 候选；implement pointer                  |
| O-06 | **已写入** — `task.json` predecessor + archived Batch2 audit path                 |

**project-map-omission-check: PASS**（自检修补后）
