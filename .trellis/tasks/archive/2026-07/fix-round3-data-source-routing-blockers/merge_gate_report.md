# Merge report — fix/round3-data-source-routing-blockers

## Branch

| Field        | Value                                                                 |
| ------------ | --------------------------------------------------------------------- |
| Branch       | `fix/round3-data-source-routing-blockers`                             |
| Worktree     | `15ez` (implementation); suggested alt: `../quant-monitor-desk-wt-fix-r3-data-source-routing-blockers` |
| Base         | `master` @ `8961691a`                                                 |
| Target merge | `integration/round3`                                                  |
| Source ID    | R3X_data_source_routing_blockers / ADV-A2 cluster                       |
| Task card    | `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_data_source_routing_blockers.md` |

## Scope

Minimal data-source routing blocker repair for staged pilot readiness. **No production-live enablement.** Disabled/validation-only boundaries preserved.

## Audit items addressed

| ID         | Severity | Resolution |
| ---------- | -------- | ---------- |
| ADV-A2-001 | HIGH     | `data_adapter_contract.md` syncs `DISABLED_SOURCE` / `NOT_PUBLISHED_YET` |
| ADV-A2-003 | HIGH     | Added `domain_roles` for 10 missing declared domains |
| ADV-A2-005 | MEDIUM   | `_default_operation()` maps all `domain_roles` keys |
| ADV-A2-006 | MEDIUM   | `platform_source_matrix.yaml` adds cninfo / yahoo_finance / tdx_pytdx |
| ADV-A2-007 | MEDIUM   | `DataSourceService.fetch()` records `REQUESTED_SOURCE_OVERRIDDEN_BY_ROUTE` + `requested_source_id` |

## Deferred (out of scope)

| ID         | Reason |
| ---------- | ------ |
| ADV-A2-002 | health_check() — design-only gap |
| ADV-A2-004 | cninfo adapter domain gap — adapter implementation debt |
| ADV-A2-009 | TdxPytdxAdapter factory registration — disabled-by-default; no enablement |
| ADV-A2-010 | BaseDataAdapter guard hardening — separate slice |
| ADV-A2-012 | platform matrix reload perf — non-blocker |

## Changed files

| File | Change |
| ---- | ------ |
| `specs/contracts/data_adapter_contract.md` | FetchResult status union |
| `specs/datasource_registry/source_registry.yaml` | 10 new `domain_roles` entries |
| `specs/contracts/platform_source_matrix.yaml` | cninfo / yahoo_finance / tdx_pytdx per platform |
| `backend/app/datasources/route_models.py` | `requested_source_id` on SourceRoutePlan |
| `backend/app/datasources/route_planner.py` | DISABLED_SOURCE priority for tdx_pytdx / disabled primary |
| `backend/app/datasources/service.py` | `_default_operation`, route override audit |
| `tests/test_r3x_data_source_routing_blockers.py` | New ADV-A2 blocker tests |
| `tests/test_datasource_service.py` | Source override audit test |
| `tests/test_data_adapter_contract.py` | DISABLED_SOURCE contract coverage |
| `tests/test_source_route_planner.py` | USER_AUTH_REQUIRED test alignment |

## Current batch evidence

| Branch | Status |
| ------ | ------ |
| `feature/round3-019-layer2-sensor` | `MISSING_CURRENT_BATCH_EVIDENCE` in this worktree (not merged locally) |
| `feature/round3-023a-evidence-foundation` | `MISSING_CURRENT_BATCH_EVIDENCE` |
| `review/round3-019-plan-audit` | `MISSING_CURRENT_BATCH_EVIDENCE` |
| `debt/r3b275-018c-live-manual-probe-plan` | Present on base @ 8961691a (planning-only) |

## Tests run

```bash
pytest tests/test_source_capabilities.py -q
pytest tests/test_source_route_planner.py -q
pytest tests/test_datasource_service.py -q
pytest tests/test_data_adapter_contract.py -q
pytest tests/test_platform_source_matrix.py -q
pytest tests/test_production_live_pilot_policy.py -q
pytest tests/test_r3x_data_source_routing_blockers.py -q
pytest tests/test_interface_probe_018c.py -q
python scripts/check_doc_links.py
# All passed
```

## Data safety

| Check | Status |
| ----- | ------ |
| Production DB mutation | None |
| Live network fetch | None |
| tdx_pytdx default enable | Not changed (remains disabled) |
| QMT / xqshare / Yahoo default enable | Not changed |
| production-live readiness claim | None |

## Registry

Untouched (`AUDIT_DEFERRED_REGISTRY.md`, `UNRESOLVED_ISSUES_REGISTRY.md`).

## Semantics

Fixes route-preview trust for declared domains under **staged-only** posture. Does **not** open production-live data access or close Eastmoney hist Request 2.

## Remaining deferred source/domain items

- `cn_filings` / `cn_pdf_reports`: cninfo adapter domain implementation gap (ADV-A2-004)
- `tdx_pytdx` domains: remain `DISABLED_SOURCE` until explicit user authorization
- `cn_equity_realtime` / `cn_equity_minute_bar`: QMT local authorization required
- `us_equity_daily_bar` / `etf_daily_bar` / `global_asset_reference`: Yahoo validation-only, user confirmation required
- `akshare` index/sector domains: validation-only primary; clean-write requires quality_flags
