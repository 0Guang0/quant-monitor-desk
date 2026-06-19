# Execute Boot — 06-19-round2-6-contract-gate

## AC 摘要（来自 MASTER §2）

| ID | 摘要 |
|---|---|
| AC-B1 | source_registry allowed_domain ⊆ source_capabilities |
| AC-B2 | adapter supported_domains reconciled or compatibility map tested |
| AC-B3 | RoutePlan contract tests (disabled/no-source/fallback/null selected) |
| AC-B4 | DataSourceService boundary — no direct adapter factory in api/agents |
| AC-B5 | module boundary checker + tests |
| AC-B6 | data CLI + dependency extras contract tests |
| AC-B7 | platform matrix qmt_xtdata/qmt_xqshare disabled rules |
| AC-B8 | AUDIT_DEFERRED_REGISTRY reconciliation |
| AC-B9 | benchmark handoff to Task 2 (016F) |
| AC-B10 | Phase A self-check migrated to Trellis research |

## implement.jsonl

Every path in `implement.jsonl` was read in full during Phase 0 (27 entries). Evidence: `research/execute-evidence/8.0-boot-reads.txt`.

## §8 执行顺序

8.1 → 8.2 → 8.3 → 8.4 → 8.5 → 8.6 → 8.7 → 8.8 → 8.9 → 8.10 → §9 → §10

## Red Flags（来自 MASTER §7）

- No production DataSourceService / route planner implementation
- No qmt/xqshare enablement
- Business semantic assertions required (not file-exists only)
- No silent xfail on adapter domain mismatch
- No pyproject.toml / migration edits

## §10 验收命令清单

- Tier A: contract test modules + `check_module_boundaries.py` + docs index
- Tier B: `init_db.py` isolated DB under `.audit-sandbox/contract-gate/`
- Tier C: vendor E2E + doc links (or documented blocker)

## Phase 0 complete
