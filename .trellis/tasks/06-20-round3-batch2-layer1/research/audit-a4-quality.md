# A4 audit-quality — §3.4

> Dimension: INSUFFICIENT_HISTORY, SHADOW diagnostics, lineage DB persistence, WriteManager+ValidationGate integration, error handling, edge cases  
> Scope: `backend/app/layer1_axes/*`, `tests/test_layer1_axis_loader.py`, `tests/test_layer1_interpretation.py`, migration `011_layer1_tables.sql`  
> Skills: code-review-and-quality + doubt-driven-development  
> Adversarial trigger: WriteManager bypass on lineage; rolling window not enforced; contract test gaps

---

## Verdict: **PASS** (post-repair)

Layer 1 core behaviors for INSUFFICIENT_HISTORY, SHADOW guardrails, no-future-data, and feature-snapshot WriteManager integration are implemented and **23/23** targeted pytest cases pass. Two **P1** gaps remain: `axis_snapshot_lineage` is persisted with a direct `INSERT` (MASTER §7 Red Flag — bypass WriteManager), and `AxisFeatureEngine` does not truncate history to the configured rolling window (module doc §7.3 / AC-RES-1 unbounded-scan risk). Neither blocks local Batch 2 closure with documented §4.3 repairs, but lineage write-path parity must not be deferred silently.

---

## Axis scores (1–5)

| Axis         | Score | Rationale                                                                                                                                               |
| ------------ | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Correctness  | 3     | INSUFFICIENT_HISTORY / SHADOW / future-input paths correct in tested fixtures; rolling window + observation ordering gaps affect production-scale stats |
| Readability  | 4     | Clear module split (loader / feature / interpretation / lineage); frozen dataclasses; guardrail errors named                                            |
| Architecture | 3     | Feature writes honor staging→ValidationGate→WriteManager; lineage + interpretation lack symmetric clean-table write paths                               |
| Security     | 4     | Parameterized SQL in persist; dynamic staging name uses uuid hex (low injection risk); no secrets in layer1 code                                        |
| Performance  | 3     | Full-history scan in `_compute_one` ignores `window_len` cap; ResourceGuard hook present but WARN not gated                                             |

---

## Findings

