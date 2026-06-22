# PROMPT_14 merge gate report — feature/round3-real-data-staged-pilot

> Generated: 2026-06-22  
> Pilot ID: `r3x-staged-pilot-20260622`  
> Outcome: **PILOT_PASS_STAGED_RAW** (partial — akshare validation NETWORK_ERROR)

## Scope

| Item | Value |
| ---- | ----- |
| Branch | `feature/round3-real-data-staged-pilot` |
| Base | `master` @ `b200e03c` |
| Run mode | `staged_only` / sandbox raw + staging evidence |
| Production clean write | **false** |
| Production-live readiness | **not claimed** |

## Changed files (implementation)

- `docs/quality/prompt14_user_authorization_2026-06-22.md` — user authorization evidence
- `backend/app/ops/staged_pilot.py` — staged pilot orchestrator
- `backend/app/ops/staged_pilot_fetch_ports.py` — baostock/akshare/cninfo fetch ports
- `scripts/run_staged_pilot.py` — thin CLI wrapper
- `tests/test_staged_pilot.py` — fail-closed gate tests
- `tests/contract_gate_support.py` — allow staged_pilot adapter factory path

## Source / domain results

| Request | Source | Domain | Operation | Fetch | Rows | Taxonomy |
| ------- | ------ | ------ | --------- | ----- | ---- | -------- |
| staged-req-1 | baostock | cn_equity_daily_bar | fetch_daily_bar | SUCCESS | 10 | SUCCESS |
| staged-req-2 | akshare | cn_equity_daily_bar | fetch_daily_bar_validation | NETWORK_ERROR | 0 | NETWORK_ERROR |
| staged-req-3 | cninfo | cn_announcements | fetch_announcement_index | SUCCESS | 7 | SUCCESS |

### akshare re-defer

Request 2 failed with `NETWORK_ERROR` (proxy/direct both failed in current environment). **Re-defer** akshare equity validation live shape until network/proxy path is stable; baostock primary + cninfo metadata evidence is sufficient for staged pilot closeout.

## Evidence paths

| Artifact | Path |
| -------- | ---- |
| Route preview matrix | `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/route_preview_matrix.json` |
| Fetch summary | `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/source_fetch_attempt_summary.json` |
| Raw manifest | `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/raw_evidence_manifest.json` |
| Staging manifest | `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/staging_evidence_manifest.json` |
| Validation report | `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/validation_report_summary.json` |
| ResourceGuard caps | `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/resource_guard_caps.json` |
| No-mutation proof | `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/production_db_no_mutation_proof.md` |
| Closeout | `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/pilot_closeout.json` |
| RED (SP-01) | `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/SP-01-red.txt` |
| GREEN (SP-01) | `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/SP-01-green.txt` |

## Production DB no-mutation

- Production DB path: `data/duckdb/quant_monitor.duckdb` (absent in worktree — hash/count proof `unchanged=true`)
- Sandbox writes only under `.audit-sandbox/r3x-staged-pilot/`
- `allow_clean_write=false` on all pilot requests

## Verification

```text
uv run python -m pytest tests/test_staged_pilot.py -q  # 11 passed
uv run python -m pytest tests/test_source_capabilities.py tests/test_source_route_planner.py tests/test_datasource_service.py tests/test_data_adapter_contract.py tests/test_raw_store.py tests/test_db_validation_gate.py tests/test_ops_db_inspector.py tests/test_production_live_pilot_policy.py -q  # passed (1 skipped)
uv run python -m pytest -q  # full suite passed
```

## Next expansion / re-defer

| Source | Recommendation |
| ------ | -------------- |
| baostock | Expand trade-day window cautiously after review |
| cninfo | Metadata pilot OK; PDF fetch remains deferred |
| akshare validation | Re-defer until network/proxy stable; retry with `stock_zh_a_hist` sidecar |
| tdx/qmt/yahoo/fred | Remain deferred per authorization |

## Merge gate

- [x] Bounded caps enforced (symbols≤3, rows≤10/request, network≤10)
- [x] At least one source produced staged/raw evidence
- [x] Failed source has explicit taxonomy
- [x] No production clean write
- [x] No production-live readiness claim
- [ ] Commit on branch (main session — implement agent does not commit)
