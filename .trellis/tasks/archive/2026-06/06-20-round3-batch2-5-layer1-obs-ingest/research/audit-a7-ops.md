# A7 audit-ops — §4.7

**Agent:** audit-ops (A7)  
**Task:** `06-20-round3-batch2-5-layer1-obs-ingest` (Round 3 Batch 2.5)  
**Date:** 2026-06-20  
**Skill:** doubt-driven-development  
**Verdict: PASS**

---

## Protocol trace

| Step | Artifact                                                                   | Status   |
| ---- | -------------------------------------------------------------------------- | -------- |
| 1    | Phase 7 + `AUDIT.plan.md` + `audit.jsonl`                                  | Read     |
| 2    | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §3/§4.2 Batch 2.5 + `018A` + ops docs | Read     |
| 3    | MASTER §0.6 + `011_layer1_tables.sql`                                      | Verified |
| 4    | `research/gitnexus-audit-summary.md` (7.pre)                               | Read     |
| 5    | doubt-driven-development adversarial cycle                                 | §6 below |
| 6    | AUDIT.plan §2 A7 matrix                                                    | Executed |

**Isolation constants (AUDIT.plan §0):**

- `AUDIT_SANDBOX`: `.audit-sandbox/r3b25-audit`
- `AUDIT_PROD_ROOT`: `.audit-sandbox/r3b25-audit-prod-equiv` (not required for A7; prod-path uses read-only hash on project `data/duckdb/`)

---

## 1. Production path — `data/duckdb/` hash unchanged

Audit performed read-only hash on project production tree; **no writes to `data/duckdb/`**.

| Field         | Value                                                              |
| ------------- | ------------------------------------------------------------------ |
| Path          | `data/duckdb/quant_monitor.duckdb`                                 |
| Size          | 4,468,736 bytes                                                    |
| SHA256 before | `5EB65E0EDAAAB223A77C5A5D2660603383836704B4C0ECE1EB4AEBB047F1682E` |
| SHA256 after  | `5EB65E0EDAAAB223A77C5A5D2660603383836704B4C0ECE1EB4AEBB047F1682E` |
| Unchanged     | **true**                                                           |

**Sidecar sweep** (`data/duckdb/`):

| File                   | SHA256                                                             | Size      |
| ---------------------- | ------------------------------------------------------------------ | --------- |
| `.gitkeep`             | `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` | 0         |
| `quant_monitor.duckdb` | `5EB65E0EDAAAB223A77C5A5D2660603383836704B4C0ECE1EB4AEBB047F1682E` | 4,468,736 |

Matches Batch 2 A7 baseline hash — production DB was not mutated during this audit.

---

## 2. cli-sandbox — `init_db` ×2 on prod-equivalent copy

**Environment:** Windows PowerShell; `.venv\Scripts\python.exe`; `QMD_DATA_ROOT=.audit-sandbox/r3b25-audit`

```powershell
Copy-Item data\duckdb\quant_monitor.duckdb .audit-sandbox\r3b25-audit\duckdb\
$env:QMD_DATA_ROOT = (Resolve-Path .audit-sandbox\r3b25-audit).Path
python scripts/init_db.py   # run 1
python scripts/init_db.py   # run 2
```

| Run | Output                      | DB SHA256 after                                                    |
| --- | --------------------------- | ------------------------------------------------------------------ |
| 1   | `applied none (up to date)` | `5EB65E0EDAAAB223A77C5A5D2660603383836704B4C0ECE1EB4AEBB047F1682E` |
| 2   | `applied none (up to date)` | `5EB65E0EDAAAB223A77C5A5D2660603383836704B4C0ECE1EB4AEBB047F1682E` |

**Run1 hash == Run2 hash:** **true**

### Migration 011 state (sandbox copy)

| Check                                   | Result                                                                                                                                                                        |
| --------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `011_layer1_tables` in `schema_version` | **yes** (1 row)                                                                                                                                                               |
| Axis tables present                     | 7: `axis_registry`, `axis_indicator_registry`, `axis_indicator_profile`, `axis_observation`, `axis_feature_snapshot`, `axis_interpretation_snapshot`, `axis_snapshot_lineage` |
| All migrations applied                  | `001` … `011` (11 versions)                                                                                                                                                   |

### Fresh-DB idempotency (sandbox `.audit-sandbox/r3b25-audit-adv2-fresh`)

| Run | Applied                                      | DB SHA256                                                          |
| --- | -------------------------------------------- | ------------------------------------------------------------------ |
| 1   | `['001_foundation', …, '011_layer1_tables']` | `DA40F8553A670C060C194C131BD88A833E337A329D8AF2A6F8420A7D870398CB` |
| 2   | `none (up to date)`                          | `DA40F8553A670C060C194C131BD88A833E337A329D8AF2A6F8420A7D870398CB` |

**Run1 hash == Run2 hash:** **true** — full migration chain including 011 is idempotent on cold init.

---

## 3. Migration 011 strategy (MASTER §0.6 + DDL review)

**MASTER §0.6** marks `backend/app/db/migrations/011_layer1_tables.sql` as **must-read** — authoritative DDL for `axis_observation` and related Layer 1 tables. §0.6.1 filters migrations `004`–`010` as historical; Phase 0 gate treats 011 as runtime authority (`execute-evidence/phase0_db_contract_gate.md`).

**Idempotency mechanisms:**

