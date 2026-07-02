# M-DATA-03 Plan — Task Breakdown

## Overview

Convert 11 Tier A sources from replay-primary incremental e2e (DCP-05) to **isolated-sandbox live-network** acceptance. One complex Trellis ticket; unified A1–A8 audit at end. Module rating target: C3/D1/E1/E2/F0/B2 → R4 live scope.

## Architecture Decisions

| ID  | Decision                                                         | Rationale                                             |
| --- | ---------------------------------------------------------------- | ----------------------------------------------------- |
| D1  | Reuse DCP-05 incremental ops/orchestrator                        | Ponytail; no rewrite                                  |
| D2  | Live tests use `@pytest.mark.network` + skip by default          | CI green without keys; `--run-network` for acceptance |
| D3  | ADR-034 isolated `DATA_ROOT` harness                             | Zero canonical DB pollution                           |
| D4  | Reference L ladder only on `参考项目/**`                         | guardrails.yaml                                       |
| D5  | OpenBB = L3 align; digital-oracle macro = L2; EasyXT = forbidden | Prior R3H-08/DCP-05 precedent                         |
| D6  | Peak 3–4 parallel agents; registry merge coordinator             | roadmap §1.6                                          |

## Task List

### Phase 0 — Plan（本阶段）

| Task | Description                             | AC                                                           | Verify                 |
| ---- | --------------------------------------- | ------------------------------------------------------------ | ---------------------- |
| P0   | Boot + inventory + reference research   | plan-boot.md · tier-a-live-inventory.md · reference-adoption | 文件存在               |
| P1   | to-issues + parallel protocol           | to-issues-slices.md                                          | 15 切片                |
| P2   | 5e bundle + ADR-034                     | ENTRY · EXTERNAL-INDEX · consolidation                       | validate-plan-phase 5e |
| P3   | freeze-task-card + validate-plan-freeze | frozen 薄指针                                                | exit 0                 |

### Phase 1 — Execute S00（串行 · 1 agent）

| Task        | Description                     | AC                | Files            |
| ----------- | ------------------------------- | ----------------- | ---------------- |
| E-S00-ELIG  | tier-a-live-eligibility.md      | 11 源 KEY 矩阵    | research/        |
| E-S00-INFRA | live harness + acceptance shell | harness pytest 绿 | tests/, scripts/ |

### Phase 2 — Execute 2a 试点（并行 · 2 agent）

| Task            | Description       | AC                       | Verify         |
| --------------- | ----------------- | ------------------------ | -------------- |
| E-LIVE-FRED     | fred live e2e     | axis_observation live 行 | pytest network |
| E-LIVE-BAOSTOCK | baostock live e2e | security_bar_1d live 行  | pytest network |

### Phase 3 — Execute 2b/2c（并行 · 3–4 agent）

| Task             | Sources                            | Batch |
| ---------------- | ---------------------------------- | ----- |
| E-LIVE-MACRO     | us_treasury, bis, world_bank, cftc | 2b    |
| E-LIVE-US-CRYPTO | sec_edgar, alpha_vantage, deribit  | 2b/2c |
| E-LIVE-CN        | cninfo, mootdx                     | 2c    |

### Phase 4 — Close（串行 · 1 coordinator）

| Task     | Description             | AC                |
| -------- | ----------------------- | ----------------- |
| E-MERGE  | registry 三件套         | loop_maintain 绿  |
| E-ACCEPT | 11/11 acceptance script | exit 0 隔离库     |
| Audit    | A1–A8 一次              | audit.report PASS |

## Checkpoints

| CP  | Gate                   |
| --- | ---------------------- |
| CP1 | S00-INFRA 绿 → 开 2a   |
| CP2 | 2a 绿 → 开 2b/2c       |
| CP3 | 全源 live 绿 → S-MERGE |
| CP4 | S-ACCEPT 绿 → Audit    |
| CP5 | Audit PASS → MCR 更新  |

## Risks

| Risk            | Mitigation                                |
| --------------- | ----------------------------------------- |
| API key 缺失    | eligibility 文档 + skip 非 fail；用户 env |
| 源 rate limit   | ResourceGuard + 有界窗；重试 policy 已有  |
| 并行 merge 冲突 | registry 仅 coordinator；按源分 worktree  |
| 误写主库        | ADR-034 harness 硬编码隔离路径 + 负向测   |

## Open Questions

- 无（路线图 §0.3.4 已确认 11/11 真网无 ADR）
