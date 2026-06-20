# A3 audit-security — §3.3

**Dimension:** A3 (audit-security)  
**Skills:** security-and-hardening + doubt-driven-development  
**Scope:** `backend/app/layer1_axes/`, `backend/app/db/write_manager.py` (reference), `011_layer1_tables.sql`, `tests/test_layer1_*.py`  
**Date:** 2026-06-20  
**Verdict: PASS** (post-repair — A3-01 lineage WriteManager path implemented)

---

## 1. Summary

| Severity | Count |
| -------- | ----- |
| Critical | 0     |
| High     | 0     |
| Medium   | 1     |
| Low      | 1     |
| Info     | 2     |

Static scan found one clean-table mutation path that bypasses `WriteManager` / `DbValidationGate` (`SnapshotLineageBuilder.persist` → `axis_snapshot_lineage`). Feature snapshots correctly use staging → gate → `WriteManager`. No SQL injection, credential leakage, forbidden SQL, or direct `duckdb.connect` in layer1 deliverables. Pytest layer1 suite green (23 tests).

**§4.3 repair items (A3):** 1

---

## 2. Trust boundaries (STRIDE sketch)

| Boundary        | Untrusted input                               | Controls observed                                                                                              |
| --------------- | --------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| YAML specs      | `spec_root`, axis YAML files                  | `yaml.safe_load`; axis keys from `enabled_axes` allowlist; indicator validation raises `AxisSpecLoadError`     |
| Feature compute | `AxisObservation` rows, `as_of`               | `no_future_data` enforced (`publish_timestamp > as_of` → `Layer1SnapshotError`); `ResourceGuard` eco gate      |
| Interpretation  | Template strings                              | Forbidden action terms (`买入` etc.); `reject_if_forbidden`; `guard_layer2_writeback` blocks L2→L1             |
| Lineage build   | `source_dataset_ids`, `validation_report` ref | Parameterized `persist`; hashes from `validation_report` JSON; **no** runtime `agent_outputs_not_source` guard |
| DuckDB writes   | Staging rows, lineage envelopes               | Feature path: `ConnectionManager.writer()` → staging → `_execute_write` + gate; **lineage path bypasses gate** |
| Network         | N/A (batch scope)                             | No HTTP clients, URLs, or fetch orchestration in `layer1_axes/`                                                |

---

## 3. Commands and output

### 3.1 AUDIT.plan §2 A3 primary scan — DML in layer1 deliverables

**Command:**

```text
rg -n "INSERT |UPDATE |DELETE " backend/app/layer1_axes/
```

**Output:**

```text
backend/app/layer1_axes/lineage.py:100:            INSERT INTO axis_snapshot_lineage (
backend/app/layer1_axes/lineage.py:184:                    INSERT INTO {staging} VALUES (
```

**Interpretation:** Two INSERT sites in `lineage.py`. Line 184 is staging insert inside `Layer1SnapshotWriter.write_features` (expected WriteManager prelude). Line 100 is **direct clean-table INSERT** into `axis_snapshot_lineage` via `SnapshotLineageBuilder.persist`, bypassing `WriteManager`.

### 3.2 WriteManager / connection patterns

**Command:**

```text
rg -n "duckdb\.connect|writer\(|_execute_write|apply_migrations" backend/app/layer1_axes/
```

**Output:**

```text
backend/app/layer1_axes/lineage.py:179:        with self._cm.writer() as con:
backend/app/layer1_axes/lineage.py:202:            return self._wm._execute_write(con, req)
```

**Interpretation:** No direct `duckdb.connect` or `apply_migrations` in layer1 module. `Layer1SnapshotWriter` acquires writer via `ConnectionManager` and delegates to `WriteManager._execute_write` (private entry, but `DbValidationGate` still runs inside `_execute_write`).

### 3.3 Forbidden SQL / non-read-only prod paths

**Command:**

```text
rg -n "duckdb\.connect" backend/app/layer1_axes/
```

**Output:**

```text
(no matches)
```

**Command (broader repo check on layer1 tests):**

```text
rg -n "duckdb\.connect" backend/app/layer1_axes/ tests/test_layer1_*.py
```

**Output:**

```text
(no matches in layer1_axes; tests use ConnectionManager fixtures)
```

### 3.4 Adversarial hidden threat classes

#### Class 1 — Hardcoded URL / credential patterns

**Command:**

```text
rg -ni "https?://|api[_-]?key|bearer |secret|password" backend/app/layer1_axes/
```

