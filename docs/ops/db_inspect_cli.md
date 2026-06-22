# QMD Ops DB Inspect CLI Design

> Status: user-frozen design input for Round 3 early planning. This document is not runtime code and does not participate in DB migration.
>
> Scope: long-lived, local-first, read-only operations CLI for inspecting the local DuckDB database and adjacent data-root evidence.
>
> Contract: `specs/contracts/ops_db_inspect_contract.yaml`.

## 1. Decision summary

The DB inspect tool is a **long-term formal read-only operations tool**, not a one-off Round 3 scratch script.

The final command family is:

```bash
qmd ops db-inspect
```

Round 3 v1 may use a transitional script entry only if packaging is not yet ready:

```bash
python scripts/qmd_ops.py db-inspect
```

The transitional script must call the same backend implementation module as the final console script. It must not become a separate implementation path.

## 2. First principles

The tool exists to answer one question safely:

> What does the local project database and data root prove right now, without changing anything?

Therefore the invariant is:

1. Open DuckDB in read-only mode.
2. Never mutate production DB.
3. Never trigger migration.
4. Never trigger external network fetch.
5. Never enable QMT / xqshare / Yahoo / broker terminal access by default.
6. Never execute user-supplied free SQL in v1.
7. Never print secrets, tokens, credentials, or raw large data rows.
8. Produce audit-friendly evidence that Plan / Audit can trace back to Round 3 deferred items.

## 3. Reference adoption boundary

External reference landing task: `R3-REF-OPS-DB-DATA-HEALTH` (`docs/implementation_tasks/ROUND_3_REFERENCE_LANDING/R3D_ops_db_data_health_reference.md`). Machine trace: `specs/contracts/ops_db_inspect_contract.yaml` `reference_landing`.

| Reference | URL | Adopt in db-inspect v1 | Deferred to |
| --------- | --- | ---------------------- | ----------- |
| EasyXT data integrity / diagnostics | `https://github.com/quant-king299/EasyXT` | Metadata-only inspect; PASS/WARN/FAIL status vocabulary | `docs/ops/data_health_cli.md` for domain rules (missing days, OHLC, outliers) |
| JQ2PTrade local DuckDB path override | `https://github.com/quant-king299/JQ2PTrade` | `--db` read-only path override | — |
| ptqmt-site local/privacy documentation | `https://github.com/quant-king299/ptqmt-site` | — (db-inspect emits JSON only) | `docs/ops/ops_report_cli.md` for offline Markdown/HTML |

| Reference pattern | Adopt | Do not adopt |
| ----------------- | ----- | ------------ |
| EasyXT data integrity / diagnostics | High-level check categories land in data-health design, not db-inspect v1 | Trading, order placement, GUI/QMT auto-login, hard-coded local paths, fixed single-table stock-daily assumptions, direct string-concatenated SQL |
| JQ2PTrade local DuckDB path override | `--db` / `--duckdb-path`-style local DB override and repeatable local validation | Backtest engine, strategy conversion, PTrade simulation loop |
| ptqmt-site local/privacy documentation | Local-only privacy language in report CLI | Online site shape or trading-platform tutorial content |

Adoption rule: borrow inspection concepts and local-first UX only; implement through this project's contracts, schema, resource boundaries, and Trellis traceability.

## 4. Final target shape

The final operations CLI family should become:

```bash
qmd ops env-doctor
qmd ops db-inspect
qmd data health
qmd source probe
qmd ops source-health snapshot
qmd ops report
```

Only `qmd ops db-inspect` is authorized for Round 3 v1 implementation. The others are future phases and must not be silently implemented as part of v1.

