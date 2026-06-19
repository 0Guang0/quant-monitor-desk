# Plan 冻结 — Round2.6 Phase B Contract Gate

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
| [x] | §8 RED/GREEN + §9/§10 | [x] | §1 skill freeze + §2 dimension matrix |
| [x] | §10 Execute-only, B/C prod-path | [x] | Audit sandbox/prod-path rows where relevant |
| [x] | §12 Execute skills only | [x] | A9 main-session summary |

## 4. Manifest Gate

- [x] `implement.jsonl` first line is MASTER.
- [x] Global files included.
- [x] Six Round2.6 task cards included.
- [x] Key specs/contracts included.
- [x] Root self-check included as migration input.
- [x] Follow-up Task 2 identified.

## 5. Known caveats before `task.py start`

- Live GitNexus was not executed during plan authoring; Execute Phase 0 must run it.
- `validate-plan-freeze` should be run after both Task 1 and Task 2 plan files are written.
- If `python scripts/check_doc_links.py` is blocked by local allowlist during Execute, record exact blocker and run `pytest tests/test_documentation_index.py -q` as partial substitute, without claiming full link-check PASS.
