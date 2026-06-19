# Round 3 Batch Implementation Map

> Purpose: one root-level index for splitting Round 3 into executable Trellis batches without losing task/deferred-item traceability.
>
> Status: planning/index document. It is not runtime code and does not participate in DB migration.
>
> Scope rule: `docs/` and `specs/` are design/contract inputs only. Runtime implementation must land in `backend/`, `frontend/`, `scripts/`, `configs/`, `tests/`, or other implementation paths already mapped by `MIGRATION_MAP.md`.

## 0. Mandatory inputs before planning or executing any Round 3 batch

| Input                                                         | Why it is mandatory                                                                   |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `MIGRATION_MAP.md`                                            | Project-level map and implementation-directory boundary.                              |
| `docs/implementation_tasks/TASK_INPUT_CONTEXT_INDEX.md`       | Cross-task input index and Trellis archive pointers.                                  |
| `docs/AUDIT_DEFERRED_REGISTRY.md`                             | Authoritative registry for OPEN / DEFERRED / RESOLVED audit items.                    |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md`                          | Operator-facing unresolved/deferred split.                                            |
| `docs/RESOLVED_ISSUES_REGISTRY.md`                            | Prevents reopening items that are already closed.                                     |
| `docs/ROUND3_HANDOFF.md`                                      | Round 3 entry handoff and start checklist.                                            |
| `docs/implementation_tasks/ROUND3_EARLY_CLOSE_PLAN.md`        | Round 3 early ops and deferral closeout plan.                                         |
| `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/README.md` | Declares formal Round 3 tasks `017`-`023` and the unnumbered DB inspect CLI boundary. |
| `.trellis/spec/guides/complex-task-planning-protocol.md`      | Trellis complex-task planning, batching, Execute, Audit, and Repair rules.            |

## 1. ID convention used by this file

Round 3 has two classes of work:

1. **Formal numbered implementation tasks:** `017`-`023` under `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/`.
2. **Unnumbered or deferred repay items:** registry IDs from `docs/AUDIT_DEFERRED_REGISTRY.md` / `docs/UNRESOLVED_ISSUES_REGISTRY.md`, plus a small number of local index aliases for items that have no formal task number.

Local aliases introduced here do **not** replace the authoritative registry. They only make Trellis batch planning unambiguous.

| Local alias                  | Authority / source                                                                                                    | Meaning                                                                                                                                          |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `R3-EARLY-DB-INSPECT-CLI`    | `docs/ROUND3_HANDOFF.md`; `docs/implementation_tasks/ROUND3_EARLY_CLOSE_PLAN.md`; `ROUND_3_MODELING_LAYERS/README.md` | Local DuckDB read-only inspect CLI. Full design must be written and frozen by the user before implementation. Do not reuse `.tmp/inspect_db.py`. |
| `R3-EARLY-LINEAGE-CONSUMERS` | `docs/implementation_tasks/ROUND3_EARLY_CLOSE_PLAN.md`                                                                | Layer snapshot lineage consumers, dependent on existing validation_report rule_version fields.                                                   |
| `R3-EARLY-PROD-SCALE-BENCH`  | `docs/implementation_tasks/ROUND3_EARLY_CLOSE_PLAN.md`; `scripts/production_equivalent_smoke.py`                      | Production-scale shard latency benchmark / production-equivalent smoke closeout.                                                                 |
| `DOC-R3-001`                 | `docs/UNRESOLVED_ISSUES_REGISTRY.md`                                                                                  | `docs/ROUND3_HANDOFF.md` needs current Round2.6 PASS status surfaced clearly.                                                                    |
| `DOC-R3-002`                 | `docs/UNRESOLVED_ISSUES_REGISTRY.md`                                                                                  | `ROUND3_EARLY_CLOSE_PLAN.md` should state that `AUDIT_DEFERRED_REGISTRY.md` wins on conflict.                                                    |

## 2. Formal Round 3 numbered tasks

| Task ID | Task file                                                                                           | Short scope                                                                       | Batch   |
| ------- | --------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ------- |
| `017`   | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/017_implement_layer1_axis_loader.md`             | Layer 1 axis loader: load five-axis specs and initialize axis registries/profile. | Batch 2 |
| `018`   | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018_implement_layer1_interpretation_snapshot.md` | Layer 1 feature and interpretation snapshots.                                     | Batch 2 |
| `019`   | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/019_implement_layer2_cross_asset_sensor.md`      | Layer 2 cross-asset registry, observations, daily snapshots, double-count guard.  | Batch 3 |
| `020`   | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/020_implement_layer3_industry_chain_loader.md`   | Layer 3 chain/anchor/node/edge/cross-chain-edge loader and strict validation.     | Batch 4 |
| `021`   | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/021_implement_layer3_snapshot_builder.md`        | Layer 3 industry-chain daily snapshot and Layer5 mapping view.                    | Batch 4 |
| `022`   | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/022_implement_layer4_market_structure.md`        | Layer 4 market registry, calendars, breadth, market snapshots.                    | Batch 5 |
| `023`   | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/023_implement_layer5_evidence_chain.md`          | Layer 5 instrument registry, bars, events, financials, valuation, evidence chain. | Batch 5 |

