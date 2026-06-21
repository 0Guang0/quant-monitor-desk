# Phase 0 Authorization Record — Batch 2.75

> Execute §8.2 · AC-P0-1..4 · 2026-06-21

## Authorization evidence

| Field             | Value                                                    |
| ----------------- | -------------------------------------------------------- |
| Path              | `docs/quality/batch275_user_authorization_2026-06-21.md` |
| Approved by       | User (project owner)                                     |
| Approved on       | 2026-06-21                                               |
| Sprint constraint | No ingestion R2b–R2d in same sprint                      |

## Wired defaults (fail-closed)

| Control             | Value                                                                      |
| ------------------- | -------------------------------------------------------------------------- |
| `dry_run`           | `true` (route preview); live fetch sets `false` only in sandbox after HITL |
| `raw_only`          | `true`                                                                     |
| `write_target`      | `sandbox` (`.audit-sandbox/batch275-live-pilot/`)                          |
| `allow_clean_write` | `false`                                                                    |
| Production DB       | read-only inspect; no mutation                                             |
| Row cap             | ≤100 (approved requests ≤40 total)                                         |

## Three approved micro-pilot requests

| #   | source_id | data_domain         | operation                  | symbol    | max_rows |
| --- | --------- | ------------------- | -------------------------- | --------- | -------- |
| 1   | baostock  | cn_equity_daily_bar | fetch_daily_bar            | sh.600519 | 10       |
| 2   | akshare   | cn_equity_daily_bar | fetch_daily_bar_validation | sh.600519 | 10       |
| 3   | akshare   | macro_supplementary | fetch_macro_series         | DGS10     | 20       |

Request 2: validation-only — must not promote to Primary.  
Request 3: shape probe only — does **not** close FRED primary for ENV-E1-DGS10.

## Source risk rationale (AC-P0-2)

| Source                       | Pilot role                                   | Risk vs QMT/FRED/Yahoo                                                                                                                   |
| ---------------------------- | -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **baostock**                 | Request 1 primary daily bar                  | Open HTTP API; no broker terminal; bounded single-symbol window; lower credential/terminal risk than **qmt**                             |
| **akshare**                  | Request 2 validation + Request 3 macro shape | Aggregator with declared validation/supplementary roles; still bounded rows; lower than **fred** primary or **yahoo** production primary |
| **qmt_xtdata / qmt_xqshare** | **Not authorized**                           | Requires terminal/env + user config; D-11 default disabled                                                                               |
| **yahoo_finance**            | **Not authorized**                           | Auxiliary only per policy; not in three-request set                                                                                      |
| **fred**                     | **Not authorized as source_id**              | FRED primary for DGS10 remains deferred (B2.5-O-05); Request 3 uses akshare shape only                                                   |

Rationale: first live pass uses lowest-friction, registry-aligned sources with explicit user authorization and sandbox isolation before any higher-trust primary (FRED) or terminal (QMT) access.

## Fail-closed enforcement

- `validate_authorization()` in `backend/app/ops/live_pilot.py` checks evidence file, approved triple, defaults, and disabled sources.
- `run_live_pilot_raw_only()` calls gate before any `DataSourceService.fetch`.
- Tests: `test_livePilot_missingAuthorization_blocksBeforeFetch`, `test_livePilot_disabledSource_blocksBeforeFetch`.

## Phase 0 outcome

Authorization wired. Proceed to §8.3 Phase 1 read-only baseline.
