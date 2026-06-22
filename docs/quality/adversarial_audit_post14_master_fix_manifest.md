# Post-14 Master Fix Manifest — 零遗漏

> Coordinator verified @ master `5c16c675`  
> Sources: `adversarial_audit_post14_ops_data_lane.md`, `adversarial_audit_post14_contract_ponytail_lane.md`  
> **Hard constraint:** do NOT close `R3-B2.75-REQ2-EM`

## Slice 1 — `fix/round3-post14-audit-staged-pilot`

| ID                   | Verified                                            | Fix owner                              |
| -------------------- | --------------------------------------------------- | -------------------------------------- |
| ADV-POST14-A-001     | YES `mutation_proof.py:13`                          | mutation_proof + staged_pilot closeout |
| ADV-POST14-A-002     | YES no conflict in staged_pilot                     | conflict step or defer artifact        |
| ADV-POST14-A-003     | YES akshare vendor for cninfo                       | vendor_api in evidence                 |
| ADV-POST14-A-004     | YES dual register path                              | single path + quality_flag             |
| ADV-POST14-A-005     | YES 14 calendar days                                | bind date_window                       |
| ADV-POST14-A-006     | YES shallow validation                              | sandbox validators                     |
| ADV-POST14-A-007     | PARTIAL grep shows False at 876; verify stub at 501 | can_write_clean=False                  |
| ADV-POST14-A-008     | route override flag in evidence                     | staged_pilot                           |
| ADV-POST14-A-011     | YES                                                 | test_staged_pilot.py TDD               |
| ADV-POST14-A-012     | YES                                                 | test_production_live_pilot_policy.py   |
| ADV-POST14-A-013–019 | LOW batch                                           | staged_pilot + evidence paths          |
| ADV-POST14-B-002     | YES staged_evidence INSERT                          | unify with A-004                       |
| ADV-POST14-B-007     | YES phase3 bypass                                   | document or WriteManager path          |

## Slice 2 — `fix/round3-post14-audit-registry-docs`

| ID               | Verified                     | Fix owner                                  |
| ---------------- | ---------------------------- | ------------------------------------------ |
| ADV-POST14-A-009 | YES no PROMPT_14 in registry | AUDIT_DEFERRED + UNRESOLVED                |
| ADV-POST14-A-010 | cross-ref REQ2-EM            | registry narrative                         |
| ADV-POST14-A-016 | closeout narrative           | pilot_closeout evidence regen note in docs |
| ADV-POST14-B-001 | YES report contradicts       | adversarial_audit_report.md RESOLVED sync  |
| ADV-POST14-B-003 | SC-05 semantics              | ponytail scan + merge_gate note            |
| ADV-POST14-B-004 | YES R3-PARTIAL-1 stale       | RESOLVED or rewrite defer                  |
| ADV-POST14-B-005 | database-guidelines drift    | spec fix                                   |
| ADV-POST14-B-006 | ponytail scan stale          | add post-16/17 delta section               |
| ADV-POST14-B-011 | akshare validation defer     | new registry row                           |

## Slice 3 — `fix/round3-post14-audit-test-gaps`

| ID               | Fix owner                              |
| ---------------- | -------------------------------------- |
| ADV-POST14-B-026 | test_data_quality_validator docstrings |
| ADV-POST14-B-027 | ops inspector --limit tests            |
| ADV-POST14-B-028 | test_ops_interface_probe.py            |

## Slice 4 — `debt/round3-ponytail-structural-bucket-b` (53 items)

All ADV-POST14-B-008–B-025 STILL-OPEN structural + ponytail §4 Bucket B:

- B-008 write_contract modes
- B-009 health_check stub docs/tests
- B-010 DS-04/05 triple validation
- B-012 L1-01 re-export
- B-013 L1-02/03 commit monolith
- B-014 OP-01 live_pilot split
- B-015 SC-01/L2-01/02 lineage kernel
- B-016 SY-01 backfill monolith
- B-017 DB-01 WriteManager
- B-018–B-025 all remaining LOW/MED per ponytail scan §4

**Exclude from slice 4 if slice 1 merged:** B-007 staged bypass (coordinate after slice 1).
