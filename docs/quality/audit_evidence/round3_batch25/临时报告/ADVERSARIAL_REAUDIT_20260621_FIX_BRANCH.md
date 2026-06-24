# Adversarial Re-Audit — `fix/audit-report-issues-20260621`

**Date:** 2026-06-21  
**Baseline:** Round3 Batch2.5 nine-agent audit (`docs/quality/audit_evidence/round3_batch25/临时报告/ROUND3_BATCH25_AUDIT_AGENT_*.md` + `ROUND3_BATCH25_ADVERSARIAL_AUDIT_FINAL_SUMMARY.md`)  
**Fix branch under review:** `fix/audit-report-issues-20260621`  
**Registries:** `docs/quality/ROUND3_BATCH25_PENDING_FIX_REGISTRY.md`, `docs/AUDIT_DEFERRED_REGISTRY.md`, `docs/UNRESOLVED_ISSUES_REGISTRY.md`  
**High-risk deferral authority:** `docs/architecture/layer1_ingestion_refactor_rollback_plan.md`

---

## 1. Executive summary

The fix branch closes the **blocking P1 failures** from the pre-fix audit round (`GLOBAL-P1-01` Windows MAX_PATH evidence I/O, `GLOBAL-P1-02` full pytest red) and most **documented low-risk hygiene** items (`uv.lock`, `ruff`, `KNOWN_PYTEST_SKIPS.md`, `schema.sql` sync, `ROUND3_HANDOFF.md` staged-only wording, `test_observation_mapper.py`, `test_path_compat.py`, gate tests in `test_layer1_ingestion_gates.py`).

**Verification run (this re-audit):**

| Check                                                 | Result                                                               |
| ----------------------------------------------------- | -------------------------------------------------------------------- |
| `pytest -q`                                           | **PASS** (1 expected skip on Windows: symlink test)                  |
| `ruff check .`                                        | **PASS**                                                             |
| `ruff format --check .`                               | **PASS** (136 files)                                                 |
| `pytest` phase3/4 deep basetemp evidence              | **PASS**                                                             |
| `uv.lock` at repo root                                | **Present**                                                          |
| `specs/schema/schema.sql` contains `axis_observation` | **Yes** (line 482+)                                                  |
| `path_compat.py` wired in `raw_store.py`              | **Yes** (`mkdir_parents`, `write_bytes`, `is_relative_to_data_root`) |
| `_fetch_staging_on_connection` in `ingestion.py`      | **Present** (Phase3/4 reuse)                                         |

**Overall verdict: FAIL** (adversarial rules)

1. **No agent dimension reaches 95+** after re-scoring (best: Agent 02 at 92).
2. **Low-risk OPEN items remain** (`=` / `frontend/=` junk paths, partial boundary coverage, `.audit-sandbox*` review noise, pytest tiering, performance budget file) — counted as failures per audit rules.
3. **Several FIXED-category items score below 95** on fix quality (notably partial `A05-P1-01` coverage closure).
4. **Deferred high-risk items** (`ingestion.py` split) are **acceptable** — rollback plan exists and is referenced in registries + gate test `test_layer1Ingestion_phase0_batch25PendingFixRegistryPresent`.

**What improved:** Branch is mergeable for **staged Batch 2.5 closure**; not for **production-live** or **95+ adversarial PASS**.

---

## 2. Per-agent scores (01–09) — post fix branch

| Agent | Dimension                  | Pre-fix | Re-audit | Verdict | Primary delta                                                                   |
| ----: | -------------------------- | ------: | -------: | ------- | ------------------------------------------------------------------------------- |
|    01 | Completion / readiness     |      88 |   **91** | FAIL    | Pytest green + schema fixed; Batch2.75 still deferred; workspace junk remains   |
|    02 | Design deviation           |      86 |   **92** | FAIL    | `schema.sql` synced; registries reconciled; live pilot still planning-only      |
|    03 | Ponytail / simplification  |      82 |   **83** | FAIL    | `_fetch_staging_on_connection` partial; 1,516 LOC monolith unchanged            |
|    04 | Code quality               |      91 |   **94** | FAIL    | `ruff` green; mapper tests added; `=` paths still on disk                       |
|    05 | Maintainability / coverage |      90 |   **93** | FAIL    | Skip documented; mapper boundaries tested; `raw_store`/`db_inspector` gaps      |
|    06 | Engineering / architecture |      90 |   **91** | FAIL    | Handoff corrected; schema authority closed; workspace + Batch2.75 open          |
|    07 | Decoupling / nesting       |      83 |   **87** | FAIL    | `path_compat` integrated + tested; internal service coupling unchanged          |
|    08 | Performance                |      87 |   **88** | FAIL    | Full suite ~90s; no live benchmark / perf budget / test tiers                   |
|    09 | Database                   |      84 |   **90** | FAIL    | Schema sync closed; app-layer O-03 documented; migration 008 + live DB deferred |

