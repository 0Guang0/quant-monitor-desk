# Plan Boot — round3-readonly-data-health-v1

## 用户目标摘要

在 Wave C **C-20** 分支交付 **read-only data health v1**：对 staged pilot（PROMPT_14 / v2）产出的 raw/staging evidence 与 bounded manifest 执行只读质量检查，输出 JSON + 人可读 summary；**不得**写 production DB、不得 source fetch、不得声称 production-live。

## 原计划已读（ROUND + 任务卡 + GLOBAL）

| 顺序 | 路径                                                    | 要点                          |
| ---- | ------------------------------------------------------- | ----------------------------- |
| 1    | `docs/implementation_tasks/README.md`                   | Round 入口；GLOBAL 索引       |
| 2–5  | `GLOBAL_*.md`（4）                                      | 执行/测试/资源/模板边界       |
| 6    | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.2 C-20          | allowed/forbidden、验证命令   |
| 7    | `PROMPT_20_feature_round3_readonly_data_health_v1.md`   | 分支启动、九切片              |
| 8    | `R3Y_readonly_data_health_v1.md`                        | AC、rule_id 子集、报告 schema |
| 9    | `R3Y_execution_discipline_addendum.md`                  | TDD / ponytail / 全量 pytest  |
| 10   | `WAVE_C_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` §3.1+§3.2 | 权威必读索引                  |
| 11   | `archive/.../06-24-round3-real-data-staged-pilot-v2/`   | v2 evidence（优先输入）       |

## 前置依赖 / Batch 关系

| 前置                        | 状态              | 证据                                                                                      |
| --------------------------- | ----------------- | ----------------------------------------------------------------------------------------- |
| PROMPT_14 / v2 staged pilot | merged / archived | `.trellis/tasks/archive/2026-06/06-24-round3-real-data-staged-pilot-v2/execute-evidence/` |
| `R3-B2.75-REQ2-EM`          | **DEFERRED**      | staged-only；不得作 live 前提                                                             |
| `db_inspector` Phase A      | on master         | `backend/app/ops/db_inspector.py`                                                         |

## 预期 AC 草稿（→ MASTER §2）

| AC          | 草稿                                                                       |
| ----------- | -------------------------------------------------------------------------- |
| AC-DH-PLAN  | `validate-plan-freeze` exit 0；`implement.jsonl` 覆盖 R3Y-DH-01..09        |
| AC-DH-IMPL  | `data_health*.py` 存在；只读；无 prod DB 写 / fetch / migration / free SQL |
| AC-DH-BIZ   | 对 v2 evidence 产出 JSON + summary；坏 fixture meaningful FAIL             |
| AC-DH-RULES | 覆盖任务卡 §5.1 rule_id 子集                                               |
| AC-DH-SLICE | 每切片独立测试 + execute-evidence                                          |
| AC-DH-TEST  | `test_ops_data_health.py` 绿；五字段 + 测试 ponytail                       |
| AC-DH-MAP   | MAP §2.2 验证命令绿                                                        |
| AC-DH-AUDIT | A1–A8 + 对抗性零遗留                                                       |
| AC-DH-BOUND | 未改 forbidden 路径；merge gate 陈述 sandbox gate 充分性                   |

## Plan Phase 顺序

P0 Boot → 1a 概览 → 2a prd → 2b spec AC → 3 grill-me → 3.5 vertical-slices → 1b GitNexus → 5a/5b §8 → 5c ledger → 5d integration-audit → 冻结

## Phase P0 complete
