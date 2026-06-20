# Doubt-Driven Checklist — PH-A1 (Phase 1 Read-Only Inventory)

> F-A3-11 · doubt-driven-development · 2026-06-20 (post F-A3 remediation)

## CLAIM

Phase 1 inventory is **read-only** on project target paths, classifies DB/data-root evidence correctly, and gates Phase 2 unless schema-only **or** operator classification memo authorizes dry-run.

## CONTRACT (must hold)

- AC-P1-1: `baseline_context` binds `data/duckdb/quant_monitor.duckdb`; sandbox copy provenance when DB exists
- AC-P1-2: zero mutation — DB hash, row counts, data-root fingerprint unchanged
- 018A Phase 1 stop rule: `phase2_gate` reflects classification + memo
- Inspect WARN ≠ automatic Phase 2 authorization

## Adversarial questions (answered)

| #   | Doubt                                                | Reconciliation                                                                                               |
| --- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| 1   | Does inspect mutate production DB?                   | **No** when target exists — `copy_sandbox_db` then inspect copy; test `captureDoesNotCallWriterOrMigrations` |
| 2   | Can temp paths hide wrong DB?                        | Remediated: `capture_task_phase1_evidence` uses project targets                                              |
| 3   | Is `schema_only_empty` assumed when raw files exist? | **No** — classifier returns `fixture_or_staged_evidence`; memo required                                      |
| 4   | Does JSON disagree with handoff prose?               | Rule: **trust JSON** over handoff (`execute-handoff.md` updated F-A3-02)                                     |
| 5   | Is `user_provided_data` dead code?                   | Test `test_layer1Ingestion_phase1_classify_userProvidedData`                                                 |
| 6   | Can writer/migrations run during capture?            | Patched guard test blocks `apply_migrations` / WriteManager                                                  |
| 7   | Are data-root files unproven?                        | Memo + JSON `data_root_file_samples` with sha256 (F-A3-12)                                                   |
| 8   | Path traversal via data_root scan?                   | `rglob` under resolved `DATA_ROOT` only; samples are relative paths                                          |

## STOP condition

G-01..G-12 + F-A3-01..19 remediated (`adversarial-audit-ph-a3-remediation.md`). PH-A1 re-signed `research/audit-ph-a1-inventory.md`.
