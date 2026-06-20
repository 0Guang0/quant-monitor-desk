# A4 audit-quality — Round 3 Batch 2.5 Layer 1 Observation Ingestion

> Dimension: pipeline test semantics, WriteManager + DbValidationGate integration, error/boundary coverage, GLOBAL_TESTING_POLICY compliance  
> Scope: `tests/test_layer1_ingestion_gates.py`, `tests/test_layer1_observation_ingestion.py`, prerequisite `tests/test_db_validation_gate.py` + `tests/test_data_quality_validator.py`, `backend/app/layer1_axes/ingestion.py`, `observation_writer.py`, `backend/app/db/validation_gate.py`  
> Skills: code-review-and-quality + doubt-driven-development  
> Sources: `AUDIT.plan.md` §4.4, `MASTER.plan.md` §0.6/§2, `018A`, `ROUND3_BATCH_IMPLEMENTATION_MAP.md` Batch 2.5, `MIGRATION_MAP.md`, `docs/modules/write_manager.md`, `GLOBAL_TESTING_POLICY.md`, `research/gitnexus-audit-summary.md`  
> Adversarial trigger: semantic tests not call-only; find ≥1 missing error handling or boundary gap

---

## Verdict: **PASS**

All P2 pipeline/gate gaps closed in audit repair (2026-06-20).

---

## Axis scores (1–5)

| Axis         | Score | Rationale                                                                                                                                  |
| ------------ | ----- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Correctness  | 4     | Happy path + validation/severe/manual-review/duplicate/no-future/guard blocks covered; fetch-failure commit and WARNING-success paths thin |
| Readability  | 4     | Consistent `functionName_condition_expectedBehavior` naming; phase-grouped tests map to 018A §8 evidence                                   |
| Architecture | 4     | Tests enforce staging→validation→WriteManager chain; Phase 0 static gates mirror contracts without duplicating Batch C unit depth          |
| Security     | 4     | No silent fallback, adapter-factory ban, read-only Phase 1/2 mutation proofs; A3 owns full static scan                                     |
| Performance  | 4     | Eco micro-window; ResourceGuard PAUSE tested at preview/micro-fetch/commit; no unbounded fixture scans in tests                            |

---

## Findings

