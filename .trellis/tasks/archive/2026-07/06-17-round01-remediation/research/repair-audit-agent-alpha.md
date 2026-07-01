# Round 0/1 GPT Repair — Independent Audit (Agent Alpha)

**Auditor:** independent verify agent  
**Date:** 2026-06-17  
**Baseline:** `3d7f93a` (`docs: close audit nits after Round 0/1 remediation verify`)  
**Status doc:** `.trellis/tasks/06-17-round01-remediation/GPT_ROUND01_REPAIR_STATUS.md`

---

## 1. Verdict

**BLOCK**

Repair work is largely implemented and runtime tests pass locally, but **`ruff check .` fails** (CI gate in `.github/workflows/ci.yml` L18). Additionally, **`backend/app/db/migrations/003_resource_guard_metrics.sql` is untracked** while modified tests and `schema.sql` already depend on it — a committed PR without that file would break clean checkout.

The status doc claim “上述命令 **全部 exit 0**” is **false** for `ruff check .`.

---

## 2. Command evidence

| Command                                         | Exit  | Key output                                                               |
| ----------------------------------------------- | ----- | ------------------------------------------------------------------------ |
| `pip install -e ".[dev]"`                       | 0     | Dev deps installed (Python 3.14 site-packages)                           |
| `pytest -q` (pre-init_db)                       | 0     | 114 passed; 1 Starlette/httpx deprecation warning                        |
| `ruff check .`                                  | **1** | `E501 Line too long (102 > 100)` → `backend/app/db/write_manager.py:255` |
| `python -m compileall -q backend scripts tests` | 0     | No compile errors                                                        |
| `python scripts/check_doc_links.py`             | 0     | `OK: checked links in 107 markdown files under docs/`                    |
| `QMD_DATA_ROOT=data/ python scripts/init_db.py` | 0     | `init_db: applied ['003_resource_guard_metrics']`                        |
| `pytest -q` (post-init_db)                      | 0     | 114 passed                                                               |
| `cd frontend && npm ci`                         | 0     | 24 packages audited                                                      |
| `npm audit --audit-level=high`                  | 0     | `found 0 vulnerabilities`                                                |
| `npm run typecheck`                             | 0     | `tsc --noEmit` clean                                                     |
| `npm run build`                                 | 0     | `vite v8.0.16` built in 81ms                                             |

---

## 3. GPT item checklist

### P0

| ID       | Claim                                      | Result       | Evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| -------- | ------------------------------------------ | ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **P0-1** | clean checkout pytest                      | **VERIFIED** | `tests/test_project_scaffold.py` `REQUIRED_DIRS` has no `data/` or `data/duckdb` (L11–24). `test_initDb_createsDuckDbDirectory` uses `tmp_path` (L38–45). `README.md` L42–59 documents `init_db` after clone and states pytest passes without pre-creating `data/duckdb/`.                                                                                                                                                                                                                                       |
| **P0-2** | Vite/esbuild CVE                           | **VERIFIED** | `frontend/package.json`: `vite@^8.0.16`, `@vitejs/plugin-react@^6.0.2`. `npm audit --audit-level=high` → 0 vulnerabilities. Build uses `vite v8.0.16`.                                                                                                                                                                                                                                                                                                                                                           |
| **P0-3** | reader pragmas                             | **VERIFIED** | `backend/app/db/connection.py` L172–177: `reader()` calls `self._apply_pragmas(con)` before yield. Tests `test_reader_appliesThreadsAndMemoryLimit` / `test_reader_appliesTempDirectory` in `tests/test_duckdb_connection.py` L57–76. _(Note: reader pragma call existed at `3d7f93a`; repair added explicit GPT-named tests.)_                                                                                                                                                                                  |
| **P0-4** | ResourceGuard full signals + migration 003 | **PARTIAL**  | Code: `ResourceSnapshot` fields + `evaluate()` thresholds in `resource_guard.py`; extended INSERT in `check()`; tests in `test_resource_guard.py` (e.g. `test_check_lowMemorySnapshot_writesExtendedGuardLogColumns` L196–225). Migration SQL exists on disk. **FAIL sub-check:** `003_resource_guard_metrics.sql` is **not git-tracked** (`git ls-files` empty); `test_schema_migration.py` L31/L59 and `test_schema_contract.py` L48 require it. Clean committed checkout without this file would fail pytest. |

### P1

