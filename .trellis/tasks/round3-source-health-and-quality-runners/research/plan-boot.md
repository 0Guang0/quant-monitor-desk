# Plan Boot — B3F-SH Source Health & Quality Runners

> Phase P0 complete

## 用户目标

将 Batch 01 read-only data health（DH2）升级为 Batch6 可持久化的 source health 跟踪与 quality runner 闭包：表 + writer、revision_audit / data_quality job、readiness rollup、FRED live primary（用户授权）、硬约束 no-false-close。

## 依赖

| 依赖 | 状态 | Plan 策略 |
| ---- | ---- | --------- |
| B01-DH2 `round3-readonly-data-health-v2` | 已合并 master | v2 只读路径 **禁止** 建 `source_health_snapshot` |
| B3F-MIG migration 文件锁 | 并行 Plan/Execute | **R3F-SH-01** migration SQL 等 MIG 合并或主会话书面协调；可先 ADR + 测试骨架 |
| FRED live 用户授权 | **2026-06-25 owner 已授权** | `fred_live_authorization_2026-06-25.yaml` + `docs/quality/batch3f_fred_live_pilot_authorization_2026-06-25.md` |
| B3F-HYG ResourceGuard/perf | 并行 | 本分支只读；不混 PR |

## AC 草稿（roadmap R3F-SH-01..07）

- SH-01：`source_health_snapshot` ADR + writer + pytest（migration 文件归属 MIG）
- SH-02：`run_revision_audit` 实现（非 DeferredJobTypeError）
- SH-03：`run_data_quality` 实现
- SH-04：source readiness rollup 持久化扩展
- SH-05：`VR-DATAHEALTH-001` — DH2 路径不得建表
- SH-06：`B2.5-O-05` FRED-only live + sandbox/no-mutation 证据
- SH-07：Eastmoney/AkShare 不得 sidecar 误关闭

## 原计划已读

- [x] `docs/implementation_tasks/README.md`
- [x] GLOBAL×4（`GLOBAL_EXECUTION_RULES` / `GLOBAL_TESTING_POLICY` / `GLOBAL_RESOURCE_LIMITS` / `GLOBAL_TASK_TEMPLATE`）
- [x] `ROUND_3_BATCH6_DATA_GOVERNANCE/README.md`
- [x] `BATCH_3F_TASK_CARD_MANIFEST.md` · `BATCH_3F_COORDINATOR_PLAYBOOK.md` §3.5 · §2.5/§2.6
- [x] `BATCH_3F_HARDENING_RULES.md` · `BATCH_3F_PLAYBOOK_ADVERSARIAL_AUDIT.report.md`
- [x] `PROJECT_IMPLEMENTATION_ROADMAP.md` Round 3F.3
- [x] `R3F_verified_audit_ops_perf_hygiene.md`（`VR-DATAHEALTH-001`）
- [x] `014_implement_data_sync_orchestrator.md`（runner 矩阵）
- [x] `PROMPT_04_debt_r3b275_fred_staged_semantics.md`（`B2.5-O-05` 边界）
- [x] `docs/schema/MIGRATION_008_PLAN.md` · `MIGRATION_COVERAGE.md`（只读；migration 归属 MIG）

**Phase P0 complete**
