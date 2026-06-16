# ROUND 1 DATA FOUNDATION

本目录包含 6 个正式 implementation task 文件（005-010）。必须按文件编号顺序执行。

## Round 1 目标

把「本地数据底座」搭起来，做到三件事：

1. **能版本化地建库**：用 migration 机制初始化 DuckDB，不一次性铺满所有表。
2. **能安全地写**：所有 clean 写入走 WriteManager，支持事务与失败回滚。
3. **能审计、能保护**：写入留 `write_audit_log`，重任务前过 ResourceGuard。

校验（DataQualityValidator / SourceConflictValidator）是 Round 2 的事，本轮用 stub ValidationGate 把边界划清楚。

## 执行前必读

- `../GLOBAL_EXECUTION_RULES.md`
- `../GLOBAL_TESTING_POLICY.md`
- `../GLOBAL_RESOURCE_LIMITS.md`
- `../GLOBAL_TASK_TEMPLATE.md`
- `./DECISIONS.md` — 本轮已确认的架构与范围决策（路径、范围、依赖、stub 口径）

## 任务清单与依赖关系

| 编号 | 任务 | 主要产出 | 深度计划 |
|------|------|----------|----------|
| 005 | 创建 DuckDB schema 初始化 | `migrations/001_foundation.sql`、`init_db.py` | `plans/005_schema.plan.md` |
| 006 | 实现 ResourceGuard | `core/resource_guard.py` | `plans/006_resource_guard.plan.md` |
| 007 | 实现 DuckDB 连接管理 | `db/connection.py` | `plans/007_connection.plan.md` |
| 008 | 实现 WriteManager | `db/write_manager.py`、`db/validation_gate.py` | `plans/008_write_manager.plan.md` |
| 009 | 实现 file_registry 与 Raw Store | `storage/raw_store.py`、`storage/file_registry.py` | `plans/009_raw_store.plan.md` |
| 010 | 数据底座 smoke test | `tests/smoke/test_foundation_smoke.py` | `plans/010_smoke.plan.md` |

依赖图（自底向上构建）：

```text
005 schema ─┬─→ 007 connection ─┬─→ 008 write_manager ─┬─→ 010 smoke
            │                   │                       │
006 guard ──┴───────────────────┘                       │
            │                                            │
009 raw_store（依赖 005 file_registry + 007 connection）─┘
```

- 005 先行：没有表，后面无处可写。
- 006 ResourceGuard 与 005 互不依赖，可并行。
- 007 连接管理依赖 005 的库结构。
- 008 WriteManager 依赖 007（连接）+ 005（`write_audit_log`）。
- 009 Raw Store 依赖 005（`file_registry`）+ 007（连接）。
- 010 smoke 串起 006 + 007 + 008 + 009，必须最后做。

## Checkpoint：Foundation（008 完成后、010 之前）

- [ ] `pytest -q` 全绿
- [ ] `ruff check .` 通过
- [ ] `python -m compileall backend scripts` 通过
- [ ] `python scripts/init_db.py` 能在临时库上建出 5 张 foundation 表
- [ ] WriteManager 能完成一次 staging→clean 写入并写出 audit 行
- [ ] 失败路径能 rollback 且写出 `status=FAILED` 审计行

Checkpoint 未全绿不得进入 010。

## 备注

本目录文件不是临时文件，最终交付包应保留 `DECISIONS.md`、`plans/` 与 6 个任务文件。
