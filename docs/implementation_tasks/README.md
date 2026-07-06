# Implementation Tasks（活工单目录）

> **2026-07-02 收敛：** 旧 `ROUND_*` / Wave / DCP 任务包已迁入 **`archive/legacy-pre-module-v2-20260702/`**（只读证据）。  
> **活规划 SSOT：** 根目录 [`PROJECT_IMPLEMENTATION_ROADMAP.md`](../../PROJECT_IMPLEMENTATION_ROADMAP.md) §3 · [`MODULE_COMPLETION_RATING.md`](../../MODULE_COMPLETION_RATING.md)。

## 当前下一入口（v2）

| 优先级 | 票 ID             | 任务卡目录（Plan 冻结时创建）                                         |
| ------ | ----------------- | --------------------------------------------------------------------- |
| ~~P0~~ | ~~**M-DATA-03**~~ | ~~`M_DATA_03_TIER_A_LIVE/`~~ — **CLOSED** @ 2026-07-04 · 只读一行摘要 |
| **P0** | **M-G1-03**       | `M_G1_03_LAYER1_FULL/` — **下一入口**                                 |
| **P1** | **M-G2-FULL**     | `M_G2_FULL/`（待建）                                                  |
| **P1** | **M-G4-FULL**     | `M_G4_FULL/`（待建）                                                  |
| **P1** | **M-G5-FULL**     | `M_G5_FULL/`（待建）                                                  |
| **P0** | **M-PASS-01**     | `M_PASS_01/`（待建）                                                  |

**规则：** 一个模块完整成品 = **一张**活票 + 一个 canonical 文件夹；票内可多切片。见路线图 §1.7–§1.8。

## Plan 阶段仍须读（全局契约）

- `MIGRATION_MAP.md`
- `GLOBAL_EXECUTION_RULES.md` · `GLOBAL_TESTING_POLICY.md` · `GLOBAL_RESOURCE_LIMITS.md` · `GLOBAL_TASK_TEMPLATE.md`
- `MODULE_COMPLETION_RATING.md`
- `TASK_INPUT_CONTEXT_INDEX.md` · `UNRESOLVED_ITEM_TASK_COVERAGE.md`

## 历史归档

- **路径：** [`archive/legacy-pre-module-v2-20260702/`](archive/legacy-pre-module-v2-20260702/README.md)
- **Trellis / Loop 遗留：** [`archive/trellis-loop-2026/`](../archive/trellis-loop-2026/)（只读，不再使用）

## 任务计划存放

| 阶段      | 位置                                             |
| --------- | ------------------------------------------------ |
| Plan 输入 | `docs/implementation_tasks/<票>/` 活卡（薄指针） |
| 执行跟踪  | GitHub Issues + `.scratch/<feature-slug>/`       |
| 迁入时机  | 用户确认开工后，在 Issues / `.scratch/` 维护 AC  |
