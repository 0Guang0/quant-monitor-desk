# Final Plan Self-Check — Contract Gate

## Result

PASS for plan handoff, subject to running `validate-plan-freeze` in a full/trusted shell before `task.py start`.

## Checked

- Task directory contains required Trellis complex-task files: `task.json`, `prd.md`, `design.md`, `implement.md`, `MASTER.plan.md`, `AUDIT.plan.md`, `plan.freeze.md`, `implement.jsonl`, `check.jsonl`, `audit.jsonl`, and research artifacts.
- `implement.jsonl` first entry is `MASTER.plan.md`.
- All original Round2.6 task cards 016A–016F are represented with full paths in implementation context.
- Global inputs are indexed: `README.md`, `GLOBAL_EXECUTION_RULES.md`, `GLOBAL_TESTING_POLICY.md`, `GLOBAL_RESOURCE_LIMITS.md`, `GLOBAL_TASK_TEMPLATE.md`.
- Contract inputs are indexed: source capability, source route, datasource service, module boundary, platform matrix, data CLI, dependency extras, reference guardrails.
- Scope excludes production DataSourceService implementation; that belongs to `06-19-round2-6-routing-service-gate`.
- Root `ROUND2_6_PHASE_A_SELF_CHECK.md` is indexed only as migration source and exists at plan time.

## Issues found and fixed in final review

- Input inventory originally used shortened `016A`–`016F` filenames. Replaced them with full `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016*.md` paths.

## Known validation caveat

`python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/06-19-round2-6-contract-gate` was not run because the current CodexPro safe bash allowlist blocks this command. Run it in a full/trusted shell before start.
