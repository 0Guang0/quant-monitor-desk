# Adversarial Audit PH-A1 — Agent 2 (security / runtime)

> Substitute for failed Agent 2 launch · main-session review · 2026-06-20

## Scope

Read-only Phase 1 inventory: mutation paths, sandbox isolation, path traversal, WAL/concurrency.

## Findings

| ID   | Sev | Finding                           | Status                                                                                                                                  |
| ---- | --- | --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| S-01 | P2  | Inspect could touch production DB | **MITIGATED** — `capture_task_phase1_evidence` copies to `execute-evidence/.phase1-baseline-sandbox/` before inspect when target exists |
| S-02 | P2  | `apply_migrations` during capture | **ACCEPTED** — only `create_migrated_baseline_db` when target DB absent; guarded by test patching migrations during capture             |
| S-03 | P2  | WAL / journal sidecars not copied | **ACCEPTED** — DuckDB single-file copy; inspect is read-only SELECT; re-copy if WAL drift suspected                                     |
| S-04 | P3  | `data_root.rglob` traversal       | **LOW** — rooted at configured `DATA_ROOT`; samples store relative paths only                                                           |
| S-05 | P3  | Memo path injection               | **LOW** — `record_operator_classification` resolves memo under evidence dir; sha256 recorded                                            |
| S-06 | P3  | Concurrent writer during copy     | **OPERATIONAL** — Phase 1 doc warns re-capture before Phase 4 if live writes occur                                                      |

## Verdict

**PASS_WITH_NOTES** — No blocking security defects for Phase 1 read-only gate. Phase 2+ must re-audit mutation paths in `ingestion.py`.

## Evidence

- `backend/app/layer1_axes/ingestion_inventory.py` — `copy_sandbox_db`, `capture_phase1_inventory`
- `tests/test_layer1_observation_ingestion.py` — `captureDoesNotCallWriterOrMigrations`, `zeroMutation`, sandbox copy test
