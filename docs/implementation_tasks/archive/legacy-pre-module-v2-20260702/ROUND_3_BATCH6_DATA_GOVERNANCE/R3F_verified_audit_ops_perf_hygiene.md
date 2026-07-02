# R3F_verified_audit_ops_perf_hygiene — Source Health, ResourceGuard, Layer1 Perf, Production Budget

> Owns: `VR-DATAHEALTH-001`, `VR-RG-001`, `VR-L1PERF-001`, `VR-PERF-001`.  
> Roadmap: Round 3F.3 and 3F.5.  
> Suggested branches: `feature/round3-source-health-and-quality-runners`, `chore/round3-batch6-technical-debt`.  
> Parallel: can split into source-health, ResourceGuard, Layer1 perf, and budget branches; do not mix with Round4 UI/API.

---

## 1. Goal

Move verified ops/performance findings into the existing Batch6 plan without re-opening Batch 01 or mixing with Round4/Round5 product/release work.

---

## 2. Scope by finding

### `VR-DATAHEALTH-001`

- Keep Batch 01 / DH2 read-only path forbidden from creating `source_health_snapshot`.
- Create a Batch6 migration/writer task for `source_health_snapshot` only after schema, writer, rollback, and db-inspect coverage exist.

### `VR-RG-001`

- Add shared/cache-aware ResourceGuard threshold loading and directory-size measurement strategy.
- Cover L3/L4 production entrypoints with ResourceGuard gate while preserving staged fixture-only behavior.

### `VR-L1PERF-001`

- Optimize Layer1 feature computation by grouping/sorting history per indicator instead of repeated per-observation sorting.
- Add complexity regression tests.

### `VR-PERF-001`

- Turn production-equivalent smoke into thresholded artifact in Batch6.
- Round5 may later promote the artifact to release/nightly gate.

---

## 3. Forbidden scope

- Do not implement frontend dashboards.
- Do not enable production clean write.
- Do not run full-market/full-history scans.
- Do not create `source_health_snapshot` inside Batch 01/DH2 paths.
- Do not make performance gate depend on live sources.

---

## 4. Implementation slices

1. `R3F-SH-05` — `source_health_snapshot` persist plan + migration/writer tests.
2. `R3F-RG-01` — ResourceGuard module-level cache and measurement provider tests.
3. `R3F-RG-02` — L3/L4 production entrypoint guard coverage.
4. `R3F-L1PERF-01` — Layer1 pre-group/pre-sort refactor with gold-result tests.
5. `R3F-PERF-01` — production-equivalent smoke JSON artifact and threshold config.
6. `R3F-CLOSE-01` — registry closeout/re-defer for all owned `VR-*` IDs.

---

## 5. Testing requirements

- Data health persistence tests must prove Batch01/DH2 does not create the table.
- ResourceGuard repeated instances should not repeatedly parse YAML or rescan dirs inside TTL/cache window.
- L3/L4 production entrypoint rejects execution when ResourceGuard hard-stop is active.
- Layer1 optimized features match existing gold semantics.
- Performance budget exceeds threshold → FAIL.
- Tests document coverage scope, test object, and purpose.

---

## 6. Acceptance commands

```bash
uv sync --locked
uv run pytest tests/test_ops_data_health.py tests/test_resource_guard.py -q
uv run pytest tests/test_layer1_feature_engine.py -q
uv run pytest tests/test_production_equivalent_smoke.py -q
uv run ruff check backend/app/core backend/app/layer1_axes backend/app/ops tests
```

Substitute nearest existing tests if names differ and document the substitution.

---

## 7. Done criteria

- Each owned `VR-*` is resolved or precisely re-deferred.
- Batch6 owns source-health persistence and performance budget; Round5 owns release gate promotion.
- No production DB mutation occurs except explicit migration tests in isolated test DB.
