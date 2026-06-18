# AUDIT 计划 — Round 2 Batch C validation/conflict

> Audit 入口 · 2026-06-17  
> Audit agent 只读本文件 + `audit.jsonl` + `MASTER.plan.md` §2/§9/§10 + Execute evidence。  
> 不复写代码；只做验证与报告。若发现问题，写入 `audit.report.md` §4.3，交给 Repair。

---

## 0. 元信息

| 字段 | 值 |
|------|-----|
| slug | `06-17-round2-batch-c-validation-conflict` |
| 关联 Execute | `MASTER.plan.md` |
| Audit 输出 | `audit.report.md` |
| Repair 入口 | `REPAIR.plan.md` |
| 判定 | PASS / PASS_WITH_FIXES / FAIL |

---

## 1. Audit Skill freeze

| 维度 | Skill | 本任务 | 读取 | 输出 |
|------|-------|--------|------|------|
| A1 Spec compliance | `audit-spec` | 必做 | `check.jsonl` + specs/docs | audit.report §A1 |
| A2 Code review | `ponytail-review` | 必做 | changed backend files | audit.report §A2 |
| A3 DB/migration | `diagnose` | 必做 | migrations + init_db evidence | audit.report §A3 |
| A4 Tests | `qa` | 必做 | tests + evidence | audit.report §A4 |
| A5 Traceability | `trace-ac` | 必做 | MASTER §2 + evidence | audit.report §A5 |
| A6 Security/logging | `security` | 必做 | fetch_port/fetch_log/status | audit.report §A6 |
| A7 Resource/scope | `resource-review` | 必做 | changed files + docs | audit.report §A7 |
| A8 Docs/handoff | `docs-review` | 必做 | BATCH_C_REPAIR_STATUS + README/DECISIONS | audit.report §A8 |
| A9 Risk summary | 主会话 | 必做 | A1–A8 | audit.report §4 |

---

## 2. 维度验证矩阵

### A1 Spec compliance

Verify:

- Data quality rules follow `specs/contracts/data_quality_rules.yaml`.
- Conflict logic follows `specs/contracts/source_conflict_rules.yaml`.
- Runtime flow follows `docs/modules/data_validation_and_conflict.md`.
- Original tasks 015/016 acceptance items are covered.
- Paths use `backend/app/validators/*`, not `backend/validation/*`.

### A2 Code review

Verify:

- Responsibilities are separated: pure logic, persistence, gate.
- No unrelated refactor.
- No new large dependencies.
- No `WriteManager` import from adapters.
- No production default stub gate restored.
- No broad catch/quiet fallback that hides validation failure.

### A3 DB/migration

Verify:

- Migration 005 exists and is idempotent.
- Migration 004 is not modified.
- `validation_report`, `data_quality_log`, `source_conflict`, `manual_review_queue` are created.
- fetch_log/source_registry defensive checks are implemented where feasible or explicitly documented with app-layer tests.
- `init_db.py` twice succeeds.

### A4 Tests

Verify targeted tests exist and assert business semantics, not just non-null/no-throw:

- `tests/test_data_quality_validator.py`
- `tests/test_source_conflict_validator.py`
- `tests/test_db_validation_gate.py`
- `tests/test_ingestion_validation_migration.py`
- `tests/test_batch_c_validation_flow.py`

### A5 Traceability

For every MASTER §2 AC-1 through AC-11:

- find implementation file
- find test file
- find evidence path
- mark PASS / PARTIAL / FAIL

### A6 Security/logging

Verify:

- token/password/api_key/apikey/secret/authorization/bearer are redacted in persisted errors.
- PortErrorStatus and FetchStatus cannot drift silently.
- no credential-like values in test fixtures or docs.
- no Agent write/free SQL introduced.

### A7 Resource/scope

Verify:

- no full-market/full-history default scan.
- ResourceGuard constraints respected.
- no Orchestrator implementation.
- no frontend/API production work.
- no real vendor HTTP/SDK scope creep.

### A8 Docs/handoff

Verify:

- `BATCH_C_REPAIR_STATUS.md` documents completed and deferred items.
- README/DECISIONS state Batch C status accurately.
- Execute handoff includes commands, results, ResourceGuard status, unresolved items.
- No scratch/tmp/final-package pollution.

---

## 3. Audit commands

Use Execute evidence first. Re-run only when necessary.

```bash
pytest tests/test_data_quality_validator.py \
       tests/test_source_conflict_validator.py \
       tests/test_db_validation_gate.py \
       tests/test_ingestion_validation_migration.py \
       tests/test_batch_c_validation_flow.py -q

pytest -q --cov=backend --cov-fail-under=75
ruff check .
python -m compileall -q backend scripts tests
python scripts/production_gate.py
python scripts/check_doc_links.py
```

---

## 4. audit.report.md required shape

```markdown
# AUDIT REPORT — Round 2 Batch C

## 1. Verdict
PASS / PASS_WITH_FIXES / FAIL

## 2. Evidence reviewed
...

## 3. A1–A8 results
...

## 4. Findings
### 4.1 Confirmed pass
### 4.2 Non-blocking notes
### 4.3 Required fixes
### 4.4 Deferred with approved stage

## 5. Final recommendation
READY_FOR_REPAIR / READY_FOR_FINISH
```

---

## 5. PASS criteria

PASS only if:

- No §4.3 required fixes remain.
- All AC-1 through AC-11 are PASS.
- §10 commands pass or non-run is honestly documented and non-blocking.
- No scope creep into Batch D/Round 4/Round 5.
