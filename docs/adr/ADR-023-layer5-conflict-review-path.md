# ADR-023 — Layer5 severe conflict → manual review queue

> **Status:** Accepted (Plan freeze) · **closes Plan scope for** `R3-PARTIAL-4` (UX path only; no review UI)

## Context

`023A` foundation 已冻结 `ManualReviewState.QUEUED` 与 `need_human_review=True` 配对；`data_validation_and_conflict.md` 描述 severe conflict 与 `manual_review_queue` 表，但未规定 instant severe queue UI。

## Decision

**failed reconcile 且 severity=severe 时：**

1. 设置 `need_human_review=True`
2. 设置 `manual_review_state=queued`
3. **不**实现 instant severe queue UI（Round4 defer）
4. evidence chain builder 在 severe 路径上 fail-closed 或产出 queued 记录（由测试冻结）

## Consequences

- Execute SLICE-CONFLICT：`test_evidenceChain_severeConflictQueuesManualReview`
- Registry 行 `R3-PARTIAL-4`：**本分支不闭合**；主会话根据 evidence 更新 COVERAGE
- 与 023A `EvidenceFoundationValidator._validate_manual_review` 一致

## Alternatives rejected

- **Instant severe queue UI** — 超出 Batch 5 scope；任务卡 §17 明确 UX/ADR + pytest，非 UI

## 023b scope note (AC-023-2)

`023b` Execute 以 **bar-only staged slice** 闭合 MASTER §5.3 与 Tier A 门禁；`event_registry` / financial / valuation staged validators 诚实登记于 `layer5_evidence_contract.yaml` `deferred_to_023b`。不得因 `models` 段 schema 定义而声称全族 validator 已落地。