**Rule:** All dimensions must be ≥95 for overall PASS → **not met**.

---

## 3. Global P0–P3 matrix (every item across nine agents)

Status key: **FIXED** | **PARTIAL** | **DEFERRED-DOCUMENTED** | **OPEN** | **ACCEPTED**

| Report ID                                                                              | Item                                                            | Status                  | Score /100 | Gap or next action                                                                                                                                                                             |
| -------------------------------------------------------------------------------------- | --------------------------------------------------------------- | ----------------------- | ---------: | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| —                                                                                      | P0 (all agents)                                                 | —                       |          — | No P0 items in Round3 Batch2.5 audit                                                                                                                                                           |
| GLOBAL-P1-01 / B2.5-WIN-PATH-01 / A07-P2-02                                            | Windows MAX_PATH breaks phase3/4 raw evidence I/O               | **FIXED**               |     **97** | `path_compat.py` + `raw_store.py` + `test_path_compat.py` + `test_save_windowsLongPath_writesSuccessfully`; phase3/4 targeted green                                                            |
| GLOBAL-P1-02                                                                           | Full `pytest -q` failing                                        | **FIXED**               |     **96** | Full suite green; 1 documented platform skip                                                                                                                                                   |
| A01-P1-01 / A02-P1-02 / A06-P1-01 / A08-P1-01 / A09-P1-03 / R3-B2.75-01 / GLOBAL-P2-01 | Batch2.5 staged only; Batch2.75 live pilot not executed         | **DEFERRED-DOCUMENTED** |          — | Phase **Batch 2.75** in all three registries; `018B` + `production_live_pilot_policy.md`; user auth required                                                                                   |
| A01-P1-02 / R3-B25-DOC-01                                                              | Batch3 MASTER must inherit staged-only handoff limits           | **OPEN**                |     **40** | Add explicit reference in Batch 3 planning PR to `final_registry_update.md` §handoff + `018A` §13                                                                                              |
| A02-P1-01 / A06-P1-02 / A09-P1-01 / A01-P2-01 / GLOBAL-P2-02 / B2.5-O-02               | `specs/schema/schema.sql` lags migration 011 axis tables        | **FIXED**               |     **98** | `axis_observation` et al. in `schema.sql`; `test_layer1Ingestion_phase0_schemaSqlLagTrackedAsO02`                                                                                              |
| A02-P2-01 / A01-P2-02 / B2.5-O-05                                                      | FRED primary vs staged `macro_supplementary` route              | **DEFERRED-DOCUMENTED** |          — | **Batch 2.75**; staged route tests green; live needs auth                                                                                                                                      |
| A02-P2-02 / A09-P1-02 / GLOBAL-P2-03 / B2.5-O-03                                       | `axis_observation` timestamp ordering — no DB CHECK             | **DEFERRED-DOCUMENTED** |     **96** | App-layer closure ADR-002; `test_layer1Observation_noFutureDataRejected` + gate `test_layer1Ingestion_phase0_axisObservation_appValidatorEnforcesTimestampOrder`; migration 008 optional later |
| A03-P1-01 / A04-P1-02 / A07-P1-01 / R3-B25-HYG-01                                      | `ingestion.py` ~1,516 LOC; `commit_*` monolith                  | **DEFERRED-DOCUMENTED** |          — | **PR-R2a–R2d** per `layer1_ingestion_refactor_rollback_plan.md`; gate test references plan                                                                                                     |
| A03-P1-02 / A07-P1-02                                                                  | Phase3/Phase4 fetch/route/guard duplication                     | **PARTIAL**             |     **78** | `_fetch_staging_on_connection` exists; PR-R2b still needed; add explicit regression asserting single `fetch_log` on both phases                                                                |
| A03-P2-01 / A05-P2-03 / A06-P2-02 / A07-P2-01 / A08-P2-01                              | Evidence writers mixed in runtime module                        | **DEFERRED-DOCUMENTED** |          — | **PR-R2a** extract `ingestion_evidence.py` per rollback plan                                                                                                                                   |
| A03-P2-02 / A07-P3-01                                                                  | Markdown formatter / sandbox helper duplication                 | **DEFERRED-DOCUMENTED** |          — | **PR-R2a/PR-R2b** steps 2–3                                                                                                                                                                    |
| A03-P3-01                                                                              | Sandbox bootstrap repeated across phases                        | **DEFERRED-DOCUMENTED** |          — | **PR-R2b** `sandbox_bootstrap.py`                                                                                                                                                              |
| A04-P1-01 / GLOBAL-P2-06                                                               | `ruff check` / format not verified                              | **FIXED**               |    **100** | `ruff check .` + `ruff format --check .` green on fix branch                                                                                                                                   |
| A04-P2-01 / A05-P1-01                                                                  | Low coverage: `observation_mapper`, `raw_store`, `db_inspector` | **PARTIAL**             |     **72** | `test_observation_mapper.py` (10 tests) added; no new focused `db_inspector` boundary file; `raw_store` long-path only                                                                         |
| A04-P2-02 / A05-P1-02                                                                  | Full pytest skip undocumented                                   | **FIXED**               |     **98** | `docs/quality/KNOWN_PYTEST_SKIPS.md` + `test_layer1Ingestion_phase0_knownPytestSkipsDocumented`                                                                                                |
| A04-P3-01                                                                              | `except OSError: pass` in resource_guard / axis_loader          | **ACCEPTED**            |          — | Registry §3.1 marks **不修复**; best-effort path compat                                                                                                                                        |
| A04-P3-02 / A06-P2-01                                                                  | Untracked `=` / `frontend/=` paths                              | **OPEN**                |      **0** | **7 files still present** under `=/npm-cache/` and `frontend/=/`; delete + add to `.gitignore`                                                                                                 |
| A05-P2-01                                                                              | Stale audit narrative risk                                      | **PARTIAL**             |     **88** | `ROUND3_HANDOFF.md` updated; authoritative path via registries + gate test                                                                                                                     |
| A05-P2-02 / R3-B25-HYG-02                                                              | Module-level coverage weak despite 91% total                    | **PARTIAL**             |     **70** | Add module thresholds or focused ops/storage tests                                                                                                                                             |
| A05-P3-01 / A09-P3-01 / R3-B25-HYG-04                                                  | `.audit-sandbox*` test artifact noise                           | **OPEN**                |     **30** | Clean before release or document retention in `final_package_rules`                                                                                                                            |
| A06-P2-03                                                                              | Live pilot policy exists but not executed                       | **DEFERRED-DOCUMENTED** |          — | Same as R3-B2.75-01                                                                                                                                                                            |
| A06-P3-01                                                                              | `ROUND3_HANDOFF.md` “execute ready” misread                     | **FIXED**               |     **97** | §Batch 2.5 now **archived PASS · staged/fixture only**                                                                                                                                         |
| A08-P1-02 / R3-B25-HYG-03                                                              | Full pytest ~90–155s; no test tier                              | **OPEN**                |     **45** | Add `@pytest.mark.slow` + CI quick/affected profile                                                                                                                                            |
| A08-P2-02                                                                              | No performance budget report artifact                           | **OPEN**                |     **50** | Extend `scripts/production_equivalent_smoke.py` output thresholds                                                                                                                              |
| A08-P3-01                                                                              | Frontend bundle lacks CI gzip budget                            | **DEFERRED-DOCUMENTED** |          — | **Round 4 CI hygiene**                                                                                                                                                                         |
| A09-P2-01 / B2.5-O-06 / A9-P1-01                                                       | Migration 008 broad CHECK closeout                              | **DEFERRED-DOCUMENTED** |          — | **Round 3 migration 008** per `MIGRATION_008_PLAN.md`                                                                                                                                          |
| A09-P2-02 / A08-P2-03                                                                  | Production DB before/after checksum on live data                | **DEFERRED-DOCUMENTED** |          — | **Batch 2.75** read-only replica policy                                                                                                                                                        |
| A01-P3-01                                                                              | Workspace non-clean baseline                                    | **PARTIAL**             |     **55** | Audit reports + `.audit-sandbox*` + `=` paths remain                                                                                                                                           |
| A02-P3-01                                                                              | Registry O-02/O-03 wording drift                                | **FIXED**               |     **95** | Three registries reconciled 2026-06-21; B2.5-O-02/03 resolution text aligned                                                                                                                   |
| GLOBAL-P2-04                                                                           | Missing `uv.lock`                                               | **FIXED**               |    **100** | Root `uv.lock` present                                                                                                                                                                         |
| GLOBAL-P2-05                                                                           | Archived `audit.report.md` §3 pending                           | **FIXED**               |     **94** | §3.1–3.8 A1–A8 summaries filled; §4 header still says “待 A1–A8” (cosmetic)                                                                                                                    |
| GLOBAL-P3-01 (pre-fix)                                                                 | Untracked `path_compat.py` should delete                        | **FIXED**               |     **97** | Now tracked, tested, integrated — opposite of pre-fix recommendation                                                                                                                           |

