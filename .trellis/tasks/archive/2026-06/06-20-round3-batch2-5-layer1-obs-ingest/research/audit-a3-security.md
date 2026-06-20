# Audit A3 — Security & Hardening (Dimension)

> 2026-06-20 · audit-security (A3) · static/read-only local  
> Skills: security-and-hardening + doubt-driven-development (per AUDIT.plan §1.2)  
> Inputs: AUDIT.plan §2 A3, audit.jsonl, MASTER §0.6, `gitnexus-audit-summary.md`, module/write/datasource contracts

## Verdict

**PASS** — No P0 or P1 security defects. Layer 1 ingestion respects adapter-factory ban, phase mutation gates, and `DbValidationGate` on all clean-write paths. Three threat-class scans are clean or acceptably bounded.

---

## Scope

| Item         | Value                                                                                   |
| ------------ | --------------------------------------------------------------------------------------- |
| Task         | `06-20-round3-batch2-5-layer1-obs-ingest` (`R3-B2.5-L1-OBS-INGEST`)                     |
| Code surface | `backend/app/layer1_axes/` (+ Phase 4 adjacency: `file_registry.py`, `data_quality.py`) |
| Audit mode   | Static analysis + read-only evidence cross-check (no sandbox writes)                    |
| Batch intent | Staged/fixture Layer 1 `axis_observation` bridge; live FRED deferred (`B2.5-O-05`)      |

---

## A3 verification matrix (AUDIT.plan §2.2)

| #     | Check                                     | Method                                                        | Result             | Evidence                                                                                                                                    |
| ----- | ----------------------------------------- | ------------------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| A3-01 | `layer1_axes` has no `create_adapter`     | `rg create_adapter backend/app/layer1_axes`                   | **PASS**           | 0 matches; `test_layer1_axes_doesNotImportCreateAdapter`                                                                                    |
| A3-02 | Forbidden packages boundary               | `module_boundary_contract.yaml` + `test_module_boundaries.py` | **PASS**           | `layer1_axes.must_not_import: datasources.adapters`                                                                                         |
| A3-03 | Fetch via `DataSourceService` only        | Source review + runtime test                                  | **PASS**           | `ingestion.py` imports `DataSourceService`; `test_layer1MicroIngestion_usesDataSourceServiceBeforeFetch` patches `create_adapter` → no call |
| A3-04 | Phase 1 zero mutation                     | PH-A1 evidence                                                | **PASS**           | `audit-ph-a1-inventory.md`; DB hash + data-root fingerprint                                                                                 |
| A3-05 | Phase 2 zero mutation                     | PH-A2 evidence                                                | **PASS**           | `phase2_no_mutation_proof.md` — `db_file_hash_unchanged: True`, row counts unchanged                                                        |
| A3-06 | Phase 3 no clean `axis_observation` write | PH-A3 evidence                                                | **PASS**           | `audit-ph-a3-staging.md` A3-06; `phase3_no_clean_write_proof.md`                                                                            |
| A3-07 | `DbValidationGate` on clean path          | Source + tests                                                | **PASS**           | See §DbValidationGate below                                                                                                                 |
| A3-08 | ResourceGuard before fetch/commit         | Source + tests                                                | **PASS**           | `_enforce_resource_guard` in preview/micro-fetch/commit; `test_layer1Observation_resourceGuardPauseBlocksCommit`                            |
| A3-09 | Threat: hardcoded URLs                    | `rg 'https?://' layer1_axes`                                  | **PASS**           | 0 matches in package                                                                                                                        |
| A3-10 | Threat: API keys / secrets                | `rg -i 'api_key\|password\|secret\|token' layer1_axes`        | **PASS**           | 0 matches in package                                                                                                                        |
| A3-11 | Threat: SQL concatenation                 | Manual review of `f"…SELECT…"` sites                          | **PASS (bounded)** | See §SQL interpolation; no user-controlled SQL fragments                                                                                    |

---

## 1. Adapter factory boundary (`create_adapter`)

### Static scan

```text
rg create_adapter backend/app/layer1_axes  → 0 matches
```

### Contract alignment

| Contract                           | Rule                                                             | Observed                                                        |
| ---------------------------------- | ---------------------------------------------------------------- | --------------------------------------------------------------- |
| `datasource_service_contract.yaml` | `layer1_axes` in `forbidden_direct_callers` for `create_adapter` | Honored — only `DataSourceService.fetch` / `preview_route` used |
| `module_boundary_matrix.md` §3     | `layer1*` forbids direct adapter factory / raw vendor classes    | Honored                                                         |
| `module_boundary_contract.yaml`    | `layer1_axes.must_not_import: backend.app.datasources.adapters`  | Honored                                                         |

### Allowed imports (by design)

`ingestion.py` imports `backend.app.datasources.service.DataSourceService` and DTO modules (`fetch_result`, `route_models`). This matches the facade contract: Layer modules call the service, not adapters.

### Automated enforcement