| ID    | Priority | Location                                                                | Finding                                                                                                                                                                                                                                                                                                                                                                                                                   | Recommended fix                                                                                                                                                                                                                |
| ----- | -------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| A4-01 | **P2**   | `ingestion.py` `commit_clean_observation_and_snapshots`; pipeline tests | **Fetch FAILURE during Phase 4 commit untested.** Mapper raises `ObservationMappingError` when `fetch_result.status != "SUCCESS"` (`observation_mapper.py` L81–84), surfaced as `IngestionCommitBlockedError(reason_code="OBSERVATION_MAPPING")`. No pipeline test simulates failed fetch on commit; only success-path mapping is exercised.                                                                              | Add `test_layer1Observation_fetchFailure_blocksCleanWrite`: monkeypatch/stub port returning `status="FAILED"`; assert `reason_code=="OBSERVATION_MAPPING"` and `axis_observation` count 0.                                     |
| A4-02 | **P2**   | `ingestion.py` `_validation_source_requires_conflict`; frozen indicator | **SourceConflictValidator skipped for `ENV-E1-DGS10`.** Spec has `validation_source: none_optional` → conflict validator not invoked on commit. `test_layer1Observation_severeConflict_blocksCleanWrite` injects `source_conflict` inside a mocked `validate_table`, exercising **DbValidationGate** at write time only—not the conflict-validator staging path documented in MASTER §3.4.                                | When a validation-source indicator is added to allowlist, add integration test through real `SourceConflictValidator.validate_table`. For frozen indicator, document in test comment that severe block is gate-only by design. |
| A4-03 | **P2**   | `test_layer1_ingestion_gates.py` L288–300, L318–320, L333–345           | **Phase 0 call-only / existence tests** violate `GLOBAL_TESTING_POLICY.md` §2 (no semantic business assertion): `test_layer1Ingestion_phase0_validationGateModule_exposesDbValidationGate`, `test_layer1Ingestion_phase0_resourceGuard_exposesCheckBeforeFetch`, `test_layer1Ingestion_phase0_fetchTraceFieldsDocumented`, `test_layer1Ingestion_phase0_axisObservationWritePath_implementedInPhase4` (source-text grep). | Replace with behavioral smoke: e.g. `DbValidationGate` rejects missing report on tmp DB; `ResourceGuard.check` returns Decision enum on empty DB; commit function importable and callable in sandbox.                          |
| A4-04 | **P2**   | `test_layer1Observation_cleanWrite_requiresValidationReport` L966–1002  | **Weak negative post-condition.** Asserts `WriteResult.status == "FAILED"` only; does not assert `axis_observation` / `write_audit_log` remain empty (GLOBAL §2 persistence assertion).                                                                                                                                                                                                                                   | Add row-count assertions: `axis_observation == 0`, no SUCCESS audit row for target job.                                                                                                                                        |
| A4-05 | **P2**   | Phase 4 pipeline tests; `DbValidationGate` WARNING policy               | **WARNING + can_write_clean=true success path not covered at pipeline level.** `test_db_validation_gate.py::test_warningReport_canWriteTrue_noReview_allows` covers gate unit behavior; no `commit_clean_observation_and_snapshots` test with WARNING report that still writes clean rows.                                                                                                                                | Add pipeline test with mocked validator returning WARNING + `can_write_clean=True`; assert observation + audit SUCCESS.                                                                                                        |
| A4-06 | **P3**   | `test_layer1Ingestion_phase1_captureDoesNotCallWriterOrMigrations`      | **Implementation-coupled safety test** (patches `ConnectionManager.writer` / `apply_migrations`). Acceptable as invariant guard but borders GLOBAL §3 “do not assert internal call order.” Semantic tail assertion (`read_only_open`) is thin.                                                                                                                                                                            | Optional: replace with read-only connection fingerprint test only (no writer patch).                                                                                                                                           |
| A4-07 | **INFO** | Pipeline Phase 1–4 tests                                                | **Strong semantic coverage** where it matters: hash/row-count mutation proofs, route_status/skip_reason, fetch-before-route ordering, lineage JSON non-empty, post-commit table deltas, duplicate commit guard.                                                                                                                                                                                                           | Keep as regression anchors.                                                                                                                                                                                                    |
| A4-08 | **INFO** | Prerequisite suite                                                      | **`test_db_validation_gate.py` + `test_data_quality_validator.py` + `test_write_manager.py`** green (54 tests, A4 re-run). Layer 1 pipeline does not regress Batch C gate semantics.                                                                                                                                                                                                                                      | No action.                                                                                                                                                                                                                     |

### Adversarial reconciliation (doubt-driven)

| Claim                                           | Attack                                                             | Result               |
| ----------------------------------------------- | ------------------------------------------------------------------ | -------------------- |
| “Pipeline tests are semantic, not call-only”    | Grep: no `assert_called` in `test_layer1_observation_ingestion.py` | **Holds**            |
| “Every Phase 4 block path has a test”           | Fetch FAILURE on commit; WARNING success                           | **Gap A4-01, A4-05** |
| “Severe conflict blocked on real ingest path”   | Frozen indicator skips SourceConflictValidator; test mocks DQ path | **Partial A4-02**    |
| “WriteManager + DbValidationGate on clean path” | `test_layer1Observation_cleanWrite_usesWriteManager` + audit rows  | **Holds**            |
| “Phase 1/2 zero mutation”                       | Hash + row counts + data-root fingerprint                          | **Holds**            |
| “Prerequisite validator tests still green”      | pytest 108/108 (A4 audit run)                                      | **Holds**            |

Cross-model skipped: subagent context (degraded self-questioning per doubt-driven §Loading Constraints).

---

## Ingestion / validator chain (read-only + GitNexus)

```text
indicator allowlist → preview_route / micro_fetch_staging
  → ResourceGuard.check
  → DataSourceService.fetch → fetch_log + file_registry + raw
  → map_micro_fetch_to_observation_row (staging shape)
  → DataQualityValidator.validate_table → validation_report
  → [SourceConflictValidator if validation_source requires]
  → Layer1ObservationWriter → WriteManager + DbValidationGate → axis_observation
  → AxisFeatureEngine / AxisInterpretationEngine
  → Layer1SnapshotWriter (features, interpretation, lineage) + write_audit_log
```

