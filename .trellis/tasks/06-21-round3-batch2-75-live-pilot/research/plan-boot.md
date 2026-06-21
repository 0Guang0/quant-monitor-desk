# Plan Boot — 06-21-round3-batch2-75-live-pilot

## 用户目标摘要

在 Batch 2.5（staged-only）归档 PASS 之后、Batch 3（019）开始之前，执行 Round 3 **Batch 2.75** 受控 production/live-data 试点门禁：按 `018B` §3.1 三个 micro-pilot 请求，在 sandbox-first、raw-only、fail-closed 约束下收集真实源 shape 证据，刷新或 re-defer A6 performance-budget 证据，并以五种 `PILOT_*` 状态之一完成 registry closeout 与 Batch 3 handoff。

## 原计划已读（ROUND + NNN 任务卡 + DECISIONS）

| 来源                                                             | 状态                                                                 |
| ---------------------------------------------------------------- | -------------------------------------------------------------------- |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §3 Batch 2.75、§4.2         | 已读                                                                 |
| `018B_production_live_pilot_gate.md`（含 §3.1 默认试点集）       | 已读                                                                 |
| `docs/quality/production_live_pilot_policy.md`                   | 已读                                                                 |
| `ROUND_3_MODELING_LAYERS/README.md`（017→018→018A→**018B**→019） | 已读                                                                 |
| `ROUND_3_MODELING_LAYERS/DECISIONS.md`                           | **不存在** — 以 `PENDING_USER_DECISIONS.md` + 018B §3.1 授权文件替代 |
| `docs/quality/batch275_user_authorization_2026-06-21.md`         | 已创建（018B 指定授权证据）                                          |
| Batch 2.5 archived MASTER + `final_registry_update.md`           | trace：staged-only handoff                                           |

## 前置依赖 / Batch 关系

| 前置                             | 状态                                    |
| -------------------------------- | --------------------------------------- |
| Batch 1 early ops                | archived PASS                           |
| Batch 2 Layer 1 017+018          | archived PASS                           |
| Batch 2.5 018A five-phase bridge | archived PASS · **staged/fixture only** |
| R2.6 contract + routing gates    | archived PASS                           |
| Ingestion split PR-R2a           | DONE；**R2b–R2d 与本 sprint 互斥**      |

## 三层上下文归并原则（README §上下文三层追溯模型）

1. **第一层**（设计/契约/规则）：能无损总结的约束写入 MASTER §0.7 / §3；契约 YAML、registry、policy 原文标为 Execute must-read（见 §0.6）。
2. **第二层**（018B 原始任务卡）：范围与 phase 门禁归并到 §2 AC + §8；原文不进 implement.jsonl（Plan only）。
3. **第三层**（本 MASTER + manifest）：Execute 只读 MASTER + implement.jsonl 列出的 must-read；Audit 读 AUDIT.plan + audit.jsonl。

## 预期 AC 草稿（→ MASTER §2）

- AC-PRE：Batch 2.5 staged handoff + policy tests green
- AC-PM1..PM4：Phase -1 对账与 not-in-scope
- AC-P0：authorization 三请求 + fail-closed
- AC-P1：只读 baseline + no mutation
- AC-P2：route READY matrix（3 requests）
- AC-P3：raw-only sandbox fetch（3 requests）+ production DB unchanged
- AC-P4：validation on raw evidence；default no clean write
- AC-P45：perf budget artifact or re-defer
- AC-P5：single `PILOT_*` + registry + Batch 3 handoff
- AC-GATE：§9–§10 full regression

## Plan Phase 顺序（1a→2→3→3.5→1b→4→5a→5d）

1. **3.5 to-issues** — `research/vertical-slices.md`（**先于 MASTER §8 定稿**）
2. 1a project-overview · 1b gitnexus-summary
3. 2a prd · 2b §2 AC
4. 3 grill-me-session
5. 4 §6 LivePilot API sketch
6. 5a–5d slices · tests md · ledger · integration-audit · freeze

## Phase P0 complete
