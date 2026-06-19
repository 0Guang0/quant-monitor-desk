# Round3 Early Close Plan (from Round2 ABCD audit)

Items deferred from strict Round2 skeleton to Round3 early phase:

| Item | Round3 phase | Notes |
|------|--------------|-------|
| Real QMT / broker terminal vendor E2E | R3 early | Requires user authorization; keep default disabled |
| Real Yahoo / rate-limited public API soak | R3 early | Staging snapshot + read-only sandbox |
| Layer snapshot lineage consumers | R3 mid | Depends on validation_report rule_version fields (closed in audit remediation) |
| Playwright / route-level frontend contract tests | R4 | Frontend shell only in Round2 |
| Production-scale shard latency benchmarks | R3 early | Use `scripts/production_equivalent_smoke.py` + fixture-scale datasets |

Round2 audit remediation closes: fixture vendor E2E, DB lineage fields, orchestrator runner split, backfill validate+write, reconcile re-fetch.
