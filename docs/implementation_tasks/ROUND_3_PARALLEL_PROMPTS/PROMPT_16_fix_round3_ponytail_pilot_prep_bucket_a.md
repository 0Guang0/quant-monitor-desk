# PROMPT_16 — fix/round3-ponytail-pilot-prep-bucket-a

## Setup

- Branch: `fix/round3-ponytail-pilot-prep-bucket-a`
- Base: `master` @ `d1a15e4b`
- Worktree: `../quant-monitor-desk-wt-fix-r3-ponytail-pilot-prep`
- Task card: `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_ponytail_pilot_prep_bucket_a.md`

## Mission

Close **Bucket A** ponytail pilot-prep items (DS-01/02/03, SC-02, OP-02 minimal, SY-04, VA-03, DB-03 if still duplicated). Prepare trustworthy paths for PROMPT_14 without structural refactors.

## Mandatory reads before code

1. Task card above
2. `docs/quality/PONYTAIL_MODULE_SCAN_20260622.md` §4.2 DS, §4.4 SY-04, §4.5 OP-02, §4.7 SC-02, §4.7 VA-03
3. `/karpathy-guidelines`, `/testing-guidelines`, `/tdd`, `/ponytail` (full)

## User-mandatory engineering rules

- **TDD only** for every behavior change
- **Ponytail full**: shortest diff, no unrequested abstractions
- **Every test** must document in docstring: 覆盖范围、测试对象、目的/目标
- **Never** weaken test intent to pass; fix production code or adjust assertion to match **documented contract**
- **No** production DB mutation, **no** live network fetch, **no** real vendor calls
- GitNexus `impact()` before symbol edits

## Deliverables

- `.trellis/tasks/fix-round3-ponytail-pilot-prep-bucket-a/execute-evidence/merge_gate_report.md`
- RED/GREEN evidence per item
- Full `pytest -q` green
- One commit; do not merge/push
