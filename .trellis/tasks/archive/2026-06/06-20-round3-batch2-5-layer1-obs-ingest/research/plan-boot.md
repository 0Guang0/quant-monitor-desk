# Plan Boot — 06-20-round3-batch2-5-layer1-obs-ingest

## 用户目标摘要

进入 Round 3 **Batch 2.5** Plan 阶段：按 `018A_layer1_observation_ingestion_bridge.md` 规划 Layer 1 `axis_observation` 受控摄取桥接（本地 alias `R3-B2.5-L1-OBS-INGEST`）。本批是 Batch 2（`017`+`018`）与 Batch 3（`019`）之间的**强制门控桥**，须拆成五阶段 Execute + 逐阶段 Audit，不得合并为单次大提交，不得把真实数据摄取藏进 Batch 2 或推迟到 Batch 6。

## 当前 Round batch map 已读

| 来源                                    | 确认内容                                                                         |
| --------------------------------------- | -------------------------------------------------------------------------------- |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §1 | Plan 必读共享上下文 12 项                                                        |
| §3 Batch 2.5                            | Item `R3-B2.5-L1-OBS-INGEST`；五阶段 gate；禁止与 Batch 2/6 合并                 |
| §4.2 Batch 2.5 bundle                   | 018A + 架构/模块/契约/代码参考清单（约 40+ 路径）                                |
| §5 执行顺序                             | Batch 2 → **Batch 2.5** → Batch 3                                                |
| §6 Trellis 约束                         | 独立 complex task；MASTER Source Context Index + AUDIT Source Trace；窄 manifest |

## 原计划已读（ROUND + 任务卡 + DECISIONS）

| 顺序 | 路径                                          | 要点                                                                      |
| ---- | --------------------------------------------- | ------------------------------------------------------------------------- |
| 1    | `docs/implementation_tasks/README.md`         | Round 顺序；GLOBAL 规则索引                                               |
| 2    | `TASK_INPUT_CONTEXT_INDEX.md`                 | 三层模型；Batch 2.5 须按 018A 五阶段 Gate                                 |
| 3    | `ROUND3_BATCH_IMPLEMENTATION_MAP.md`          | 本批权威切片与 source bundle                                              |
| 4    | `MIGRATION_MAP.md`                            | 实现目录边界；Layer 1 / 数据源 / WriteManager 映射                        |
| 5–8  | `GLOBAL_*.md`（4）                            | 执行/测试/资源/模板边界                                                   |
| 9    | `ROUND_3_MODELING_LAYERS/README.md`           | `017`→`018`→`018A`→`019` 顺序                                             |
| 10   | `ROUND_3_MODELING_LAYERS/DECISIONS.md`        | **不存在** — 以 `PENDING_USER_DECISIONS.md` + Round 2 `DECISIONS.md` 代替 |
| 11   | `018A_layer1_observation_ingestion_bridge.md` | 本批唯一正式 alias 执行文件；§5 全量 Plan 输入；§8 五阶段模型             |
| 12   | `017` / `018` 任务卡                          | Batch 2 上游依赖（loader + snapshot，fixture 驱动）                       |
| 13   | Round 2 `011`–`016` + Round 2.6 `016A`–`016F` | 摄取/路由/validator 设计上下文（018A §5.4）                               |

## 前置依赖 / Batch 关系

| 前置                                                    | 状态          | 证据                                                                              |
| ------------------------------------------------------- | ------------- | --------------------------------------------------------------------------------- |
| Round 2.6 Contract + Routing Service Gate               | archived PASS | `06-19-round2-6-*-gate/audit.report.md`                                           |
| Round 3 Batch 1 early ops                               | archived PASS | `06-20-round3-batch1-early-ops/audit.report.md`                                   |
| Round 3 Batch 2 Layer 1 (`017`+`018`)                   | archived PASS | `06-20-round3-batch2-layer1/audit.report.md`（2026-06-20）                        |
| Layer 1 表 + loader/feature/interpretation/lineage 代码 | 已落地        | `backend/app/db/migrations/011_layer1_tables.sql`；`backend/app/layer1_axes/*.py` |
| Layer 1 **真实/staged observation 摄取桥**              | **未实现**    | 无 `layer1_axes/ingestion.py`；Batch 2 仅用 fixture observation 驱动快照          |

**Batch 2 → Batch 2.5 门控：** Batch 2 audit PASS 解除本批 Plan；Execute Phase 0 须复验 schema/route/write/lineage 测试集（018A §8 Phase 0）。

## 预期 AC 草稿（→ MASTER §2）

按 018A §8 五阶段拆 child deliverable（Execute 每阶段 Audit 签字后才能进入下一阶段）：

| Phase      | 草稿 AC                                                                                                                                         |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| P0 Execute | DB/设计/契约 gate：`phase0_source_context_matrix.md` + `phase0_db_contract_gate.md`；指定 pytest 全绿；缺口分类为 BLOCKER/DEFERRED/OUT_OF_SCOPE |
| P1 Execute | 只读 DB/data-root 基线清单 `phase1_before_ingestion_inventory.*`；零 mutation                                                                   |
| P2 Execute | 指标 allowlist + route preview dry-run；`fetch_log`/`axis_observation`/快照行数不变                                                             |
| P3 Execute | 微摄取仅 evidence/staging；经 DataSourceService；`axis_observation` 行数不变                                                                    |
| P4 Execute | validation + conflict + WriteManager 写 clean observation；重建 feature/interpretation snapshot + lineage；前后 inspect delta 可审计            |
| 整批       | `pytest -q` 全绿；registry 更新；Batch 3 handoff 字段（ingestion type / allowed scope）                                                         |

## Plan Phase 顺序（1a→2→3→3.5→1b→4→5a→5d）

P0 Boot（本文件）→ 1a GitNexus 概览 → 2a brainstorm/prd → 2b spec AC → 3 grill-me → 3.5 to-issues → 1b GitNexus 深度 → 4 设计 §4–6 → 5a 切片 → 5b §8 RED/GREEN → 5c ledger/manifest → 5d integration-audit → P5 冻结

**P0b GitNexus：** defer → Phase 1b（本批代码路径广，1a/1b 深度分析必做）。

## 路径纠偏（任务卡 vs 仓库）

| 018A / 设计路径                       | 仓库实际                                                   | 说明                                        |
| ------------------------------------- | ---------------------------------------------------------- | ------------------------------------------- |
| `backend/layers/layer1/*`             | `backend/app/layer1_axes/*`                                | `MIGRATION_MAP.md` §6                       |
| `specs/schema/schema.sql` 无 axis DDL | migration `011_layer1_tables.sql` 有 `axis_observation` 等 | Plan 须在 Phase 0 gate 记录 schema.sql 滞后 |
| 可能 `scripts/qmd_layer1_ingest.py`   | 尚未存在                                                   | Execute 新建须 MASTER 批准且默认 dry-run    |
| `layer1_axes/ingestion.py`            | 尚未存在                                                   | 本批候选实现目标（018A §7.1）               |

## Phase P0 complete
