# Plan 质检 §3.10 — B3F-MIG

| 路径 | 已入 MASTER/implement | 摘要一句 | 遗漏风险 |
|------|----------------------|----------|----------|
| `BATCH_3F_COORDINATOR_PLAYBOOK.md` §3.1 | MASTER §0 Source Context | 共用底座 | 无 |
| `BATCH_3F_COORDINATOR_PLAYBOOK.md` §3.3 | MASTER §0 + implement | B3F-MIG 必读 | 无 |
| `PROJECT_IMPLEMENTATION_ROADMAP.md` R3F-MIG-* | MASTER §4 + §8 | 六 AC | 无 |
| `012_migration_residuals.sql` | implement + §9.3–9.4 | 显式重建 + 列 | 无 |
| `ADR-002-db-check-vs-app-validation.md` | implement + §9.2 | priority app-layer | 无 |
| `MIGRATION_COVERAGE.md` | implement + §9.5 | 3F 路由 | 无 |
| `MIGRATION_008_PLAN.md` | implement + §9.5 | 008 残余表 | 无 |
| `test_round3f_migration_residuals.py` | implement + §5.3 | 六用例 | 无 |
| `source_health_snapshot` | §3.2 defer | B3F-SH owns | 无（刻意 defer） |

**复检**: Playbook §3.3 可执行路径均已索引。
