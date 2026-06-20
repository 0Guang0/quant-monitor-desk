# A4 audit-quality — §3.4

> Dimension: error handling, path traversal guard, JSON serialization  
> Scope: `backend/app/ops/db_inspector.py`, `scripts/qmd_ops.py`  
> Skills: code-review-and-quality + doubt-driven-development  
> Adversarial trigger: ≥1 boundary gap documented below

---

## Verdict: **PASS_WITH_FIXES**

Core inspect flow is sound: DB failures surface in `report.errors`, schema introspection degrades per-table, evidence partial failure becomes `warnings`, CLI maps `FAIL` → exit 1, and JSON output round-trips in tests. Two **Important** gaps remain in filesystem error handling and symlink-aware path guarding; neither blocks Batch 1 local-first closure but should be tracked in §4.3.

---

## Axis scores (1–5)

| Axis               | Score | Rationale                                                                                                            |
| ------------------ | ----- | -------------------------------------------------------------------------------------------------------------------- |
| Correctness        | 4     | Status derivation matches contract; `stat()` / `rglob` can escape structured `InspectReport` on edge IO failures     |
| Readability        | 5     | Clear dataclass report, fixed subdir scan, per-layer try/except with semantic `errors` vs `warnings`                 |
| Architecture       | 5     | Single `DbInspector` backend; `qmd_ops.py` is thin argparse + serialize wrapper                                      |
| Security (path/IO) | 4     | Fixed subdirs limit arbitrary traversal; **symlink/junction follow via `rglob` not bounded to resolved `data_root`** |
| Performance        | 4     | `--limit` hard-capped at 100; eco scan bounded; three separate `ConnectionManager.reader()` opens per inspect        |

---

## Findings

| ID    | Severity      | Location                                        | Finding                                                                                                                                                                                                                                                                                                                                                                                                                                                  | Recommended fix                                                                                                                                                                                                       |
| ----- | ------------- | ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A4-01 | **Important** | `db_inspector.py` `_count_files_under` L248–258 | **Path traversal guard incomplete:** scan uses `directory.rglob("*")`, which follows symlinks/junctions. If `data_root/raw` (or `parquet`/`audit`/`report`) is a link to a path outside `data_root`, files outside the configured root are counted — violating `db_inspect_cli.md` §9.4 (“must stay inside the configured data root”). Existing test `test_dbInspect_pathOutsideDataRoot_rejectedFromScan` only covers sibling dirs, not symlink escape. | Resolve each candidate with `path.resolve()` and require `is_relative_to(data_root.resolve())`, or walk with `followlinks=False` and skip non-relative paths; add `test_dbInspect_symlinkOutsideDataRoot_notCounted`. |
| A4-02 | **Important** | `db_inspector.py` `_inspect_db` L173            | **Unhandled `OSError` on `stat()`:** `file_size_bytes` calls `self.db_path.stat()` when `exists()` is true. Permission denied, race (file deleted/replaced), or special files can raise before `InspectReport` is returned — CLI exits with traceback instead of structured `FAIL` + `errors`.                                                                                                                                                           | Wrap `stat()` in try/except; set `file_size_bytes=0` and append `errors` (mirror connection_error pattern).                                                                                                           |
| A4-03 | **Important** | `db_inspector.py` `_count_files_under` L248–258 | **Unhandled filesystem errors during scan:** `rglob` on unreadable directories or broken symlinks can raise `PermissionError`/`OSError`, aborting `inspect()` without populating `data_root` or top-level `errors`.                                                                                                                                                                                                                                      | try/except around scan loop; set counts to 0, `scan_limited` as appropriate, append `warnings` or `errors` with path context.                                                                                         |
| A4-04 | Suggestion    | `qmd_ops.py` L71–73                             | **`--output` IO failures unhandled:** `mkdir` / `write_text` propagate as uncaught exceptions (disk full, permission denied). Acceptable for transitional CLI but inconsistent with structured error reporting elsewhere.                                                                                                                                                                                                                                | Catch `OSError`, print concise message to stderr, return exit 2.                                                                                                                                                      |
| A4-05 | Suggestion    | `db_inspector.py` L180–237                      | **Triple DB open:** `_inspect_db`, `_populate_schema_and_tables`, `_populate_evidence` each open a new read-only connection. Not incorrect; adds latency on large DBs.                                                                                                                                                                                                                                                                                   | Optional follow-up: single `with cm.reader()` context for all DB phases.                                                                                                                                              |
| A4-06 | Suggestion    | `qmd_ops.py` L67                                | **`json.dumps(..., default=str)` masks type bugs:** non-JSON-native values stringify silently instead of failing fast. Tests use `json.dumps(payload)` without `default=str`, so divergence between test and CLI paths.                                                                                                                                                                                                                                  | Prefer explicit serializers in `_latest_fetch` / `_latest_write` (already partial); drop `default=str` once contract types are guaranteed, or assert JSON round-trip in CLI test.                                     |

