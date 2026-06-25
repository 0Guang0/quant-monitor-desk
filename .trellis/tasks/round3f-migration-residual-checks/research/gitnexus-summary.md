# GitNexus summary — B3F-MIG

## query: migration residuals round 3F

- **Processes**: `apply_migrations` → sequential SQL in `backend/app/db/migrations/`
- **Clusters**: `db/migrate`, `datasources/source_registry`, `tests/test_round3f_migration_residuals`

## impact targets (Execute 前必跑)

| Symbol | 预期风险 | 切片 |
|--------|----------|------|
| `apply_migrations` | LOW — 新 012 文件 | Boot |
| `SourceRegistry.sync_to_db` | MEDIUM — tombstone 列写入 | MIG-04 |

## context

- 009 `fetch_log_v2` / `manual_review_queue_v2` CHECK 已落地；MIG-01 禁止 013 重复。
- 012 使用显式列 INSERT（A9-P3-01 hygiene）。
- `registry_generation` / `removed_from_yaml_at` 关闭 D2-P3-1 migration 侧（列 owner B3F-MIG）。

## 邻接只读

- B3F-SH：`source_health_snapshot` migration 不在本分支。
- B3F-HYG：不与本分支同改 migration 列。
