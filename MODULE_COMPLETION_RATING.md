# Module Completion Rating

> **Purpose:** operator-facing status snapshot for planning and audit only.  
> **Not a design authority:** design documents, architecture documents, contracts, and rule definitions describe the desired complete product shape. They should not be downgraded with implementation-status labels.  
> **Planning authority:** execution plans and task cards must use this file to avoid claiming a module is complete when only scaffold, staged fixture, or sandbox evidence exists.

---

## 1. Rating scale

| Level                               | Meaning                                                                                                                                                           | Can be called complete?         |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------- |
| `R0_NOT_STARTED`                    | No meaningful runtime implementation beyond placeholder files or planning docs.                                                                                   | No                              |
| `R1_SCAFFOLD`                       | API/module skeleton, contracts, or placeholders exist but no useful executable vertical slice.                                                                    | No                              |
| `R2_MINIMAL_VERTICAL_SLICE`         | A bounded end-to-end slice works with tests, real module boundaries, and no fake success claims. This is the minimum acceptable first implementation batch.       | No, only minimal slice complete |
| `R3_STAGED_FIXTURE_CLOSED`          | The module runs against staged fixtures with validation, lineage/evidence, and negative tests.                                                                    | No, staged implementation only  |
| `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` | The module runs against bounded sandbox real-data/evidence or sandbox clean-write rehearsal with explicit caps.                                                   | No, sandbox only                |
| `R5_LIMITED_PRODUCTION_ENTRY`       | Explicitly approved, capped production entry exists with before/after proof, rollback, and regression tests.                                                      | Production-limited only         |
| `R6_FULL_PRODUCTION_STABLE`         | Stable production path, complete target-domain behavior, operational runbooks, monitoring, regression suite, and no open blocker for the module's promised scope. | Yes                             |

---

## 2. Anti-overengineering completion rule

For every module or major feature after this file lands:

1. The **first implementation batch** must deliver at least `R2_MINIMAL_VERTICAL_SLICE`; a pure shell, placeholder, single-field guard, or isolated registry note is not enough.
2. The module must reach `R6_FULL_PRODUCTION_STABLE` in **no more than three implementation batches** for the declared scope.
3. Existing partially implemented modules must use their **next implementation batch** to close the main promised scope directly, unless a written ADR proves that the promise was too broad and narrows the module boundary.
4. Future task cards must distinguish:
   - first vertical slice;
   - production-complete closure;
   - hardening/regression closure.
5. Repeated micro-slices such as “add one metric”, “add one flag”, “add one registry note”, or “add one narrow test” without moving the module to the next rating level are treated as overengineering unless they are part of the same batch PR.

---

## 3. Current module rating snapshot

