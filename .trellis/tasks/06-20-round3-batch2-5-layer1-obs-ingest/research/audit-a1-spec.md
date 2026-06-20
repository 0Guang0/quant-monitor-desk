# A1 Spec Compliance Audit — Round 3 Batch 2.5 Layer 1 Observation Ingestion Bridge

> **Agent:** audit-spec (A1)  
> **Date:** 2026-06-20  
> **Mode:** read-only (no implementation edits)  
> **Skills:** trellis-check + doubt-driven-development (latter skill file absent on disk; applied adversarial checklist inline)  
> **Inputs:** AUDIT.plan §2 A1 row, `audit.jsonl`, `check.jsonl`, `implement.jsonl`, 018A §5, MASTER §0.6 + §2, contract YAMLs, `research/gitnexus-audit-summary.md`

---

## Verdict: **PASS**

Implementation matches 018A scope, contract boundaries, and five-phase gate intent. Manifest, registry, and Batch 3 handoff items closed in audit repair (2026-06-20).

---

## Executive summary

| Area                                                | Result                                                                                   |
| --------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| 018A §4 non-goals                                   | **PASS** — micro staged bridge only; no production CLI, live QMT/FRED, Layer 2+          |
| 018A §7.2 forbidden patterns                        | **PASS** — `rg create_adapter layer1_axes` = 0; clean writes via WriteManager            |
| Contract YAML (route/service/write/lineage/inspect) | **PASS** — enforced by gate + pipeline tests                                             |
| MASTER §0.6 Source Context Index                    | **PASS** — curated subset + §0.6.1 filter appendix                                       |
| `implement.jsonl` manifest                          | **PASS** — curated Batch 2.5 runtime paths added (F-A1-01 closed)                        |
| AC-REG-1 registry closeout                          | **PASS** — B2.5-O-04/O-07 synced across registries (F-A1-02 closed)                      |
| AC-HANDOFF-1 Batch 3 handoff                        | **PASS** — 018A §13 normative block in `final_registry_update.md` (F-A1-03 closed)       |
| GitNexus `impact` on new symbols                    | **STALE** — `ingestion.py` / `Layer1ObservationIngestionService` not indexed; `query` OK |

---

## Findings table

| ID          | Severity | Category                    | Finding                                               | Evidence                                                       | Repair                                                       |
| ----------- | -------- | --------------------------- | ----------------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------ |
| **F-A1-01** | MEDIUM   | Manifest                    | ~~`implement.jsonl` omits core paths~~                | **CLOSED** — 8 paths appended                                  | —                                                            |
| **F-A1-02** | MEDIUM   | Registry                    | ~~B2.5-O-04 registry drift~~                          | **CLOSED** — UNRESOLVED/RESOLVED synced                        | —                                                            |
| **F-A1-03** | LOW      | Handoff                     | ~~Handoff template gap~~                              | **CLOSED** — 018A §13 block in `final_registry_update.md`      | —                                                            |
| **F-A1-04** | INFO     | Deferred (accepted)         | `schema.sql` lags migration 011 (B2.5-O-02)           | `test_layer1Ingestion_phase0_schemaSqlLagTrackedAsO02`         | Keep DEFERRED; optional narrow PR                            |
| **F-A1-05** | INFO     | Deferred (accepted)         | Live FRED vs staged `macro_supplementary` (B2.5-O-05) | MASTER AC-P2-0; `FRED_PRIMARY_DEFERRED_NOTE` in `ingestion.py` | Keep DEFERRED until user authorization                       |
| **F-A1-06** | INFO     | Staged exception (accepted) | Phase 3 `file_registry` bypasses WriteManager         | `staged_evidence.py` + `staged_acceptance_policy.md` §6        | Documented exception; Phase 4 uses FileRegistry+WriteManager |

---

## Adversarial: `implement.jsonl` undeclared dependencies

**Trigger:** find ≥1 undeclared dependency.

**Result:** **FOUND** — multiple runtime paths used in Execute are absent from `implement.jsonl`:

| Undeclared path                                   | Used by                                          | Declared in implement.jsonl?           |
| ------------------------------------------------- | ------------------------------------------------ | -------------------------------------- |
| `backend/app/layer1_axes/ingestion.py`            | All phases 2–4 orchestration                     | **No**                                 |
| `backend/app/layer1_axes/ingestion_inventory.py`  | Phase 1 inventory + phase gates                  | **No**                                 |
| `backend/app/layer1_axes/observation_mapper.py`   | Phase 4 mapping                                  | **No**                                 |
| `backend/app/layer1_axes/observation_writer.py`   | Phase 4 WriteManager path                        | **No**                                 |
| `backend/app/layer1_axes/observation_contract.py` | Phase 0 DDL gate + validators                    | **No**                                 |
| `backend/app/storage/staged_evidence.py`          | Phase 3 micro-fetch `file_registry`              | **No**                                 |
| `backend/app/datasources/adapters/fetch_port.py`  | `build_staged_fixture_service` → Phase 3/4 tests | **No** (only in archived Round2 tasks) |

**Mitigation note:** MASTER §0.6 lists `backend/app/layer1_axes/*.py` as must-read code, but 018A §9 rule 5 and ROUND3 map require **curated** `implement.jsonl` — wildcard in MASTER does not satisfy manifest trace for Execute hook reads.

