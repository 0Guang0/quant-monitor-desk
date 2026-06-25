# Batch 3F User Authorization — FRED Live Primary Pilot (R3F-SH-06)

> Status: user-approved authorization record for Round 3F Batch 3F.3 (`R3F-SH-06` / `B2.5-O-05`).  
> This file is **authorization evidence only**; it does not enable network fetch or production DB mutation by itself. Execute must still pass fail-closed gates in `LivePilotRequest`, `production_live_pilot_policy.md`, and policy tests.

## Authorization scope

| Field             | Value                                                                                                |
| ----------------- | ---------------------------------------------------------------------------------------------------- |
| Batch             | Round 3F — Batch 3F.3 Source Health & Quality Runners                                                |
| Playbook ID       | `B3F-SH`                                                                                             |
| Task              | `R3F-SH-06` — FRED live primary closeout (`B2.5-O-05`)                                               |
| Policy            | `docs/quality/production_live_pilot_policy.md`                                                       |
| Approved by       | User (project owner)                                                                                 |
| Approved on       | 2026-06-25                                                                                           |
| Coordinator       | Batch 3F main session                                                                                |
| Sprint constraint | **FRED-only**; no TDX/QMT/xqshare/Yahoo; no production clean write; no full-market/full-history scan |

## Global defaults (every live request)

| Control                 | Approved value                                                                    |
| ----------------------- | --------------------------------------------------------------------------------- |
| `dry_run`               | `true` for route preview; live fetch only after route READY and with YAML present |
| `raw_only`              | `true` for first live pass                                                        |
| `write_target`          | `sandbox` under `.audit-sandbox/batch3f-fred-live-pilot/`                         |
| `allow_clean_write`     | `false`                                                                           |
| Production DB           | `data/duckdb/quant_monitor.duckdb` — **read-only inspect only**; no mutation      |
| Total row cap           | `<= 100`                                                                          |
| Fixture/staged fallback | **Forbidden** for live pilot evidence                                             |
| `api_key_env`           | `FRED_API_KEY` (must be set by operator; not committed)                           |

## Approved micro-pilot request — FRED primary macro series

| Field                   | Value                                                          |
| ----------------------- | -------------------------------------------------------------- |
| `source_id`             | `fred`                                                         |
| `data_domain`           | `macro_series`                                                 |
| `operation`             | `fetch_macro_series`                                           |
| `symbols_or_indicators` | `DGS10` (default); optional tiny allowlist: `T10Y3M`, `VIXCLS` |
| `date_window`           | recent 3 years or shorter bounded window                       |
| `max_rows`              | `100`                                                          |
| `max_calls`             | `10`                                                           |

## Machine-readable companion

YAML: `.trellis/tasks/round3-source-health-and-quality-runners/execute-evidence/fred_live_authorization_2026-06-25.yaml`

## Explicit prohibitions

- No production clean write
- No enablement of TDX, QMT, xqshare, or Yahoo
- No claim of production-live readiness from this pilot alone
- AkShare / Eastmoney evidence must not close `R3-B2.75-REQ2-EM` or `R3-PROMPT14-AKSHARE-VAL-01`
