# Plan Boot — B-19 staged pilot v2

## 用户目标摘要

在 PROMPT_14 staged pilot、PROMPT_15 残余闭合、PROMPT_18 strict adversarial audit（`WARN_ALLOW_WITH_CONTROLS`）之后，**受控扩样**真实数据 staged/raw/sandbox 证据，暴露 baostock / cninfo / akshare validation 的质量、路由、校验、冲突与 no-mutation 行为。**staged-only**；不得声称 production-live readiness。

## 原计划已读（ROUND + NNN 任务卡 + GLOBAL）

| 顺序 | 路径                                                    | 要点                              |
| ---- | ------------------------------------------------------- | --------------------------------- |
| 1    | `docs/implementation_tasks/README.md`                   | Round 入口；GLOBAL 索引           |
| 2–5  | `GLOBAL_*.md`（4）                                      | 执行/测试/资源/模板               |
| 6    | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.2               | PROMPT_19 并行索引                |
| 7    | `PROMPT_19_feature_round3_real_data_staged_pilot_v2.md` | 分支、切片、验证命令              |
| 8    | `R3Y_real_data_staged_pilot_v2.md`                      | R3Y-SP2-01..09 AC 表              |
| 9    | `R3Y_staged_pilot_v2_execution_addendum.md`             | /to-issues、TDD、ponytail         |
| 10   | `R3Y_post_r3x_strict_adversarial_audit.md`              | AUD-01..08 维度                   |
| 11   | `R3Y-AUD-08-go-no-go.md`                                | **WARN_ALLOW_WITH_CONTROLS** 控件 |
| 12   | PROMPT_14 证据包                                        | v1 baseline manifests / closeout  |

## 前置依赖 / Batch 关系

| 前置                     | 状态         | 证据                                                    |
| ------------------------ | ------------ | ------------------------------------------------------- |
| PROMPT_14 staged pilot   | merged       | `.trellis/tasks/feature-round3-real-data-staged-pilot/` |
| post-14 audit fix        | merged       | `fix-round3-post14-audit-staged-pilot/`                 |
| R3X residual closure     | merged       | `fix-round3-r3x-residual-open-items-closure/`           |
| R3Y strict audit         | PASS WARN    | `archive/2026-06/06-23-round3-post-r3x-strict-audit/`   |
| `R3-B2.75-REQ2-EM`       | **DEFERRED** | 不得作 live 前提                                        |
| PROMPT_20 data health v1 | 后续         | 本任务 evidence 为其输入                                |

## 预期 AC 草稿（→ MASTER §2）

| AC        | 草稿                                              |
| --------- | ------------------------------------------------- |
| AC-SP2-01 | pilot_id + caps JSON；ResourceGuard 对齐          |
| AC-SP2-02 | baostock 扩样 raw/staging manifest v2             |
| AC-SP2-03 | cninfo metadata 扩样 + schema notes               |
| AC-SP2-04 | akshare validation retry/re-defer taxonomy        |
| AC-SP2-05 | route_preview_matrix_v2 全状态                    |
| AC-SP2-06 | validation_report_v2 字段/质量暴露                |
| AC-SP2-07 | conflict_check_summary_v2                         |
| AC-SP2-08 | no_mutation_proof_v2 + **R3Y-MUT-PROOF-001** 闭合 |
| AC-SP2-09 | pilot_v2_closeout.json expand/re-defer 矩阵       |

## Plan Phase 顺序

P0 Boot → 1a 概览 → 2a prd → 2b spec AC → 3 grill-me → 3.5 vertical-slices → 1b GitNexus → 4 架构摘要 → 5a/5b §8 → 5c ledger → 5d integration-audit → 冻结

## AUD-08 控件（Plan 冻结）

1. `R3-B2.75-REQ2-EM` 保持 DEFERRED
2. 扩样前确认生产 CLI 不经 sync `adapter=` 旁路
3. closeout 不得仅引用 `proof_status=VERIFIED`；须 hash/row-count 明细或修复 AUD-04
4. 授权链 + sandbox WriteManager 路径维持现状
5. 无 production-live readiness 声称

## Phase P0 complete
