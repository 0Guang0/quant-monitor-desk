# 005 Schema — 技术设计索引

> **完整设计见 `MASTER.plan.md` §4–§6。**

- 架构：`scripts/init_db.py` → `backend/app/db/migrate.py` → `migrations/*.sql`
- 幂等：`schema_version` 记录 version_id + checksum；重复 apply 跳过
- 事务：每条 migration BEGIN → DDL + INSERT version → COMMIT
- 写路径：`init_db` 经 `ConnectionManager.writer()`（与 007 联动）
