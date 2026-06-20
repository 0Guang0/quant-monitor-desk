# Adversarial Audit Phase 1 — Remediation Log

> F-P1-01..12 → G-01..12 · 2026-06-20

## Remediation matrix

| ID             | Fix                                                                                                                                                                         |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| G-01 / F-P1-01 | `capture_task_phase1_evidence()` + `baseline_context` with `data/duckdb/quant_monitor.duckdb` targets; sandbox copy provenance; regen `phase1_before_ingestion_inventory.*` |
| G-02 / F-P1-02 | Dual adversarial audit (`adversarial-audit-ph-a1-agent1.md`) + doubt-driven re-sign in `audit-ph-a1-inventory.md`                                                           |
| G-03 / F-P1-03 | Canonical audit file `research/audit-ph-a1-inventory.md`; deprecated name noted                                                                                             |
| G-04 / F-P1-04 | `ruff check backend/app/layer1_axes tests/test_layer1_observation_ingestion.py` exit 0 → `8.2-green.txt`                                                                    |
| G-05 / F-P1-05 | MASTER §3.1 + §4 list `ingestion_inventory.py`                                                                                                                              |
| G-06 / F-P1-06 | MASTER §12 `[x]` for skills executed through §8.2                                                                                                                           |
| G-07 / F-P1-07 | `8.2-green.txt` documents `uv run` canonical + `.venv` fallback when `uv` absent                                                                                            |
| G-08 / F-P1-08 | `classify_db_evidence()` returns `user_provided_data` for file_registry/validation/manual_review without fetch                                                              |
| G-09 / F-P1-09 | Tests: fixture/staged, production, user_provided, `assess_phase2_gate`, `phase2Gate_blocksUntilReview`                                                                      |
| G-10 / F-P1-10 | `data_root_content_fingerprint()` in `zeroMutation` test                                                                                                                    |
| G-11 / F-P1-11 | `_inspect_status_note()` separates WARN from Phase 2 authorization; md uses `phase2_gate`                                                                                   |
| G-12 / F-P1-12 | `test_layer1Ingestion_phase1_captureDoesNotCallWriterOrMigrations` patches writer + migrations                                                                              |

## Data classification (018A stop rule)

Project inventory (2026-06-20) shows `raw_files_count=1`, `parquet_files_count=1`, `fetch_log=0`, `axis_observation=0`.

**Classification:** `fixture_or_staged_evidence` (data-root vendor artifacts from prior Round 3 pytest/vendor e2e; not production observation writes).

**Phase 2 authorization:** Requires explicit classification memo → `execute-evidence/phase1_data_classification.md`. After memo, operator may proceed to §8.3 dry-run on sandbox; gate API remains the enforcement point.

## Post-remediation pytest

```text
phase1 tests: 11 passed
full pytest: exit 0 (1 skip symlink)
ruff: All checks passed!
```