## 3. Round 3 split into 6 Trellis batches

### Batch 1 — R3 early entry, real-data/DB proof, and prerequisite ops

**Batch intent:** close or explicitly re-defer Round3 early evidence gaps before heavy modeling depends on unclear data state.

| Item ID                     | Source                                                                 | Required outcome / decision                                                                                               | Notes                                                                                                            |
| --------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `DOC-R3-001`                | `docs/UNRESOLVED_ISSUES_REGISTRY.md`                                   | Handoff wording reflects current Round2.6 archived PASS / routing service gate state.                                     | Docs-only if edited.                                                                                             |
| `DOC-R3-002`                | `docs/UNRESOLVED_ISSUES_REGISTRY.md`                                   | Early close plan points readers to `AUDIT_DEFERRED_REGISTRY.md` as authority on conflicts.                                | Docs-only if edited.                                                                                             |
| `R2.6-IMPL-8`               | `docs/AUDIT_DEFERRED_REGISTRY.md`                                      | Live QMT / Yahoo / xqshare validation remains disabled by default; run only in user-authorized staging/read-only sandbox. | Do not enable QMT/xqshare by default.                                                                            |
| `DB-R3-001`                 | `docs/UNRESOLVED_ISSUES_REGISTRY.md`                                   | Prove or close the absence of real raw/parquet vendor data in the project data root.                                      | Expected evidence: row counts, source_used, route_status, fetch_log, raw/parquet presence or documented absence. |
| `DB-R3-002`                 | `docs/UNRESOLVED_ISSUES_REGISTRY.md`                                   | Query local DuckDB in read-only mode or defer to sanctioned inspect CLI.                                                  | Do not mutate production DB.                                                                                     |
| `R3-PARTIAL-2`              | `docs/AUDIT_DEFERRED_REGISTRY.md`                                      | Provide one real/staged vendor `FetchPort` E2E or `run_full_load` production skeleton pytest.                             | Closely related to real-data proof.                                                                              |
| `R3-EARLY-DB-INSPECT-CLI`   | `docs/ROUND3_HANDOFF.md`; `ROUND3_EARLY_CLOSE_PLAN.md`                 | Implement only after user-authored design is frozen; provide read-only CLI + tests.                                       | No formal numeric task file. Must be tracked by this alias if planned.                                           |
| `R3-EARLY-PROD-SCALE-BENCH` | `ROUND3_EARLY_CLOSE_PLAN.md`; `scripts/production_equivalent_smoke.py` | Run or schedule production-equivalent scale benchmark with fixture-scale datasets.                                        | Can be closed here or re-deferred with explicit evidence.                                                        |

