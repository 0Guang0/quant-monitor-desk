# Plan Boot — 06-19-round2-6-contract-gate

## 用户目标摘要

用户确认将 Round2.6 pre-Round3 work 拆成两个 Trellis 复杂任务。本任务是第一轮：确认并执行 Phase B 的 contract gate 计划，使 Claude Code / Codex / Cursor 后续执行时不会漏读 Phase A 设计文件和契约。

## 原计划已读

- `docs/implementation_tasks/README.md`
- `GLOBAL_EXECUTION_RULES.md`
- `GLOBAL_TESTING_POLICY.md`
- `GLOBAL_RESOURCE_LIMITS.md`
- `GLOBAL_TASK_TEMPLATE.md`
- `ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/README.md`
- `016A`–`016F` 任务卡

## 前置依赖 / Batch 关系

- Round2 core and Round2.5 repair alignment are complete enough for contract planning.
- Phase A documents exist but are not implemented.
- This task must complete before `06-19-round2-6-routing-service-gate` starts.

## 预期 AC 草稿

- AC-B1: SourceRegistry ↔ SourceCapabilityRegistry domain alignment test exists and passes.
- AC-B2: adapter supported_domains mismatch is captured by test and reconciliation path is explicit.
- AC-B3: RoutePlan contract tests exist for disabled/no-source/fallback states.
- AC-B4: DataSourceService boundary tests exist; direct adapter factory use is constrained.
- AC-B5: module boundary checker exists and tests import rules.
- AC-B6: data CLI contract tests exist for dry-run/route-preview/error docs.
- AC-B7: platform matrix tests exist for QMT/xqshare disabled behavior.
- AC-B8: `docs/AUDIT_DEFERRED_REGISTRY.md` reconciles stale Round2 deferred rows.
- AC-B9: Phase D benchmark requirements are handed off to Task 2.
- AC-B10: root Phase A self-check is migrated or explicitly retained until Task 2.

## Plan Phase 顺序

P0/P0i/P0o complete; Phase 1a/1b summarized in `project-overview.md` and `gitnexus-summary.md`; Phase 3 doubt captured in `grill-me-session.md`; Phase 5 artifacts generated in MASTER/AUDIT/freeze/jsonl.

## Phase P0 complete
