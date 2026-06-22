# Round 3 Repair/Debt Worktree Execution Plan

> Status: planning protocol addendum. This file does not create branches or worktrees by itself.
> Scope: Round 3 after Batch 2.75 repair closeout. It applies Phase 8D from `complex-task-planning-protocol.md` to split staged mainline work from known non-blocking repair/debt work.

## 1. Current checkpoint

- Batch 1, Batch 2, and Batch 2.5 are completed/archived.
- Batch 2.5 remains staged/fixture-only and is not production-live evidence.
- Batch 2.75 controlled pilot executed and repaired with closeout `PILOT_FAIL_SOURCE`.
- Batch 2.75 Request 2 Eastmoney hist remains deferred as `R3-B2.75-REQ2-EM`.
- `R3-B25-PERF-BUDGET-01` and `R3-B25-HYG-03` remain CI/Batch6-owned deferred evidence refresh items.
- Batch 3 / `019` may proceed only as staged-only downstream work after `R3-B3-STAGED-DOWNSTREAM-GATE` is closed.

## 2. Required first step

Before creating any Round 3 worktree branch, commit or otherwise stabilize the protocol baseline:

| Step            | Required state                                                                                                        |
| --------------- | --------------------------------------------------------------------------------------------------------------------- |
| Protocol branch | `chore/trellis-repair-debt-lite-protocol` or equivalent committed baseline                                            |
| Files           | `complex-task-planning-protocol.md`, `workflow.md`, `AGENTS.md`, `CLAUDE.md`, this file, Round3 map/task-card updates |
| Gate            | no worktree creation until this baseline is visible to every agent                                                    |

## 3. Branch / worktree matrix

| Stream                     | Suggested branch                          | Worktree timing                                        | Parallel?           | Owner shape          | Purpose                                                                                        |
| -------------------------- | ----------------------------------------- | ------------------------------------------------------ | ------------------- | -------------------- | ---------------------------------------------------------------------------------------------- |
| Integration                | `integration/round3`                      | after protocol baseline                                | Serial              | merge coordinator    | Receives only reviewed branches that passed merge gate.                                        |
| Batch 3 staged gate        | `feature/round3-batch3-staged-gate`       | before `019`                                           | Serial before `019` | main session         | Freezes staged-only limitations and closes `R3-B3-STAGED-DOWNSTREAM-GATE`.                     |
| Layer2 mainline            | `feature/round3-019-layer2-sensor`        | after staged gate                                      | Serial mainline     | implementation agent | Implements `019` under staged-only semantics.                                                  |
| Layer3 loader              | `feature/round3-020-layer3-loader`        | after `019` gate/lineage stability                     | Can run with 023A   | implementation agent | Implements `020`.                                                                              |
| Evidence foundation        | `feature/round3-023a-evidence-foundation` | after `019` gate                                       | Can run with `020`  | evidence agent       | Minimal Layer5 evidence contract, ids, hashes, manual-review flags, Agent-text-not-fact tests. |
| Layer3 snapshot            | `feature/round3-021-layer3-snapshot`      | after `020` and evidence foundation contract stability | Serial              | implementation agent | Implements `021`.                                                                              |
| Layer4 market              | `feature/round3-022-layer4-market`        | after `021`                                            | Serial by default   | implementation agent | Implements `022`.                                                                              |
| Full Layer5                | `feature/round3-023b-evidence-chain-full` | after `022` / Layer3-4 integration readiness           | Serial              | implementation agent | Completes full `023`.                                                                          |
| 018C source probe debt     | `debt/r3b275-018c-low-cost-probe`         | after Batch 2.75 Request 2 reconciliation              | Parallel            | probe agent          | Sidecar raw-only candidate probe; does not close Request 2 by itself.                          |
| Perf/hyg registry debt     | `debt/r3b275-perf-hyg-registry`           | after protocol baseline                                | Parallel            | docs/evidence agent  | CI/Batch6 perf/hyg evidence and registry alignment.                                            |
| FRED staged semantics debt | `debt/r3b275-fred-staged-semantics`       | after protocol baseline                                | Parallel            | policy agent         | Keeps FRED/macro supplementary semantics staged-only.                                          |
| CI gate hardening          | `chore/round3-ci-gate-hardening`          | after protocol baseline                                | Parallel            | CI agent             | Verification command hygiene and staged/live readiness guard tests.                            |

Do not pre-create all branches. Create each branch/worktree only after its slice plan has owner, base branch, target branch, allowed files, forbidden files, verification commands, and merge gate.

## 4. Serial order

The mainline order is:

1. protocol baseline
2. `integration/round3`
3. `feature/round3-batch3-staged-gate`
4. `feature/round3-019-layer2-sensor`
5. `feature/round3-020-layer3-loader`
6. `feature/round3-021-layer3-snapshot`
7. `feature/round3-022-layer4-market`
8. `feature/round3-023b-evidence-chain-full`
9. final integration / Round3 closeout gate

`feature/round3-023a-evidence-foundation` may run beside `020` once `019` staged gate is closed. It must remain a minimal foundation slice and must not implement full Layer5 bars/events/financials/valuation.

## 5. Parallel Phase 8D debt slices

These may run in parallel with staged-only mainline work:

