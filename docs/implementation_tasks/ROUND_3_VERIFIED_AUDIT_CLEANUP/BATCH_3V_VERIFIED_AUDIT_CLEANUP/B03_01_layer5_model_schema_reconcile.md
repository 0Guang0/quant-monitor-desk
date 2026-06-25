# B03_01 — Layer5 and Model Schema Post-audit Reconcile

> Owns: `VR-L5-001`, `VR-MODEL-001`.  
> Roadmap: Round 3V.2 · Batch package: `BATCH_3V_VERIFIED_AUDIT_CLEANUP`.  
> Suggested branch: `review/round3v-layer5-model-schema-reconcile`.  
> Parallel: read-only reconcile may run with Batch 02; runtime/schema edits must be split.

---

## 1. Goal

Reconcile the verified audit's Layer5/model-schema findings against the latest post Batch 01 master state, without blindly redoing work that may already have been completed by `376e30e6`.

---

## 2. Scope

### `VR-L5-001`

- Check whether full Layer5 evidence chain, builder, provenance, agent-text rejection, manual review state, and lineage hash tests are now implemented.
- If yes, close or mark audit finding stale with exact evidence.
- If no, create a dedicated Layer5 follow-up branch/task and do not mix it into Batch 02.

### `VR-MODEL-001`

- Build a designed-vs-implemented table matrix for L3/L4/L5 tables.
- Separate `designed_tables`, `implemented_tables`, and `deferred_tables`.
- If migrations are missing, route to Round 3F migration ownership.
- If docs overclaim implemented tables, update docs/coverage/registry.

---

## 3. Required inputs

- `PROJECT_IMPLEMENTATION_ROADMAP.md` Round 3D and Round 3V.
- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/023_implement_layer5_evidence_chain.md`.
- `specs/contracts/layer5_evidence_contract.yaml`.
- `backend/app/layer5_evidence/`.
- `tests/test_layer5_evidence_chain.py` or nearest Layer5 tests.
- `docs/architecture/04_data_architecture.md`.
- `docs/modules/layer3_industry_shock_anchor.md`.
- `docs/modules/layer4_market_structure.md`.
- `docs/modules/layer5_security_evidence.md`.
- `specs/schema/schema.sql`.
- `backend/app/db/migrations/`.
- `docs/schema/MIGRATION_COVERAGE.md`.

---

## 4. Forbidden scope

- Do not declare Layer5 production-ready merely because staged tests pass.
- Do not mark designed tables as implemented unless schema/migration/tests exist.
- Do not remove `deferred_to_023b`-style notes unless evidence proves closure.
- Do not implement schema changes in this reconcile branch if they conflict with Round 3F migration ownership.

---

## 5. Implementation slices

1. `B03-L5-01` — Read current Layer5 implementation/tests and produce evidence-chain status matrix.
2. `B03-L5-02` — Verify agent text rejection, provenance, manual review, lineage hash coverage.
3. `B03-MODEL-01` — Build L3/L4/L5 designed/implemented/deferred table matrix.
4. `B03-MODEL-02` — Reconcile docs/schema/migration coverage claims.
5. `B03-CLOSE-01` — Close stale audit findings or create precise follow-up tasks.

---

## 6. Testing / verification requirements

- **Mandatory artifacts:** `research/l5-reconcile-matrix.md` with per-`VR-*` row (evidence / stale / follow-up).
- **Mandatory pytest:** `tests/test_layer5_evidence_chain.py` and `tests/test_migration_coverage.py` must run green before any `VR-*` close.
- Stale close requires post-Batch-01 commit hash + test name that would fail if regression occurred.
- If runtime gap found: **split branch** — do not edit `layer5_evidence/**` in this reconcile branch.
- New/changed tests must document coverage scope, test object, and purpose.

---

## 7. Acceptance commands

```bash
uv sync --locked
uv run pytest tests/test_layer5_evidence_chain.py -q
uv run pytest tests/test_migration_coverage.py -q
uv run python scripts/check_docs_specs_indexed.py
```

If a test file does not exist, document the nearest available command or create a follow-up validation task.

---

## 8. Done criteria

- `VR-L5-001` is resolved, marked stale with proof, or split into a dedicated Layer5 follow-up.
- `VR-MODEL-001` has a table-state matrix and registry/coverage alignment.
- No production-ready claim is added.
- No production DB mutation occurred.
