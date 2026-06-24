# Batch 01 — Model Source Readiness

> Canonical batch entrypoint for the next execution batch after `PROJECT_IMPLEMENTATION_ROADMAP.md`.  
> This folder groups the first batch of task cards and the legacy/original cards they depend on.  
> Legacy cards stay at their original paths to preserve historical links; this batch folder includes them by manifest and audit binding rather than moving files.

---

## 1. Batch purpose

Batch 01 prepares the project for controlled real-data source work without allowing production-live claims or production clean writes.

Business objective:

- Define exactly which Layer1–Layer5 model inputs may ask real sources for data.
- Add a safe FRED-only sandbox pilot path.
- Tighten TDX manual probe execution rules.
- Move baostock/cninfo/akshare from v2 sample expansion toward model-driven staged pilot v3.
- Add read-only data health v2 to check source readiness evidence.

This batch does **not** enable production ingestion, clean-table writes, full-market data ingestion, full-history backfill, production monitoring, or front-end user-facing dashboards.

---

## 2. Canonical task cards in this batch

### New / forward cards

| Batch order | Card                          | Canonical path                                                                                     | Status                                   |
| ----------- | ----------------------------- | -------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| 01          | Model input whitelist         | `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/R3D_model_input_whitelist.md`         | Ready for `/to-issues` planning          |
| 02          | FRED authorized sandbox pilot | `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/R3E_fred_authorized_sandbox_pilot.md` | Ready after whitelist planning           |
| 03          | TDX manual probe addendum     | `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/R3E_tdx_manual_probe_addendum.md`     | Addendum to 018C; authorization required |
| 04          | Real-data staged pilot v3     | `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/R3E_real_data_staged_pilot_v3.md`     | Blocked until whitelist exists           |
| 05          | Read-only data health v2      | `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/R3E_readonly_data_health_v2.md`       | Runs after/alongside evidence producers  |

### Legacy/original cards included by reference

| Legacy card                  | Canonical path                                                                                           | Why included                                                                      |
| ---------------------------- | -------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| TDX 018C low-cost probe      | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018C_tdx_pytdx_low_cost_probe.md`                     | Original TDX/pytdx sidecar probe constraints.                                     |
| Real data staged pilot v2    | `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_real_data_staged_pilot_v2.md`          | Prior baostock/cninfo/akshare staged pilot scope and evidence model.              |
| Read-only data health v1     | `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_readonly_data_health_v1.md`            | Prior read-only health scope and non-write boundary.                              |
| FRED staged semantics prompt | `docs/implementation_tasks/ROUND_3_PARALLEL_PROMPTS/PROMPT_04_debt_r3b275_fred_staged_semantics.md`      | Historical note that macro supplementary cannot substitute FRED primary evidence. |
| Live pilot gate              | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018B_production_live_pilot_gate.md`                   | Historical production-live and sandbox clean-write boundary.                      |
| Staged pilot v2 addendum     | `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_staged_pilot_v2_execution_addendum.md` | Execution discipline and test-quality addendum for v2.                            |

---

## 3. Mandatory companion files

| File                                                                      | Purpose                                                                            |
| ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `BATCH_01_TASK_CARD_MANIFEST.md`                                          | Full task-card inclusion manifest and dependency order.                            |
| `BATCH_01_ADVERSARIAL_AUDIT.md`                                           | Adversarial audit of new and legacy cards, with findings and required hardening.   |
| `BATCH_01_HARDENING_RULES.md`                                             | Batch-level rules that every card in this batch inherits.                          |
| `docs/quality/coordination/BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` | **主会话**七路并行派发、Audit 队列、合并顺序与 PASS 门禁（执行 Batch 01 前必读）。 |
| `docs/quality/coordination/BATCH_01_PLAYBOOK_ADVERSARIAL_AUDIT.report.md` | Playbook 对抗性审计与修复闭环索引。                                                |

Executors must read all companion files above before turning any card into `/to-issues` issues. Merge coordinators must read the playbook before opening worktrees.

---

## 4. Execution order

1. Read this README, manifest, audit, and hardening rules.
2. Read the relevant canonical task card.
3. Read the listed legacy/original cards for that task.
4. Run `/to-issues` and split into vertical slices.
5. Run `/tdd` one RED → GREEN slice at a time.
6. Produce task-local evidence.
7. Run the card-specific gates.
8. Update registry rows only when evidence is exact; otherwise re-defer with owner, phase, and closure test.

---

## 5. Batch-level hard stop conditions

Stop immediately if any task attempts to:

- enable production clean write,
- mark FRED/TDX/Yahoo/QMT/xqshare as production-live,
- promote AkShare or TDX to Primary,
- run full-market or full-history ingestion,
- fetch live data without explicit authorization,
- use staged/fixture/sandbox evidence as production readiness proof,
- close a deferred registry row without exact closure evidence,
- bypass `DataSourceService`, `SourceRoutePlanner`, `WriteManager`, `DbValidationGate`, or `ResourceGuard`.