| Layer       | Mechanism                                        | Evidence                       |
| ----------- | ------------------------------------------------ | ------------------------------ |
| SQL         | All 7 tables use `CREATE TABLE IF NOT EXISTS`    | `011_layer1_tables.sql` L3–148 |
| Runner      | `apply_migrations` skips `version_id in already` | `migrate.py` L66–67            |
| Integrity   | `verify_applied_checksums` before apply          | `migrate.py` L59, L31–51       |
| Transaction | Per-migration `BEGIN`/`COMMIT`/`ROLLBACK`        | `migrate.py` L70–91            |

**Phase 0 cross-check:** `phase0_db_contract_gate.md` confirms 7× `axis_*` tables via `test_layer1Ingestion_phase0_applyMigrations_createsAxisTables`.

**Deferred (non-blocking):** `B2.5-O-02` — `specs/schema/schema.sql` lags migration 011; runtime authority is migrations, not spec mirror.

---

## 4. Ops docs alignment

### `docs/ops/db_inspect_cli.md`

| Invariant                                | Batch 2.5 relevance                            | A7 check                                                           |
| ---------------------------------------- | ---------------------------------------------- | ------------------------------------------------------------------ |
| Read-only DuckDB open                    | Phase 1/4 inspect evidence uses `db_inspector` | **PASS** — A7 did not invoke inspect; prod hash proves no mutation |
| Never mutate production DB               | AUDIT.plan A7 prod-path                        | **PASS**                                                           |
| Never trigger migration                  | Inspect path separate from `init_db`           | **PASS**                                                           |
| Contract: `ops_db_inspect_contract.yaml` | MASTER §0.6 must-read                          | Indexed in `audit.jsonl` L7                                        |

### `docs/ops/lock_and_concurrency_policy.md`

| Policy                                 | Implementation               | A7 relevance                                                      |
| -------------------------------------- | ---------------------------- | ----------------------------------------------------------------- |
| Single-writer via `DuckDBWriteManager` | Phase 4 clean write          | Ingestion path compliant (PH-A4 PASS)                             |
| Cross-process `.write.lock`            | `ConnectionManager.writer()` | `init_db` uses writer lock — no concurrent write during migration |
| Read-only connections for inspect      | `read_only=True`             | Inspect path isolated from migration                              |

`init_db` correctly acquires writer via `ConnectionManager` (`scripts/init_db.py` L25–27); no bypass of WriteManager policy for clean-table ingestion (migrations are schema DDL, not clean observation writes).

---

## 5. GitNexus audit summary (7.pre)

From `research/gitnexus-audit-summary.md`:

- A7 focus: **init_db migration 011 idempotency**
- Touch surfaces: `ingestion.py`, observation writer/mapper, `DbValidationGate`, `DuckDBWriteManager`
- Isolation constants match AUDIT.plan §0

No code edits in this audit; GitNexus `impact(apply_migrations)` not required for read-only verification.

---

## 6. Doubt-driven adversarial — failure scenario (re-run idempotency)

**CLAIM:** Second `init_db` on a DB that already has migration 011 applied produces no DDL drift and no duplicate `schema_version` rows.

**WHY IT MATTERS:** Batch 2.5 clean-write path depends on stable `axis_observation` schema; a non-idempotent re-apply could corrupt production during ops recovery.

### Scenario — crash after 011 DDL, before `schema_version` insert

Simulated on sandbox copy (`.audit-sandbox/r3b25-audit-adv1`):

1. Copy prod DB (011 tables present, `schema_version` row for 011 deleted).
2. Run `init_db` once.

| Step                                      | Observation                                                    |
| ----------------------------------------- | -------------------------------------------------------------- |
| Pre-rerun                                 | `011` schema_version rows = 0; `axis_observation` table exists |
| `init_db` output                          | `applied ['011_layer1_tables']`                                |
| Post-rerun `schema_version` count for 011 | **1**                                                          |
| Duplicate version rows                    | **[]**                                                         |
| `axis_observation` still present          | **yes**                                                        |

**RECONCILE:** `CREATE TABLE IF NOT EXISTS` makes DDL replay safe; `apply_migrations` restores the missing `schema_version` row without duplicates. **Finding: none — claim holds.**

### Stop condition

One adversarial cycle; no P1/P2 findings on ops/migration path.

---

## 7. Findings summary

| ID         | Severity | Status     | Notes                                                                  |
| ---------- | -------- | ---------- | ---------------------------------------------------------------------- |
| A7-PROD-01 | —        | **CLOSED** | Prod `data/duckdb/` hash unchanged                                     |
| A7-IDEM-01 | —        | **CLOSED** | `init_db` ×2 on prod copy → `none (up to date)`                        |
| A7-IDEM-02 | —        | **CLOSED** | Fresh init applies 011 once; second run idempotent                     |
| A7-ADV-01  | —        | **CLOSED** | Crash-recovery rerun restores 011 row, no dupes                        |
| B2.5-O-02  | P2 defer | **OPEN**   | `schema.sql` lag vs 011 — tracked in deferred registry; not A7 blocker |

**§4.3 open count for A7 scope: 0**

---

## 8. Verdict

| Matrix row                                         | Result   |
| -------------------------------------------------- | -------- |
| A7 cli-sandbox — `init_db` ×2 migration 011        | **PASS** |
| A7 audit-prod-path — `data/duckdb/` hash unchanged | **PASS** |
| Adversarial re-run idempotency                     | **PASS** |

**Overall A7 verdict: PASS**

**Output path:** `.trellis/tasks/06-20-round3-batch2-5-layer1-obs-ingest/research/audit-a7-ops.md`
