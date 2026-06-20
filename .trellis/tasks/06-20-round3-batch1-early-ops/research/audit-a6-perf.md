# A6 audit-perf — §3.6

**Verdict: PASS**

> **Re-evaluation note:** Plan Phase 5 originally marked A6 SKIP (“无 perf SLA”). That was **incorrect** for Batch 1: `db-inspect` is an operator-facing local CLI bound by `GLOBAL_RESOURCE_LIMITS.md` eco profile (CPU/memory/DuckDB limits) and `--limit` scan cap. Performance = **wall-clock latency + process RSS** on real production-shaped data, without touching the production DB.

## Method (audit-prod-path)

1. `sha256` project DB **before**
2. `shutil.copytree(data → .audit-sandbox/r3b1-audit-prod-equiv/data)` — full prod data tree copy
3. `DbInspector(..., profile='eco', limit=100).inspect()` on **copy only**
4. Measure `elapsed_s`, `tracemalloc` peak, `psutil` RSS
5. `sha256` project DB **after** — must match

## Results (2026-06-20)

```json
{
  "environment": "audit-prod-path",
  "audit_db_bytes": 4206592,
  "elapsed_s": 0.041,
  "peak_traced_bytes": 228605,
  "rss_after_mb": 44.12,
  "inspect_status": "PASS",
  "read_only_open": true,
  "schema_table_count": 14,
  "raw_files_count": 1,
  "parquet_files_count": 1,
  "prod_db_unpolluted": true,
  "thresholds": {
    "elapsed_s_max_eco": 30.0,
    "rss_after_mb_max_eco_soft": 1024.0
  },
  "pass_elapsed": true,
  "pass_rss": true
}
```

Artifact: `.audit-sandbox/r3b1-audit-prod-equiv/a6-perf-output.json`

## Threshold rationale

| Metric            | Threshold | Source                                                                               |
| ----------------- | --------- | ------------------------------------------------------------------------------------ |
| `elapsed_s`       | ≤ 30s     | Operator-tolerable single inspect on eco; current data ~4MB DB + minimal raw/parquet |
| RSS after inspect | ≤ 1024 MB | `GLOBAL_RESOURCE_LIMITS.md` eco process soft cap ~1GB                                |

## Findings

| ID  | Sev | Finding                                 | §4.3? |
| --- | --- | --------------------------------------- | ----- |
| —   | —   | No perf regressions on prod-shaped copy | No    |

## §4.3

None.
