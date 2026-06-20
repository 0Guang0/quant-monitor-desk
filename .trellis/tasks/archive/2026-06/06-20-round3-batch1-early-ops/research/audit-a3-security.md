# A3 audit-security — §3.3

**Dimension:** A3 (audit-security)  
**Skills:** security-and-hardening + doubt-driven-development  
**Scope:** `backend/app/ops/`, `scripts/qmd_ops.py`  
**Date:** 2026-06-20  
**Verdict: PASS**

---

## 1. Summary

| Severity | Count |
| -------- | ----- |
| Critical | 0     |
| High     | 0     |
| Medium   | 0     |
| Low      | 0     |
| Info     | 2     |

Static scan confirms Phase A read-only invariants: no write path, no migration hooks, no forbidden CLI flags, no DML SQL. Adversarial hidden-class scans (hardcoded URLs, credential patterns, SQL concatenation) found no exploitable issues in scope. Two informational notes document trust-boundary assumptions appropriate for a local ops CLI.

**§4.3 repair items (A3):** None.

---

## 2. Trust boundaries (STRIDE sketch)

| Boundary   | Untrusted input                                           | Controls observed                                                                                         |
| ---------- | --------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| CLI argv   | `--db`, `--data-root`, `--limit`, `--output`, `--profile` | Thin wrapper → `DbInspector`; no free SQL; limit hard-capped 1–100; path scan fixed subdirs only          |
| DuckDB     | Local file at `--db`                                      | `ConnectionManager.reader()` → `duckdb.connect(..., read_only=True)`; no `writer()`                       |
| Filesystem | `data_root` subtree                                       | Scan limited to `raw/`, `parquet/`, `audit/`, `report` under configured root; `rglob` capped by `--limit` |
| Network    | N/A                                                       | No HTTP clients, URLs, or fetch orchestration in scope                                                    |

---

## 3. Commands and output

### 3.1 AUDIT.plan §2 A3 primary scan

**Command:**

```text
rg -n "writer\(|apply_migrations|duckdb\.connect\([^)]*\)(?!.*read_only)|--enable-qmt|INSERT |UPDATE |DELETE " backend/app/ops scripts/qmd_ops.py
```

**Output:**

```text
(no matches)
```

**Interpretation:** No mutation writers, migration application, non-read-only DuckDB opens, QMT enable flags, or DML verbs in the audited paths.

### 3.2 Supplementary in-scope checks

| Pattern                        | Command                                                      | Result                                                                      |
| ------------------------------ | ------------------------------------------------------------ | --------------------------------------------------------------------------- | ---------- |
| Direct `duckdb.connect`        | `rg -n "duckdb\.connect" backend/app/ops scripts/qmd_ops.py` | No matches (delegates to `ConnectionManager`)                               |
| `ConnectionManager.writer`     | `rg -n "writer" backend/app/ops scripts/qmd_ops.py`          | No matches                                                                  |
| `subprocess` / `eval` / `exec` | `rg -n "subprocess\|os\.system\|eval\(                       | exec\(" backend/app/ops scripts/qmd_ops.py`                                 | No matches |
| Forbidden contract flags       | Manual review of `qmd_ops.py` argparse                       | Only `db-inspect`; no `--sql`, `--write`, `--migrate`, `--enable-qmt`, etc. |

### 3.3 Adversarial hidden threat classes

#### Class 1 — Hardcoded URL variants

**Command:**

```text
rg -n "https?://|http://|www\.|api\.|\.com/|\.cn/" backend/app/ops scripts/qmd_ops.py
```

**Output:**

```text
(no matches)
```

**Why no finding:** Inspect path is offline/local. Contract `network_allowed_by_default: false` is satisfied. No SSRF or outbound callback surface.

#### Class 2 — JWT / API key / secret patterns

**Command:**

```text
rg -ni "jwt|api[_-]?key|bearer |secret|token|password|sk-[a-zA-Z0-9]" backend/app/ops scripts/qmd_ops.py
```

**Output:**

```text
(no matches)
```

**Why no finding:** No authentication, no secret material handling, no `print_secrets` path. JSON report exposes DB metadata only (paths, counts, statuses)—no credential fields in schema.

#### Class 3 — SQL concatenation / injection

**Command:**

```text
rg -n "f[\"'].*SELECT|f[\"'].*INSERT|execute\(f[\"']|\.format\(.*SELECT" backend/app/ops scripts/qmd_ops.py
```

**Output:**

```text
backend/app/ops/db_inspector.py:285:        row_count = con.execute(f"SELECT COUNT(*) FROM {quoted}").fetchone()[0]
backend/app/ops/db_inspector.py:327-331:    rows = con.execute(
        f"""
        SELECT {quoted_col}, COUNT(*)
        FROM {quoted_table}
        GROUP BY {quoted_col}
        """
```

**Analysis (not a vulnerability):**

