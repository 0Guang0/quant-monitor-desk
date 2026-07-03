# Round 3 Data Production Readiness

> Status: planning task-card package only. These cards do not authorize production live access or production clean write.  
> Parent roadmap: `PROJECT_IMPLEMENTATION_ROADMAP.md` Round 3D / 3E.  
> Purpose: turn the first batch of future-roadmap items into execution-ready task cards so agents do not infer full-market ingestion, production readiness, or live-source enablement from staged evidence.  
> Batch entrypoint: `BATCH_01_MODEL_SOURCE_READINESS/README.md` is mandatory before executing any first-batch card.  
> Historical status: Batch 01 / Round 3D–3E is complete; current executable entrypoint has moved to `../ROUND_3_BATCH6_DATA_GOVERNANCE/BATCH_3F_BATCH6_DATA_GOVERNANCE/README.md`.

---

## 0. Batch-first execution note

The flat files in this directory are the canonical forward task cards. The first execution batch is organized under:

- `BATCH_01_MODEL_SOURCE_READINESS/README.md`
- `BATCH_01_MODEL_SOURCE_READINESS/BATCH_01_TASK_CARD_MANIFEST.md`
- `BATCH_01_MODEL_SOURCE_READINESS/BATCH_01_ADVERSARIAL_AUDIT.md`
- `BATCH_01_MODEL_SOURCE_READINESS/BATCH_01_HARDENING_RULES.md`
- `docs/quality/coordination/BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` — merge coordinator playbook for seven-way parallel execution

Executors must treat those batch files as mandatory companions. Legacy/original task cards stay at their historical paths and are included by the batch manifest; they are not copied or moved to avoid stale duplicates.

---

## 1. Package scope

This directory contains the first batch of forward task cards that did not yet have dedicated original task cards:

| Card                                   | Roadmap batch | Purpose                                                                  | Execution priority         |
| -------------------------------------- | ------------- | ------------------------------------------------------------------------ | -------------------------- |
| `R3D_model_input_whitelist.md`         | Round 3D.2    | Define the first production-readiness input whitelist for Layer1–Layer5. | P0                         |
| `R3E_fred_authorized_sandbox_pilot.md` | Round 3E.1    | Add a FRED-only sandbox/raw pilot path without production write.         | P0                         |
| `R3E_tdx_manual_probe_addendum.md`     | Round 3E.2    | Add execution details on top of existing 018C TDX/manual probe cards.    | P0/P1                      |
| `R3E_real_data_staged_pilot_v3.md`     | Round 3E.3    | Expand baostock/cninfo/akshare staged pilot by model input whitelist.    | P1                         |
| `R3E_readonly_data_health_v2.md`       | Round 3E.4    | Extend read-only data health to source-readiness and pilot-v3 evidence.  | P1                         |
| `FIRST_BATCH_SELF_CHECK.md`            | This package  | Static self-check of coverage, gates, constraints, and risks.            | Required before execution  |
| `BATCH_01_MODEL_SOURCE_READINESS/`     | Batch 01      | Batch-first manifest, adversarial audit, and hardening rules.            | Mandatory before execution |

---

## 2. Execution ordering

Recommended order:

1. `R3D_model_input_whitelist.md` — decide what the model is allowed to ask real sources for.
2. `R3E_fred_authorized_sandbox_pilot.md` and `R3E_tdx_manual_probe_addendum.md` — can run in parallel after explicit authorization rules are clear.
3. `R3E_real_data_staged_pilot_v3.md` — expands staged real data using the whitelist.
4. `R3E_readonly_data_health_v2.md` — checks the evidence produced by FRED / TDX / v3 staged pilot.

Do not start sandbox clean-write rehearsal until these tasks and the full Layer5 evidence-chain work have closed or explicitly re-deferred their gates.

---

## 3. Global boundaries for this package

All cards in this package inherit these rules:

- Use `/to-issues` to turn each card into vertical-slice issues before implementation.
- Use `/tdd` and one RED → GREEN tracer bullet at a time for code tasks.
- Follow `/ponytail` full: no speculative abstractions, no large framework, no broad refactor, no full-market default path.
- Follow `/karpathy-guidelines`: simple, explicit, inspectable code; prefer boring direct paths.
- Follow `/testing-guidelines`: tests assert business behavior; no call-only or not-null-only tests.
- Every changed or new test must explain coverage scope, test object, and purpose/goal in a docstring or close comment.
- Any implementation fix must run the task-specific tests and the broader merge gate listed by the card, unless the environment blocks execution; blocked execution must be reported with exact command and error.
- Batch 01 files under `BATCH_01_MODEL_SOURCE_READINESS/` are mandatory companions. If they are stricter than an individual card, the stricter batch-level rule wins.

---

## 4. Source and production safety rules

The following claims remain forbidden after completing this package unless a later production-entry gate explicitly changes them:

- `production-live ready`
- `production clean write enabled`
- `full-market ingestion complete`
- `full-history backfill complete`
- `FRED production source enabled`
- `TDX production primary enabled`
- `AkShare primary source enabled`
- `Layer2/3/4 production data fully connected`

Allowed outcome language:

- `raw/staging/sandbox evidence collected`
- `source readiness assessed`
- `validation-only candidate evaluated`
- `model input whitelist established`
- `eligible for later sandbox clean-write rehearsal` only when the card's gates explicitly pass

---

## 5. Required closure report for every card

Each task execution report must include:

1. Branch / worktree / task ID.
2. What changed.
3. What did not change.
4. Test commands and results.
5. ResourceGuard status.
6. Source access authorization status.
7. Production DB mutation proof or statement that no production DB path was touched.
8. Registry updates: resolved, re-deferred, or no registry row affected.
9. Remaining risks and next gate.