| Slice  | Source ID                                                     | Suggested branch                    | Allowed files                                                                                                                                                         | Forbidden files                                                                           | Verification                                                       |
| ------ | ------------------------------------------------------------- | ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| D-018C | `R3-B2.75-REQ2-EM` / `R3-B2.75-FOLLOWUP-DATA-INTERFACE-PROBE` | `debt/r3b275-018c-low-cost-probe`   | `018C_tdx_pytdx_low_cost_probe.md`, task-local evidence, narrow `specs/datasource_registry/`, narrow `backend/app/ops/` or adapter files if explicitly planned, tests | production DB, default source enablement, broad CLI/backfill, Batch 2.75 closeout rewrite | disabled-by-default tests, raw-only evidence, no-mutation proof    |
| D-PERF | `R3-B25-PERF-BUDGET-01` / `R3-B25-HYG-03`                     | `debt/r3b275-perf-hyg-registry`     | registry docs, repair/debt evidence, registry alignment tests                                                                                                         | backend runtime, source routing defaults, production DB                                   | registry tests and smoke evidence or explicit tool-limitation note |
| D-FRED | `B2.5-O-05`                                                   | `debt/r3b275-fred-staged-semantics` | staged policy docs, production-live pilot policy docs, relevant tests                                                                                                 | live FRED fetch, production DB, route default promotion                                   | staged gate tests and policy tests                                 |
| D-CI   | Round3 gate hygiene                                           | `chore/round3-ci-gate-hardening`    | tests, docs/ops verification commands, pytest markers if needed                                                                                                       | business runtime behavior                                                                 | targeted tests, full gate command list                             |

## 5.1 External reference landing task cards

The following original task cards define how external project references land into QMD work. Plan must cite these task cards in MASTER Source Context Index before creating any related branch.

| Task card                                                                                     | Round / batch                                       | Branch                                                             | Parallel?                                           | Required external links                                                                                                                                                                                                                                                                                   |
| --------------------------------------------------------------------------------------------- | --------------------------------------------------- | ------------------------------------------------------------------ | --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `docs/implementation_tasks/ROUND_3_REFERENCE_LANDING/R3D_018C_low_cost_source_probe.md`       | Round 3 / Batch 2.75 follow-up / Phase 8D           | `debt/r3b275-018c-low-cost-probe`                                  | Yes, with staged-only `019`                         | `https://github.com/henrylin99/tdx_quant`, `https://github.com/quant-king299/EasyXT`, `https://github.com/quant-king299/JQ2PTrade`, `https://github.com/quant-king299/ptqmt-site`, `https://github.com/bebopze/tdx-quant`, `https://github.com/afute/TdxQuantNet`, `https://github.com/hlh2518/tdx-quant` |
| `docs/implementation_tasks/ROUND_3_REFERENCE_LANDING/R3D_ops_db_data_health_reference.md`     | Round 3 / Batch 1 carry-forward + Batch 6 sub-batch | `debt/r3-ops-inspect-data-health-references` or Batch 6 sub-branch | Yes for docs/contracts; runtime waits for owner map | `https://github.com/quant-king299/EasyXT`, `https://github.com/quant-king299/JQ2PTrade`, `https://github.com/quant-king299/ptqmt-site`                                                                                                                                                                    |
| `docs/implementation_tasks/ROUND_3_REFERENCE_LANDING/R4D_readonly_sql_assistant_reference.md` | Round 4 candidate, not Round 3 execution            | future `research/r4-readonly-sql-assistant`                        | Not a Round 3 branch                                | `https://github.com/eosphoros-ai/DB-GPT`, `https://github.com/eosphoros-ai/DB-GPT-Hub`                                                                                                                                                                                                                    |

## 6. Core file ownership locks

Only one active branch at a time may own write access to each group:

- `backend/app/ops/`
- `backend/app/datasources/`
- `backend/app/db/`
- `backend/app/validators/`
- `backend/app/layer2_sensors/`
- `backend/app/layer3_chains/`
- `backend/app/layer4_markets/`
- `backend/app/layer5_evidence/`
- `specs/contracts/`
- `specs/datasource_registry/`
- `specs/schema/`
- `configs/datasource.yml`
- `configs/resource_limits.yaml`
- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`
- `docs/RESOLVED_ISSUES_REGISTRY.md`
- `docs/quality/*REGISTRY*.md`
- `data/duckdb/quant_monitor.duckdb`

Registry files should normally be reconciled by one merge coordinator. A debt branch may propose registry deltas in evidence, but concurrent registry row edits are not allowed unless the branch owns the registry slice.

## 7. Merge gate

Every branch must provide this before merge into `integration/round3`:

| Gate               | Required evidence                                                                                |
| ------------------ | ------------------------------------------------------------------------------------------------ |
| Scope              | changed files, intended scope, out-of-scope untouched files                                      |
| Tests              | targeted tests and result                                                                        |
| Broad verification | full pytest / ruff / format / compile / production_gate / doc_links, or explicit tool limitation |
| Data safety        | production DB no-mutation proof if any data path is touched                                      |
| Registry           | reconciliation summary or statement that registry is untouched                                   |
| Semantics          | staged-only / production-live claims checked against Batch 2.75 closeout                         |
| Deferred           | remaining deferred IDs with owner, phase, and closure command                                    |

Recommended merge order:

1. tests-only / CI-gate branches
2. docs/evidence-only branches
3. registry-only branches
4. mainline staged-gate branch
5. mainline runtime branches in order: 019 -> 020 -> 023A -> 021 -> 022 -> 023B
6. source/data/probe branch after isolated review

## 8. Self-check before branch creation

A coordinator must answer yes to every item before running `git worktree add`:

- [ ] Is the protocol baseline committed or otherwise visible to the agent?
- [ ] Is the base branch named?
- [ ] Is the target branch named?
- [ ] Is the owner agent named?
- [ ] Is the source ID mapped to audit/registry/task-card authority?
- [ ] Are allowed files listed?
- [ ] Are forbidden files listed?
- [ ] Is production/data boundary explicit?
- [ ] Is verification command set explicit?
- [ ] Is merge gate explicit?
- [ ] Does the slice avoid owning a core file group already owned by another active branch?