- Dynamic identifiers pass through `quote_ident()` (`backend/app/db/sql_identifiers.py`), which enforces `^[a-z][a-z0-9_]{0,62}$` and doubles embedded quotes.
- `_table_stats` receives `name` from frozen `KEY_TABLES` tuple only.
- `_status_counts` is called exclusively with compile-time literals (`"data_sync_job"`, `"status"`, etc.) from `_populate_evidence`.
- Evidence queries (`_latest_fetch`, `_latest_write`) use static SQL strings.
- Contract forbids `--sql` and `free_sql_allowed: false` — satisfied.

**Why no finding:** F-string assembly is identifier-quoting with allowlist validation, not user-controlled SQL concatenation. No injection path from CLI arguments into query text.

---

## 4. GitNexus MCP

| Tool                                                     | Result                                                                                    |
| -------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `list_repos`                                             | `quant-monitor-desk` indexed; **34 commits behind HEAD** (stale)                          |
| `impact({target: "DbInspector", direction: "upstream"})` | Symbol not found (index lag)                                                              |
| `context({name: "DbInspector"})`                         | Symbol not found (index lag)                                                              |
| `detect_changes({scope: "compare", base_ref: "master"})` | `risk_level: low`; changed symbols are docs only; **no affected processes**               |
| `query({query: "DbInspector inspect db_inspector ops"})` | Returns `ConnectionManager.reader` in process symbols; confirms read-only connection path |

**Pre-audit summary** (`research/gitnexus-audit-summary.md`): blast radius confined to ops inspect path; `DbInspector.inspect` LOW risk; no HIGH/CRITICAL regressions.

**Note:** Re-run `node .gitnexus/run.cjs analyze` before future edits to refresh symbol-level impact on `DbInspector`.

---

## 5. Findings

### [INFO] Local CLI trust model — arbitrary `--db` / `--output`

- **Location:** `scripts/qmd_ops.py:29-37`, `72-73`
- **Description:** Operator may point `--db` at any filesystem DuckDB file and `--output` at any writable path.
- **Impact:** Intended for local diagnostics (JQ2PTrade-style `--db` override per `db_inspect_cli.md`). Risk is limited to the invoking OS user; not a remote attack surface.
- **Recommendation:** Document in runbooks that inspect is operator-trusted; no code change required for Phase A.

### [INFO] Path scan does not resolve symlinks

- **Location:** `backend/app/ops/db_inspector.py:248-257` (`_count_files_under` → `directory.rglob("*")`)
- **Description:** A symlink under `data_root/raw` (etc.) could cause counts to include files outside the nominal tree.
- **Impact:** Metadata count inflation only; no file content read, no DB write. Requires pre-existing filesystem access to plant symlinks.
- **Recommendation:** Optional hardening (future): `path.resolve().is_relative_to(directory.resolve())` per matched file. Not a Phase A blocker.

---

## 6. Positive observations

- **Read-only DB open enforced:** `ConnectionManager.reader()` uses `read_only=True` (`backend/app/db/connection.py:190-197`).
- **Contract alignment:** `ops_db_inspect_contract.yaml` `safety_invariants` (no writer, no migrations, no DML, no network, no QMT default) match implementation.
- **Identifier hygiene:** Shared `quote_ident` allowlist reused from DB layer.
- **Scan bounds:** `--limit` hard-capped at 100 in `DbInspector.__init__`; A8 test `test_dbInspect_limit_hardCapsAtContractMaximum` enforces.
- **Path scope:** File enumeration uses fixed subdirectories; A8 tests confirm outside-tree files are not counted.
- **No secret leakage:** Report JSON schema has no secret fields; errors stringify exceptions without stack traces to stdout by default.

---

## 7. §4.3 repair items (A3 contribution)

| ID  | Source | Item                            | Status     |
| --- | ------ | ------------------------------- | ---------- |
| —   | —      | No A3 security repairs required | **Closed** |

Cross-dimension §4.3 items (A8 boundary tests) are tracked in `audit.report.md` §3 and are **not** A3 security defects:

| ID    | Owner | Description                                           | Status |
| ----- | ----- | ----------------------------------------------------- | ------ |
| A8-01 | A8    | `test_dbInspect_limit_hardCapsAtContractMaximum`      | Done   |
| A8-02 | A8    | `test_dbInspect_pathOutsideDataRoot_rejectedFromScan` | Done   |

---

## 8. Recommendations (proactive, non-blocking)

1. Refresh GitNexus index post-merge so `impact(DbInspector)` resolves for future rounds.
2. If inspect CLI is ever exposed beyond operator shell (CI artifact upload, web wrapper), re-audit trust boundaries and add path allowlists.
3. Consider symlink guard in `_count_files_under` if data roots may be attacker-influenced.

---

## 9. Verdict rationale

**PASS** — AUDIT.plan §2 A3 pass condition met: no mutation/SQL-injection path in `backend/app/ops` or `scripts/qmd_ops.py`. Adversarial scans for URLs, credentials, and SQL concatenation produced no Critical/High/Medium findings; the sole dynamic SQL uses allowlisted identifiers via `quote_ident`. Aligns with A9 overall **PASS** and `gitnexus-audit-summary.md` LOW blast radius.
