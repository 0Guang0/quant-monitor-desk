# Batch 3F-R Coordinator Playbook

## 0. Scope

Coordinate a controlled reference-adoption refactor after Batch 3F completion and before Round 3G.

This playbook assumes Batch 3F integration is green. It does not authorize production clean write, default live source enablement, or broad runtime behavior changes.

## 1. Dispatch tracks

| Track                            | Branch suggestion                             | Task cards           | Parallel?                                                                         |
| -------------------------------- | --------------------------------------------- | -------------------- | --------------------------------------------------------------------------------- |
| Task-local rules + license gate  | `chore/round3fr-reference-rules-license-gate` | `R3FR-01`            | first, blocks all direct adoption until task-local reference rules are updated    |
| Data health + CLI vertical slice | `refactor/round3fr-data-health-cli`           | `R3FR-02`, `R3FR-06` | next as one coordinated slice; do not split into rule-only or CLI-only micro-work |
| TDX provider                     | `refactor/round3fr-tdx-provider`              | `R3FR-03`            | after task-local rules; preferably after data health profile contracts are stable |
| Round4 backtest planning         | `docs/round4-reference-backtest`              | `R3FR-04`            | parallel after R3FR-01                                                            |
| Provider catalog                 | `feature/round3fr-provider-catalog`           | `R3FR-05`            | parallel after R3FR-01                                                            |
| Cleanup/rehome                   | `chore/round3fr-cleanup-rehome`               | `R3FR-07`            | last only                                                                         |

## 2. File locks

Avoid concurrent edits to these files:

- `PROJECT_IMPLEMENTATION_ROADMAP.md`
- `docs/implementation_tasks/README.md`
- `specs/contracts/reference_adoption_guardrails.yaml`
- `backend/app/ops/data_health.py`
- `backend/app/cli/data_commands.py`
- `backend/app/ops/interface_probe_fetch_ports.py`
- `backend/app/ops/tdx_manual_probe.py`
- `specs/contracts/data_quality_rules.yaml`
- `docs/modules/backtest_review_lifecycle.md`

## 3. Merge order

1. Task-local reference rules and license guardrails.
2. Data health profile refactor and `qmd data health` runtime wiring as one vertical slice.
3. TDX provider refactor.
4. Provider catalog and Round4 planning updates.
5. Cleanup/rehome.
6. Full pytest and roadmap/index consistency check.

## 4. Plan requirements per branch

Every branch plan must include:

- exact reference files read from `参考项目/**`
- license posture
- exact QMD target files
- forbidden symbols / forbidden behavior
- expected test additions
- rollback plan

For code-adaptation branches, the plan must include a before/after table showing which self-built wheel is replaced and how compatibility is preserved.

## 5. Acceptance gates

Batch 3F-R cannot close unless:

- root roadmap points to the correct next entrypoint or records 3F-R completion before 3G
- `docs/implementation_tasks/README.md` includes Round 3F-R in execution order
- all new task cards are discoverable through the batch README and manifest
- task-local reference adoption rules and license guardrails are updated
- no central executable reference inventory is required or created
- no backend runtime import path points to `参考项目/**`
- data-health CLI has a real read-only path backed by the same profile runtime as R3FR-02
- Round4 backtest planning explicitly adopts JQ2PTrade/EasyXT instead of from-scratch design
- OpenBB remains architecture-only
- no module is planned to need more than three implementation batches to reach full production-stable scope
- design, contract, architecture, and rule-definition files describe complete target shape; current completion ratings stay in `MODULE_COMPLETION_RATING.md` and planning/task files only

## 6. Do not close by assertion

Do not mark any R3FR row done by documentation statement alone if it changes runtime behavior. Runtime refactors require tests.

Planning-only tasks may close with updated task cards/docs and tests that verify wording or contracts where such tests already exist or are added.