---

## 4. Fix-quality scores for completed fixes (must be ≥95 each)

| Fix cluster                                   | Items closed                              |   Score | Meets 95+?                                     |
| --------------------------------------------- | ----------------------------------------- | ------: | ---------------------------------------------- |
| Windows long-path I/O                         | GLOBAL-P1-01, B2.5-WIN-PATH-01, A07-P2-02 |  **97** | Yes                                            |
| Full pytest regression                        | GLOBAL-P1-02                              |  **96** | Yes                                            |
| Schema contract sync                          | B2.5-O-02, A02-P1-01, A09-P1-01           |  **98** | Yes                                            |
| App-layer timestamp guard                     | B2.5-O-03, GLOBAL-P2-03                   |  **96** | Yes                                            |
| Static quality (`ruff`)                       | GLOBAL-P2-06, A04-P1-01                   | **100** | Yes                                            |
| Dependency lockfile                           | GLOBAL-P2-04                              | **100** | Yes                                            |
| Pytest skip documentation                     | A04-P2-02, A05-P1-02                      |  **98** | Yes                                            |
| Handoff narrative                             | A06-P3-01                                 |  **97** | Yes                                            |
| Registry wording                              | A02-P3-01                                 |  **95** | Yes (borderline)                               |
| Audit report §3                               | GLOBAL-P2-05                              |  **94** | **No** — §4 banner stale                       |
| Observation mapper boundaries                 | A05-P1-01 (mapper slice only)             |  **94** | **No** — `db_inspector`/`raw_store` still thin |
| **Category aggregate: boundary test hygiene** | A04-P2-01, A05-P1-01                      |  **72** | **No**                                         |