**Do not merge with:** `017`-`023` model implementation. Data authorization, DB inspection, and vendor E2E require different acceptance gates and isolation rules.

---

### Batch 2 — Layer 1 base: formal tasks `017` + `018`

**Batch intent:** build the Layer 1 regime/axis foundation and its interpretation snapshots.

| Item ID                      | Source                                                                    | Required outcome / decision                                                                                     | Notes                                                                           |
| ---------------------------- | ------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `017`                        | `ROUND_3_MODELING_LAYERS/017_implement_layer1_axis_loader.md`             | Implement Layer 1 five-axis spec loader and initialize `axis_registry`, `axis_indicator_registry`, and profile. | Must follow `specs/contracts/layer1_axis_contract.yaml` and Layer 1 axis specs. |
| `018`                        | `ROUND_3_MODELING_LAYERS/018_implement_layer1_interpretation_snapshot.md` | Generate `axis_feature_snapshot` and `axis_interpretation_snapshot`.                                            | Must enforce `as_of` / no-future-data behavior.                                 |
| `R3-EARLY-LINEAGE-CONSUMERS` | `ROUND3_EARLY_CLOSE_PLAN.md`                                              | Wire or validate snapshot lineage consumers needed by Layer snapshots.                                          | Keep scoped to snapshot lineage; do not pull in unrelated pipeline repay.       |

**Shared acceptance theme:** Layer 1 specs load, Layer 1 snapshots generate, lineage is traceable, and tests include business semantics rather than only call assertions.

---

### Batch 3 — Layer 2 cross-asset sensor: formal task `019`

**Batch intent:** add the cross-asset sensing layer after Layer 1 outputs are available.

| Item ID | Source                                                               | Required outcome / decision                                                               | Notes                                                       |
| ------- | -------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| `019`   | `ROUND_3_MODELING_LAYERS/019_implement_layer2_cross_asset_sensor.md` | Implement `cross_asset_registry`, observations, daily snapshot, and `double_count_guard`. | Must prove cross-asset semantics and avoid double counting. |

**Optional closeout only if naturally touched:** If Batch 3 exposes a narrow lineage or source-health read need, record it as evidence, but do not add DB migration or CLI work to this batch.

---

### Batch 4 — Layer 3 industry chain: formal tasks `020` + `021`

**Batch intent:** load Layer 3 industry-chain configuration and produce Layer 3 daily snapshots plus Layer5 mapping view.

| Item ID | Source                                                                  | Required outcome / decision                                                             | Notes                                                                                 |
| ------- | ----------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `020`   | `ROUND_3_MODELING_LAYERS/020_implement_layer3_industry_chain_loader.md` | Load chain, anchor, node, edge, and cross-chain edge registries with strict validation. | Must follow `specs/contracts/layer3_loader_contract.yaml` and Layer 3 registry specs. |
| `021`   | `ROUND_3_MODELING_LAYERS/021_implement_layer3_snapshot_builder.md`      | Generate `industry_chain_daily_snapshot` and Layer5 mapping view.                       | Must keep `as_of` and lineage guarantees.                                             |

**Shared acceptance theme:** invalid Layer 3 configs fail loudly; valid configs load deterministically; snapshots and Layer5 mapping are testable.

---

### Batch 5 — Downstream market/security evidence: formal tasks `022` + `023` plus related conflict UX

**Batch intent:** finish market structure and security-level evidence chain after upstream Layer 1-3 foundations exist.

