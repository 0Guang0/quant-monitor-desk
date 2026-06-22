# PROMPT_17 — debt/round3-ponytail-low-touch

## Setup

- Branch: `debt/round3-ponytail-low-touch`
- Base: `master` @ 协调者指定（PROMPT_16 + map checkpoint 之后）
- Worktree: `../quant-monitor-desk-wt-debt-r3-ponytail-low-touch`
- Task card: `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_ponytail_low_touch_bucket_c.md`

## Mission

Close **Bucket C** ponytail low-touch items (VA-01/02/07/08, SC-03/04/05/06). Parallel with PROMPT_14; **no** ops/datasources/storage/db/sync edits.

## Mandatory reads before code

1. Task card above
2. `docs/quality/PONYTAIL_MODULE_SCAN_20260622.md` §4.7–4.8
3. `.trellis/spec/guides/round3-repair-debt-worktree-plan.md` §6 core-file locks
4. `/karpathy-guidelines`, `/testing-guidelines`, `/tdd`, `/ponytail` (full)

## User-mandatory engineering rules

- **TDD only** for every behavior change
- **Ponytail full**: shortest diff, no unrequested abstractions
- **Every test** must document in docstring: 覆盖范围、测试对象、目的/目标
- **Never** weaken test intent to pass
- **No** production DB mutation, **no** live network fetch
- GitNexus `impact()` before symbol edits

## Deliverables

- `.trellis/tasks/debt-round3-ponytail-low-touch/execute-evidence/merge_gate_report.md`
- RED/GREEN evidence per item
- Full `pytest -q` green
- One commit; do not merge/push
