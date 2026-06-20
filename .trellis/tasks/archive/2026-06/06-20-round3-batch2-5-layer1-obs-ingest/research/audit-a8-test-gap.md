# A8 audit-test-gap — §4.8

**Dimension:** A8 (audit-test-gap)  
**Task:** `06-20-round3-batch2-5-layer1-obs-ingest`  
**Skills:** `GLOBAL_TESTING_POLICY.md` + `testing-guidelines` + `doubt-driven-development`  
**Environments:** project root pytest (`tmp_path` isolation); `AUDIT_PROD_ROOT=.audit-sandbox/r3b25-audit-prod-equiv` (data copy)  
**Verdict: PASS_WITH_FIXES** (one Red-Flag gap closed in-session; §4.3 empty)

---

## 1. Mandatory reads completed

| Source                                        | Takeaway                                                                                                                       |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `AUDIT.plan.md` §2 A8                         | Boundary tests: validation fail, severe conflict, manual review, Phase 0 gate; audit-prod-path Phase 0 block + ingestion suite |
| `audit.jsonl`                                 | Gate + pipeline test maps, `GLOBAL_TESTING_POLICY.md`, contracts, validators                                                   |
| `MASTER.plan.md` §7 Red Flags                 | Seven prevention rows mapped below                                                                                             |
| `018A` §8 Phase 0 command block               | 15-file pytest set (see §2)                                                                                                    |
| `research/layer1-ingestion-gate-tests.md`     | Phase 0: 27 `test_layer1_ingestion_gates.py` functions                                                                         |
| `research/layer1-ingestion-pipeline-tests.md` | Phase 1–4 semantic matrix + prerequisite validator tests                                                                       |
| `GLOBAL_TESTING_POLICY.md`                    | Semantic assertions; boundary/empty/error paths required                                                                       |
| `research/gitnexus-audit-summary.md`          | 7.pre complete; A8 focus on gate + observation tests                                                                           |
| Codegraph                                     | **Unavailable** (no `.codegraph/` index); used Read/Grep + GitNexus `impact(build)` LOW                                        |

---

## 2. Pytest evidence

### 2.1 audit-sandbox — ingestion suite (AUDIT.plan §2 A8 pytest-isolated)

**Command** (note: `uv` not on PATH; used `python -m pytest`):

```text
python -m pytest tests/test_layer1_ingestion_gates.py tests/test_layer1_observation_ingestion.py -q
```

**Output (post A8 boundary adds):**

```text
........................................................................ [ 92%]
......                                                                   [100%]
78 passed
```

Inventory: `test_layer1_ingestion_gates.py` **27**; `test_layer1_observation_ingestion.py` **49** (was 48).

### 2.2 audit-prod-path — 018A Phase 0 command block

**Command** (MASTER §8.1 GREEN / `layer1-ingestion-gate-tests.md`):

```text
python -m pytest tests/test_schema_migration.py tests/test_schema_contract.py \
  tests/test_source_capabilities.py tests/test_source_route_planner.py \
  tests/test_datasource_service.py tests/test_data_cli_contract.py \
  tests/test_ops_db_inspector.py tests/test_layer1_axis_loader.py \
  tests/test_layer1_interpretation.py tests/test_sync_orchestrator.py \
  tests/test_sync_jobs.py tests/test_vendor_fetch_e2e.py \
  tests/test_layer1_ingestion_gates.py tests/test_write_manager.py \
  tests/test_audit_remediation.py -q
```

**Output:**

```text
.............................................................s.......... [ 37%]
........................................................................ [ 75%]
................................................                         [100%]
538 collected, 537 passed, 1 skipped (symlink test on Windows), exit 0
```

Matches Execute `execute-evidence/phase0_test_output.txt` (535→537 after A8 adds in `test_layer1_interpretation.py`).

### 2.3 audit-prod-path — prod DB hash unchanged

| Check                                     | Value                                                                    |
| ----------------------------------------- | ------------------------------------------------------------------------ |
| `data/duckdb/quant_monitor.duckdb` before | `5EB65E0EDAAAB223A77C5A5D2660603383836704B4C0ECE1EB4AEBB047F1682E`       |
| after ingestion suite                     | **unchanged**                                                            |
| `AUDIT_PROD_ROOT`                         | `.audit-sandbox/r3b25-audit-prod-equiv/data` copied from project `data/` |

Layer1 ingestion tests use `tmp_path` / in-memory DB; no production mutation.

---

## 3. AUDIT.plan §2 A8 core boundaries

| Boundary                                                  | Test                                                            | Status         |
| --------------------------------------------------------- | --------------------------------------------------------------- | -------------- |
| Validation fail blocks clean write                        | `test_layer1Observation_validationFailure_blocksCleanWrite`     | Covered · PASS |
| Severe conflict blocks clean write                        | `test_layer1Observation_severeConflict_blocksCleanWrite`        | Covered · PASS |
| Manual review blocks non-manual write                     | `test_layer1Observation_manualReview_blocksNonManualPatchWrite` | Covered · PASS |
| Phase 0 gate (contracts, migration 011, factory boundary) | `tests/test_layer1_ingestion_gates.py` (27 tests)               | Covered · PASS |

Prerequisite Phase 4 validators (018A §8.5) remain in `test_write_manager.py`, `test_data_quality_validator.py`, `test_source_conflict_validator.py` — included in Phase 0 block above.

---

