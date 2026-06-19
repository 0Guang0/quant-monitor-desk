# Final Plan Self-Check — Routing Service Gate

## Result

PASS for plan handoff, subject to two start-time gates:

1. `06-19-round2-6-contract-gate` must PASS Audit or the user must explicitly override.
2. `validate-plan-freeze` must be run in a full/trusted shell before `task.py start`.

## Checked

- Task directory contains required Trellis complex-task files: `task.json`, `prd.md`, `design.md`, `implement.md`, `MASTER.plan.md`, `AUDIT.plan.md`, `plan.freeze.md`, `implement.jsonl`, `check.jsonl`, `audit.jsonl`, and research artifacts.
- `implement.jsonl` first entry is `MASTER.plan.md`.
- All plan-time indexed files exist, based on visible repository tree and prior reads.
- Parent Contract Gate artifacts are referenced correctly: `MASTER.plan.md` is hard-indexed because it exists; future `audit.report.md` is not hard-indexed because it does not exist until parent Execute/Audit completes.
- Original Round2.6 task cards are represented with full paths.
- Implementation inputs include datasource adapters, source registry, sync runners/orchestrator, event payload, and production smoke script.
- Scope excludes Round4 API/frontend/backtest work and excludes qmt_xqshare adapter/source enablement.
- Default RoutePlan persistence is `job_event_log.payload_json`; schema migration requires ADR and user approval.

## Issues found and fixed in final review

- Removed hard `implement.jsonl` / `audit.jsonl` references to future parent `audit.report.md` to avoid broken context indexes.
- Rewrote prerequisite rows in `research/input-inventory.md` and `research/integration-ledger.md` so future parent evidence is a runtime gate, not a plan-time broken file path.
- Replaced shortened `016B`–`016F` filenames with full `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016*.md` paths.

## Known validation caveat

`python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/06-19-round2-6-routing-service-gate` was not run because the current CodexPro safe bash allowlist blocks this command. Run it in a full/trusted shell before start.
