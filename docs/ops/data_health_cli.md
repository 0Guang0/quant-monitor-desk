# QMD Data Health CLI Design

> Status: user-frozen design input for Batch 6 / Phase C. This document is not runtime code and does not participate in DB migration.
>
> Scope: local-first, read-only-by-default domain data quality checks against QMD-owned tables and contracts.
>
> Contract inputs: `specs/contracts/data_quality_rules.yaml` (`ops_cli_profiles`), `specs/contracts/source_conflict_rules.yaml`, `docs/modules/data_validation_and_conflict.md`.
>
> Reference landing: `R3-REF-OPS-DB-DATA-HEALTH` / `R3D_ops_db_data_health_reference.md`.

## 1. Decision summary

The data health tool answers:

> For a chosen data domain and date window, do QMD tables satisfy contract-driven quality rules—without mutating production data or fetching external sources?

Final command family:

```bash
qmd data health
```

Round 3 v1 (`qmd ops db-inspect`) does **not** implement domain quality rules. This design is the Batch 6 implementation authority.

Transitional entry (when packaging is not ready):

```bash
python scripts/qmd_ops.py data-health
```

## 2. Reference adoption boundary

| Reference pattern | Source | Adopt | Do not adopt |
| ----------------- | ------ | ----- | ------------ |
| Integrity categories: missing trading days, field quality, price-relation, outliers | [EasyXT](https://github.com/quant-king299/EasyXT) | Map categories to `data_quality_rules.yaml` rule IDs per domain; PASS/WARN/FAIL summary | Hardcoded `stock_daily` table, string-concatenated SQL, automatic source fallback, QMT auto-login |
| Local DB path override and repeatable CLI runs | [JQ2PTrade](https://github.com/quant-king299/JQ2PTrade) | `--db` / `--duckdb-path`-style override; `--domain` + `--format json` for automation | Backtest engine, strategy conversion, PTrade/JoinQuant order APIs |
| Operator-readable status and troubleshooting flow | EasyXT + `docs/ops/TROUBLESHOOTING.md` | Text mode with meaning + next-step hints; `error_code` + `docs_anchor` on failures | Trading-platform tutorial content |

Adoption rule: borrow check **categories** and local CLI ergonomics only. Rules, tables, and severities come from QMD contracts—not external schemas.

## 3. Relationship to `qmd ops db-inspect`

| Tool | Question | Default mode | Phase |
| ---- | -------- | ------------ | ----- |
| `qmd ops db-inspect` | Does the DB exist, open read-only, and expose metadata/evidence row counts? | read-only | Round 3 Batch 1 (Phase A) |
| `qmd data health` | Do domain rows satisfy `data_quality_rules.yaml` for the requested window? | read-only | Batch 6 (Phase C) |

`db-inspect` must not silently grow into data-health checks. Operators run `db-inspect` first for presence/evidence, then `data health` for domain rules.

## 4. Check categories (QMD-owned)

Each category maps to existing validator contracts—not EasyXT table names.

| Category | Example rule IDs | QMD tables (indicative) |
| -------- | ---------------- | ----------------------- |
| Calendar completeness | `STALE_DATA`, `INSUFFICIENT_HISTORY` + domain extensions | `security_bar_1d`, layer tables per `--domain` |
| Field / schema quality | `MISSING_REQUIRED_FIELD`, `SCHEMA_DRIFT`, `INVALID_ENUM` | staging or clean tables per domain |
| Price relation | `INVALID_PRICE_RANGE`, `NEGATIVE_PRICE`, `INVALID_VOLUME` | `security_bar_1d` |
| Duplicate keys | `DUPLICATE_PRIMARY_KEY`, `MISSING_PRIMARY_KEY` | domain primary keys |
| Source lineage | `MISSING_SOURCE_USED`, `FALLBACK_WITHOUT_REASON` | `fetch_log`, `validation_report`, layer1 tables |
| Conflict awareness | read-only summary from `source_conflict` | `source_conflict`, `manual_review_queue` |

Conflict **resolution** stays in `SourceConflictValidator` / `ReconcileJob`. Data health CLI may **report** open conflicts but must not auto-reconcile or write.

## 5. CLI contract (design)

### 5.1 Command shape (R3FR-06 canonical)

```bash
qmd data health \
  --domain market_bar_1d \
  --profile market_bar_p0 \
  --evidence-dir tests/fixtures/data_health/good_bundle \
  --format json
```

Optional read-only DB override:

```bash
qmd data health --db-path data/duckdb/quant_monitor.duckdb --domain market_bar_1d --profile market_bar_p0 --evidence-dir <path>
```

### 5.2 Arguments (canonical — frozen §6.3)

| Argument | Required | Default | Behavior |
| -------- | -------- | ------- | -------- |
| `--domain` | Yes | — | `market_bar_1d` (maps to `ops_cli_profiles`) |
| `--profile` | Yes | — | `market_bar_p0` (not `--rule-set`) |
| `--evidence-dir` | Yes* | — | Evidence bundle root (`good_bundle` in tests) |
| `--db-path` | No | — | Optional read-only DuckDB (not `--db`) |
| `--start` / `--end` | No | — | Inclusive date window on bar rows |
| `--max-rows` | No | 1000 | Cap report detail rows |
| `--format` | No | `json` | `json` or `text` |

\* Required for supported profiles in the R3FR-02+06 vertical slice.

Legacy design note: older drafts used `--db` and `--rule-set`; implementation uses `--db-path` and `--profile`.

### 5.3 Forbidden arguments (v1 design)

```text
--write
--migrate
--allow-network
--enable-qmt
--enable-xqshare
--sql
--full-market-scan
--show-secrets
--auto-reconcile
```

Optional `--write-report` may be designed in a later sub-batch only after explicit user approval and migration for persisted health snapshots.

## 6. Report model (JSON — R3FR-06 §5)

CLI JSON envelope (authoritative for `qmd data health`):

```json
{
  "command": "health",
  "dry_run": true,
  "side_effects_allowed": false,
  "domain": "market_bar_1d",
  "profile": "market_bar_p0",
  "status": "PASS",
  "rules_run": [],
  "issue_counts_by_severity": {},
  "row_count_checked": 0,
  "window": { "start": "", "end": "" },
  "source_ids": [],
  "content_hash_coverage": {},
  "schema_hash_coverage": {},
  "limitations": [],
  "report_path": null
}
```

`report_path` is optional. Internal `DataHealthReport` checks remain available for C-20 staged profiles; CLI maps to the envelope above.

Legacy design shape (superseded for CLI output):

Each finding item:

```json
{
  "rule_id": "INVALID_PRICE_RANGE",
  "severity": "failed",
  "affected_rows": 0,
  "sample_count": 0,
  "docs_anchor": "specs/contracts/data_quality_rules.yaml"
}
```

Text mode must state meaning and next step (EasyXT-style operator UX), e.g.:

```text
QMD Data Health: WARN (market_bar_1d)
Window: 2024-01-01 .. 2024-12-31 | checked_rows=120
Failed: 0 | Warning: 2 (STALE_DATA, INSUFFICIENT_HISTORY)
DB: data/duckdb/quant_monitor.duckdb (read-only)
Next: run user-authorized staging fetch or narrow --start/--end.
```

## 7. Safety invariants

1. Open DuckDB read-only by default (`ConnectionManager.reader()` or `duckdb.connect(..., read_only=True)`).
2. Never call `apply_migrations`, `ConnectionManager.writer()`, or `DuckDBWriteManager`.
3. Never trigger external fetch or enable QMT/xqshare from this CLI.
4. Never print secrets, tokens, or large raw row dumps.
5. Respect `resource_limits.yaml` row/sample caps; default to bounded windows.
6. Every FAIL must include `error_code` and `docs_anchor` compatible with `docs/ops/ERROR_CODE_GUIDE.md`.

## 8. Implementation locations (future)

| Artifact | Path |
| -------- | ---- |
| Backend service | `backend/app/ops/data_health.py` |
| CLI wrapper | `scripts/qmd_ops.py` or `backend/app/cli/main.py` |
| Tests | `tests/test_ops_data_health.py` |
| Design doc | `docs/ops/data_health_cli.md` (this file) |
| Machine rules | `specs/contracts/data_quality_rules.yaml` |

## 9. Phase plan

| Phase | When | Scope |
| ----- | ---- | ----- |
| Phase A | Round 3 Batch 1 | `qmd ops db-inspect` only (no domain rules) |
| Phase C | Batch 6 | `qmd data health` read-only checks from `ops_cli_profiles` |
| Later | After migration design | optional persisted health snapshot write mode |

## 10. Trellis trace

- Plan Source Context Index must cite this doc when implementing Batch 6 data health.
- External URLs: EasyXT, JQ2PTrade (see §2); ptqmt-site applies to `ops_report_cli.md` report rendering only.
