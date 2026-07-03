# B02_05 — Migration Registry and Manifest Consistency

> Owns: `VR-REG-001`, `VR-DOC-001`.  
> Roadmap: Round 3V.1 · Batch package: `BATCH_3V_VERIFIED_AUDIT_CLEANUP`.  
> Suggested branch: `fix/round3v-registry-manifest-consistency`.  
> Parallel: docs/registry-focused; coordinate with migration/schema owners if migration files are touched.

---

## 1. Goal

Make registry, migration coverage, schema, manifest, and README claims agree with current repository state, without duplicating already-completed migration work or faking missing release artifacts.

---

## 2. Scope

### `VR-REG-001`

- Reconcile migration 009 actual CHECK coverage against `schema.sql`, migration files, `MIGRATION_COVERAGE.md`, and unresolved/resolved registries.
- Move already-covered CHECK items to resolved with exact evidence, or precisely re-defer remaining gaps.
- Distinguish “schema/migration file contains CHECK” from “production DuckDB has applied migration”.

### `VR-DOC-001`

- Reconcile `FINAL_AUDIT_REPORT.md` across README, MANIFEST, final package rules, allowlists, and actual root tree.
- Either restore the file from trusted source and match hash, or update all references to the replacement closeout artifact.
- Add or plan a manifest existence/hash check.

---

## 3. Required inputs

- `backend/app/db/migrations/009_status_check_constraints.sql`.
- `specs/schema/schema.sql`.
- `docs/schema/MIGRATION_COVERAGE.md`.
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`.
- `docs/RESOLVED_ISSUES_REGISTRY.md`.
- `README.md`.
- `MANIFEST.json`.
- `docs/quality/final_package_rules.md`.
- `release_cleanup_allowlist.yaml` or equivalent allowlist path if present.

---

## 4. Forbidden scope

- Do not repeat or rewrite migration 009 unless tests prove it is wrong.
- Do not claim production DB has applied migration 009 without read-only DB evidence.
- Do not create fake `FINAL_AUDIT_REPORT.md` content to satisfy manifest.
- Do not remove references without writing the replacement closeout path.

---

## 5. Implementation slices

1. `B02-REG-01` — Build migration 009 coverage matrix: migration file, schema.sql, registry rows.
2. `B02-REG-02` — Update unresolved/resolved registries with exact evidence or precise re-defer.
3. `B02-DOC-01` — Decide restore-vs-replace path for `FINAL_AUDIT_REPORT.md`.
4. `B02-DOC-02` — Update README/MANIFEST/final package rules/allowlists consistently.
5. `B02-DOC-03` — Add manifest file existence/hash validation if missing.

---

## 6. Testing requirements

- Manifest file checker fails when `MANIFEST.json` lists a missing file (`tests/test_manifest_files_check.py` — **TDD required**).
- Migration coverage docs do not contradict migration 009/schema.sql state.
- Registry tests or static checks catch unresolved/resolved duplicate claims.
- Tests document coverage scope, test object, and purpose.

---

## 7. Acceptance commands

```bash
uv sync --locked
uv run pytest tests/test_unresolved_item_task_coverage.py tests/test_manifest_files_check.py -q
uv run python scripts/check_docs_specs_indexed.py
uv run python scripts/check_manifest_files.py
```

If `check_manifest_files.py` does not exist, create it or document a precise follow-up task.

> **2026-06-25:** `scripts/check_manifest_files.py` added. Default run reports missing `FINAL_AUDIT_REPORT.md` until B3V-REG restore-or-replace (`VR-DOC-001`). Use existence-only check during planning; `--verify-hash` after manifest reconcile.

---

## 8. Done criteria

- `VR-REG-001` is closed or precisely re-deferred.
- `VR-DOC-001` is closed or precisely re-deferred.
- README/MANIFEST/allowlist/final package rules no longer contradict the file tree.
- No production DB mutation occurred.
