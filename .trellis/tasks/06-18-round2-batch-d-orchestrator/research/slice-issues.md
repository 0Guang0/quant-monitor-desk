# Vertical Slice Issues — Batch D（Plan Phase 3.5）

> to-issues 产出 · Trellis MASTER §8 映射 · 无 GitHub issue tracker 时存本地

## 粒度确认

用户已授权进入 Plan；切片与 MASTER §8 一一对应，Execute 按 §8.x 逐步 RED/GREEN。

| # | Title | Type | Blocked by | MASTER §8 | User stories |
|---|-------|------|------------|-----------|--------------|
| D-S1 | migration 006 sync tables | AFK | — | 8.1 | AC-7 |
| D-S2 | Job state machine + event log | AFK | D-S1 | 8.2 | AC-1, AC-4 |
| D-S3 | Orchestrator core + job persistence | AFK | D-S2 | 8.3 | AC-4 |
| D-S4 | ResourceGuard before fetch | AFK | D-S3 | 8.4 | AC-5 |
| D-S5 | Incremental job E2E (FakeAdapter) | AFK | D-S4 | 8.5 | AC-6 |
| D-S6 | Backfill partition + guard pause | AFK | D-S5 | 8.6 | AC-3, AC-5 |
| D-S7 | Reconcile job + conflict validator | AFK | D-S5 | 8.7 | AC-2 |
| D-S8 | Registry bootstrap + sync_registry CLI | AFK | D-S3 | 8.8 | AC-10 |
| D-S9 | Ingestion orchestrator smoke | AFK | D-S5 | 8.9 | AC-9 |
| D-S10 | Docs + status + final gates | AFK | D-S9 | 8.10–8.11 | AC-11, AC-12 |

## 依赖图

```text
D-S1 → D-S2 → D-S3 → D-S4 → D-S5 → D-S6
                          └→ D-S7
              D-S3 → D-S8
              D-S5 → D-S9 → D-S10
```

## 用户确认（Plan 代理裁决）

- 粒度：**与 §8 步对齐** — 适合 TDD 逐步证据
- 无 HITL 切片 — DECISIONS 已冻结边界
- 不合并 S5/S7 — reconcile 有独立语义测
