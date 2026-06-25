# Batch 3F Coordinator Playbook

> Use this before creating any Batch 3F Trellis tasks or implementation branches.  
> The roadmap owns planning; this file owns execution ordering and merge hygiene.

---

## 1. Recommended execution order

1. **3F.6 lineage/Layer3 closure** can start early because it closes the highest-risk registry mismatch left by 3D.3.
2. **3F.1 migration residuals** can run in parallel, but migration files must have one branch owner.
3. **3F.2 CLI / ops entrypoints** can run in parallel after migration ownership is clear.
4. **3F.3 source health** should wait for migration/writer ownership if it needs persistent tables.
5. **3F.4 backfill/reconcile** should wait for sync support matrix/registry clarity.
6. **3F.5 hygiene/perf** can split into small branches, but registry reconcile must run near the end.

---

## 2. Parallel boundaries

- Do not edit the same migration file in multiple branches.
- Do not mix live-source authorization work with generic CLI work.
- Do not mix lineage/Layer3 closure with source-health table migration unless explicitly coordinated.
- Do not mix registry reconcile with implementation branches until evidence exists.
- Do not move Round4/Round5 product/release items into 3F.

---

## 3. Closeout requirement

Each branch must output:

- exact roadmap rows owned,
- exact registry rows touched,
- tests run,
- evidence path,
- no-production-clean-write statement,
- remaining re-deferrals with owner/phase/closure test.

---

## 4. Required final batch audit

Before Round 3G starts, run a Batch 3F closeout audit that verifies:

- every Batch 3F roadmap row is resolved or explicitly re-deferred,
- every registry open item has a single owner,
- `B2.5-O-05` live FRED remains guarded unless user-authorized evidence exists,
- Eastmoney/AkShare validation failures are not falsely closed,
- `R3-PARTIAL-5`, `R2-RISK-3`, and `R3-AUDIT-DEF-03` are not reopened accidentally.
