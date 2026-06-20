# A6 audit-perf — §4.6

> Agent: **audit-perf (A6)** · Round 3 Batch 2.5 · 2026-06-20  
> Skills: systematic-debugging + doubt-driven-development  
> Protocol: AUDIT.plan §2.2 A6 · MASTER §10 eco · `resource_limits.yaml` · `GLOBAL_RESOURCE_LIMITS.md`

**Verdict: PASS**

## Scope

Single-indicator micro-fetch staging for frozen indicator `ENV-E1-DGS10` (`as_of=2024-06-15`), staged `macro_supplementary.fetch_macro_series` route (B2.5-O-05 FRED deferred), `QMD_RESOURCE_PROFILE=eco`, `ResourceGuard.check()` before fetch inside writer txn (`ingestion.py` `micro_fetch_staging`).

## Thresholds (AUDIT.plan §2.2 A6)

| Metric  | Limit   | Source                         |
| ------- | ------- | ------------------------------ |
| elapsed | ≤ 5 s   | AUDIT.plan §2.2 A6             |
| RSS     | ≤ 512MB | AUDIT.plan §2.2 A6             |
| profile | eco     | `configs/resource_limits.yaml` |

Eco profile contract: `process_rss_hard_stop_mb=1800` (contract); audit gate uses stricter 512MB ceiling for micro-window acceptance.

## Measured results

| Environment     | Data root                                    | elapsed_s | rss_after_mb | peak_traced | fetch           | ResourceGuard | Pass |
| --------------- | -------------------------------------------- | --------- | ------------ | ----------- | --------------- | ------------- | ---- |
| cli-sandbox     | `.audit-sandbox/r3b25-audit/data`            | **0.430** | **57.67**    | 319491 B    | SUCCESS (1 row) | OK            | ✓    |
| audit-prod-path | `.audit-sandbox/r3b25-audit-prod-equiv/data` | **0.444** | **58.09**    | 319491 B    | SUCCESS (1 row) | OK            | ✓    |

Both environments satisfy elapsed ≤ 5s and RSS ≤ 512MB.

## Environment setup

### cli-sandbox

1. Wipe/recreate `.audit-sandbox/r3b25-audit/data`
2. `QMD_DATA_ROOT=.audit-sandbox/r3b25-audit/data python scripts/init_db.py`
3. `build_staged_fixture_service` + `Layer1ObservationIngestionService.micro_fetch_staging`

### audit-prod-path

1. `shutil.copytree(data/ → .audit-sandbox/r3b25-audit-prod-equiv/data)` (copy only)
2. Same micro-fetch on prod-shaped data copy; **project `data/` tree not written**

### Prod integrity

| Check                 | Value                                                              |
| --------------------- | ------------------------------------------------------------------ |
| prod DB SHA256 before | `5EB65E0EDAAAB223A77C5A5D2660603383836704B4C0ECE1EB4AEBB047F1682E` |
| prod DB SHA256 after  | `5EB65E0EDAAAB223A77C5A5D2660603383836704B4C0ECE1EB4AEBB047F1682E` |
| prod tree modified    | **no**                                                             |

## Cross-check vs Execute evidence

| Field                   | Execute (`phase3_micro_fetch_evidence.json`) | A6 audit                                                                                    |
| ----------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------- |
| indicator               | `ENV-E1-DGS10`                               | same                                                                                        |
| as_of                   | `2024-06-15`                                 | same                                                                                        |
| resource_guard_decision | OK                                           | OK (both envs)                                                                              |
| fetch status            | SUCCESS                                      | SUCCESS (both envs)                                                                         |
| row_count               | 1                                            | 1                                                                                           |
| latency                 | 5 ms (fetch_result only)                     | ~430–444 ms wall (full staging path incl. init_db snapshot, route preview, guard, registry) |

Execute `latency_ms=5` measures DataSourceService fetch slice inside an already-warmed Phase 3 sandbox; A6 wall time includes cold sandbox DB + first-run imports — still well under 5s gate.

## GitNexus / codegraph

- **GitNexus `impact(ResourceGuard)`:** LOW risk · 4 direct upstream importers (orchestrator, datasource service, feature engine, ci smoke).
- **Codegraph:** not indexed this session; verified via `resource_guard.py` + `ingestion.py` `micro_fetch_staging` (guard before fetch in writer txn).

## Command (repro)

```powershell
cd C:\Users\Guang\Desktop\quant-monitor-desk
.\.venv\Scripts\python.exe .trellis/tasks/06-20-round3-batch2-5-layer1-obs-ingest/research/a6_perf_benchmark.py cli-sandbox
.\.venv\Scripts\python.exe .trellis/tasks/06-20-round3-batch2-5-layer1-obs-ingest/research/a6_perf_benchmark.py audit-prod-path
```

## Evidence artifacts

- `research/a6-perf-output.json` — machine-readable metrics
- `research/a6_perf_benchmark.py` — audit runner (sandbox setup + measure)

**§4.3 open count: 0**
