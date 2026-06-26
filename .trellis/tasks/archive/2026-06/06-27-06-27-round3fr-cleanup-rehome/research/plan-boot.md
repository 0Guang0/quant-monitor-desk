# Plan Boot — R3FR-07 Legacy Wrapper Cleanup and Redirects

> **Phase P0 complete**

## 用户目标

作为 Batch 3F-R **最后一张任务卡**，在 R3FR-01~06 已合并 `master` 的前提下，清理旧薄 wrapper 与过时规划叙事，正式关闭 3F-R，解锁 Round 3G 入口。本任务 **不** 做新功能、不删证据、不宣称 production-live。

## 批次与前置

| 项       | 值                                                              |
| -------- | --------------------------------------------------------------- |
| Batch    | 3F-R — `BATCH_3FR_REFERENCE_ADOPTION_REFACTOR`                  |
| Item ID  | `R3FR-07`                                                       |
| 建议分支 | `chore/round3fr-cleanup-rehome`（Playbook §1）                  |
| 前置     | R3FR-01~06 已 DONE @ `master` `6c1a0d37`+；targeted pytest 已绿 |
| 后置     | Round 3G `R3G-01` sandbox clean-write rehearsal（严格串行）     |

## 原计划已读

- [x] `docs/implementation_tasks/README.md`
- [x] `docs/implementation_tasks/TASK_INPUT_CONTEXT_INDEX.md`（3F-R / 3G 入口段）
- [x] `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`（§3F-R 相关）
- [x] `PROJECT_IMPLEMENTATION_ROADMAP.md` §2–§3.6
- [x] `docs/ROUND3_HANDOFF.md`
- [x] `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.1 Wave E / 3F-R checkpoint
- [x] `MODULE_COMPLETION_RATING.md`
- [x] `GLOBAL_EXECUTION_RULES.md` · `GLOBAL_TESTING_POLICY.md` · `GLOBAL_RESOURCE_LIMITS.md` · `GLOBAL_TASK_TEMPLATE.md`
- [x] `BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/README.md`
- [x] `BATCH_3FR_TASK_CARD_MANIFEST.md`
- [x] `BATCH_3FR_COORDINATOR_PLAYBOOK.md`
- [x] `BATCH_3FR_HARDENING_RULES.md` §9
- [x] `R3FR_07_LEGACY_WRAPPER_CLEANUP_AND_REDIRECTS.md`（已按 GLOBAL 模板加固）
- [x] `ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/README.md`
- [x] `specs/contracts/reference_adoption_guardrails.yaml`
- [x] 归档 Trellis：`06-26-round3fr-data-health-cli` · `06-26-round3fr-tdx-provider` · `06-26-round3fr-provider-catalog`

## 现状摘要（Plan 期侦察 @ master）

| 模块                                               | 替换实现状态                                               | R3FR-07 仍需                                   |
| -------------------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------- |
| `data_commands.health_check`                       | **已接线** `run_data_health_profile`                       | 修正仍写 placeholder 的规划文档                |
| `data_health.check_daily_bars`                     | 证据路径 shim；profile 用 `build_market_bar_p0_checks`     | redirect docstring；可选 DRY 到共享 OHLCV 规则 |
| `TdxPytdxProbeFetchPort`                           | 已委托 `TdxPytdxFetchPort`                                 | 模块级 canonical 注释；防未来在此膨胀          |
| `tdx_manual_probe`                                 | 编排层；port 在 `fetch_ports/`                             | 顶部边界说明指向 R3FR-03                       |
| `ROUND_3_REFERENCE_ADOPTION_REFACTOR/README.md` §3 | **过时**：仍称 health_check 返回 `not_implemented_phase_c` | 改为 DONE + redirect                           |
| `BATCH_3G README`                                  | 仍写 blocked by 3F-R                                       | 3F-R 完成后改为 precondition satisfied         |
| `MODULE_COMPLETION_RATING` provider catalog        | 仍 `R1_SCAFFOLD`                                           | 升至 `R2` 或 `R3` 并注明 R3H 后续              |

## 非目标

- 不启动 3G 实现（仅解锁规划入口）
- 不关闭 B2.5-O-05 / R3-B2.75-REQ2-EM（属 3H/DEFERRED）
- 不改 registry 三件套（无新 source 行）
- 不删除 `R3FR_01_REFERENCE_INVENTORY_AND_LICENSE_MATRIX.md`（保留 redirect）

## Trellis 任务目录

`.trellis/tasks/06-27-06-27-round3fr-cleanup-rehome/`
