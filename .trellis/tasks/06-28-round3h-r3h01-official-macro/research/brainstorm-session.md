# Trellis Brainstorm — R3H-01（Plan 2a）

## 问题陈述

Batch 3H 首切片：六官方宏观/披露源 production-entry 闭环；首优 G10 FRED 证据分裂。

## 方案选项（已否决/采纳）

| 选项                              | 结论                          |
| --------------------------------- | ----------------------------- |
| A. 保留 bridge + sidecar 永久     | **否决** — G14 pilot hack     |
| B. 统一 normalizer + 迁 fred_port | **采纳** — grill-me Q3/Q4     |
| C. 仅 debt-lite G10 不修六源      | **否决** — Batch 3H hardening |
| D. 本卡写主库验证                 | **否决** — 路线图 §5.0        |

## 风险

| 风险                 | 缓解                            |
| -------------------- | ------------------------------- |
| registry 并行冲突    | §9.6 coordinator manifest       |
| 双份 fred fetch 实现 | L2 迁入 `fred_port`，ops 薄封装 |
| 工期膨胀六源         | replay-first；ADR 仅显式收窄    |

**Phase 2a complete** — 细节见 `prd.md`（薄索引）