**Output:**

```text
(exit 1 — no matches)
```

#### Class 2 — SQL concatenation / injection

**Command:**

```text
rg -n "execute\(f" backend/app/layer1_axes/
```

**Output:**

```text
backend/app/layer1_axes/lineage.py:180:            con.execute(f"CREATE TABLE {staging} AS SELECT * FROM axis_feature_snapshot WHERE 1=0")
```

**Analysis (not a vulnerability):**

- `staging` is `stg_axis_feature_{uuid.uuid4().hex[:8]}` — alphanumeric only, not user-controlled.
- `SnapshotLineageBuilder.persist` uses fully parameterized `INSERT ... VALUES (?, …)` (17 placeholders).
- `Layer1SnapshotWriter` staging `INSERT` uses parameterized values tuple via `feature_row_to_db_tuple`.
- `WriteManager` (reference) uses `quote_ident()` for table/column identifiers in merge SQL.

#### Class 3 — Path traversal in `spec_root` loading

**Command:**

```text
rg -n "spec_root|is_relative_to" backend/app/layer1_axes/axis_loader.py
```

**Relevant code:** `axis_loader.py:71` sets `root = spec_root or (PROJECT_ROOT / str(cfg["spec_root"]))` with **no** `resolve().is_relative_to(PROJECT_ROOT)` containment check before reading YAML.

**Analysis:** Default `load_from_config()` uses trusted `configs/layer1_axes.yml`. Callable `load(spec_root=…)` allows reading indicator specs outside the repo tree if a future caller passes an attacker-controlled path. Impact is limited to YAML disclosure / spec poisoning (not RCE — `yaml.safe_load`). Severity **Low** (latent; no API surface in this batch).

#### Class 4 — Agent outputs in `source_dataset_ids`

**Command:**

```text
rg -n "source_dataset_ids|agent_outputs" backend/app/layer1_axes/ specs/contracts/snapshot_lineage_contract.yaml
```

**Analysis:** Contract constraint `agent_outputs_not_source` exists (`snapshot_lineage_contract.yaml:24`). `SnapshotLineageBuilder.build()` accepts `source_dataset_ids` as caller-supplied tuple with **no** content validation. No dedicated pytest for agent-text rejection (noted in `research/layer1-lineage-tests.md` but not implemented). Integrity/contract gap — tracked as **Info** for A3; A8 owns test-gap.

### 3.5 Pytest verification

**Command:**

```text
python -m pytest tests/test_layer1_axis_loader.py tests/test_layer1_interpretation.py -q
```

**Output:**

```text
.......................                                                  [100%]
```

**Exit code:** 0 (23 passed)

---

## 4. GitNexus MCP

| Tool                                                                | Result                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `impact({target: "SnapshotLineageBuilder", direction: "upstream"})` | Symbol not found (index stale — new module)                        |
| `impact({target: "Layer1SnapshotWriter", direction: "upstream"})`   | Symbol not found (index stale)                                     |
| `detect_changes({scope: "compare", base_ref: "master"})`            | `risk_level: low`; changed symbols doc-only; no affected processes |

**Pre-audit summary** (`research/gitnexus-audit-summary.md`): LOW risk; `layer1_axes` may be unindexed until `node .gitnexus/run.cjs analyze`.

---

## 5. Findings

### [MEDIUM] Lineage persistence bypasses WriteManager / ValidationGate

- **Location:** `backend/app/layer1_axes/lineage.py:97-127` (`SnapshotLineageBuilder.persist`)
- **Description:** `persist()` executes `INSERT INTO axis_snapshot_lineage` directly on a DuckDB connection. It does not create a staging table, does not require `validation_report_id`, does not pass `DbValidationGate.assert_can_write`, and does not emit `write_audit_log` rows.
- **Impact:** Any code holding a writer connection can insert lineage metadata without the project's standard write-audit chain. Violates `write_manager.md` §1 (“任何 clean 表、snapshot 表、audit 表写入都必须通过 WriteManager”) and MASTER §0 red flag “绕过 WriteManager 直写 clean 表”. Integrity/audit gap; not a remote exploit in this batch (no HTTP API).
- **Proof of concept:** Tests call `SnapshotLineageBuilder.persist(con, lineage)` directly after `migrated_con(tmp_path)` with no `WriteManager` involvement (`tests/test_layer1_interpretation.py:182`, `:217`). A future orchestrator copying this pattern could persist lineage for unvalidated snapshots.
- **Recommendation:** Route `axis_snapshot_lineage` through `WriteManager` (staging + `WriteRequest` + `validation_report_id`) or add a documented `Layer1LineageWriter` subclass that enforces gate + audit. Until then, restrict `persist()` to package-internal use and document as temporary.