| ID    | Priority | Location                                                                                       | Finding                                                                                                                                                                                                                                                                                                                                                | Recommended fix                                                                                                                                                                                                                                        |
| ----- | -------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| A4-01 | **P1**   | `lineage.py` `SnapshotLineageBuilder.persist` L97–127                                          | **Lineage bypasses WriteManager.** Direct `INSERT INTO axis_snapshot_lineage` on a clean table violates `write_manager.md` §1 (“任何 clean 表…写入都必须通过 WriteManager”), MASTER §3.4 write chain, and §7 Red Flag “绕过 WriteManager”. Feature snapshots use `Layer1SnapshotWriter`; lineage does not. No write audit row for lineage inserts.     | Add `Layer1LineageWriter` (or extend `Layer1SnapshotWriter`) staging→`DbValidationGate`→`WriteManager.write()` for `axis_snapshot_lineage`; integration test mirroring `test_layer1Snapshot_writeViaWriteManager`.                                     |
| A4-02 | **P1**   | `feature_engine.py` `_compute_one` L82–85                                                      | **Rolling window not applied.** `values` includes every non-null observation in `past`, not the last `window_len` points per module doc §7.3 / §8 step 3. `window_len` only drives `coverage_ratio` denominator and metadata. With long histories, z-score/percentile use unbounded data (AC-RES-1 / GLOBAL_RESOURCE_LIMITS concern).                  | After filtering by `indicator_id` and `publish_timestamp <= as_of`, sort by `publish_timestamp`, take trailing `window_len` observations, then compute stats. Add test: 600 obs with `window_len=20` — stats must match 20-point window, not full 600. |
| A4-03 | **P1**   | `lineage.py` `build`; `layer1-lineage-tests.md`                                                | **`agent_outputs_not_source` unenforced.** Contract constraint (`snapshot_lineage_contract.yaml`) requires agent prose never in `source_dataset_ids`; no builder validation and no pytest (design doc lists it; not implemented).                                                                                                                      | Reject `source_dataset_ids` matching agent-output patterns (e.g. prose tokens, `generated_by=agent` prefixes); add `test_snapshotLineage_rejectsAgentOutputsInSourceDatasets`.                                                                         |
| A4-04 | **P2**   | `tests/test_layer1_interpretation.py` `test_snapshotLineageIncludesAllRequiredFields` L163–196 | **Lineage field test incomplete vs AC-LINEAGE-1.** Asserts only 5 column names exist in `information_schema`; does not verify all 17 `required_fields` populated or non-null where contract disallows null. `LINEAGE_REQUIRED_FIELDS` in `lineage.py` is unused.                                                                                       | Assert every `snapshot_lineage_contract.yaml` field present **and** round-trip values after `persist`; use `LINEAGE_REQUIRED_FIELDS` as single source of truth.                                                                                        |
| A4-05 | **P2**   | `feature_engine.py` `_compute_one` L67–71, L141                                                | **Observation ordering assumed, not enforced.** `past` filter preserves input list order; `past[-2]` for delta and unsorted percentile input can be wrong if caller supplies unordered history.                                                                                                                                                        | Sort `past` by `publish_timestamp` ascending before stats and delta; test with deliberately shuffled history fixture.                                                                                                                                  |
| A4-06 | **P2**   | `interpretation.py` `build_interpretation` L62–64; AC-WRIT-1                                   | **Interpretation snapshot has no WriteManager path; partial forbidden-term handling.** Only `"买入"` is replaced; `"卖出"`, `"信号"`, etc. remain in emitted text (AC-018-3 allows `needs_human_review` — flag set — but output still contains forbidden terms). No staging/WriteManager writer for `axis_interpretation_snapshot`.                    | Either reject write on any forbidden term (`reject_if_forbidden`) or sanitize all `FORBIDDEN_OUTPUT_TERMS`; add `Layer1InterpretationWriter` via WriteManager for AC-WRIT-1 parity.                                                                    |
| A4-07 | **P2**   | `lineage.py` `Layer1SnapshotWriter.write_features` L202                                        | **Uses private `WriteManager._execute_write`.** Skips public `write()` entry (mode validation, connection lifecycle). Works in tests but couples to internal API.                                                                                                                                                                                      | Call `self._wm.write(req, con=con, own_transaction=True)` instead of `_execute_write`.                                                                                                                                                                 |
| A4-08 | **P3**   | `lineage.py` `build` L61–62                                                                    | **`json.loads` on validation_report fields unguarded.** Malformed `source_fetch_ids_json` / `source_content_hashes_json` raises `JSONDecodeError` without domain error.                                                                                                                                                                                | Wrap with try/except; raise `ValueError` with `validation_report_id` context.                                                                                                                                                                          |
| A4-09 | **P3**   | `lineage.py` `build` L63–66                                                                    | **Synthetic hash fallback masks missing validation data.** When `source_content_hashes_json` is empty, SHA256 of dataset ids is invented — lineage appears complete but may not reflect fetch hashes from `validation_report`.                                                                                                                         | Require non-empty hashes from validation_report for production path; fallback only in explicit test/fixture mode with `quality_flags` or log warning.                                                                                                  |
| A4-10 | **INFO** | `feature_engine.py` L56–58                                                                     | **ResourceGuard WARN proceeds.** Only `HARD_STOP` / `PAUSE` block; `WARN` continues. Likely intentional for eco profile but undocumented in Layer 1 module.                                                                                                                                                                                            | Document in module doc or gate WARN if policy requires degradation.                                                                                                                                                                                    |
| A4-11 | **INFO** | `guardrails.py`, loader tests                                                                  | **SHADOW three named tests pass** (`test_layer1ShadowDiagnostics_areExplicitlyAllowedButNoTakeover`, `test_shadowDiagnosticLabels_doNotEnterSourceRegistryRoles`, `test_shadowDiagnosticsOutsideGroup_requireExplicitDiagnosticOnly`). Loader sets `diagnostic_only=True` for `shadow_diagnostics` group; guardrails enforce orphan shadow constraint. | No action — keep as regression anchor.                                                                                                                                                                                                                 |
| A4-12 | **INFO** | `feature_engine.py` L91–120                                                                    | **INSUFFICIENT_HISTORY behavior matches contract.** Sets `state_bucket=insufficient_history`, null z/percentile/robust_z, appends `INSUFFICIENT_HISTORY` flag; raw_value retained. Verified by `test_axisFeatureEngine_insufficientHistory_noFakeZ`.                                                                                                   | No action.                                                                                                                                                                                                                                             |

