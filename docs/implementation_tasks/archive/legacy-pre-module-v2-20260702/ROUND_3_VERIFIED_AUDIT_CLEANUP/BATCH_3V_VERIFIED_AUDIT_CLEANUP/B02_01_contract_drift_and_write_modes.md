# B02_01 — Contract Drift and Write Modes Hardening

> Owns: `VR-OPS-001`, `VR-WRITE-001`.  
> Roadmap: Round 3V.1 · Batch package: `BATCH_3V_VERIFIED_AUDIT_CLEANUP`.  
> Suggested branch: `fix/round3v-contract-drift-write-modes`.  
> Parallel: can run with schema_hash/rawstore tasks; avoid concurrent edits to the same contract files.

---

## 1. Goal

Remove ambiguity between runtime implementation and YAML/Markdown contracts for ops db-inspect and WriteManager write modes.

---

## 2. Scope

### `VR-OPS-001`

- Make `specs/contracts/ops_db_inspect_contract.yaml` the single source of truth for key tables and deferred mapping, or generate read-only constants from it.
- Add drift tests comparing contract content to `db_inspector` output/model.
- Keep db-inspect read-only: no DB mutation, no network access.

### `VR-WRITE-001`

- Split write mode contract semantics into `implemented_modes` and `reserved_modes`.
- Runtime-supported modes must match `WriteManager.SUPPORTED_MODES`.
- Reserved modes must return stable unsupported/deferred errors and must not be shown as available production capabilities.

---

## 3. Required inputs

- `PROJECT_IMPLEMENTATION_ROADMAP.md` Round 3V.
- `specs/contracts/ops_db_inspect_contract.yaml`.
- `backend/app/ops/db_inspector.py`.
- `specs/contracts/write_contract.yaml`.
- `backend/app/db/write_manager.py`.
- `docs/UNRESOLVED_ISSUES_REGISTRY.md` rows for db-inspect drift and write-mode mismatch.
- `specs/contracts/runtime_versions.md`.
- `docs/quality/staged_acceptance_policy.md`.

---

## 4. Forbidden scope

- Do not implement `manual_patch`, `replace_partition`, or `schema_migration` runtime behavior in this task.
- Do not change production clean-write permission.
- Do not add an API/CLI surface for reserved write modes.
- Do not write DB or run migrations.

---

## 5. Implementation slices

1. `B02-OPS-01` — Add contract loader/generator path for db-inspect table mapping.
2. `B02-OPS-02` — Add drift test: YAML contract vs runtime model/output.
3. `B02-WRITE-01` — Update write contract to separate implemented/reserved modes.
4. `B02-WRITE-02` — Add runtime parity test for supported modes.
5. `B02-WRITE-03` — Ensure reserved modes return explicit unsupported/deferred errors.
6. `B02-CLOSE-01` — Update registries or re-defer with exact closure test.

---

## 6. Testing requirements

- Drift test fails if YAML key tables or deferred mappings change without runtime alignment.
- Test asserts `implemented_modes == WriteManager.SUPPORTED_MODES`.
- Test asserts reserved modes do not execute writes.
- New/changed tests must document coverage scope, test object, and purpose.

---

## 7. Acceptance commands

```bash
uv sync --locked
uv run pytest tests/test_ops_db_inspector.py -q
uv run pytest tests/test_write_manager.py tests/test_db_validation_gate.py -q
uv run ruff check backend/app/ops backend/app/db tests
```

If filenames differ, use the nearest existing tests and document substitutions.

---

## 8. Done criteria

- `VR-OPS-001` closed or precisely re-deferred with evidence.
- `VR-WRITE-001` closed or precisely re-deferred with evidence.
- Contract/runtime drift is test-detectable.
- No production DB mutation occurred.
