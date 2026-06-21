# Batch 2.75 Final Pilot Closeout

> **Generated:** 2026-06-21  
> **Task:** `06-21-round3-batch2-75-live-pilot`  
> **Authorization:** `docs/quality/batch275_user_authorization_2026-06-21.md`

## Pilot outcome

**`PILOT_FAIL_SOURCE`**

Request 2 original approved endpoint (`akshare` / `fetch_daily_bar_validation` / `stock_zh_a_hist` / Eastmoney `push2his.eastmoney.com`) remains unreachable. `PILOT_PASS_RAW_ONLY` was **not** selected because not all three requests have raw evidence under original approved semantics.

## Per-request outcome table

| Request                                    | Approved semantics                     | Phase 3 raw                                                | Phase 4 validation                             | Closeout                                                             |
| ------------------------------------------ | -------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------- | -------------------------------------------------------------------- |
| 1 — baostock `fetch_daily_bar`             | Primary daily bar `sh.600519`          | SUCCESS (9 rows, sandbox)                                  | Structure **PASSED**                           | Partial pilot success                                                |
| 2 — akshare `fetch_daily_bar_validation`   | `stock_zh_a_hist` / Eastmoney push2his | Sidecar file present (`vendor_api=stock_zh_a_daily`, Sina) | Original semantics **SOURCE_ENDPOINT_FAILURE** | **Failed** (endpoint)                                                |
| 3 — akshare `fetch_macro_series` / `DGS10` | Macro supplementary shape only         | SUCCESS (20 rows, sandbox)                                 | Structure **PASSED**                           | Partial pilot success; **FRED primary still deferred** (`B2.5-O-05`) |

## Request 2 original endpoint verdict

Authority: `execute-evidence/eastmoney_stock_zh_a_hist_verdict.md`

- Endpoint: `push2his.eastmoney.com` / `stock_zh_a_hist`
- Verdict: **不可用** (connection/TLS failure)
- Rerun probe (2026-06-21, restored `stock_zh_a_hist` fetch port): **FAIL** (`ProxyError` / unreachable)
- Reconciliation: `execute-evidence/phase3_request2_evidence_reconciliation.md`

## Sina sidecar evidence classification

| Field                           | Value                              |
| ------------------------------- | ---------------------------------- |
| `vendor_api`                    | `stock_zh_a_daily`                 |
| Endpoint                        | `finance.sina.com.cn`              |
| Classification                  | **sidecar / candidate only**       |
| Closes original Request 2?      | **No**                             |
| Supports `PILOT_PASS_RAW_ONLY`? | **No**                             |
| Future work pointer             | `018C_tdx_pytdx_low_cost_probe.md` |

Phase 4 informational baostock vs Sina close diffs are in `phase4_conflict_inspect.txt` and are **not** authoritative for Request 2 closeout.

## Production DB mutation proof

- Phase 3: `phase3_no_production_mutation_proof.md` — all three fetches `hash_unchanged=True`
- Phase 4: `phase4_no_production_mutation_proof.md` — `allow_clean_write=false`, no clean write
- Target: `data/duckdb/quant_monitor.duckdb` — **unchanged**

## Phase 4.5 perf budget

- `phase45_perf_budget.json` — **RE_DEFERRED**
- Owner: `batch275-execute`
- Closure: `scripts/production_equivalent_smoke.py --data-root .audit-sandbox/batch275-perf-smoke`
- Not used as live-source authorization

## Batch 3 handoff (allowed citations)

| Topic                                             | Batch 3 may cite?           | Notes                                                     |
| ------------------------------------------------- | --------------------------- | --------------------------------------------------------- |
| baostock live raw shape for `cn_equity_daily_bar` | **Yes** (sandbox evidence)  | Request 1 only; staged-only downstream gate still applies |
| akshare macro `DGS10` shape probe                 | **Yes** (shape only)        | Does **not** close FRED primary                           |
| Eastmoney `stock_zh_a_hist` validation path       | **No** as PASS              | Endpoint failure                                          |
| Sina `stock_zh_a_daily` sidecar rows              | **No** as Request 2 success | Candidate only; see `018C`                                |
| `PILOT_PASS_RAW_ONLY` / production-live readiness | **No**                      | Closeout is `PILOT_FAIL_SOURCE`                           |
| Production DB live mutation                       | **No**                      | Zero mutation proven                                      |

Reference: `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md` until explicit production-live closeout.

## Remaining deferred items

| ID                      | Owner           | Phase                           | Closure test                                                                              |
| ----------------------- | --------------- | ------------------------------- | ----------------------------------------------------------------------------------------- |
| `B2.5-O-05`             | Batch 2.75+     | FRED primary for `ENV-E1-DGS10` | User-authorized FRED live + evidence; Request 3 does not close                            |
| `R3-B25-PERF-BUDGET-01` | Execute / CI    | 4.5 re-defer                    | `production_equivalent_smoke.py` PASS in `.audit-sandbox/batch275-perf-smoke`             |
| `R3-B25-HYG-03`         | Execute / CI    | 4.5 re-defer                    | Same smoke artifact refresh                                                               |
| `R3-B2.75-REQ2-EM`      | Platform / 018C | Batch 2.75 follow-up            | Eastmoney `stock_zh_a_hist` reachable **or** approved alternate validation path in `018C` |

## Evidence index

- `phase3_request2_evidence_reconciliation.md`
- `eastmoney_stock_zh_a_hist_verdict.md`
- `phase3_raw_micro_fetch_evidence.json`
- `phase4_validation_report.json`
- `phase4_conflict_inspect.txt`
- `phase45_perf_budget.json`
- `final_registry_update.md`
- `final_pytest_output.txt`