### Adversarial reconciliation (doubt-driven)

| Claim                                | Attack                                              | Result                            |
| ------------------------------------ | --------------------------------------------------- | --------------------------------- |
| “Lineage persistence is audit-safe”  | Direct INSERT, no WriteManager audit row            | **Gap (A4-01)**                   |
| “Rolling window policy enforced”     | 600 obs, window_len=20 — all 600 used               | **Gap (A4-02)**                   |
| “Contract validation_tests complete” | `agent_outputs_not_source` missing                  | **Gap (A4-03)**                   |
| “INSUFFICIENT_HISTORY never fakes z” | 3 obs vs min_obs=10                                 | **Holds**                         |
| “SHADOW cannot takeover main value”  | Three §4.1 tests + `is_observable=False` for shadow | **Holds**                         |
| “Future data rejected”               | publish > as_of                                     | **Holds** (`Layer1SnapshotError`) |

Cross-model skipped: non-interactive subagent context.

---

## What's done well

- INSUFFICIENT_HISTORY path is clean: no fabricated z/percentile, explicit `state_bucket` and quality flag — matches module doc §7.3 and AC-018-2.
- SHADOW diagnostics: loader classification (`is_shadow`, `dest_tag=SHADOW`, non-observable) plus guardrail validator covers in-group `no_takeover` and out-of-group `diagnostic_only` — aligned with `common_axis_rules.md` §4.1.
- Feature snapshot WriteManager integration test (`test_layer1Snapshot_writeViaWriteManager`) exercises staging, validation_report gate, and clean-table insert end-to-end.
- Forbidden / BlindSpot indicators excluded from observable set with dedicated tests (AC-017-3).
- Frozen datamodels and explicit error types (`Layer1SnapshotError`, `GuardrailViolationError`, `InterpretationRejectedError`) improve traceability.

---

## Verification story

| Check                        | Result                                                                                                                                     |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Tests reviewed               | **Yes** — 23 tests across loader + interpretation; semantic assertions on flags/state_bucket/lineage columns                               |
| Build verified               | **Yes** — `python -m pytest tests/test_layer1_axis_loader.py tests/test_layer1_interpretation.py -q` → **23 passed** (2026-06-20 A4 audit) |
| Execute evidence cross-check | **Yes** — `execute-evidence/8.3-green.txt`, `8.5-green.txt` show GREEN for feature/lineage steps                                           |
| Security checked             | **Partial** — no direct clean-table SQL bypass in feature path; lineage direct INSERT flagged (A4-01); A3 owns full static scan            |

---

## §4.3 Repair items

| ID    | Priority | Action                                                                                          | Owner phase                          |
| ----- | -------- | ----------------------------------------------------------------------------------------------- | ------------------------------------ |
| A4-01 | P1       | Route `axis_snapshot_lineage` through staging→ValidationGate→WriteManager; add integration test | Batch 2 repair or Batch 3 pre-flight |
| A4-02 | P1       | Truncate history to `window_len` before stats; add window-boundary regression test              | Batch 2 repair                       |
| A4-03 | P1       | Enforce + test `agent_outputs_not_source` on `source_dataset_ids`                               | Batch 2 repair                       |
| A4-04 | P2       | Strengthen `test_snapshotLineageIncludesAllRequiredFields` to all 17 contract fields            | Batch 2 repair                       |
| A4-05 | P2       | Sort observations by `publish_timestamp` before delta/stats                                     | Batch 2 repair                       |
| A4-06 | P2       | Interpretation WriteManager writer + consistent forbidden-term policy                           | Batch 3 or repair                    |
| A4-07 | P2       | Replace `_execute_write` with public `WriteManager.write()`                                     | Batch 2 repair                       |
| A4-08 | P3       | Guard `json.loads` in lineage builder                                                           | Optional hardening                   |
| A4-09 | P3       | Restrict synthetic content-hash fallback to test/fixture mode                                   | Optional hardening                   |

**§4.3 count: 9** (3× P1, 4× P2, 2× P3). **P0: 0.** Batch 2 gate: no P0; P1 items A4-01–A4-03 should be tracked before Batch 3 consumers rely on lineage audit trail.
