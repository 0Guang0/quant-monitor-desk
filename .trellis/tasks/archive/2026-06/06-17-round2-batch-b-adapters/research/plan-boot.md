# Plan Boot — Round 2 Batch B（013 adapter skeletons）

> Protocol v2 追溯补录 · Plan 已冻结后代际对齐

## 用户目标摘要

交付五 vendor adapter skeleton + factory；FetchPort 可注入；SUCCESS 写真实 raw + 可选 FileRegistry。

## 前置依赖 / Batch 关系

- Batch A PASS @ ab8d1eb
- DECISIONS.md §2 Batch B
- Round 2 数据 ingestion 验证

## 预期 AC 草稿（→ MASTER §2）

AC-1..10：五 adapter、raw+hash、PortError 映射、QMT AUTH/SUCCESS、无 WriteManager、FileRegistry、cninfo EMPTY_RESPONSE、cov≥75%

## Plan Phase 顺序

P0 → P1 GitNexus → 2a brainstorm → 2b SDD → 3 grill-me → 4 API design → 5a→5d → 5e 对抗审计 → 冻结

## Phase P0 complete
