# Adversarial Audit PH-A1 Round 2 — Remediation Log (F-A3)

> Agent 1 PASS_WITH_GAPS · Agent 2 security pass (main session) · 2026-06-20

## Verdict

**PASS** — F-A3-01..19 remediated. PH-A1 re-signed after full pytest + Tier A ruff.

## Remediation matrix

| ID      | Sev | Fix                                                                                                                                   |
| ------- | --- | ------------------------------------------------------------------------------------------------------------------------------------- |
| F-A3-01 | P1  | `record_operator_classification` auto-applies when `phase1_data_classification.md` present; JSON `phase2_gate.phase2_authorized=true` |
| F-A3-02 | P1  | `execute-handoff.md` baseline → `fixture_or_staged_evidence`; JSON-over-prose rule                                                    |
| F-A3-03 | P2  | `research/phase0_source_context_crosswalk.md` maps annex §5.1–5.5                                                                     |
| F-A3-04 | P2  | `test_layer1Ingestion_phase0_frozenIndicator_metadataEligible` (ENV-E1-DGS10)                                                         |
| F-A3-05 | P2  | `test_layer1Ingestion_phase0_datasourceServiceFactoryBoundaryEnforced` replaces call-only                                             |
| F-A3-06 | P2  | `phase0_db_contract_gate.md` rows: runtime_flow, resource_limits, platform_source_matrix, reference_adoption_guardrails               |
| F-A3-07 | P2  | `8.0-boot-reads.txt` E11b: validation_gate.py, resource_guard.py + gate tests                                                         |
| F-A3-08 | P2  | `staging_table_row_counts` in inventory (prior G remediation)                                                                         |
| F-A3-09 | P2  | `data_root_file_samples` in inventory JSON/md                                                                                         |
| F-A3-10 | P2  | `source_registry_snapshot` in inventory                                                                                               |
| F-A3-11 | P2  | `research/doubt-driven-ph-a0.md`, `research/doubt-driven-ph-a1.md`                                                                    |
| F-A3-12 | P2  | `phase1_data_classification.md` file-path sha256 proof table                                                                          |
| F-A3-13 | P2  | `test_layer1Ingestion_phase1_taskEvidenceSandboxCopyPath`                                                                             |
| F-A3-14 | P3  | `phase0_test_output.txt` summary footer                                                                                               |
| F-A3-15 | P3  | `8.2-green.txt` Tier A includes `test_layer1_ingestion_gates.py`                                                                      |
| F-A3-16 | P3  | `phase0_source_context_matrix.md` — `layer1_axes.yml` Phase 2 must-read                                                               |
| F-A3-17 | P3  | Canonical `audit-ph-a1-inventory.md`; stub `audit-ph-a1-phase1-inventory.md` redirect only                                            |
| F-A3-18 | P3  | Documented `DATA_ROOT` brittleness in doubt-driven-ph-a1 + sandbox copy strategy                                                      |
| F-A3-19 | P3  | `8.1-green.txt` pytest summary footer                                                                                                 |

## Agent 2 gap (security / runtime)

Agent 2 launch failed twice. Main session completed `research/adversarial-audit-ph-a1-agent2-security.md`:

- Sandbox copy isolates inspect from production DuckDB file
- `create_migrated_baseline_db` only when target DB missing (synthetic path)
- No WAL sidecar copy — single-file `shutil.copy2`; acceptable for read-only inspect gate
- Path resolution via `resolve_phase1_target_paths()` / config `DATA_ROOT`

## Post-remediation verification

```text
ruff: All checks passed! (backend/app/layer1_axes + both test files)
pytest tests/test_layer1_observation_ingestion.py tests/test_layer1_ingestion_gates.py: 40 passed
full pytest: exit 0, 536 collected, 535 passed, 1 skipped (symlink Windows)
```