| Module                                                       | Current rating              | Evidence                                                                                       | Required next movement                                                                                                        |
| ------------------------------------------------------------ | --------------------------- | ---------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Project scaffold/config/test harness                         | `R3_STAGED_FIXTURE_CLOSED`  | pytest catalog, config templates, scaffold checks                                              | Keep stable; no new completion batch unless release packaging requires it.                                                    |
| DuckDB schema/migration foundation                           | `R3_STAGED_FIXTURE_CLOSED`  | migration tests, schema contract tests, migration coverage docs                                | Close residual migration hygiene in next release/security batch, not endless slices.                                          |
| WriteManager + DbValidationGate                              | `R3_STAGED_FIXTURE_CLOSED`  | `backend/app/db/write_manager.py`, `backend/app/db/validation_gate.py`, write/validation tests | R3G must move clean-write use from infrastructure-only to sandbox/limited production path.                                    |
| RawStore/FileRegistry/fetch_log                              | `R3_STAGED_FIXTURE_CLOSED`  | raw evidence/file registry/fetch log paths and tests                                           | **R3H must bind every in-scope source adapter to these primitives, not only one sample path.**                                |
| DataSourceService / SourceRoutePlanner / capability registry | `R3_STAGED_FIXTURE_CLOSED`  | service facade, route planner, source registry/capability tests                                | **R3H must close every target source to `READY_WITH_EVIDENCE` or `ADR_DISABLED_OUT_OF_SCOPE`; another facade is not enough.** |
| Vendor adapters / provider fetch ports                       | `R1_SCAFFOLD`               | adapter skeletons and disabled/probe ports                                                     | **R3H must move all target sources to bounded QMD-owned provider ports or explicit ADR-disabled status before Round4.**       |
| `qmd data` CLI                                               | `R2_MINIMAL_VERTICAL_SLICE` | route-preview/sync-plan/init-basic exist; health is placeholder                                | R3F-R must complete real read-only `qmd data health`; no extra placeholder batch.                                             |
| Data health engine                                           | `R2_MINIMAL_VERTICAL_SLICE` | `backend/app/ops/data_health.py` read-only checks                                              | R3F-R must complete EasyXT-style profile refactor + CLI in one vertical slice.                                                |
| Layer1 axes                                                  | `R3_STAGED_FIXTURE_CLOSED`  | YAML loader, spec validation, ingestion/evidence paths                                         | **R3H must bind declared Layer1 production-entry axes to real official/macro sources or ADR-narrow scope.**                   |
| Layer2 sensors                                               | `R3_STAGED_FIXTURE_CLOSED`  | staged fixture registry, snapshots, WriteManager-gated writes                                  | **R3H must move declared Layer2 sensors from staged fixture to real market/validation sources or ADR-narrow scope.**          |
| Layer3 chains                                                | `R3_STAGED_FIXTURE_CLOSED`  | staged bundle loader/snapshot builder                                                          | **R3H must complete real CN/industry-chain source/evidence paths for declared scope or ADR-narrow chain scope.**              |
| Layer4 markets                                               | `R3_STAGED_FIXTURE_CLOSED`  | CN_A staged market structure fixture                                                           | **R3H must complete real market-structure source/evidence paths for declared scope or ADR-narrow Layer4 scope.**              |
| Layer5 evidence                                              | `R2_MINIMAL_VERTICAL_SLICE` | foundation validator and minimal staged evidence-chain pieces                                  | **R3H must close real source_fetch_id/content_hash/schema_hash evidence-chain binding for declared production-entry scope.**  |
| Sandbox clean write / limited production entry               | `R1_SCAFFOLD`               | Round 3G planning and contract only                                                            | R3G-01 must deliver sandbox rehearsal; R3G-03 must reach limited production entry if approved.                                |
| API backend                                                  | `R1_SCAFFOLD`               | FastAPI placeholder shell and security contract                                                | Round4 first API batch must deliver a real bounded HTTP vertical slice.                                                       |
| Frontend dashboard                                           | `R0_NOT_STARTED`            | planning/contracts only                                                                        | Round4 frontend work must deliver usable route/page shell + real API contract binding in first batch.                         |
| Agent layer                                                  | `R0_NOT_STARTED`            | contract/planning only                                                                         | Round4 Agent work must deliver read-only bounded artifact flow, no action semantics.                                          |
| Notifications/reports                                        | `R0_NOT_STARTED`            | contract/planning only                                                                         | Round4 first report/notification batch must deliver a bounded report artifact, not only contract.                             |
| Backtest/review                                              | `R0_NOT_STARTED`            | Round4 planning only                                                                           | Round4 backtest/review must adapt JQ2PTrade/EasyXT and deliver a working read-only review slice in first batch.               |
| Release/security packaging                                   | `R1_SCAFFOLD`               | Round5 planning only                                                                           | Round5 must close CI/release gates, not implement delayed product features.                                                   |

---

## 4. Planning consequences

- Design/contract files remain complete-product targets.
- Task cards must state which rating movement they deliver.
- A batch that does not move the module at least one rating level must explain why it is a hardening/regression batch, not a feature batch.
- No module may require more than three implementation batches to reach the complete stable shape for the declared scope.
