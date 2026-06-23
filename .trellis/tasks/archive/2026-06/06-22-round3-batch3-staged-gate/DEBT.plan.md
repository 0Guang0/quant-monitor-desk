# Repair/Debt Lite Plan — round3-batch3-staged-gate

## Source of truth

- audit / registry ID: `R3-B3-STAGED-DOWNSTREAM-GATE`
- base branch: `master` @ `7729419d`
- target branch: `integration/round3`
- worktree: `../quant-monitor-desk-wt-r3-batch3-staged-gate`
- owner agent: PROMPT_01 staged-gate session

## Boundary

- allowed files: `BATCH3_STAGED_DOWNSTREAM_GATE.md`, `ROUND3_HANDOFF.md`, `ROUND3_BATCH_IMPLEMENTATION_MAP.md`, `tests/test_batch3_staged_downstream_gate.py`, task evidence
- forbidden: backend runtime, registry edits, live fetch, `019` implementation, `018C` implementation
- production/data boundary: docs/tests only; no DB mutation

## Required decision record

| Decision                 | State                            |
| ------------------------ | -------------------------------- |
| Batch 2.75 closeout      | `PILOT_FAIL_SOURCE`              |
| Request 2 Eastmoney hist | `R3-B2.75-REQ2-EM` deferred      |
| Batch 3 / `019`          | staged-only only                 |
| This branch evidence     | does not open production-live    |
| `018C` parallel          | does not unblock production-live |

## Merge gate

- 22 targeted tests: 20 passed, 2 skipped (local DB absent)
- `check_doc_links.py`: OK
- no backend / no registry / no production DB mutation