| Item ID        | Source                                                             | Required outcome / decision                                                                                     | Notes                                                                              |
| -------------- | ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `022`          | `ROUND_3_MODELING_LAYERS/022_implement_layer4_market_structure.md` | Implement market registry, calendar, breadth, and market snapshots.                                             | Must follow `specs/contracts/layer4_market_contract.yaml`.                         |
| `023`          | `ROUND_3_MODELING_LAYERS/023_implement_layer5_evidence_chain.md`   | Implement instrument registry, bar, event, financial, valuation, and evidence chain.                            | Must follow `specs/contracts/layer5_evidence_contract.yaml`.                       |
| `R3-PARTIAL-4` | `docs/AUDIT_DEFERRED_REGISTRY.md`                                  | Decide failed reconcile manual-review queue vs instant severe queue behavior and add tests for the chosen path. | Best handled near `023` because it affects evidence-chain/manual-review semantics. |
| `R2-RISK-2`    | `docs/AUDIT_DEFERRED_REGISTRY.md`                                  | Reduce adapter dependency on storage concrete classes via port injection if evidence path needs it.             | Keep minimal: one adapter port injection or documented deferral.                   |

**Shared acceptance theme:** Layer 4 market snapshots and Layer 5 evidence chains are traceable, `as_of` safe, and no-action semantics remain intact.

---

### Batch 6 — Round3 repay and closeout: pipeline, migration, CLI, packaging, hygiene

**Batch intent:** close non-modeling Round3 repay items before Round4, or re-defer them with explicit IDs, owners, and tests.

| Item ID        | Source                                                                 | Required outcome / decision                                                                                  | Notes                               |
| -------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ----------------------------------- |
| `R2.6-IMPL-6`  | `docs/AUDIT_DEFERRED_REGISTRY.md`                                      | Implement or explicitly defer `qmd data` production CLI with dry-run, route-preview, error_code/docs_anchor. | Related to ops/packaging.           |
| `R3-PARTIAL-1` | `docs/AUDIT_DEFERRED_REGISTRY.md`                                      | Backfill either gains post-shard validate+write path + pytest, or ADR documents retained scope.              | Pipeline repay.                     |
| `R3-PARTIAL-3` | `docs/AUDIT_DEFERRED_REGISTRY.md`                                      | Add reconcile re-fetch / compare closure pytest.                                                             | Alias target for `D2-P2-2`.         |
| `R3-PARTIAL-5` | `docs/AUDIT_DEFERRED_REGISTRY.md`                                      | Close COMPLETED-vs-write crash window by same-transaction change or recovery runbook.                        | Optional if explicitly re-deferred. |
| `D2-P1-1`      | `docs/AUDIT_DEFERRED_REGISTRY.md`                                      | Implement `run_revision_audit` and `run_data_quality` runners or re-defer with tests.                        | Orchestrator job matrix.            |
| `D2-P1-3`      | `docs/AUDIT_DEFERRED_REGISTRY.md`                                      | Implement `python -m quant_monitor.sync` or successor console script smoke.                                  | Packaging/CLI.                      |
| `D2-P2-1`      | `docs/AUDIT_DEFERRED_REGISTRY.md`                                      | Add `source_health_snapshot` table and snapshot pytest.                                                      | Migration + ops.                    |
| `D2-P2-2`      | `docs/AUDIT_DEFERRED_REGISTRY.md`                                      | Alias only: close through `R3-PARTIAL-3`.                                                                    | Do not duplicate work.              |
| `R2-GAP-1`     | `docs/AUDIT_DEFERRED_REGISTRY.md`                                      | Add `init_db --sync-registry` flag or documented CI one-liner.                                               | Initialization hygiene.             |
| `D2-P3-1`      | `docs/AUDIT_DEFERRED_REGISTRY.md`                                      | Add `registry_generation` / `removed_from_yaml_at` columns and sync pytest, or re-defer.                     | Registry lifecycle.                 |
| `D7-P1-1`      | `docs/AUDIT_DEFERRED_REGISTRY.md`                                      | Extract orchestrator full handler registry and add handler registry pytest.                                  | Also closes `R2-RISK-1` if done.    |
| `D7-P2-2`      | `docs/AUDIT_DEFERRED_REGISTRY.md`                                      | Remove `sys.path.insert` script smell via editable install / console scripts.                                | Packaging.                          |
| `D3-P1-2`      | `docs/AUDIT_DEFERRED_REGISTRY.md`                                      | Resolve C901 on `_validate_domain_roles` / `_execute_write` through refactor or justified ADR/noqa.          | Hygiene.                            |
| `A9-P1-01`     | `docs/AUDIT_DEFERRED_REGISTRY.md`; `docs/schema/MIGRATION_008_PLAN.md` | Move agreed `fetch_log` / `source_registry` DB CHECK constraints into migration 008 and tests.               | Migration 008.                      |
| `A9-P2-01`     | `docs/AUDIT_DEFERRED_REGISTRY.md`; `docs/schema/MIGRATION_008_PLAN.md` | Add `manual_review_queue` CHECK in migration 008.                                                            | Migration 008.                      |
| `A9-P2-02`     | `docs/AUDIT_DEFERRED_REGISTRY.md`; `docs/schema/MIGRATION_008_PLAN.md` | Add `source_conflict.reconcile_status` CHECK in migration 008.                                               | Migration 008.                      |
| `A9-P3-01`     | `docs/AUDIT_DEFERRED_REGISTRY.md`                                      | Remove migration rebuild `INSERT SELECT *` risk through explicit column list and review sign-off.            | Migration safety.                   |
| `R2-RISK-1`    | `docs/AUDIT_DEFERRED_REGISTRY.md`                                      | Alias to orchestrator aggregation coupling; close through `D7-P1-1`.                                         | Do not duplicate work.              |
| `R2-RISK-3`    | `docs/AUDIT_DEFERRED_REGISTRY.md`                                      | Add write_contract matrix doc or re-defer to Round5.                                                         | Contract coverage.                  |
| `R2-RISK-4`    | `docs/AUDIT_DEFERRED_REGISTRY.md`                                      | Document app-layer CHECK by design in `MIGRATION_COVERAGE.md`; migration 008 only for agreed subset.         | Design/migration boundary.          |
| `R2-HYG-4`     | `docs/AUDIT_DEFERRED_REGISTRY.md`                                      | Refactor `test_duckdb_connection` inter-call smell or close as wont-fix ADR.                                 | Test hygiene.                       |
| `R2-HYG-5`     | `docs/AUDIT_DEFERRED_REGISTRY.md`                                      | Expose adapter metadata fields and add skeleton metadata pytest, or re-defer.                                | Adapter contract hygiene.           |

