# R4D_readonly_sql_assistant_reference — DB-GPT / DB-GPT-Hub Reference Landing Task

## 1. Round / batch / branch

| Field                             | Value                                                                  |
| --------------------------------- | ---------------------------------------------------------------------- |
| Round                             | Round 4 candidate, not Round 3 execution                               |
| Batch                             | Future read-only database reporting and evaluation research batch      |
| Suggested branch                  | `research/r4-readonly-sql-assistant`                                   |
| Can run in parallel with Round 3? | No Round 3 branch. Keep as future research unless explicitly approved. |
| Blocking?                         | Does not block Round 3.                                                |

## 2. Purpose

Land DB-GPT and DB-GPT-Hub references as future read-only database assistant, sandboxed report generation, and Text-to-SQL evaluation ideas. These projects must not be used to satisfy Round 3 data-source or live market-data tasks.

## 3. External project links execute must see

| Project    | URL                                          | Borrowable detail                                                                       | Required boundary                                                                                                  |
| ---------- | -------------------------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| DB-GPT     | `https://github.com/eosphoros-ai/DB-GPT`     | Multi-source data access, sandboxed execution, skills-driven report and analysis ideas. | No write access, no production DB write path, no live market-data acquisition, no Round 3 data-source integration. |
| DB-GPT-Hub | `https://github.com/eosphoros-ai/DB-GPT-Hub` | Text-to-SQL dataset, evaluation, and fine-tuning methodology.                           | No model training or Text-to-SQL evaluation may close a Round 3 source-probe or DB-inspect item.                   |

## 4. Future Plan-stage input index

A future Round 4 plan must read:

- `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`
- `docs/quality/staged_acceptance_policy.md`
- `docs/ops/privacy_data_flow.md` if present
- `specs/contracts/module_boundary_contract.yaml` if present
- `specs/contracts/user_input_privacy_contract.yaml` if present
- `specs/contracts/runtime_versions.md`
- `docs/modules/duckdb_and_parquet.md`
- `docs/modules/write_manager.md`
- this task card

## 5. Required boundaries

- Read-only by default.
- No production DB writes.
- Query budget, timeout, result redaction, and audit log required.
- No secrets or raw user data in prompts/logs.
- No replacement for QMD SourceRegistry, CapabilityRegistry, RoutePreview, or ResourceGuard.
- No use in Round 3 data acquisition.

## 6. Acceptance criteria for future work

- A future design defines allowed query scope, read-only connection, query budget, timeout, and result redaction.
- Text-to-SQL evaluation uses synthetic or sandbox DBs first.
- Any report generation proves no writes and no future-data leakage.
