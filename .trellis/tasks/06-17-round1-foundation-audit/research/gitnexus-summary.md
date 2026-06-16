# GitNexus 摘要 — Round 1 Plan（retrospective）

> Phase 1 回填

## 模块触点

| 模块 | 路径 |
|------|------|
| migration | `backend/app/db/migrate.py` + `migrations/001_*.sql` `002_*.sql` |
| 连接 | `backend/app/db/connection.py` |
| 写入 | `backend/app/db/write_manager.py` + `validation_gate.py` + `sql_identifiers.py` |
| 资源 | `backend/app/core/resource_guard.py` |
| 存储 | `backend/app/storage/raw_store.py` + `file_registry.py` |
| CLI | `scripts/init_db.py` |

## 核心调用链

```text
init_db.py
  └─ ConnectionManager.writer()
       └─ apply_migrations(con)

WriteManager.write(req)
  └─ StubValidationGate.check(report_id)
  └─ staging → merge → write_audit_log

test_foundation_smoke
  └─ ResourceGuard → ConnectionManager → WriteManager → RawStore
```

## DECISIONS 边界

- stub ValidationGate（Round 2 替换）
- 仅 append_only + upsert_by_pk
- foundation 5 表 + stg_foundation_smoke
