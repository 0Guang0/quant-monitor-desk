# Repair/Debt Lite Plan — chore/round3-ci-gate-hardening

## Source of truth

- audit / registry ID: D-CI (Round 3 gate hygiene) — `.trellis/spec/guides/round3-repair-debt-worktree-plan.md` §5
- roadmap ID: `R3F-HYG-12` — `PROMPT_05` / CI command matrix (`PROJECT_IMPLEMENTATION_ROADMAP.md`)
- base branch: `integration/round3`
- target branch: `chore/round3-ci-gate-hardening`
- owner agent: CI agent (PROMPT_05 session)

## Boundary

- allowed files: `docs/ops/verification_commands.md`, `tests/test_round3_verification_command_matrix.py`, `ROUND3_BATCH_IMPLEMENTATION_MAP.md` (command index pointer only), task evidence
- forbidden files: `backend/**` runtime, `configs/datasource.yml`, production DB, registry concurrent edits
- production/data boundary: docs/tests only; no network-default CI
- explicit non-goals: runtime behavior, source routing defaults, broad formatting

## Vertical slices

| Slice | Source ID | AC | Allowed files | Forbidden files | Verification | Evidence |
| ----- | --------- | -- | ------------- | --------------- | ------------ | -------- |
| S1 | D-CI | Round 3 command matrix current in `verification_commands.md` | `docs/ops/verification_commands.md` | backend runtime | `test_verificationCommandsDoc_*` | this plan |
| S2 | D-CI | Staged/live gate tests discoverable | `tests/test_round3_verification_command_matrix.py` | network-default CI | matrix test green | merge report |
| S3 | D-CI | Batch map points to command matrix | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` | unrelated sections | doc link check | merge report |

## Merge gate

- targeted tests: PROMPT_05 pytest list + new matrix test
- full tests: not required (docs/tests-only slice)
- lint/format/compile: ruff on changed tests if needed
- production-equivalent gate: not run (out of scope)
- DB hash proof: N/A
- registry reconciliation: untouched
