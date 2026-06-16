# GitNexus / 代码库分析摘要 — 005 Schema

> Plan Phase 1 产出（示范）。Execute 阶段**不读本文件**，结论已并入 MASTER §4。

## 任务相关模块

| 模块 | 路径 | 说明 |
|------|------|------|
| Migration runner | `backend/app/db/migrate.py` | 新建；被 `init_db` 调用 |
| Migrations | `backend/app/db/migrations/*.sql` | 按文件名排序 apply |
| CLI | `scripts/init_db.py` | 建库入口 |
| 测试 | `tests/test_schema_migration.py` | 内存 DuckDB 验证 |

## 依赖方向

```text
scripts/init_db.py
    → backend.app.db.migrate.apply_migrations
        → migrations/001_foundation.sql (+ 002_registry_hardening.sql)
        → schema_version 表（幂等记录）
```

## 改动影响面

- 后续 ROUND 任务依赖 foundation 表存在（file_registry、write_audit_log 等）
- 改 migration 文件内容会触发 checksum 校验失败（故意 fail-fast）

## Open Questions（Plan 阶段已关闭）

- [x] 是否整库执行 schema.sql → **否**（DECISIONS §3）
- [x] init_db 是否走写锁 → **是**（ConnectionManager）