| Command                          | Final purpose                                                                                          | Implementation phase                                                                      |
| -------------------------------- | ------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------- |
| `qmd ops db-inspect`             | Read-only DB and data-root evidence inspection                                                         | Round 3 Batch 1 v1                                                                        |
| `qmd ops env-doctor`             | Local environment, dependency, config, and install checks                                              | Round 5 / release-readiness phase                                                         |
| `qmd data health`                | Domain-aware data quality checks such as missing dates, OHLC validity, duplicate keys, and as-of leaks | Batch 6 Phase C; design: `docs/ops/data_health_cli.md`; rules: `specs/contracts/data_quality_rules.yaml` `ops_cli_profiles` |
| `qmd source probe`               | Route preview and user-authorized staging source probe                                                 | Round 3 Batch 1 extension or Round 3 Batch 6, after source authorization rules are frozen |
| `qmd ops source-health snapshot` | Preview and later persist source health metrics                                                        | Batch 6, only after `source_health_snapshot` migration is designed                        |
| `qmd ops report`                 | Convert JSON evidence into local Markdown / HTML report                                                | Round 5 Phase E; design: `docs/ops/ops_report_cli.md`                                     |

## 5. Round 3 v1 scope

Round 3 v1 implements only the read-only DB inspect minimum closure.

### 5.1 v1 must answer

1. Does the DB file exist?
2. Can it be opened read-only?
3. Which tables exist?
4. How many rows are in each key table?
5. Does the DB look schema-only / empty-data?
6. Does the project data root contain raw / parquet evidence?
7. What are the latest fetch, sync job, validation, conflict, manual review, and write evidence rows by metadata?

### 5.2 v1 must not implement

- Free SQL execution.
- Raw row browsing by default.
- External network source probing.
- QMT / xqshare / Yahoo live validation.
- Data quality domain rules such as OHLC or missing-trading-day checks.
- `source_health_snapshot` table write.
- Markdown / HTML report generation.
- Any migration or schema auto-repair.

## 6. CLI contract

### 6.1 Final command

```bash
qmd ops db-inspect \
  --db data/duckdb/quant_monitor.duckdb \
  --data-root data \
  --format text
```

### 6.2 Transitional command

```bash
python scripts/qmd_ops.py db-inspect \
  --db data/duckdb/quant_monitor.duckdb \
  --data-root data \
  --format json
```

The transitional command is allowed only as a thin wrapper around `backend/app/ops/db_inspector.py`.

### 6.3 Arguments

| Argument               | Required | Default                                                                                                       | v1 behavior                                                                                                   |
| ---------------------- | -------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `--db`                 | No       | `$QMD_DATA_ROOT/duckdb/quant_monitor.duckdb`; if `QMD_DATA_ROOT` is unset, `data/duckdb/quant_monitor.duckdb` | Read-only target DB path                                                                                      |
| `--data-root`          | No       | `$QMD_DATA_ROOT`; if unset, `data`                                                                            | Root scanned for raw/parquet/file evidence                                                                    |
| `--format`             | No       | `text`                                                                                                        | `text` or `json`                                                                                              |
| `--output`             | No       | stdout                                                                                                        | Optional output file for JSON/text; parent directory must already exist (Phase A does not create parent dirs) |
| `--limit`              | No       | `20`                                                                                                          | Maximum preview metadata rows per evidence category; hard cap `100`                                           |
| `--include-path-check` | No       | enabled in v1                                                                                                 | Count raw/parquet candidate files under safe data-root subdirectories                                         |
| `--profile`            | No       | current `QMD_RESOURCE_PROFILE` or `eco`                                                                       | Resource profile passed to connection manager when applicable                                                 |

### 6.4 Forbidden arguments in v1

The following must not exist in v1:

```text
--sql
--write
--migrate
--allow-network
--enable-qmt
--enable-xqshare
--show-secrets
--full-scan
```

If any future version adds a risky flag, the design must be amended first and the flag must default to disabled.

## 7. Implementation locations

