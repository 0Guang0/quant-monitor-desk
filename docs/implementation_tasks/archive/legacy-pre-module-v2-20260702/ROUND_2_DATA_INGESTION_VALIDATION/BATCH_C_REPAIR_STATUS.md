# Batch C Repair / Status — Round 2 Data Ingestion Validation

> This file is created by the Batch C Trellis plan package.  
> Execute must update it at §8.9.  
> Do not mark Batch C complete until Audit PASS and Repair closure.

---

## 1. Scope

Batch C covers:

- `015_implement_data_quality_validator.md`
- `016_implement_source_conflict_validator.md`
- `005_ingestion_validation.sql`
- `DbValidationGate`
- SUCCESS evidence/staging existence validation
- FetchStatus / PortErrorStatus alignment
- minimal error redaction

Batch C does not cover:

- DataSyncOrchestrator
- ResourceGuard action loop
- real vendor FetchPorts
- frontend/API productionization
- Agent sandbox
- Release manifest / final package
- full Batch D security CI

---

## 2. C-C0 inherited closure

The following are expected to be already complete before Batch C implementation:

| Item                                    | Expected state                               |
| --------------------------------------- | -------------------------------------------- |
| `validation: "null"` string             | rejected; YAML null remains allowed          |
| `FetchLogWriter._parse_timestamp()`     | raises domain error for invalid timestamp    |
| `SourceRegistry.sync_to_db()` atomicity | caller-owned transaction strategy documented |

If any is not true, stop and repair before continuing Batch C.

---

## 3. Batch C implementation status

| Item                                  | Status       | Evidence                                                                                                  |
| ------------------------------------- | ------------ | --------------------------------------------------------------------------------------------------------- |
| migration 005                         | EXECUTE_DONE | `.trellis/tasks/06-17-round2-batch-c-validation-conflict/execute-evidence/8.1-green.txt`                  |
| DataQualityValidator                  | EXECUTE_DONE | `.trellis/tasks/06-17-round2-batch-c-validation-conflict/execute-evidence/8.3-green.txt`, `8.4-green.txt` |
| SourceConflictValidator               | EXECUTE_DONE | `.trellis/tasks/06-17-round2-batch-c-validation-conflict/execute-evidence/8.5-green.txt`, `8.6-green.txt` |
| DbValidationGate                      | EXECUTE_DONE | `.trellis/tasks/06-17-round2-batch-c-validation-conflict/execute-evidence/8.2-green.txt`                  |
| SUCCESS evidence/staging validation   | EXECUTE_DONE | `.trellis/tasks/06-17-round2-batch-c-validation-conflict/execute-evidence/8.4-green.txt`                  |
| FetchStatus/PortErrorStatus alignment | EXECUTE_DONE | `.trellis/tasks/06-17-round2-batch-c-validation-conflict/execute-evidence/8.7-green.txt`                  |
| error redaction                       | EXECUTE_DONE | `.trellis/tasks/06-17-round2-batch-c-validation-conflict/execute-evidence/8.7-green.txt`                  |
| docs/status update                    | EXECUTE_DONE | `.trellis/tasks/06-17-round2-batch-c-validation-conflict/execute-evidence/8.9-docs.txt`                   |

Migration caveat: DuckDB cannot safely `ALTER TABLE ADD CONSTRAINT` onto already
applied migration 004 tables. Batch C therefore creates the new validation/
conflict/manual-review tables with inline constraints in migration 005, while
`fetch_log` SUCCESS-evidence/status guards remain enforced by `FetchResult` and
`FetchLogWriter._validate_for_persist`.

---

## 4. Deferred items

| Item                                             | Stage             | Reason                                          |
| ------------------------------------------------ | ----------------- | ----------------------------------------------- |
| DataSyncOrchestrator                             | Batch D / Round 3 | Batch C only creates validation/gate primitives |
| ResourceGuard WARN/PAUSE/HARD_STOP orchestration | Batch D / Round 3 | Requires orchestrator                           |
| real vendor FetchPorts                           | Batch D+          | Batch C only aligns status/redaction            |
| API/frontend production UI                       | Round 4           | Explicit non-goal                               |
| Agent sandbox                                    | Round 5           | Explicit non-goal                               |
| Release manifest / FINAL_AUDIT                   | Round 5           | Explicit non-goal                               |
| CodeQL/action pin/SBOM/full security CI          | Batch D / Round 5 | Explicit non-goal                               |

---

## 5. Validation commands

Execute + Repair final gates (2026-06-17):

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
python scripts/ci_validation_smoke.py
```

```text
Targeted Batch C tests (64 passed) — Repair 2026-06-17
Full pytest (312 passed) — Repair 2026-06-17
Coverage: 94.14% (backend)
ruff check . — All checks passed
production_gate: PASS
ci_validation_smoke: ok
check_doc_links: OK (110 markdown files)
ResourceGuard triggered: no
Frontend/API/Agent/real Port work: not performed
```

---

## 6. Final verdict

`BATCH_C_COMPLETE: yes` (pending re-audit sign-off)

`READY_FOR_BATCH_D: yes` (after REPAIR.report + finish.md)

`READY_FOR_AUDIT: yes` → Audit PASS_WITH_FIXES → Repair closed