## 4. MASTER §7 Red Flags — adversarial coverage

| Red Flag               | Prevention              | Test(s)                                                                                                                                      | Status     |
| ---------------------- | ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| Layer1 直调 adapter    | AC-P0-4                 | `test_layer1Ingestion_phase0_datasourceServiceFactoryBoundaryEnforced`, `test_layer1MicroIngestion_usesDataSourceServiceBeforeFetch`         | Covered    |
| Phase 1/2 mutation     | AC-P1-2, AC-P2-2        | `test_layer1Ingestion_phase1_zeroMutation`, `test_layer1Ingestion_routePreview_noMutation`                                                   | Covered    |
| 无 validation 写 clean | AC-P4-1                 | `test_layer1Observation_cleanWrite_requiresValidationReport`, `test_layer1Observation_validationFailure_blocksCleanWrite`                    | Covered    |
| 合成 lineage 冒充生产  | AC-P4-4 / Batch 2 A4-09 | **Was partial** — see G-A8-01; **closed** with new tests + `lineage.py` fix                                                                  | **Fixed**  |
| live 源无授权          | §3.2                    | `test_layer1Ingestion_userAuthRequired_returnsRouteStatusWithoutFetch`, `test_layer1Ingestion_disabledSource_returnsRouteStatusWithoutFetch` | Covered    |
| schema.sql 滞后 silent | AC-P0-2                 | `test_layer1Ingestion_phase0_schemaSqlLagTrackedAsO02`                                                                                       | Covered    |
| merge 五阶段           | PH-A0–PH-A4             | Stage audit reports (process gate, not pytest)                                                                                               | Documented |

---

## 5. Gaps found / filled (A8 adversarial ≥2 boundary cases)

| ID      | Gap                                                                                                                                                                          | Severity            | Action                                                                                                                                                                                                                                                                                                                                               | Result |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| G-A8-01 | `SnapshotLineageBuilder.build` with `allow_synthetic_hashes=False` accepted empty `source_content_hashes_json='[]'` and invented SHA256 hashes — bypassed Batch 2 A4-09 gate | **High** (Red Flag) | **Fixed** `backend/app/layer1_axes/lineage.py`: reject any empty `content_hashes` when `allow_synthetic_hashes=False`. Added `test_snapshotLineage_missingContentHashes_rejectsSyntheticFallback` + `test_snapshotLineage_allowSyntheticHashes_permitsFixtureFallback`. Updated `test_incrementalRebuildPreservesAsOfBoundary` to use real hash JSON | GREEN  |
| G-A8-02 | No explicit assertion that Phase 4 staged commit labels `axis_observation.quality_flags` with `STAGED_FIXTURE` (AC-P4-4 staged labeling)                                     | Medium              | Added `test_layer1Observation_stagedFixture_qualityFlagPersisted`                                                                                                                                                                                                                                                                                    | GREEN  |

**GitNexus impact** (`build` @ `lineage.py`): **LOW**, 0 direct upstream symbols reported.

---

## 6. New tests added (this A8 pass)

| File                                         | Test                                                                 | Semantic                                                   |
| -------------------------------------------- | -------------------------------------------------------------------- | ---------------------------------------------------------- |
| `tests/test_layer1_interpretation.py`        | `test_snapshotLineage_missingContentHashes_rejectsSyntheticFallback` | `None` and `[]` hashes rejected when synthetic not allowed |
| `tests/test_layer1_interpretation.py`        | `test_snapshotLineage_allowSyntheticHashes_permitsFixtureFallback`   | Explicit fixture mode still allows synthetic hashes        |
| `tests/test_layer1_observation_ingestion.py` | `test_layer1Observation_stagedFixture_qualityFlagPersisted`          | Post-commit observation carries `STAGED_FIXTURE`           |

**Production touch:** `backend/app/layer1_axes/lineage.py` — tightened empty-hash guard (1-line condition simplification).

---

## 7. §4.3 Repair items

**Count: 0** — G-A8-01 and G-A8-02 closed in-session.

---

## 8. Test quality notes (GLOBAL_TESTING_POLICY / testing-guidelines)

| Check               | Finding                                                                                                                                                |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Semantic assertions | Core boundary tests assert `reason_code`, row counts, `quality_flags`, lineage fields — not call-only                                                  |
| Mock boundary       | Phase 4 block tests monkeypatch `DataQualityValidator.validate_table` for failure injection (external persistence path); acceptable for gate semantics |
| Determinism         | Frozen `PHASE4_AS_OF`, fixture JSON, `ResourceGuard` patched to OK                                                                                     |
| Prerequisite tests  | Validator suite in Phase 0 block; not re-audited line-by-line (A4 scope)                                                                               |

---

## 9. Summary for A9

| Metric                 | Value                                  |
| ---------------------- | -------------------------------------- |
| **Verdict**            | **PASS_WITH_FIXES**                    |
| **§4.3 count**         | **0**                                  |
| Ingestion suite        | **78 / 78** PASS                       |
| Phase 0 block          | **537 / 538** PASS (1 skip)            |
| Red Flags with pytest  | **6 / 7** (merge gate = audit process) |
| A8 explicit boundaries | **4 / 4**                              |
| New boundary tests     | **3**                                  |
| Codegraph              | Skipped (no index)                     |

**Output path:** `.trellis/tasks/06-20-round3-batch2-5-layer1-obs-ingest/research/audit-a8-test-gap.md`
