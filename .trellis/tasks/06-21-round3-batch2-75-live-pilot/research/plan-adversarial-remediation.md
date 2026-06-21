# Plan Adversarial Remediation — 2026-06-21

> Closure of Agent 1 (A1-CTX-_) and Agent 2 (A2-QUAL-_) findings. Status: **ALL FIXED**.

## Agent 1 — Context packing

| ID         | Pri | Fix                                                                                                |
| ---------- | --- | -------------------------------------------------------------------------------------------------- |
| A1-CTX-001 | P0  | `implement.jsonl` + MASTER §0.6: four registries + ROUND3 map                                      |
| A1-CTX-002 | P0  | §0.6 bundle: data_sources, source_capability_registry, data_validation_and_conflict, write_manager |
| A1-CTX-003 | P0  | AC-P4-5; §8.6 conflict evidence; source_conflict in manifest                                       |
| A1-CTX-004 | P0  | BATCH3_STAGED_DOWNSTREAM_GATE in manifest; §11 handoff template                                    |
| A1-CTX-005 | P1  | ENV-E1 spec yaml in manifest; §0.2 Request 3                                                       |
| A1-CTX-006 | P1  | §3.3 anti-reuse table; ingestion.py filtered                                                       |
| A1-CTX-007 | P1  | §8.7 phase45 schema; 016F in manifest                                                              |
| A1-CTX-008 | P1  | §0.8 evidence manifest                                                                             |
| A1-CTX-009 | P1  | §0.2 route stop codes                                                                              |
| A1-CTX-010 | P1  | §0.2 dry_run transition                                                                            |
| A1-CTX-011 | P1  | AC-P1-3; §8.3 capability snapshot                                                                  |
| A1-CTX-012 | P1  | AC-REG-2; §11 closeout checklist                                                                   |
| A1-CTX-013 | P2  | §8.7 smoke `--data-root` profile                                                                   |
| A1-CTX-014 | P2  | write_contract.yaml in manifest                                                                    |
| A1-CTX-015 | P2  | source_capability_registry.md manifest                                                             |
| A1-CTX-016 | P2  | input-inventory gap column corrected                                                               |
| A1-CTX-017 | P3  | staged_acceptance_policy filtered                                                                  |
| A1-CTX-018 | N/A | authorization already aligned                                                                      |

## Agent 2 — Plan quality

| ID          | Pri | Fix                                                                |
| ----------- | --- | ------------------------------------------------------------------ |
| A2-QUAL-001 | P0  | §11 Batch 3 handoff field template                                 |
| A2-QUAL-002 | P0  | §8.5a HITL + `phase3_hitl_user_confirmation.md`                    |
| A2-QUAL-003 | P0  | §8.7 phase45_perf_budget.json schema                               |
| A2-QUAL-004 | P0  | AC-P4-5 + §8.6 conflict (dup A1-CTX-003)                           |
| A2-QUAL-005 | P1  | §8.5a/8.5b split; §5 VS 1:1; vertical-slices VS-4/5                |
| A2-QUAL-006 | P1  | §8.1 registry reads (dup A1-CTX-001)                               |
| A2-QUAL-007 | P1  | AC-P0-2 → source risk; AC-P0-2b fail-closed tests                  |
| A2-QUAL-008 | P1  | §8.1 RED → phaseMinus1; auth RED → §8.2                            |
| A2-QUAL-009 | P1  | AUDIT PH-B0 checklist §3.0                                         |
| A2-QUAL-010 | P1  | AUDIT §3.0–3.6 phase bodies                                        |
| A2-QUAL-011 | P2  | §0.11 open items table                                             |
| A2-QUAL-012 | P2  | §0.8 evidence manifest per phase                                   |
| A2-QUAL-013 | P2  | §8.3 phase1_capability_snapshot                                    |
| A2-QUAL-014 | P2  | §8.6 PILOT_PASS_SANDBOX_CLEAN branch note                          |
| A2-QUAL-015 | P2  | §12 skills: api-and-interface-design, verification, detect_changes |
| A2-QUAL-016 | P2  | §10 Tier D–G expanded                                              |
| A2-QUAL-017 | P2  | §0.2 sandbox path table                                            |
| A2-QUAL-018 | P2  | audit.jsonl expanded                                               |
| A2-QUAL-019 | P2  | §9 network pytest marks                                            |
| A2-QUAL-020 | P2  | §8.0 RED path (execute-boot.md) unchanged — valid                  |
| A2-QUAL-021 | P2  | §0.9 progress table                                                |
| A2-QUAL-022 | P2  | §0.9 cninfo defer in §0.9 boundaries                               |
| A2-QUAL-023 | P2  | batch275-live-pilot-gate-tests.md expanded                         |
| A2-QUAL-024 | P2  | audit.jsonl 12 entries                                             |
| A2-QUAL-025 | P3  | integration-ledger rows                                            |
| A2-QUAL-026 | P3  | execute-handoff.md template                                        |
| A2-QUAL-027 | P3  | §0.4 context packing note                                          |
| A2-QUAL-028 | P3  | §4 source_conflict in code map                                     |
| A2-QUAL-029 | P3  | vertical-slices HITL/fetch split                                   |
| A2-QUAL-030 | P3  | AUDIT §4 inspect trace restored                                    |
| A2-QUAL-031 | P3  | AC-P1-3 added                                                      |
| A2-QUAL-032 | P3  | this remediation doc                                               |
| A2-QUAL-033 | P3  | production_live_pilot_policy in implement.jsonl                    |
| A2-QUAL-034 | P3  | §3.3 anti-reuse explicit paths                                     |

**Total:** 52 findings → 51 fixed + 1 N/A (A1-CTX-018). **Zero open.**
