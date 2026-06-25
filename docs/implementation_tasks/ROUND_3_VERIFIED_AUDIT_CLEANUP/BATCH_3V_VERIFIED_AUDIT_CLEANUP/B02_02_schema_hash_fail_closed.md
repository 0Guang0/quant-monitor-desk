# B02_02 — Structured Source Schema Hash Fail-closed

> Owns: `VR-DATA-001`.  
> Roadmap: Round 3V.1 · Batch package: `BATCH_3V_VERIFIED_AUDIT_CLEANUP`.  
> Suggested branch: `fix/round3v-schema-hash-fail-closed`.  
> Parallel: can run with RawStore atomic write; coordinate ValidationGate test ownership.

---

## 1. Goal

Ensure structured successful fetch results for JSON/CSV/Parquet cannot proceed toward clean-write validation without a trustworthy `schema_hash`, unless the source is explicitly registered as schemaless.

---

## 2. Scope

- Update data adapter contract: structured file outputs with `SUCCESS` and `row_count > 0` must provide `schema_hash`.
- Add CSV/Parquet bounded schema inference path or require fetch ports to provide it.
- Update ValidationGate fail-closed behavior for missing structured `schema_hash`.
- Add tests for missing schema_hash, corrupted Parquet/CSV, and schema_hash change.

---

## 3. Required inputs

- `specs/contracts/data_adapter_contract.md`.
- `backend/app/datasources/adapters/skeleton_base.py`.
- `backend/app/db/validation_gate.py`.
- `specs/contracts/data_quality_rules.yaml`.
- `specs/contracts/resource_limits.yaml`.
- Existing tests around adapters, data quality, ValidationGate.

---

## 4. Forbidden scope

- Do not scan full files when schema-only or limit-0 detection is enough.
- Do not write production clean tables.
- Do not silently accept missing schema_hash for structured sources.
- Do not introduce heavy dependencies without approval.
- Do not change unrelated source routing behavior.

---

## 5. Implementation slices

1. `B02-DATA-01` — Contract update for structured schema_hash requirements.
2. `B02-DATA-02` — Add or enforce schema hash derivation for CSV/Parquet success results.
3. `B02-DATA-03` — ValidationGate rejects structured clean-write when current or baseline schema_hash is missing.
4. `B02-DATA-04` — Corrupt CSV/Parquet returns `FAILED` or `SCHEMA_DRIFT`, never clean-write eligible.
5. `B02-DATA-05` — Registry closeout for `VR-DATA-001`.

---

## 6. Testing requirements

- Parquet success result without schema_hash is rejected before clean write.
- CSV success result without schema_hash is rejected before clean write.
- Corrupted Parquet does not reach clean write.
- schema_hash change still triggers `ValidationRejected`.
- Tests document coverage scope, test object, and purpose.

---

## 7. Acceptance commands

```bash
uv sync --locked
uv run pytest tests/test_data_adapter_contract.py tests/test_db_validation_gate.py -q
uv run pytest tests/test_data_quality_validator.py -q
uv run ruff check backend/app/datasources backend/app/db tests
```

Use existing nearest test files if names differ; document substitutions.

---

## 8. Done criteria

- Structured sources cannot bypass schema drift checks via nullable schema_hash.
- `VR-DATA-001` is resolved or precisely re-deferred.
- Resource limits are respected.
- No production DB mutation occurred.