| ID                                | Claim                             | Result       | Evidence                                                                                                                                                                                                                                                                                                                                                   |
| --------------------------------- | --------------------------------- | ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **docs 坏链**                     | INDEX.md fixed                    | **VERIFIED** | `docs/INDEX.md` links `architecture/01_context_and_scope.md` and `architecture/09_phase_plan.md`. `test_docsIndex_relativeLinks_resolveToExistingFiles` in `tests/test_documentation_index.py` L35–49. `check_doc_links.py` exit 0.                                                                                                                        |
| **空 env 路径**                   | `_path_env` + expanduser          | **VERIFIED** | `backend/app/config.py` L11–15: empty/whitespace → default; else `Path(raw).expanduser()`. `tests/test_config.py` L9–30.                                                                                                                                                                                                                                   |
| **configs vs specs**              | `performance_limits.md` authority | **VERIFIED** | `docs/ops/performance_limits.md` L8–15 documents contract vs config merge; references `specs/contracts/resource_limits.yaml` and `configs/resource_limits.yaml`.                                                                                                                                                                                           |
| **WriteManager 外部事务失败审计** | own_transaction=False paths       | **VERIFIED** | `write_manager.py` L255–262: SQL error with `own_transaction=False` returns FAILED without second connection. Tests `test_write_ownTransactionFalse_stubFail_doesNotRollbackOuterTxn` L234–252 and `test_write_ownTransactionFalse_duckdbError_doesNotOpenSecondAuditConnection` L255–288. **Side effect:** repair comment at L255 triggers **ruff E501**. |
| **FileRegistry 并发重复**         | constraint test                   | **VERIFIED** | `test_register_duplicateHashViaConstraint_returnsSameFileId` in `tests/test_raw_store.py` L164+ (present at `3d7f93a`). Relies on `002_registry_hardening` UNIQUE index.                                                                                                                                                                                   |
| **`.trellis/.cursor` 边界**       | agent_workflow_boundaries.md      | **VERIFIED** | `docs/ops/agent_workflow_boundaries.md` tracked in git; documents Trellis/Cursor trust model (方案 A).                                                                                                                                                                                                                                                     |

### Clean-checkout pytest (explicit check)

| Check                         | Result       | Evidence                                                                                   |
| ----------------------------- | ------------ | ------------------------------------------------------------------------------------------ |
| No `data/duckdb` in scaffold  | **VERIFIED** | Grep `REQUIRED_DIRS` — no data paths                                                       |
| Tests use tmp_path / :memory: | **VERIFIED** | DB tests use `tmp_path` or `:memory:`; no test asserts pre-existing `data/duckdb/` on disk |

### Migration 003

| Check                              | Result       | Evidence                                                                               |
| ---------------------------------- | ------------ | -------------------------------------------------------------------------------------- |
| File exists                        | **VERIFIED** | `backend/app/db/migrations/003_resource_guard_metrics.sql` (4 ALTER COLUMN statements) |
| `test_schema_migration` expects it | **VERIFIED** | L31 `assert "003_resource_guard_metrics" in applied`; L56–59 `applied_versions` set    |
| File in version control            | **FAIL**     | `git status`: `?? backend/app/db/migrations/003_resource_guard_metrics.sql`            |

---

## 4. Regressions vs `3d7f93a`

| Area                    | At `3d7f93a`                           | Current working tree                        | Regression?                                             |
| ----------------------- | -------------------------------------- | ------------------------------------------- | ------------------------------------------------------- |
| `ruff check .`          | Pass (no E501 in touched files)        | **Fail** E501 `write_manager.py:255`        | **Yes — new lint failure**                              |
| Migration 003           | Not present; tests expect 001/002 only | Tests + contract expect 003; file untracked | **Yes — commit gap**                                    |
| `test_schema_migration` | 2 migrations                           | 3 migrations                                | Intentional repair delta; safe only if 003 is committed |
| Reader pragmas          | Already in `connection.py`             | Same + new reader tests                     | No functional regression                                |
| Frontend audit          | (not re-run at baseline)               | 0 high vulnerabilities                      | No regression observed                                  |

No pytest failures vs local baseline behavior; the blockers are **lint** and **untracked migration artifact**.

---

## 5. Blockers before commit/push

1. **Fix ruff E501** — `backend/app/db/write_manager.py:255`: comment exceeds 100 chars. Wrap or shorten, e.g. split across two lines:
   ```python
   # own_transaction=False: txn may be aborted; caller ROLLBACKs.
   # No second audit connection.
   ```
2. **Stage migration 003** — `git add backend/app/db/migrations/003_resource_guard_metrics.sql` (required by `test_schema_migration`, `test_schema_contract`, `init_db`, `specs/schema/schema.sql` changes).
3. **Correct status doc** — `GPT_ROUND01_REPAIR_STATUS.md` §验收命令 must not claim `ruff check .` exit 0 until fixed.
4. **Re-run gate** after fixes: `ruff check .` then full pytest.

Optional hygiene (non-blocking for repair scope): 17 modified + many untracked Round 2 / tooling files in working tree — ensure Repair PR scopes only Round 0/1 repair files listed in status doc.

---

## Adversarial notes

- Status doc says “108+ pytest items”; this run collected **114** passes — count drift is minor but doc is stale.
- `init_db` on this machine applied only `003` (001/002 already present) — first-time prod init still depends on committed 003.
- P0-4 is **not fully closed** until migration 003 is in git; local green pytest is a false comfort for CI/clean clone.
- Repair introduced the only failing CI command (`ruff`); pytest/compileall/frontend/docs gates all pass.