**FIXED-category rule:** At least two clusters score &lt;95 → **branch fails adversarial quality bar** even where code runs green.

---

## 5. Remaining OPEN low-risk items (exact file / test)

| Priority | ID                        | File or test to add                                                             | Action                                                                                 |
| -------: | ------------------------- | ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
|        1 | A04-P3-02 / A06-P2-01     | Delete repo paths `=/`, `frontend/=/`                                           | `Remove-Item -Recurse -Force '=','frontend/='`; add `=/` to `.gitignore`               |
|        2 | A05-P1-01                 | `tests/test_raw_store.py`                                                       | Add: invalid segment rejection, `path escapes data_root`, oversize payload (&gt;256MB) |
|        3 | A05-P1-01                 | `tests/test_ops_db_inspector.py` (or new `tests/test_db_inspector_boundary.py`) | Add: malformed DB path, empty data root, scan limit edge for `parquet`/`audit` subdirs |
|        4 | A05-P3-01 / R3-B25-HYG-04 | `.gitignore` + release checklist                                                | Ignore `.audit-sandboxpytest-*` / document in `final_package_rules`                    |
|        5 | A08-P1-02                 | `pyproject.toml` + `tests/conftest.py`                                          | Register `slow` marker; default CI runs `-m "not slow"`                                |
|        6 | A01-P1-02                 | Batch 3 Trellis `MASTER.plan.md` (future)                                       | Cite staged handoff constraints before Batch 3 start                                   |
|        7 | A08-P2-02                 | `scripts/production_equivalent_smoke.py`                                        | Emit JSON thresholds file for CI gate                                                  |
|        8 | GLOBAL-P2-05              | `.trellis/.../audit.report.md` §4 header                                        | Change “待 A1–A8 完成后填写” → completed banner                                        |