---

## Spec diff matrix (018A §5 + MASTER §0.6 + contracts)

### Scope & non-goals (018A §4, §7)

| Requirement                                 | Implementation                                                          | Status |
| ------------------------------------------- | ----------------------------------------------------------------------- | ------ |
| No full-market/full-history                 | Frozen allowlist `ENV-E1-DGS10`, eco profile, single as_of              | PASS   |
| No live QMT/Yahoo/FRED default              | Staged `macro_supplementary` + `build_staged_fixture_service`           | PASS   |
| No Layer 2+ ingestion                       | Changes confined to `layer1_axes/`, `storage/staged_evidence.py`, tests | PASS   |
| No `create_adapter` from Layer 1            | Static scan + `test_layer1_axes_doesNotImportCreateAdapter`             | PASS   |
| No clean SQL outside WriteManager (Phase 4) | `Layer1ObservationWriter` → `WriteManager.write`                        | PASS   |
| No docs/specs as implementation paths       | Runtime under `backend/app/` only                                       | PASS   |

### Contract alignment

| Contract                           | Key rule                                                              | Verification                                                                                                                                         |
| ---------------------------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `source_route_contract.yaml`       | No silent fallback; route before adapter                              | `test_layer1Ingestion_noSilentFallback`; `test_layer1MicroIngestion_persistsRoutePlanBeforeFetch` (ROUTE_PLAN in `job_event_log` before `fetch_log`) |
| `datasource_service_contract.yaml` | Only DataSourceService calls factory                                  | `micro_fetch_staging` / `commit_clean_observation_and_snapshots` use `DataSourceService.fetch`; monkeypatch test blocks `create_adapter`             |
| `write_contract.yaml`              | validation_report_id required; reject severe conflict / manual review | `DbValidationGate` + commit path checks; dedicated block tests                                                                                       |
| `snapshot_lineage_contract.yaml`   | Non-empty fetch ids/hashes; no future data                            | `test_layer1Observation_lineageIncludesFetchIdsAndHashes`; `allow_synthetic_hashes=False` in lineage builder                                         |
| `ops_db_inspect_contract.yaml`     | Read-only inventory fields                                            | `phase1_before_ingestion_inventory.json` includes baseline_context, copy_provenance, key table counts                                                |
| `module_boundary_matrix.md`        | Layer\* no direct adapter                                             | Enforced (see above)                                                                                                                                 |

### MASTER §2 AC spot-check

| AC            | Status            | Notes                                                          |
| ------------- | ----------------- | -------------------------------------------------------------- |
| AC-P0-4       | PASS              | No factory import in `layer1_axes`                             |
| AC-P1-1/2     | PASS              | Inventory evidence + zero-mutation tests                       |
| AC-P2-0/1/2/3 | PASS              | Staged route READY; no mutation in Phase 2                     |
| AC-P3-1/2/3   | PASS              | DataSourceService path; no clean obs in Phase 3; ResourceGuard |
| AC-P4-1..5    | PASS              | Validation → WriteManager → snapshots → lineage → post-inspect |
| AC-TRACE-1    | PASS              | End-to-end evidence chain in phase2–4 JSON artifacts           |
| AC-REG-1      | **PARTIAL**       | F-A1-02 registry drift                                         |
| AC-HANDOFF-1  | **PARTIAL**       | F-A1-03 template gap                                           |
| AC-GATE       | Deferred to A5/A8 | Not in A1 scope                                                |

---

## GitNexus / code intelligence

| Tool                                             | Result                                                                                               |
| ------------------------------------------------ | ---------------------------------------------------------------------------------------------------- |
| `impact(commit_clean_observation_and_snapshots)` | Target not found (index stale for new symbols)                                                       |
| `impact(Layer1ObservationIngestionService)`      | Target not found                                                                                     |
| `query("Layer 1 observation ingestion")`         | Returned axis_loader observable gate, data_quality layer1 findings — consistent with ingestion chain |
| Codegraph                                        | Project not indexed in session                                                                       |

**Blast radius (from source read):** `ingestion.py` imports DataSourceService, WriteManager, validators, feature/interpretation engines, staged_evidence — all within declared architecture docs; no forbidden upward coupling.

---

## Repair items (§4.3 input for REPAIR.plan)

| Priority | Item                                                                              | Owner hook                      |
| -------- | --------------------------------------------------------------------------------- | ------------------------------- |
| P1       | Curate `implement.jsonl` with F-A1-01 paths + extract reasons                     | Repair agent / Execute closeout |
| P1       | Sync B2.5-O-04 across UNRESOLVED → RESOLVED registries (F-A1-02)                  | Repair agent                    |
| P2       | Normalize Batch 3 handoff block to 018A §13 (F-A1-03)                             | Repair agent                    |
| P3       | Optional: run `node .gitnexus/run.cjs analyze` so A2+ impact works on new symbols | Ops                             |

---

## A1 sign-off

| Field                                  | Value                                                                                             |
| -------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Dimension                              | A1 audit-spec                                                                                     |
| Verdict                                | **PASS**                                                                                          |
| Blocking for A9 PASS?                  | No — fixes are manifest/registry hygiene                                                          |
| Blocking for Batch 3 real-data claims? | Yes for **live** claims; **staged/fixture** downstream OK with documented limitations (B2.5-O-05) |
