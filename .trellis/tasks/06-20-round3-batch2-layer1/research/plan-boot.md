# Plan Boot — 06-20-round3-batch2-layer1

## 用户目标摘要

进入 Round 3 **第二批次** Plan 阶段：实现 Layer 1 五轴基础（正式任务 `017` + `018`），并闭合 `R3-EARLY-LINEAGE-CONSUMERS`。必须追溯 `ROUND3_BATCH_IMPLEMENTATION_MAP.md`、`MIGRATION_MAP.md`、`README.md` 三层上下文，将设计/契约/规则无损归并进 `MASTER.plan.md`，不可无损总结者进入 Execute must-read manifest。

## 原计划已读（ROUND + NNN 任务卡 + DECISIONS）

| 顺序 | 路径                                                        | 要点                                                              |
| ---- | ----------------------------------------------------------- | ----------------------------------------------------------------- |
| 1    | `docs/implementation_tasks/README.md`                       | Round 顺序；GLOBAL 规则索引                                       |
| 2–5  | `GLOBAL_*.md`（4）                                          | 执行/测试/资源/模板边界                                           |
| 6    | `ROUND_3_MODELING_LAYERS/README.md`                         | `017`–`023` 顺序；early CLI 不在编号内                            |
| 7    | `ROUND_3_MODELING_LAYERS/DECISIONS.md`                      | **不存在** — 以 `PENDING_USER_DECISIONS.md` D-09 与 ADR-0003 代替 |
| 8    | `017_implement_layer1_axis_loader.md`                       | 五轴 spec loader；registry/profile 初始化                         |
| 9    | `018_implement_layer1_interpretation_snapshot.md`           | feature + interpretation 快照                                     |
| 10   | `ROUND3_EARLY_CLOSE_PLAN.md`                                | lineage consumers 依赖 validation_report rule_version             |
| 11   | Batch 2 bundle（`ROUND3_BATCH_IMPLEMENTATION_MAP.md` §4.2） | 模块设计、契约、axis specs、lineage、ADR-0003                     |

## 前置依赖 / Batch 关系

| 前置                                      | 状态          | 证据                                                                                                             |
| ----------------------------------------- | ------------- | ---------------------------------------------------------------------------------------------------------------- |
| Round 2.6 Contract + Routing Service Gate | archived PASS | `06-19-round2-6-*-gate/audit.report.md`                                                                          |
| Round 3 Batch 1 early ops                 | archived PASS | `.trellis/tasks/archive/2026-06/06-20-round3-batch1-early-ops/audit.report.md`                                   |
| `validation_report.rule_version` 字段     | 已落地        | migration `008_lineage_version_fields.sql`                                                                       |
| Layer 1 axis 表 DDL                       | **未迁移**    | `layer1_global_regime_panel.md` §6 有设计 DDL；`specs/schema/schema.sql` 尚无 axis 表 — Batch 2 须新增 migration |

**Batch 1 → Batch 2 门控：** Batch 1 PASS 解除 `blocks_round3_task_017`；本批可 Plan/Execute。

## 预期 AC 草稿（→ MASTER §2）

| Item                         | 草稿 AC                                                                                                                                            |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `017`                        | 五轴 YAML spec 加载；`axis_registry` / `axis_indicator_registry` / `axis_indicator_profile` 初始化；FORBIDDEN 仅登记不进 observation；契约字段校验 |
| `018`                        | `axis_feature_snapshot` + `axis_interpretation_snapshot`；`INSUFFICIENT_HISTORY` 不伪造 z/percentile；禁止动作语义                                 |
| `R3-EARLY-LINEAGE-CONSUMERS` | 快照写入含 `snapshot_lineage_contract.yaml` 必填字段；消费 `validation_report`/`data_quality_log` 的 `rule_version`；`no_future_data` 测试         |

## Plan Phase 顺序（1a→2→3→3.5→1b→4→5a→5d）

P0 Boot → 1a GitNexus 概览 → 2a brainstorm/prd → 2b spec AC → 3 grill-me → 3.5 to-issues → 1b GitNexus 深度 → 4 设计 §4–6 → 5a 切片 → 5b §8 RED/GREEN → 5c ledger/manifest → 5d integration-audit → P5 冻结

## 路径纠偏（任务卡 vs 仓库）

| 任务卡路径                                | 实际实现路径                                | 说明                                   |
| ----------------------------------------- | ------------------------------------------- | -------------------------------------- |
| `backend/layers/layer1/axis_loader.py`    | `backend/app/layer1_axes/axis_loader.py`    | `MIGRATION_MAP.md` §6 Layer 1 实现目录 |
| `backend/layers/layer1/feature_engine.py` | `backend/app/layer1_axes/feature_engine.py` | 同上                                   |
| `backend/layers/layer1/interpretation.py` | `backend/app/layer1_axes/interpretation.py` | 同上                                   |

## Phase P0 complete
