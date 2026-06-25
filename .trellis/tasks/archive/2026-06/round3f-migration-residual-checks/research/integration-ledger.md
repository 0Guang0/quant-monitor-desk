# Integration ledger — B3F-MIG

| source                                  | category     | strategy | master_anchor    | execute_extract                | for_ac_step  |
| --------------------------------------- | ------------ | -------- | ---------------- | ------------------------------ | ------------ |
| `BATCH_3F_COORDINATOR_PLAYBOOK.md`      | business     | pointer  | §0 边界          | §3.3 §8.1 §7.2 合并序          | AC-MIG-\*    |
| `BATCH_3F_HARDENING_RULES.md`           | rule         | pointer  | §1.4 约束        | staged-only / 禁 live          | 停止条件     |
| `ADR-002-db-check-vs-app-validation.md` | decision     | pointer  | §2.5 决策        | priority app-layer             | AC-MIG-02    |
| `MIGRATION_COVERAGE.md`                 | architecture | pointer  | 2.4 契约         | Round 3F 路由桶                | AC-MIG-05    |
| `MIGRATION_008_PLAN.md`                 | architecture | pointer  | 2.4 契约         | 009 superseded + 3F 残余       | AC-MIG-05    |
| `ADR-002-db-check-vs-app-validation.md` | contract     | pointer  | 2.4 契约         | CHECK vs app-layer policy      | AC-MIG-02    |
| `012_migration_residuals.sql`           | wiring       | pointer  | ## 8.            | explicit rebuild + lifecycle列 | AC-MIG-03,04 |
| `source_registry.py`                    | wiring       | pointer  | ## 8.            | sync_to_db tombstone           | AC-MIG-04    |
| `009_status_check_constraints.sql`      | wiring       | pointer  | §9.1             | 只读 verify 009 CHECK          | AC-MIG-01    |
| `test_round3f_migration_residuals.py`   | wiring       | pointer  | 5.1 测试文件路径 | R3F-MIG-01..06 六用例          | AC-MIG-\*    |
| `test_schema_contract.py`               | wiring       | pointer  | §6 Tier A        | playbook 基线回归              | §8.1         |
| `test_migration_coverage.py`            | wiring       | pointer  | §6 Tier A        | coverage 基线回归              | §8.1         |
| `PROJECT_IMPLEMENTATION_ROADMAP.md`     | business     | pointer  | §1.6 原计划      | R3F-MIG-06 CLOSED              | AC-MIG-06    |