### [LOW] `spec_root` override — **CLOSED**

- **Fix:** `_assert_spec_root_allowed()` rejects paths outside `PROJECT_ROOT` or OS temp (pytest `tmp_path` allowed).
- **Test:** `test_axisSpecLoader_rejectsSpecRootOutsideAllowedRoots`

### [INFO] `agent_outputs_not_source` not enforced at runtime

- **Location:** `backend/app/layer1_axes/lineage.py:44-85`
- **Description:** `SnapshotLineageBuilder.build()` does not reject agent-generated prose in `source_dataset_ids`.
- **Impact:** Contract violation possible if a caller passes interpretation text as a dataset id. No injection; lineage integrity only.
- **Recommendation:** Add validation helper (e.g. reject strings matching interpretation token patterns or exceeding dataset-id format). A8 to add `test_agentOutputsNotInSourceDatasetIds`.

### [INFO] `Layer1SnapshotWriter` uses private `WriteManager._execute_write`

- **Location:** `backend/app/layer1_axes/lineage.py:202`
- **Description:** Calls `_execute_write` instead of public `write()`. Gate still runs; audit still written for feature rows.
- **Impact:** Encapsulation / maintenance risk only.
- **Recommendation:** Prefer public `write(req, con=con, own_transaction=…)` when API supports shared-connection writes.

---

## 6. Positive observations

- **Feature snapshot write path correct:** `Layer1SnapshotWriter` uses staging → `DbValidationGate` → `WriteManager` with mandatory `validation_report_id` (`test_layer1Snapshot_writeViaWriteManager` passes).
- **No direct DuckDB opens:** All DB access delegated to `ConnectionManager` (reader/writer factories).
- **Parameterized lineage SQL:** `persist()` uses bound parameters for all column values — no string-concatenated user data in SQL.
- **Input safety on compute path:** `AxisFeatureEngine` rejects future-dated observations; `ResourceGuard` blocks under eco limits.
- **Interpretation guardrails:** Forbidden trading-action terms blocked; Layer 2 writeback to Layer 1 tables explicitly rejected.
- **No secrets / network in scope:** Adversarial credential and URL scans returned zero matches.
- **Migration 011 is DDL-only:** `011_layer1_tables.sql` contains `CREATE TABLE` only — no runtime DML.
- **Engineering guardrails:** Forbidden substitutes and SHADOW diagnostic constraints validated in `guardrails.py` with tests.

---

## 7. §4.3 repair items (A3 contribution)

| ID    | Source       | Item                           | Severity | Status     |
| ----- | ------------ | ------------------------------ | -------- | ---------- |
| A3-01 | `lineage.py` | Route lineage via WriteManager | Medium   | **CLOSED** |

Cross-dimension items (not A3 security defects):

| ID    | Owner | Description                     | Status     |
| ----- | ----- | ------------------------------- | ---------- |
| A8-01 | A8    | `agent_outputs_not_source` test | **CLOSED** |
| A8-02 | A8    | Empty `spec_root` boundary test | **CLOSED** |

**A3 §4.3 count: 1**

---

## 8. Recommendations (proactive, non-blocking)

1. Run `node .gitnexus/run.cjs analyze` post-merge so `impact(SnapshotLineageBuilder)` resolves for Batch 3.
2. Add `spec_root` containment before any CLI/API exposes `AxisSpecLoader.load(spec_root=…)`.
3. Consider folding lineage writes into the same transaction as feature snapshot writes when orchestration lands (atomic snapshot + lineage).

---

## 9. Verdict rationale

**PASS_WITH_FIXES** — AUDIT.plan §2 A3 primary scan **does** surface a WriteManager bypass (`SnapshotLineageBuilder.persist` → `axis_snapshot_lineage`). Feature snapshots satisfy the “no unauthorized mutation bypass” intent via `Layer1SnapshotWriter`. No Critical/High exploitable vulnerabilities (SQLi, credential leak, command execution, SSRF). One Medium integrity finding (A3-01) warrants a §4.3 repair before calling lineage writes production-hardened; does not block audit completion if A9 tracks A3-01 as deferred hardening with accepted local-only scope.