---

## 6. Deferred items — registry compliance check

| Bucket                   | Representative IDs                | Cleanup phase in registry? | Rollback / policy doc?                             |
| ------------------------ | --------------------------------- | -------------------------- | -------------------------------------------------- |
| Batch 2.75 live pilot    | R3-B2.75-01, A01-P1-01, B2.5-O-05 | Yes — all three registries | `018B`, `production_live_pilot_policy.md`          |
| Migration 008 CHECK      | A9-P1-01, B2.5-O-06               | Yes                        | `MIGRATION_008_PLAN.md`                            |
| Orchestrator / packaging | D7-P1-1, D7-P2-2                  | Yes                        | Round 3 hygiene / task 035                         |
| Round 4 FE/API           | R4-\*, A05-P2-02                  | Yes                        | Tasks 024–028                                      |
| Ingestion split          | A03-P1-01, R3-B25-HYG-01          | Yes                        | **`layer1_ingestion_refactor_rollback_plan.md`** ✓ |
| App-layer CHECK (O-03)   | B2.5-O-03                         | Yes — closed via app-layer | ADR-002 + phase0 gate tests                        |

**Deferred compliance: PASS** — no undocumented deferrals found for Batch 2.5 scope.

---

## 7. Minimum plan to reach 95+ (adversarial PASS)

### 7.1 Immediate (same branch or tiny follow-up PR) — closes low-risk OPEN

1. Remove `=` / `frontend/=` directories; `.gitignore` npm-cache stray roots.
2. Add `tests/test_raw_store.py` cases: escape attempt, bad segments, size cap.
3. Add `tests/test_ops_db_inspector.py` (or dedicated file) for DB open failure + subdir scan caps.
4. Mark slow tests; document quick profile in `docs/quality/KNOWN_PYTEST_SKIPS.md` or CI doc.
5. Patch `audit.report.md` §4 header; optional `.audit-sandbox` gitignore.

**Expected lift:** Agents 04, 05, 06 +4–6 points → still short of 95 on Agents 01, 03, 07, 08, 09.

### 7.2 Staged semantics acceptable at 95+ (without live pilot)

To reach **95+ on Agent 01/02/06/09 without Batch2.75 execution**, adversarial bar requires:

- Explicit **Batch 3 planning gate** doc referencing staged-only (closes A01-P1-02).
- **Migration 008 plan** signed + contract test stub (raises A09 toward 95 with documented DB roadmap).
- **PR-R2a** evidence extraction (raises Agents 03, 07 toward 90+; need R2a–R2c for 95).

### 7.3 Full 95+ on all nine dimensions

Requires **either**:

- **Batch 2.75** controlled live pilot closeout (Agents 01, 02, 06, 08, 09), **or**
- Formal **re-defer** with updated MASTER prohibiting any production-live claims **plus** completion of §7.1–7.2 **plus** ingestion PR-R2a–R2c per rollback plan.

---

## 8. Codebase verification notes

### 8.1 `backend/app/storage/path_compat.py`

