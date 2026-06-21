# Project Overview — Batch 2.75 (Plan 1a)

## What this batch is

A **narrow live-data pilot gate** between Batch 2.5 (staged Layer 1 ingestion) and Batch 3 (Layer 2 modeling). It validates real vendor shape for three approved micro-requests without opening production data access or mutating `data/duckdb/quant_monitor.duckdb`.

## Current code anchors

| Module                  | Role in pilot                                               |
| ----------------------- | ----------------------------------------------------------- |
| `DataSourceService`     | route → guard → adapter → fetch_log                         |
| `SourceRoutePlanner`    | Phase 2 `READY` / failure statuses                          |
| `DbInspector`           | Phase 1/3 before-after inventory                            |
| `ResourceGuard`         | eco pause before fetch                                      |
| `ingestion_evidence.py` | **Batch 2.5 only** (staged fixture) — do not reuse for live |

## Gap to close

No `live_pilot` orchestration module; no `test_batch275_live_pilot_gate.py`; `R3-B2.75-01` DEFERRED; authorization file now exists at `docs/quality/batch275_user_authorization_2026-06-21.md`.

## Risk

Mixing live pilot with ingestion R2b–R2d in same sprint; promoting staged Batch 2.5 evidence to production-live; silent fixture fallback.