### Adversarial reconciliation (doubt-driven)

| Claim                                                 | Attack                                | Result                                                                               |
| ----------------------------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------ |
| “Path scan stays under `data_root`”                   | Symlinked `raw/` → `/tmp/outside`     | **Gap (A4-01)** — `rglob` follows links                                              |
| “Inspect always returns structured report on failure” | `stat()` or `rglob` raises mid-flight | **Gap (A4-02, A4-03)** — uncaught `OSError`                                          |
| “JSON output is contract-safe”                        | DuckDB datetime/decimal edge types    | **Mitigated** — isoformat + `default=str` in CLI; test covers `to_dict()` round-trip |

---

## What's done well

- Layered error model: connection/schema → `errors` (FAIL); evidence partial → `warnings` (PASS/WARN) — matches contract status semantics.
- `--limit` clamp `min(max(limit, 1), 100)` in `DbInspector.__init__` enforces contract `hard_cap: 100` (verified by A8 test).
- Per-table `_table_stats` isolates failures into `key_tables[].error` without aborting sibling counts.
- CLI exit code `0 if report.status != "FAIL" else 1` gives automation-friendly semantics.
- `quote_ident` on dynamic table/column names in SQL helpers (cross-check A3).

---

## Verification story

| Check              | Result                                                                                                                                        |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Tests reviewed     | **Yes** — `tests/test_ops_db_inspector.py` (10 tests): missing DB, JSON shape, path sibling isolation, limit cap, no-mutation, CLI subprocess |
| Build verified     | **Indirect** — A8/A5 report 10 passed; A4 review read-only                                                                                    |
| Security checked   | **Partial** — symlink escape cross-reviewed with A3 static scan (subdir fix insufficient for link follow)                                     |
| JSON serialization | **Yes** — `test_dbInspect_outputJsonShape_hasRequiredFields` asserts `json.dumps(payload)`; CLI adds `default=str` safety net                 |

---

## §4.3 Repair items

| ID    | Priority | Action                                                                      | Owner phase                     |
| ----- | -------- | --------------------------------------------------------------------------- | ------------------------------- |
| A4-01 | P2       | Symlink-aware path bounding in `_count_files_under` + regression test       | Next ops hardening or Batch 1.1 |
| A4-02 | P2       | Guard `db_path.stat()`; surface failure in `db.connection_error` / `errors` | Next ops hardening              |
| A4-03 | P2       | try/except around data-root file scan; degrade counts + report message      | Next ops hardening              |
| A4-04 | P3       | Optional CLI `--output` OSError handling                                    | Round 5 CLI polish              |
| A4-05 | P3       | Single-connection inspect refactor                                          | Performance follow-up           |
| A4-06 | P3       | Align JSON serialization strictness between tests and CLI                   | Contract test tighten           |

**Batch 1 gate:** No P0/P1 repairs required for `PASS_WITH_FIXES` overall verdict; A4-01–A4-03 should not block finish-work but must not be silently dropped from backlog.