| Artifact               | Path                                                                        | Role                                             |
| ---------------------- | --------------------------------------------------------------------------- | ------------------------------------------------ |
| Backend service        | `backend/app/ops/db_inspector.py`                                           | Pure inspection logic; reusable by CLI and tests |
| Output models          | `backend/app/ops/models.py` or local typed dataclasses in `db_inspector.py` | Stable report structure                          |
| Final CLI entry        | `backend/app/cli/main.py`                                                   | Long-term `qmd` console script target            |
| Transitional CLI entry | `scripts/qmd_ops.py`                                                        | Temporary wrapper only; no duplicate logic       |
| Tests                  | `tests/test_ops_db_inspector.py`                                            | Fixture DB and no-mutation tests                 |
| Design doc             | `docs/ops/db_inspect_cli.md`                                                | Human-readable authority                         |
| Machine contract       | `specs/contracts/ops_db_inspect_contract.yaml`                              | Command and output contract                      |

Implementation must not land in `docs/` or `specs/`.

## 8. Read-only and safety model

### 8.1 DuckDB access

Use the existing project read-only connection path where possible:

```text
ConnectionManager(db_path).reader()
```

If direct DuckDB access is needed internally, it must use:

```text
duckdb.connect(str(db_path), read_only=True)
```

### 8.2 Mutation prevention

The inspector must not call:

