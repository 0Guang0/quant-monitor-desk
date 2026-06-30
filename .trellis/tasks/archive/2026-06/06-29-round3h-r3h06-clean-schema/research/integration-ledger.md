# Integration Ledger — R3H-06（Plan 5c）

| 来源                                                              | 类型     | manifest           | 并入                      | 备注         |
| ----------------------------------------------------------------- | -------- | ------------------ | ------------------------- | ------------ |
| `R3H_06_CLEAN_SCHEMA.md`                                          | business | frozen             | inline §1–§15             | 活卡 SSOT    |
| `R3H_PASS_EXECUTION_PLAN.md`                                      | decision | INDEX §3 must-read | pointer                   | Wave 边界    |
| `R3G_MASS_REHEARSAL_OPEN_GAPS.md`                                 | decision | INDEX §3           | pointer                   | G3–G6        |
| `specs/schema/schema.sql`                                         | contract | INDEX §3           | pointer                   | DDL          |
| `research/grill-me-session.md`                                    | decision | INDEX §4           | merged → frozen §1.1      |              |
| `research/spec-driven-development-notes.md`                       | contract | INDEX §4           | merged cn_announcement 列 |              |
| `backend/app/ops/sandbox_clean_write/rehearsal_loader.py`         | code     | INDEX §3           | pointer                   | Execute 必读 |
| `backend/app/ops/sandbox_clean_write/limited_production_entry.py` | code     | INDEX §3           | pointer                   |              |

**规则：** 无 `research/*` 进 implement.jsonl（除 generate-manifests 从 INDEX §3 生成）。

**Phase 5c complete**
