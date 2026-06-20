# A6 audit-perf — §3.6

**Verdict: PASS**

| Environment     | elapsed_s | rss_mb | Threshold    | Pass |
| --------------- | --------- | ------ | ------------ | ---- |
| cli-sandbox     | 0.0046    | 39.18  | ≤5s / ≤512MB | ✓    |
| audit-prod-path | 0.0047    | 39.19  | ≤5s / ≤512MB | ✓    |

Prod DB SHA256 unchanged during audit (see `audit-a5-trace.md`).

Evidence: `research/a6-perf-output.json`

**§4.3 count: 0 open**
