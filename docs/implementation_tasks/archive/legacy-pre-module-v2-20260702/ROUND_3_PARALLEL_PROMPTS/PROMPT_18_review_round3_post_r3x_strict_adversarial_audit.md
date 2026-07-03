# PROMPT_18 — review/round3-post-r3x-strict-adversarial-audit

Use this prompt in a fresh review session. Create the review branch/worktree first, then execute the strict post-R3X adversarial audit task.

## 1. Branch / worktree setup

- Branch to create: `review/round3-post-r3x-strict-adversarial-audit`
- Base branch: latest user-confirmed `master` after mainline closeout
- Suggested worktree path: `../quant-monitor-desk-wt-review-r3-post-r3x-strict-audit`
- Target merge: no implementation merge; only archive report if user approves

Before starting, confirm:

- Mainline closeout is visible in `ROUND3_BATCH_IMPLEMENTATION_MAP.md` and registries.
- Existing dirty files are not overwritten.
- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_post_r3x_strict_adversarial_audit.md` exists.

## 2. Mission

Perform a strict read-only adversarial audit after R3X/PROMPT_11–17. Do not repeat shallow review. Your job is to disprove or verify closed/fixed claims and decide whether the project may proceed to real-data staged pilot v2 and read-only data health v1.

This is a review branch. Do not modify implementation code, specs, docs, registry, or DB to make findings disappear.

## 3. Required task card

Read and follow exactly:

- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_post_r3x_strict_adversarial_audit.md`

## 4. Mandatory /to-issues slicing

During plan stage, use `/to-issues` and create vertical issue slices matching the task card:

- R3Y-AUD-01 closed claims反证
- R3Y-AUD-02 source route / DataSourceService反证
- R3Y-AUD-03 write / validation / conflict反证
- R3Y-AUD-04 real-data staged pilot反证
- R3Y-AUD-05 lineage / evidence foundation反证
- R3Y-AUD-06 registry consistency反证
- R3Y-AUD-07 test quality反证
- R3Y-AUD-08 go/no-go gate

Each issue must have its own evidence, conclusion, and PASS/WARN/BLOCK. A single generic report is not sufficient.

## 5. Required read index

At minimum read and summarize all required files from the task card, especially:

- `AGENTS.md`, `CLAUDE.md`, `.trellis/workflow.md`
- `.trellis/spec/guides/complex-task-planning-protocol.md`
- `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`
- `docs/RESOLVED_ISSUES_REGISTRY.md`
- `docs/quality/adversarial_audit_report.md`
- `docs/quality/adversarial_audit_post14_contract_ponytail_lane.md`
- `docs/quality/PONYTAIL_MODULE_SCAN_20260622.md`
- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_*`
- `docs/implementation_tasks/ROUND_3_PARALLEL_PROMPTS/PROMPT_11*` through `PROMPT_17*`
- `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/`
- `.trellis/tasks/fix-round3-r3x-residual-open-items-closure/execute-evidence/merge_gate_report.md`
- `.trellis/tasks/fix-round3-ponytail-pilot-prep-bucket-a/execute-evidence/merge_gate_report.md`
- `specs/contracts/`, `specs/datasource_registry/`, `backend/app/`, `tests/`

Do not stop at this index. Follow references, imports, call paths, contract authority, merge reports, and tests before judging.

## 6. Forbidden behavior

- No implementation changes.
- No spec/doc edits to alter findings.
- No production DB writes.
- No migration execution.
- No source fetch.
- No enabling disabled or authorization-required sources.
- No full market/full history scan.
- No accepting merge reports as facts without verification.

## 7. Suggested verification

Run only safe read-oriented tests:

```bash
python -m pytest tests/test_r3x_residual_open_items_closure.py -q
python -m pytest tests/test_staged_pilot.py -q
python -m pytest tests/test_datasource_service.py tests/test_source_route_planner.py tests/test_source_capabilities.py -q
python -m pytest tests/test_db_validation_gate.py tests/test_write_manager.py tests/test_raw_store.py -q
python -m pytest tests/test_layer2_sensor_loader.py tests/test_layer5_evidence_foundation.py -q
python -m pytest tests/test_round3_audit_registry_alignment.py -q
python scripts/check_doc_links.py
```

If any command is unsafe or unavailable, record why.

## 8. Done criteria

- All `/to-issues` slices completed.
- Final gate is one of: `PASS_ALLOW_NEXT_BATCH`, `WARN_ALLOW_WITH_CONTROLS`, `BLOCK_FIX_FIRST`.
- Explicit recommendation on whether staged pilot v2 and data health v1 may proceed.
- All HIGH/WARN findings cite exact files and observed behavior.