| Test                                                                   | Assertion                                                       |
| ---------------------------------------------------------------------- | --------------------------------------------------------------- |
| `test_layer1_axes_doesNotImportCreateAdapter`                          | `scan_package_for_create_adapter("layer1_axes") == []`          |
| `test_layer1Ingestion_phase0_datasourceServiceFactoryBoundaryEnforced` | Forbidden package list includes `layer1_axes`                   |
| `test_layer1MicroIngestion_usesDataSourceServiceBeforeFetch`           | Monkeypatched `create_adapter` never invoked during micro-fetch |
| `test_layerModules_forbidAdapterImports`                               | Module boundary contract test                                   |

**GitNexus query** (`layer1_axes create_adapter adapter factory boundary`): hits boundary tests and `create_adapter` definition under `datasources/adapters` only — no Layer1 production callers.

---

## 2. Phase 1 / Phase 2 mutation checks

### Phase 1 (read-only inventory)

| Control                                     | Status    | Evidence                                                           |
| ------------------------------------------- | --------- | ------------------------------------------------------------------ |
| Sandbox DB copy before inspect              | MITIGATED | `copy_sandbox_db` → `execute-evidence/.phase1-baseline-sandbox/`   |
| No WriteManager / migrations during capture | PASS      | `test_layer1Ingestion_phase1_captureDoesNotCallWriterOrMigrations` |
| DB file hash unchanged                      | PASS      | `test_layer1Ingestion_phase1_capture_zeroMutation`                 |
| Data-root content fingerprint               | PASS      | `data_root_content_fingerprint` in inventory JSON                  |

Prior PH-A1 security review (`adversarial-audit-ph-a1-agent2-security.md`): **PASS_WITH_NOTES** — no blocking defects; operational note S-06 (concurrent writer during copy) remains P3.

### Phase 2 (route dry-run)

| Control                                  | Status | Evidence                                                 |
| ---------------------------------------- | ------ | -------------------------------------------------------- |
| `preview_route` only — no `fetch`        | PASS   | `preview_routes` calls `DataSourceService.preview_route` |
| Row counts unchanged                     | PASS   | `phase2_no_mutation_proof.md`                            |
| DB file hash unchanged                   | PASS   | `db_file_hash_unchanged: True` on sandbox DB             |
| ResourceGuard enforced (raises on PAUSE) | PASS   | `audit-ph-a2-route.md` A2-15                             |

**Conclusion:** Phase 1 and Phase 2 mutation gates hold. No unauthorized clean-table or fetch side effects before Phase 3 staging.

---

## 3. DbValidationGate on clean write path

### Write surfaces (all use `WriteManager` + `DbValidationGate`)

| Component                                | File                       | Gate wiring                                                      |
| ---------------------------------------- | -------------------------- | ---------------------------------------------------------------- |
| `Layer1ObservationWriter`                | `observation_writer.py:20` | `WriteManager(conn_manager, DbValidationGate(conn_manager))`     |
| `Layer1SnapshotWriter`                   | `lineage.py:252`           | Same pattern for feature/interpretation/lineage tables           |
| `_register_clean_file_registry_rows`     | `ingestion.py:119`         | `FileRegistry` + `WriteManager` + `DbValidationGate`             |
| `commit_clean_observation_and_snapshots` | `ingestion.py`             | App-level gates → `obs_writer.write_observations` → WriteManager |

### Gate policy (`validation_gate.py` + `write_contract.yaml`)

`DbValidationGate.assert_can_write` rejects when:

- `validation_report` row missing
- `status == FAILED`
- `can_write_clean == false`
- `needs_manual_review == true` (unless `manual_patch` write mode — not used on Layer1 clean path)

`commit_clean_observation_and_snapshots` adds **pre-WriteManager** guards:

- `quality_report.can_write_clean` → `VALIDATION_FAILED`
- `quality_report.needs_manual_review` → `MANUAL_REVIEW_REQUIRED`
- `conflict_report.status == SEVERE_CONFLICT` → `SEVERE_CONFLICT`

### Test coverage

| Test                                                            | Gate exercised                              |
| --------------------------------------------------------------- | ------------------------------------------- |
| `test_layer1Observation_cleanWrite_usesWriteManager`            | `write_audit_log` for `axis_observation`    |
| `test_layer1Observation_validationFailure_blocksCleanWrite`     | Validation failure blocks commit            |
| `test_layer1Observation_severeConflict_blocksCleanWrite`        | Severe conflict blocks commit               |
| `test_layer1Observation_manualReview_blocksNonManualPatchWrite` | Manual review blocks commit                 |
| `test_layer1Observation_writeAuditUsesSharedValidationReport`   | Shared `validation_report_id` across writes |

**GitNexus impact** (`DbValidationGate`, upstream): risk **LOW**, 4 direct dependents at d=1 (writers + tests). No bypass path found in `layer1_axes`.

**No `StubValidationGate`** usage in `layer1_axes` (production stub forbidden per `validation_gate.py` docstring).

---

## 4. Three threat classes

### 4.1 Hardcoded URLs

**Scan:** `rg 'https?://' backend/app/layer1_axes` → **0 matches**.

External endpoints remain in datasource registry/YAML and adapter layer — not duplicated in Layer1 ingestion code. Staged default uses `LocalFixtureFetchPort` / `build_staged_fixture_service` (PH-A3 A3-08).

