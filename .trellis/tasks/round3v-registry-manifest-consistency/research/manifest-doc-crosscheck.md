# Research: manifest / doc crosscheck (VR-DOC-001 tooling)

- **Query**: manifest checker, test catalog, acceptance commands baseline
- **Scope**: internal
- **Date**: 2026-06-25

## Findings

### Tooling baseline

| Path | Status |
|---|---|
| `scripts/check_manifest_files.py` | Present; existence check + optional `--verify-hash` |
| `tests/test_manifest_files_check.py` | In `tests/test_catalog.yaml`; two tests with五字段 docstrings |
| `tests/test_unresolved_item_task_coverage.py` | Lists `A9-P1-01` etc. in `EXPECTED_UNRESOLVED_IDS` — registry closure will require **main session** + possible test expectation update (out of REG direct commit) |

### Acceptance command results (2026-06-25, worktree `fix/round3v-registry-manifest-consistency`)

| Command | Result |
|---|---|
| `uv run python scripts/check_manifest_files.py` | **exit 1** — `missing file: FINAL_AUDIT_REPORT.md` |
| `uv run python scripts/check_docs_specs_indexed.py` | **exit 1** — 10 stale `MIGRATION_MAP` refs to untracked Round 4/5/Batch6 task docs |

### References to FINAL_AUDIT_REPORT (must stay consistent after restore/replace)

| Path | Reference type |
|---|---|
| `MANIFEST.json` | files[] + sha256 |
| `README.md` | layout tree + §审计修复包 |
| `docs/quality/final_package_rules.md` | must-retain list |
| `specs/contracts/release_cleanup_allowlist.yaml` | allowlist entry |
| `docs/quality/staged_acceptance_policy.md` | release validation mention |
| `docs/quality/REPAIR_EXECUTION_SELF_CHECK.md` | historical P1-04 evidence (read-only) |

### GitNexus vs codebase-memory

| Tool | Result |
|---|---|
| GitNexus `query` | Surfaced manifest/schema check scripts and `test_schemaContract_includesStatusCheckConstraints` |
| codebase-memory `search_code` | Project name `C-Users-Guang-Desktop-quant-monitor-desk`; pattern search returned empty (index/path mismatch) — **GitNexus + direct reads used as primary** |

## Caveats / Not Found

- `check_docs_specs_indexed.py` failure is **environmental** (stale MIGRATION_MAP vs untracked docs on branch) — not owned by B3V-REG allowed files; escalate to merge coordinator / `loop_maintain.py --fix` on integration branch.
- Plan phase: `FINAL_AUDIT_REPORT.md` missing is **allowed** per playbook §8.5 when documented in `DEBT.plan.md` restore slice.
