# 原计划追溯 — B3F-MIG

| 来源                                                          | Playbook / Roadmap | MASTER 锚点       | AC             | 切片          |
| ------------------------------------------------------------- | ------------------ | ----------------- | -------------- | ------------- |
| `BATCH_3F_COORDINATOR_PLAYBOOK.md` §3.3                       | B3F-MIG 必读       | §0 Source Context | R3F-MIG-01..06 | §8 MIG-01..06 |
| `BATCH_3F_TASK_CARD_MANIFEST.md` §1                           | B3F-MIG row        | §0                | 八路 ownership | §8            |
| `PROJECT_IMPLEMENTATION_ROADMAP.md`                           | R3F-MIG-01..06     | §4 AC-MIG-\*      | 六行           | §8            |
| `BATCH_3F_PLAYBOOK_ADVERSARIAL_AUDIT.report.md` B3F-AUD-VS-02 | 009 verify-only    | §1.5 #6           | 负向边界       | §9.1          |
| `MIGRATION_COVERAGE.md`                                       | 008→009→3F         | §2.4              | AC-MIG-05      | §9.5          |

### manifest 状态

| 路径                                                    | manifest          |
| ------------------------------------------------------- | ----------------- |
| `docs/schema/MIGRATION_008_PLAN.md`                     | required          |
| `docs/schema/MIGRATION_COVERAGE.md`                     | required          |
| `backend/app/db/migrations/012_migration_residuals.sql` | execute-required  |
| `tests/test_round3f_migration_residuals.py`             | execute-required  |
| `docs/decisions/ADR-002-db-check-vs-app-validation.md`  | required          |
| `source_health_snapshot` 建表                           | deferred → B3F-SH |
