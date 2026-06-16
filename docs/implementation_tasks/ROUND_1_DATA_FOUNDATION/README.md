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

- [x] `pytest -q` 全绿（70 tests，含评估报告二次修复）
- [x] `ruff check .` 通过
- [x] `python -m compileall backend scripts` 通过
- [x] `python scripts/init_db.py` 能在临时库上建出 foundation 表（经 ConnectionManager + migration 001/002）
- [x] WriteManager 能完成一次 staging→clean 写入并写出 audit 行
- [x] 失败路径能 rollback 且写出 `status=FAILED` 审计行

Checkpoint 未全绿不得进入 010。（**已完成**：010 smoke 已通过。）

## 实现与 hardening 状态（2026-06）

005~010 **首版代码已实现**；随后经 subagent 审计（code-review / security / test-engineer / architecture-critic），按 TDD 完成 **P0/P1 修复与测试缺口补充**。各 task 细节见对应 `plans/00N_*.plan.md` 末尾「实现记录（含审计修复与缺口补充）」。

**跨 task 关键变更摘要：**

| 变更 | 涉及 task | 说明 |
|------|-----------|------|
| `002_registry_hardening.sql` | 005, 009 | `content_hash` 唯一索引 + `stg_file_registry` 表 |
| `sql_identifiers.py` / `quote_ident` | 008 | SQL 标识符 allowlist，防注入 |
| `write(req, con=...)` | 008, 009 | 单 writer 会话内完成 staging→clean |
| 原子写锁 `O_EXCL` + advisory lock | 007 | 修复 TOCTOU；损坏锁 fail-closed |
| migration checksum 校验 | 005 | `MigrationChecksumError` |
| RawStore 路径/大小硬ening | 009 | 防穿越 + 256MB 上限 |
| ResourceGuard RSS + WARN 测试 | 006, 010 | 补全判定 tier 与 smoke 集成 |

**Round 2 已知遗留（非阻塞）：** Windows PID 锁启发式边缘 case；Stub ValidationGate 仍为占位；RawStore 未强制调用 ResourceGuard（已有大小上限）；`ConnectionManager.reader()` 须手动 close。

## 评估报告跟进（2026-06 二次修复）

| # | 级别 | 问题 | 状态 |
|---|------|------|------|
| 1 | P1 Bug | `rows_updated` 误报 | ✅ 已修复（plan 008） |
| 2 | P0 治理 | Round 1 未提交 | ✅ 本次 commit 固化 |
| 3 | P2 | FAILED 审计靠 autocommit | ✅ 显式事务提交 |
| 4 | P2 | guard_log 靠 autocommit | ✅ 显式 BEGIN/COMMIT |
| 5 | P2 | checksum 测试假阳性 | ✅ 真正篡改 migration 文件 |
| 6 | P3 | stub-pass 测试弱断言 | ✅ 对比 fail 行为 |
| 7 | P3 | `exists()` 半死代码 | ✅ 共用 lookup |
| 8 | P3 | staging/merge 跨事务 | ✅ `own_transaction=False` + 外层 BEGIN |

## 备注

本目录文件不是临时文件，最终交付包应保留 `DECISIONS.md`、`plans/` 与 6 个任务文件。