**Final closeout rule:** before entering Round4 planning, every Batch 6 item must be either `RESOLVED` with implementation/test evidence or explicitly re-deferred in `docs/AUDIT_DEFERRED_REGISTRY.md` and `docs/UNRESOLVED_ISSUES_REGISTRY.md`.

## 4. Recommended execution order

1. **Batch 1** — entry, real-data/DB proof, inspect CLI prerequisites, and ops evidence.
2. **Batch 2** — Layer 1 `017` + `018`.
3. **Batch 3** — Layer 2 `019`.
4. **Batch 4** — Layer 3 `020` + `021`.
5. **Batch 5** — Layer 4 `022` + Layer 5 `023` plus evidence-chain conflict UX.
6. **Batch 6** — pipeline/migration/CLI/packaging/hygiene closeout.

## 5. Trellis batching constraints

Each batch should become its own Trellis complex task unless a later human maintainer intentionally splits it further.

For every batch Trellis plan:

1. `MASTER.plan.md` must include a child deliverable table mapping each item ID above to an acceptance criterion.
2. `implement.jsonl` must include this file, `MIGRATION_MAP.md`, `TASK_INPUT_CONTEXT_INDEX.md`, the relevant numbered task files, and the relevant registry files.
3. Execute must not use docs/specs as implementation paths.
4. Audit must verify traceability from item ID → source document → code/test evidence → registry update.
5. Any item not closed must remain visible as `DEFERRED` with a concrete phase, owner/task hook, and closure test.