- Extended-path prefix (`\\?\`), `mkdir_parents`, `write_bytes`, `is_relative_to_data_root`.
- Covered by `tests/test_path_compat.py` (Windows-only) and `tests/test_raw_store.py::test_save_windowsLongPath_writesSuccessfully`.

### 8.2 `backend/app/storage/raw_store.py`

- Imports `path_compat` helpers; containment check before write.
- Long-path regression test exists; other boundary paths still under-tested (see §5).

### 8.3 `backend/app/layer1_axes/observation_mapper.py`

- Ten focused tests in `tests/test_observation_mapper.py` for failure modes and `source_used` resolution.

### 8.4 `tests/test_layer1_ingestion_gates.py` updates

- `test_layer1Ingestion_phase0_schemaSqlLagTrackedAsO02` — asserts all `LAYER1_AXIS_TABLES` in `schema.sql`.
- `test_layer1Ingestion_phase0_axisObservation_appValidatorEnforcesTimestampOrder` — O-03 app closure.
- `test_layer1Ingestion_phase0_knownPytestSkipsDocumented` — skip doc gate.
- `test_layer1Ingestion_phase0_batch25PendingFixRegistryPresent` — registry + rollback plan gate.

### 8.5 Docs

- `docs/ROUND3_HANDOFF.md` — Batch 2.5 **archived PASS**, staged-only, points to fix registry.
- `docs/quality/KNOWN_PYTEST_SKIPS.md` — platform skips table present.

---

## 9. Final adversarial verdict

| Criterion                                   | Result                                   |
| ------------------------------------------- | ---------------------------------------- |
| All P0 cleared                              | **Yes**                                  |
| Blocking P1 (pytest / Windows path) cleared | **Yes**                                  |
| Low-risk OPEN = failure                     | **Yes — FAIL** (≥5 OPEN items)           |
| High-risk deferrals documented + rollback   | **Yes**                                  |
| Every FIXED cluster ≥95                     | **No** (boundary tests, audit §4 banner) |
| Every agent dimension ≥95                   | **No**                                   |
| **Overall**                                 | **FAIL**                                 |

**Recommendation:** Merge fix branch for **staged Batch 2.5 hygiene** after deleting `=` paths and optionally adding boundary tests; do **not** claim adversarial 95+ PASS or production-live readiness until §7.3.

---

## 10. Top 5 OPEN low-risk fixes (do immediately)

1. **Delete `=/` and `frontend/=/` npm-cache junk** — paths pollute review (`A04-P3-02`, `A06-P2-01`).
2. **`tests/test_raw_store.py`** — add path-escape + invalid-segment + oversize tests (`A05-P1-01`).
3. **`tests/test_ops_db_inspector.py`** — add read-only error + subdir scan-limit parametrized tests (`A05-P1-01`, cross-ref `R3-AUDIT-DEF-03`).
4. **`.gitignore` for `.audit-sandbox*`** — reduce merge-review noise (`A05-P3-01`).
5. **`pyproject.toml` slow marker + CI quick profile** — document in `KNOWN_PYTEST_SKIPS.md` (`A08-P1-02`).

---

_Re-audit performed by adversarial agent on working tree of `fix/audit-report-issues-20260621`; commands: full `pytest -q`, `ruff check/format`, targeted phase3/4 evidence, file/registry inspection._

---

## 11. §7.1 fix completion (2026-06-21 follow-up)

**See:** `docs/quality/audit_evidence/round3_batch25/临时报告/REAUDIT_FIX_COMPLETION_20260621.md`

| §7.1 item                                             | Status                                                |
| ----------------------------------------------------- | ----------------------------------------------------- |
| Delete `=/` / `frontend/=/` + `.gitignore`            | **DONE**                                              |
| `test_raw_store.py` boundary cases                    | **DONE**                                              |
| `test_ops_db_inspector.py` subdir scan / missing root | **DONE**                                              |
| `.audit-sandboxpytest-*/` gitignore                   | **DONE**                                              |
| `slow` marker + quick CI doc                          | **DONE** (`pytest.ini` + `pyproject.toml`)            |
| Batch 3 staged gate (`A01-P1-02`)                     | **DONE** — `BATCH3_STAGED_DOWNSTREAM_GATE.md`         |
| Single `fetch_log` regression (`A03-P1-02`)           | **DONE**                                              |
| Full pytest                                           | **612 passed, 1 skipped** (after new regression test) |

**Updated verdict:** Low-risk OPEN **cleared**; staged Batch 2.5 **mergeable**. Nine-agent **≥95 all dimensions** still **not met** (Batch 2.75 + ingestion split deferred).
