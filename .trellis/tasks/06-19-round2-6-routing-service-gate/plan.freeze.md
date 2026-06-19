# Plan 冻结 — Round2.6 Phase C/D Routing Service Gate

> Execute / Audit 不读；Plan 自检用。

## 1. Phase P0–P5

| Phase | Artifact | Status |
|---|---|---|
| P0a | `research/plan-skill-reads.jsonl` | [x] |
| P0i | `research/input-inventory.md` with `P0i complete` | [x] |
| P0o | `research/original-plan-trace.md` | [x] |
| P0c | `research/plan-boot.md` with `Phase P0 complete` | [x] |
| 1a | `research/project-overview.md` | [x] |
| 1b | `research/gitnexus-summary.md` | [x] static summary; Execute must run live GitNexus |
| 3 | `research/grill-me-session.md` | [x] |
| 5c | `research/integration-ledger.md` | [x] |
| 5d | `research/integration-audit.md`, `research/plan-manifest-audit.md` | [x] |

## 2. Required files

| File | Status |
|---|---|
| `task.json` | [x] |
| `prd.md` | [x] |
| `design.md` | [x] |
| `implement.md` | [x] |
| `MASTER.plan.md` | [x] |
| `AUDIT.plan.md` | [x] |
| `implement.jsonl` | [x] |
| `check.jsonl` | [x] |
| `audit.jsonl` | [x] |

## 3. 双契约 one-pager

| ✓ | Execute（MASTER） | ✓ | Audit（AUDIT） |
|---|---|---|---|
| [x] | §8 RED/GREEN + §9/§10 | [x] | §1 skill freeze + §2 matrix |
| [x] | §10 includes prod-path smoke | [x] | A6/A7/A8 sandbox rows |
| [x] | §12 Execute skills only | [x] | A9 main-session summary |

## 4. Manifest Gate

- [x] `implement.jsonl` first line is MASTER.
- [x] Parent Contract Gate included as prerequisite.
- [x] Phase C implementation files included.
- [x] Phase D smoke/cleanup included.
- [x] Round4 API/frontend/backtest excluded.
- [x] qmt_xqshare enablement excluded.

## 5. Known caveats before `task.py start`

- Parent task audit.report will not exist until Contract Gate is executed; this plan is intentionally prepared in advance.
- Execute must not start unless parent PASS or user override is documented.
- Live GitNexus was not executed during plan authoring; Execute Phase 0 must run it.
- If payload_json cannot satisfy RoutePlan persistence, Execute must stop for ADR/user confirmation before adding migration.
