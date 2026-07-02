# B02_03 — RawStore Atomic Write Protection

> Owns: `VR-STOR-001`.  
> Roadmap: Round 3V.1 · Batch package: `BATCH_3V_VERIFIED_AUDIT_CLEANUP`.  
> Suggested branch: `fix/round3v-rawstore-atomic-write`.  
> Parallel: can run with schema_hash task; avoid conflicting edits to storage helper paths.

---

## 1. Goal

Protect raw/json/csv/parquet evidence files from partial overwrite or half-written content by adding atomic write semantics to RawStore/path compatibility helpers.

---

## 2. Scope

- Implement `write_bytes_atomic(path, data)` or equivalent helper.
- Write to same-directory unique temp file.
- Flush/fsync file before replace where platform supports it.
- Use `os.replace` to atomically replace target.
- Clean temp file on failure.
- Preserve idempotency for repeated writes of the same content_hash.

---

## 3. Required inputs

- `backend/app/storage/raw_store.py`.
- `backend/app/storage/path_compat.py`.
- `backend/app/storage/file_registry.py` if touched by current write path.
- `specs/contracts/resource_limits.yaml`.
- Existing RawStore tests.

---

## 4. Forbidden scope

- Do not change content_hash naming semantics.
- Do not rewrite FileRegistry unless required by a test-proven failure.
- Do not add production DB writes.
- Do not introduce external filesystem dependencies.
- Do not make Windows behavior depend on POSIX-only directory fsync.

---

## 5. Implementation slices

1. `B02-STOR-01` — Add atomic helper with temp-file cleanup.
2. `B02-STOR-02` — RawStore.save uses atomic helper for supported raw file types.
3. `B02-STOR-03` — Simulate exception during write and assert target file remains absent or unchanged.
4. `B02-STOR-04` — Repeated save with same content hash remains idempotent.
5. `B02-STOR-05` — Registry closeout for `VR-STOR-001`.

---

## 6. Testing requirements

- Mid-write failure does not leave partial target file.
- Existing target remains unchanged if replacement fails.
- Temp files are cleaned or quarantined with explicit naming.
- JSON/CSV/Parquet allowed suffix behavior remains unchanged.
- Tests document coverage scope, test object, and purpose.

---

## 7. Acceptance commands

```bash
uv sync --locked
uv run pytest tests/test_raw_store.py -q
uv run ruff check backend/app/storage tests/test_raw_store.py
```

Run broader storage/FileRegistry tests if touched.

---

## 8. Done criteria

- RawStore write path is atomic for supported raw evidence files.
- Failure leaves no half-written target.
- `VR-STOR-001` is resolved or precisely re-deferred.
- No production DB mutation occurred.
