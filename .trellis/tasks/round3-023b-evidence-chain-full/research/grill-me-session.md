# Grill-me session — 023b Layer5 evidence chain

## Q1: 为何不在 023A 一次做完？

**A:** 任务卡 §16 明确拆分：`023A` = identity/provenance 最小集；full `023` 需 `022` + L3/L4 集成稳定后再串 chain。023A 已归档，本 Plan 只增量。

## Q2: severe conflict 走 manual queue 还是 instant severe？

**A:** 023A 已选 `ManualReviewState.QUEUED` + `need_human_review=True` 配对（`R3-PARTIAL-4 severe defer`）。本任务冻结 ADR：**failed reconcile severe → queued manual review**，不做 instant severe UI（Round4 defer）。

## Q3: 是否接 live source？

**A:** **否。** staged fixture only；Batch 01 hardening §1–§3；playbook §2.6 B01-023 forbidden live。

## Q4: `R2-RISK-2` 本任务关还是 defer？

**A:** 仅当 chain builder 必须读 staged bundle 时引入最小 `EvidenceReadPort` Protocol + fake test double；**不**重构全局 adapter。若 staged dict 入参即可，则 ADR re-defer `R2-RISK-2` 并登记。

## Q5: registry 三件套谁闭合？

**A:** **主会话**批处理；本分支禁止并发 commit 闭合 `AUDIT_DEFERRED` / `UNRESOLVED` / `COVERAGE`。

## 开放项（Execute 前）

- Execute Boot 须确认全量 pytest 绿（§16 硬 gate）
- Playbook 文档须已在 `master` 可引用（worktree 已拷贝协调手册供 Plan freeze）