- `apply_migrations`
- `ConnectionManager.writer()`
- `DuckDBWriteManager`
- `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `DROP`, `ALTER`, `COPY TO`, or `EXPORT`
- source fetch / sync orchestration functions

### 8.3 SQL construction

v1 may issue only fixed internal metadata queries against known tables. It must validate SQL identifiers through existing identifier utilities if table names are interpolated.

No user-provided SQL string is accepted in v1.

## 9. v1 report model

### 9.1 Top-level shape

```json
{
  "status": "PASS|WARN|FAIL",
  "generated_at": "2026-06-20T00:00:00Z",
  "mode": "read_only",
  "db": {},
  "data_root": {},
  "schema": {},
  "key_tables": [],
  "evidence": {},
  "warnings": [],
  "errors": [],
  "deferred_item_mapping": []
}
```

### 9.2 Status rules

| Status | Meaning                                                                                                                    |
| ------ | -------------------------------------------------------------------------------------------------------------------------- |
| `PASS` | DB exists, opens read-only, key metadata checks complete, and no critical evidence gap is detected                         |
| `WARN` | DB opens, but appears schema-only, lacks raw/parquet evidence, lacks fetch/job evidence, or has open review/conflict items |
| `FAIL` | DB missing, cannot be opened read-only, schema introspection fails, or safety invariant is violated                        |

### 9.3 DB block

```json
{
  "path": "data/duckdb/quant_monitor.duckdb",
  "exists": true,
  "read_only_open": true,
  "file_size_bytes": 123456,
  "connection_error": null
}
```

### 9.4 Data-root block

```json
{
  "path": "data",
  "exists": true,
  "raw_files_count": 0,
  "parquet_files_count": 0,
  "audit_files_count": 0,
  "report_files_count": 0,
  "scan_limited": true
}
```

The path scan must stay inside the configured data root and must not traverse arbitrary system paths.

### 9.5 Key table row counts

v1 must attempt row counts for these tables when present:

| Table                 | Evidence purpose                    |
| --------------------- | ----------------------------------- |
| `schema_version`      | Applied schema/migration evidence   |
| `source_registry`     | Source configuration evidence       |
| `file_registry`       | Registered raw/file evidence        |
| `fetch_log`           | Fetch/source evidence               |
| `data_sync_job`       | Job lifecycle evidence              |
| `job_event_log`       | Job transition evidence             |
| `validation_report`   | Data validation evidence            |
| `data_quality_log`    | Quality issue evidence              |
| `source_conflict`     | Source conflict evidence            |
| `manual_review_queue` | Human review evidence               |
| `write_audit_log`     | Clean/write evidence                |
| `resource_guard_log`  | Resource protection evidence        |
| `instrument_registry` | Security master evidence            |
| `security_bar_1d`     | Security-level market data evidence |

Missing tables are reported as metadata facts, not automatic failures, because schema coverage may vary by phase. Missing all key tables is a `FAIL` or `WARN` depending on whether the DB can be opened and whether `schema_version` exists.

### 9.6 Evidence block

The report should include metadata-only latest/status summaries:

```json
{
  "latest_fetch": {
    "fetch_time": null,
    "source_id": null,
    "status": null,
    "row_count": null
  },
  "job_status_counts": {},
  "validation_status_counts": {},
  "conflict_status_counts": {},
  "manual_review_status_counts": {},
  "latest_write": null
}
```

Do not print full raw data payloads, request params, credentials, or large row samples.

### 9.7 Deferred item mapping

v1 output must include trace hints for Round 3 early closure:

| Deferred item             | Evidence field                                                                                            |
| ------------------------- | --------------------------------------------------------------------------------------------------------- |
| `DB-R3-001`               | `data_root.raw_files_count`, `data_root.parquet_files_count`, key table row counts, `file_registry` count |
| `DB-R3-002`               | `db.exists`, `db.read_only_open`, schema/table introspection                                              |
| `R3-PARTIAL-2`            | `latest_fetch`, `job_status_counts`, `validation_status_counts`                                           |
| `R2.6-IMPL-8`             | No live source enabled by this tool; only route/fetch evidence already present in DB may be reported      |
| `R3-EARLY-DB-INSPECT-CLI` | Command availability, read-only mode, JSON output, no-mutation tests                                      |

### 9.8 Trust boundary (Phase A)

`db-inspect` is an **operator-trusted local CLI**. The invoking OS user may pass arbitrary `--db` and `--output` paths; the tool does not sandbox filesystem access beyond fixed `data_root` scan subdirs. Do not expose this CLI to untrusted remote callers without additional path allowlists and authentication.

## 10. Text output UX

Text mode should be readable by a non-expert operator:

```text
QMD DB Inspect: WARN
DB: data/duckdb/quant_monitor.duckdb exists and opened read-only
Tables: 12 found
Evidence: fetch_log=0, data_sync_job=0, validation_report=0
Data root: raw=0, parquet=0
Meaning: database is present, but this run does not prove real vendor data ingestion yet.
Next: run user-authorized staging fetch or keep DB-R3-001 deferred.
```

Text mode is for humans. JSON mode is the audit contract.

## 11. Tests and acceptance

### 11.1 Required tests

| Test                          | Required assertion                                                    |
| ----------------------------- | --------------------------------------------------------------------- |
| Missing DB                    | Returns `FAIL`, no traceback-only output                              |
| Empty fixture DB with schema  | Returns `WARN`, reports tables and zero data rows                     |
| Fixture DB with evidence rows | Returns row counts and latest metadata correctly                      |
| Read-only invariant           | Test DB is not modified; no migration/write APIs are called           |
| Forbidden SQL flag            | v1 CLI rejects or does not expose free SQL                            |
| Output JSON shape             | JSON matches `ops_db_inspect_contract.yaml` required top-level fields |
| Path scan guard               | Scanner stays under data root and counts raw/parquet candidates only  |

### 11.2 Acceptance commands

Round 3 v1 implementation must run at least:

```bash
pytest tests/test_ops_db_inspector.py -q
pytest tests/test_documentation_index.py tests/test_project_scaffold.py -q
```

If packaging/CLI entry is implemented in the same Trellis batch, also run the relevant CLI smoke test.

## 12. Phase plan

| Phase                                          | When                                            | Scope                                                                                                          | Must not include                                                      |
| ---------------------------------------------- | ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| Phase A / Round 3 Batch 1                      | First implementation                            | `qmd ops db-inspect` read-only summary, JSON output, key table counts, raw/parquet evidence, no-mutation tests | Free SQL, network, migration, data health rules, source health writes |
| Phase B / Round 3 Batch 1 extension or Batch 6 | After v1 JSON stabilizes                        | `qmd source probe --route-preview --no-fetch`                                                                  | User-authorized staging fetch unless separately approved              |
| Phase C / Batch 6 or later                     | After data-quality profiles are selected        | `qmd data health` domain-aware checks from `data_quality_rules.yaml`                                           | Writing results to production tables by default                       |
| Phase D / Batch 6 migration work               | After `source_health_snapshot` migration design | `qmd ops source-health snapshot --read-only-preview`; optional write mode only after migration                 | Creating tables from CLI without migration                            |
| Phase E / Round 5 release/reporting            | After JSON evidence shape is stable             | `qmd ops report` local Markdown/HTML report from JSON evidence                                                 | Uploading data or reports                                             |
| Phase F / Release hardening                    | Round 5 / final packaging                       | `qmd ops env-doctor`, console script packaging, docs anchors, release manifest coverage                        | New broad dependencies without approval                               |

## 13. Trellis planning requirements

When Plan creates the Trellis task for `R3-EARLY-DB-INSPECT-CLI` or any batch that touches this tool:

1. `MASTER.plan.md` Source Context Index must include this document and `specs/contracts/ops_db_inspect_contract.yaml`.
2. `MASTER.plan.md` must state whether the batch implements only Phase A or also a later phase.
3. `implement.jsonl` may include this document only if Execute must read the original design. Otherwise MASTER must summarize the exact Phase A constraints.
4. `AUDIT.plan.md` must verify no-mutation, no-network, JSON shape, and deferred item trace evidence.
5. Any future phase not explicitly authorized here must stay out of scope and be re-deferred.

## 14. Original execution task impact

The following original task cards must treat this document as a Plan input when they are re-planned or when a new Trellis MASTER is generated:

| Task / planning source                                                                                                           | Why this design matters                                                                        |
| -------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `docs/implementation_tasks/ROUND3_EARLY_CLOSE_PLAN.md`                                                                           | Declares Local DB inspect CLI as Round 3 early work                                            |
| `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/README.md`                                                                    | Points Round 3 planning to the unnumbered DB inspect CLI boundary                              |
| `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016D_define_data_sync_quick_reference_and_error_guides.md` | Future CLI command matrix must not conflict with `qmd ops db-inspect`                          |
| `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016F_define_prod_equivalent_scale_benchmark.md`            | Production-equivalent smoke evidence may be summarized by DB inspect output                    |
| `docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/031_implement_integration_smoke_tests.md`                                 | Integration smoke can verify the DB inspect CLI as a read-only evidence check                  |
| `docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/033_implement_security_and_boundary_tests.md`                             | Boundary tests must assert no free SQL, no write, no network, and no frontend direct DB access |
| `docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/034_implement_docs_consistency_check.md`                                  | Docs/spec/index consistency must include this design and contract                              |
| `docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/035_implement_final_package_cleanup.md`                                   | Cleanup allowlist must preserve the design and contract                                        |
| `docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/036_create_final_release_manifest.md`                                     | Final manifest must include this design and contract once implemented/accepted                 |

This does not mean Execute must always read the original task cards. Plan must fold this design into MASTER/AUDIT trace according to `docs/implementation_tasks/TASK_INPUT_CONTEXT_INDEX.md`.

## 15. Open decisions now closed

The user has confirmed:

1. The DB inspect CLI is a long-term formal read-only ops tool.
2. v1 command target is `qmd ops db-inspect`.
3. `scripts/qmd_ops.py` is allowed only as a transitional thin wrapper.
4. v1 forbids free SQL, DB writes, migrations, network access, secret printing, raw row browsing by default, and production data mutation.
5. v1 must emit JSON and human-readable text.
6. v1 must inspect DB presence, read-only open, key table row counts, metadata evidence, and raw/parquet data-root evidence.
7. `qmd data health`, `qmd source probe`, `qmd ops source-health snapshot`, and `qmd ops report` are future phases, not v1 scope.