GitNexus `query("Layer 1 observation ingestion clean write")` surfaces `DbValidationGate`, `DataQualityValidator.validate_rows`, and Batch C gate tests; symbol `commit_clean_observation_and_snapshots` not indexed (stale index — read source directly). Codegraph unavailable (no `.codegraph/` in session).

---

## What's done well

- Phase 1–3 tests assert **persistence and invariants** (file hash, row counts, `inspect.mode == read_only`, route evidence before fetch_log) rather than mock call counts.
- Phase 4 negative matrix covers validation FAILED, severe conflict (gate), manual review, no-future-data, forbidden/blindspot, ResourceGuard PAUSE, duplicate commit — mapped to AC-P4-1..3 in `audit-ph-a4-clean-write.md`.
- `test_layer1MicroIngestion_usesDataSourceServiceBeforeFetch` enforces factory boundary with `create_adapter` monkeypatch failure — aligns with MASTER §3.3 and module_boundary_matrix.
- Task evidence tests (`capture_task_phase*_evidence`) verify artifact filenames and sandbox isolation strategies (`fresh_phase3_sandbox`, phase1 baseline reuse).
- `test_layer1Observation_mappingUsesRawFetchPayload` asserts **business values** (`raw_value`, `source_used`) from raw JSON, not fixture constants alone.

---

## Verification story

| Check                         | Result                                                                                                                                                                                                                                |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Tests reviewed                | **Yes** — 27 gate + 48 pipeline; spot-checked Phase 0–4 tables in `layer1-ingestion-*-tests.md`                                                                                                                                       |
| Prerequisite validators green | **Yes** — `.venv\Scripts\python.exe -m pytest tests/test_db_validation_gate.py tests/test_data_quality_validator.py tests/test_layer1_ingestion_gates.py tests/test_layer1_observation_ingestion.py -q` → **108 passed** (2026-06-20) |
| Execute evidence cross-check  | **Yes** — `final_pytest_output.txt`, `8.5-green.txt` (Phase 4 Observation subset green)                                                                                                                                               |
| write_manager.md alignment    | **Yes** — clean write via WriteManager + validation_report_id; gate rejects missing/failed reports (`validation_gate.py`, observation_writer.py)                                                                                      |
| Codegraph                     | **Skipped** — project not indexed this session                                                                                                                                                                                        |
| GitNexus                      | **Partial** — query OK; `context(commit_clean_observation_and_snapshots)` symbol missing (index lag)                                                                                                                                  |

---

## §4.4 Repair / defer items (for A8 or narrow PR)

| ID    | Priority | Action                                                | Owner                                                                            |
| ----- | -------- | ----------------------------------------------------- | -------------------------------------------------------------------------------- |
| A4-01 | P2       | Fetch-failure commit pipeline test                    | **CLOSED** `test_layer1Observation_fetchFailure_blocksCleanWrite`                |
| A4-02 | P2       | Conflict-validator path for none_optional             | **CLOSED** `test_layer1Observation_noneOptionalIndicator_skipsConflictValidator` |
| A4-03 | P2       | Replace Phase 0 existence-only gate tests             | **CLOSED** behavioral gates in `test_layer1_ingestion_gates.py`                  |
| A4-04 | P2       | Strengthen validation-report negative post-conditions | **CLOSED** row-count asserts in `cleanWrite_requiresValidationReport`            |
| A4-05 | P2       | WARNING + can_write_clean pipeline success test       | **CLOSED** `test_layer1Observation_warningValidation_allowsCleanWrite`           |
| A4-06 | P3       | Phase 1 writer/migration patches                      | **CLOSED** `test_layer1Ingestion_phase1_captureUsesReadOnlyInspect`              |

**P0: 0 · P1: 0 · P2: 0 · P3: 0 · §4.3: 0**

---

## Sign-off

| Role     | Verdict  | Date       |
| -------- | -------- | ---------- |
| Audit A4 | **PASS** | 2026-06-20 |
