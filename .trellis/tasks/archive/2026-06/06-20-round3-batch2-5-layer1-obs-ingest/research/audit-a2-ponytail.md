# A2 Ponytail Audit — §4.2

> **Task:** `06-20-round3-batch2-5-layer1-obs-ingest`  
> **Agent:** audit-ponytail (A2)  
> **Scope:** `backend/app/layer1_axes/ingestion.py` (single file per AUDIT.plan §2.2)  
> **Trace:** `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §4.2 Batch 2.5 · `018A` §7.1 / §8 Phases 2–4  
> **Skills:** ponytail-review + doubt-driven-development (minimal abstraction, no premature generalization)

---

## Verdict: **PASS**

Core duplication (A2-01/02) resolved via `_prepare_staged_route_and_request` + `_fetch_staging_on_connection`. MD table helper (A2-03) added. Evidence capture remains colocated (A2-04) — acceptable for staged batch; optional `ingestion_evidence.py` split is non-blocking.

---

## Line counts

| Segment                                                        | Lines (inclusive)              | LOC       | Role                                            |
| -------------------------------------------------------------- | ------------------------------ | --------- | ----------------------------------------------- |
| **Total file**                                                 | 1–1516                         | **1,516** | AUDIT scope                                     |
| Imports + constants + rejection codes                          | 1–103                          | 103       | Frozen staged scope (ENV-E1-DGS10)              |
| `_register_clean_file_registry_rows`                           | 106–145                        | 40        | Phase 4 file_registry via WriteManager          |
| Exceptions + frozen dataclasses                                | 148–230                        | 83        | Contract-shaped DTOs (no behavior trees)        |
| `Layer1ObservationIngestionService`                            | 233–936                        | **704**   | Runtime orchestration                           |
| — `preview_routes`                                             | 386–432                        | 47        | Phase 2 dry-run                                 |
| — `micro_fetch_staging`                                        | 449–538                        | 90        | Phase 3 staging fetch                           |
| — `commit_clean_observation_and_snapshots`                     | 568–936                        | **369**   | Phase 4 validate/write/snapshot (largest block) |
| Serialize helpers + path utils                                 | 939–1064                       | 126       | JSON/evidence prep                              |
| **Evidence / markdown / task capture**                         | 960–1516                       | **557**   | Execute artifact writers (not runtime hot path) |
| — `format_phase2_*` + `format_phase3_*` + `format_phase4_*` MD | 960–1043, 1167–1188, 1348–1368 | ~123      | Markdown report generators                      |
| — `capture_phase*` + `capture_task_phase*`                     | 1066–1516                      | ~451      | Sandbox bootstrap + JSON/MD persistence         |

**Runtime vs tooling ratio:** ~704 LOC service core vs ~557 LOC evidence tooling (~37% of file).

---

## DOUBT answer (adversarial)

| Claim                                                                | Attack                                                                                                                       | Reconcile                                                                                                                                                  |
| -------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| “Single-indicator bridge needs ~1.5k LOC”                            | 557 LOC are evidence capture/formatters; `ingestion_inventory.py` already owns Phase 1 inventory                             | Service core ~700 LOC is plausible; **file length is inflated by Execute artifacts in the same module**                                                    |
| “`commit_clean_observation_and_snapshots` is minimal ADR-001 wiring” | 369-line method duplicates fetch/route/guard/normalize from `micro_fetch_staging` then adds validation/write/snapshot inline | Required steps are real; **composition failure** (re-fetch instead of reuse) adds ~45–55 duplicate LOC                                                     |
| “Dataclass explosion is over-modeling”                               | 7 frozen dataclasses (~65 LOC)                                                                                               | Fields map 1:1 to 018A evidence JSON (`route_plan`, `fetch_result`, write statuses); no inheritance/strategy                                               |
| “Should delegate to `sync/pipeline.py`”                              | MASTER flags SyncValidationPipeline as reuse candidate                                                                       | Batch 2.5 chose explicit Layer1 facade; **not** ponytail FAIL unless duplicate pipeline abstraction appears — it does not; duplication is local copy-paste |
| “No ≥20-line simplifiable block”                                     | `commit_*` alone is 369 lines; three MD formatters share table templates                                                     | **≥4 blocks ≥20 lines** identified below                                                                                                                   |

---

## Bloat candidates table

| ID        | Sev        | Location                                              | Lines                                     | Net LOC if fixed | Issue                                                                                                                                                                                                                                                                         | §4.3?                       |
| --------- | ---------- | ----------------------------------------------------- | ----------------------------------------- | ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- | --- |
| **A2-01** | Important  | `commit_clean_observation_and_snapshots`              | **568–936 (369)**                         | −50–80           | Monolith re-runs route preview, capability check, ResourceGuard, `fetch`, path normalization, and `fetch_id` lookup already implemented in `micro_fetch_staging` (449–538). Should compose: `micro = self.micro_fetch_staging(...)` then validation/write/snapshot only.      | No                          |
| **A2-02** | Important  | Fetch path duplication                                | 461–525 vs 646–684                        | **~45**          | Parallel blocks: `FetchRequest` build, `preview_route`, `_verify_capability`, route READY gate, `fetch`, `_relative_to_data_root` loop, `fetch_log` SELECT. Classic copy-paste ponytail.                                                                                      | No                          |
| **A2-03** | Important  | Evidence MD formatters                                | 960–1017, 1021–1042, 1167–1188, 1348–1368 | **~60–75**       | Three “before/after row-count table” formatters + large Phase 2 matrix builder share identical table-header/row loops. One `_format_count_table_md(title, counts_dict)` would collapse ~123 LOC to ~45.                                                                       | No                          |
| **A2-04** | Important  | Evidence capture block                                | **1066–1516 (451)**                       | −0 (move)        | `capture_task_phase{2,3,4}_evidence`, `capture_phase*_evidence`, JSON/MD writers belong with `ingestion_inventory.py` (Phase 1) or `ingestion_evidence.py` — not in runtime service module. Reduces cognitive load; aligns 018A §11 artifact names without mixing boundaries. | No                          |
| **A2-05** | Suggestion | Sandbox bootstrap triplication                        | 1234–1284, 1287–1345, 1436–1515           | **~40–55**       | Repeated: `shutil.rmtree` / `apply_migrations` / `build_staged_fixture_service` / `Layer1ObservationIngestionService` wiring. Extract `_open_phase_sandbox(evidence_dir, phase)` (~25 LOC) called thrice.                                                                     | No                          |
| **A2-06** | Suggestion | Eligibility guard repetition                          | 399–407, 439–446, 578–585                 | ~20              | Same allowlist + `_assert_indicator_eligible` sequence in preview, micro-fetch prep, and commit. Extract `_guard_indicator_for_ingestion(indicator_id)` (~12 LOC, saves ~20 at call sites).                                                                                   | No                          |
| **A2-07** | Suggestion | `_register_clean_file_registry_rows` vs staged helper | 106–145                                   | ~15–25           | Phase 3 uses `register_staged_file_registry_rows`; Phase 4 has parallel 40-line WriteManager path. Unify behind one registrar with `mode=staged                                                                                                                               | clean` if signatures align. | No  |
| **A2-08** | Suggestion | `capture_phase2_route_evidence` payload notes         | 1109–1116                                 | ~8               | Inline prose about `job_event_log` / conflict deferral — belongs in evidence JSON from tests or `phase2_route_preview_matrix.md` template, not runtime constants.                                                                                                             | No                          |

**Largest single simplifiable block:** **A2-01** — `commit_clean_observation_and_snapshots` at **369 lines** (≥20 threshold met **4× over**).

**Estimated net shrink if A2-01–03 + A2-05–06 applied:** **~215–275 LOC (~14–18% of file)** without removing any 018A gate.

---

## Adversarial checks (018A §7.2 / ponytail principles)

| Red-flag class                                       | Ponytail read                                                                                                                       |
| ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Premature generalization (multi-indicator framework) | **Not present** — `DEFAULT_INGESTION_ALLOWLIST` + `_resolve_binding` hard-code `ENV-E1-DGS10`; non-allowlisted indicators fail fast |
| Factory / plugin registry                            | **Not present** — `DataSourceService` injected; `build_staged_fixture_service` only in evidence capture                             |
| Forbidden `create_adapter` in Layer1                 | **Not present** — grep scope clean (A3 owns static proof)                                                                           |
| Speculative config layers                            | **Not present** — constants are batch-frozen, not YAML-driven ingestion framework                                                   |
| Duplicated orchestration                             | **Present (A2-01, A2-02)** — local duplication, not two frameworks                                                                  |
| Execute tooling in runtime module                    | **Present (A2-04)** — boundary smell, not abstract over-engineering                                                                 |
| Markdown report framework                            | **Borderline (A2-03)** — string builders are procedural, not a template engine; still **~123 LOC** ponytail                         |

---

## Concrete refactor suggestions (Audit review-only — do not apply here)

1. **A2-01 / A2-02:** Refactor `commit_clean_observation_and_snapshots` to accept optional `MicroFetchResult` or call `micro_fetch_staging` inside the same writer transaction (pass `con` through) before mapping/validation/write.
2. **A2-03:** Add `_format_markdown_count_proof(title, proof, before_key, after_key)` used by Phase 2/3/4 proof MD functions.
3. **A2-04:** Move `capture_*` and `format_phase*_md` to `ingestion_evidence.py`; keep `ingestion.py` as service + thin re-exports if tests import capture helpers.
4. **A2-05:** Single `_bootstrap_sandbox_db(evidence_dir, dirname, *, fresh: bool)` shared by phase 2/3/4 task capture.
5. **A2-06:** `_guard_indicator_for_ingestion(self, indicator_id) -> tuple[AxisIndicatorDefinition, IngestionRouteBinding]`.

---

## What's done well

- **Phase-gated API surface** matches 018A §8: `preview_routes` → `micro_fetch_staging` → `commit_clean_observation_and_snapshots` with explicit mutation table constants.
- **Frozen dataclasses** carry evidence fields without service inheritance trees.
- **Rejection reason codes** are string constants, not an enum framework.
- **Write boundary** delegates to `Layer1ObservationWriter`, `Layer1SnapshotWriter`, `DataQualityValidator`, `SourceConflictValidator`, `WriteManager` — no new write framework.
- **Staged scope honesty** — `FRED_PRIMARY_DEFERRED_NOTE`, single-indicator allowlist, no silent multi-source generalization.
- **No pandas/sklearn/pipeline plugin layer** inside Layer1.

---

## §4.3 repair queue (A2 contribution)

| ID  | Priority | Action             | Blocks finish-work? |
| --- | -------- | ------------------ | ------------------- |
| —   | —        | **None mandatory** | No                  |

A2-01–A2-04 are **recommended shrink / module split** for maintainability. Per Round 3 Batch 2 A2 precedent and AUDIT.plan pass condition (“无过度抽象”), optional ponytail trim does not enter §4.3 unless A9 promotes. **No factory-layer or speculative-generalization FAIL.**

**§4.3 count (A2): 0**

---

## Verification story

| Check                       | Result                                                                                                                                         |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Full file read              | **Yes** — 1,516 lines reviewed                                                                                                                 |
| 018A §7.1 scope alignment   | **Yes** — orchestration target `ingestion.py`; evidence names §11 satisfied but co-located                                                     |
| ROUND3 §4.2 bundle          | **Yes** — narrow phase-specific manifest; file breadth is internal, not manifest dump                                                          |
| ≥20-line simplifiable block | **Yes** — A2-01 (369), A2-03 (~123), A2-04 (451 move), A2-02 (~45)                                                                             |
| Tests reviewed              | **Indirect** — tests call `capture_task_phase*` and service methods; no test requires 369-line monolith or separate MD formatters in this file |
| Build verified              | **No** (A2 review-only)                                                                                                                        |
| Security checked            | **N/A** (A3)                                                                                                                                   |

---

## Summary

| Metric                       | Value                                                |
| ---------------------------- | ---------------------------------------------------- |
| **Verdict**                  | **PASS_WITH_FIXES**                                  |
| **Total LOC**                | 1,516                                                |
| **Service core LOC**         | ~704                                                 |
| **Evidence/tooling LOC**     | ~557 (~37%)                                          |
| **Largest block**            | `commit_clean_observation_and_snapshots` — 369 lines |
| **Bloat candidates ≥20 LOC** | 4 (A2-01, A2-02, A2-03, A2-04)                       |
| **Est. shrink potential**    | ~215–275 LOC (~14–18%)                               |