### 4.2 API keys / credentials

**Scan:** `rg -i 'api_key|api-key|password|secret|token|bearer|credential' backend/app/layer1_axes` → **0 matches**.

No secrets embedded in Layer1 bridge code. Credential handling (if any for live sources) stays behind `DataSourceService` / adapter config — out of Batch 2.5 staged scope.

### 4.3 SQL string concatenation

**Sites reviewed:**

| Location                         | Pattern                                                                | Risk assessment                                                                                |
| -------------------------------- | ---------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `observation_writer.py:73`       | `f"CREATE TABLE {staging} AS SELECT * FROM {AXIS_OBSERVATION_TABLE}…"` | **Low** — `staging` = `stg_axis_obs_{uuid.hex[:8]}`; target table constant                     |
| `lineage.py:303,375,446`         | Same staging DDL pattern                                               | **Low** — uuid staging names; fixed snapshot table names                                       |
| `ingestion.py:381,723`           | `f'SELECT COUNT(*) FROM "{name}"'` / staging DDL                       | **Low** — `name` from caller-supplied table tuple (fixed phase evidence lists) or uuid staging |
| `ingestion_inventory.py:306,323` | Count + dynamic column list                                            | **Low** — `STAGING_TABLES` constant; `select_cols` whitelisted against `information_schema`    |
| All INSERT paths                 | `INSERT … VALUES (?, ?, …)`                                            | **Safe** — parameterized values                                                                |

**No user-controlled or registry-sourced strings** are interpolated into SQL identifiers on the clean-write path. Residual risk is **P3** (defense-in-depth: could adopt identifier-quoting helper for staging DDL in a future hardening pass; not required for staged local-first deployment).

---

## 5. Doubt-driven probes

| Doubt                                        | Probe                                                                      | Outcome                                               |
| -------------------------------------------- | -------------------------------------------------------------------------- | ----------------------------------------------------- |
| Could Layer1 dynamically import adapters?    | Static `scan_package_for_create_adapter` + runtime monkeypatch test        | No                                                    |
| Could Phase 3 write `axis_observation`?      | PH-A3 + `test_layer1MicroIngestion_phase3DoesNotWriteCleanAxisObservation` | No                                                    |
| Could commit skip WriteManager?              | Grep `INSERT INTO axis_observation` in `layer1_axes`                       | No direct inserts; only via `Layer1ObservationWriter` |
| Could validation pass with stub gate?        | Grep `StubValidationGate` in `layer1_axes`                                 | No                                                    |
| Does preview bypass ResourceGuard?           | `preview_routes` calls `check_resource_guard` before loop                  | No (A1-12 closed)                                     |
| Production DB touched during audit captures? | Sandbox paths under `execute-evidence/.phase*-sandbox/`                    | Isolated                                              |

---

## 6. Issues

### P0 — none

No blocking security defects requiring immediate remediation.

### P1 — none

Adversarial Phase 4 P1 items (A1-01..07, B25-A2-01..03) closed per `adversarial-audit-phase4-remediation.md`. No new P1 security findings in this A3 pass.

### P2 / P3 — informational (non-blocking)

| ID          | Sev | Finding                                                | Recommendation                                                                                        |
| ----------- | --- | ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------- |
| A3-SQL-01   | P3  | Staging DDL uses f-string table names (uuid-generated) | Optional: shared `create_empty_staging(con, template_table)` helper with strict identifier validation |
| A3-OPS-01   | P3  | Concurrent writer during Phase 1 sandbox copy (S-06)   | Operational: re-capture sandbox before Phase 4 if live writes occurred                                |
| A3-DEFER-01 | —   | Live FRED route deferred (`B2.5-O-05`)                 | By design; re-run A3 if live external fetch enabled                                                   |
| A3-DEFER-02 | —   | Double `fetch_log` rows (`B2.5-O-07`)                  | Data-quality/lineage concern, not a security boundary violation                                       |

---

## 7. Cross-references

| Artifact                                           | Role                                   |
| -------------------------------------------------- | -------------------------------------- |
| `research/gitnexus-audit-summary.md`               | 7.pre index; A3 focus symbols          |
| `research/audit-ph-a1-inventory.md`                | Phase 1 mutation PASS                  |
| `research/audit-ph-a2-route.md`                    | Phase 2 mutation PASS                  |
| `research/audit-ph-a3-staging.md`                  | Phase 3 staging + ResourceGuard PASS   |
| `research/audit-ph-a4-clean-write.md`              | Phase 4 WriteManager + validation PASS |
| `specs/contracts/write_contract.yaml`              | `validation_gate.reject_if` policy     |
| `specs/contracts/datasource_service_contract.yaml` | Factory caller boundaries              |
| `docs/architecture/module_boundary_matrix.md`      | Layer1 → no adapters                   |

---

## Sign-off

```
Dimension A3 (audit-security): PASS
Date: 2026-06-20
P0: 0 | P1: 0 | P2/P3 notes: 4 (informational)
Output: research/audit-a3-security.md
```
