# Batch C Ledger — 前置约定与未收口项

> 关联：`REPAIR.plan.md` §4 · GPT 审计严格口径补收口（2026-06-17）

---

## C-C0 — 已在本 patch 关闭

| ID     | 项                                | 状态      | 说明                                                         |
| ------ | --------------------------------- | --------- | ------------------------------------------------------------ |
| C-C0-1 | `validation: "null"` 字符串       | **FIXED** | 仅接受 YAML `null`；字符串 `"null"` → `InvalidRegistryError` |
| C-C0-3 | `FetchLogWriter._parse_timestamp` | **FIXED** | 坏 timestamp → `FetchLogValidationError`                     |

---

## C-C1 — SourceRegistry.sync_to_db 原子性策略（文档化，非代码默认）

**决策：** 保持 **caller-owned transaction**（函数内部不 `BEGIN`/`COMMIT`）。

**理由：**

- Batch C `DataSyncOrchestrator` 可能将 registry sync 与 ingestion job 包在同一事务边界内；
- 强制内部事务会与 orchestrator 的大事务/SAVEPOINT 策略冲突。

**Batch C 执行要求：**

| 调用方                 | 必须                                                                                    |
| ---------------------- | --------------------------------------------------------------------------------------- |
| Orchestrator 全量 sync | `con.execute("BEGIN")` → `sync_to_db(con)` → `COMMIT`/`ROLLBACK`                        |
| CLI 独立 sync 脚本     | 同上，或文档明确 dry-run 非原子                                                         |
| 单元测试               | 已有 `test_syncToDb_withinExplicitTransaction_rollsBackOnRollback` 覆盖 caller rollback |

**验收：** Batch C Orchestrator PR 的 `implement.md` 必须引用本条目并含集成测试：sync 中途失败 → registry 无部分写入。

**不在 Batch C 做：** 将 `sync_to_db()` 改为默认 `atomic=True` 内部事务（除非 Orchestrator 设计变更）。

---

## C-C2 — fetch_log DB CHECK（Batch C 主任务，与 C-C0-3 衔接）

| 项                              | 阶段    | 内容                                              |
| ------------------------------- | ------- | ------------------------------------------------- |
| `005_fetch_log_constraints.sql` | Batch C | status CHECK、evidence CHECK                      |
| `DbValidationGate`              | Batch C | 生产 validation_report 查询                       |
| 应用层错误统一                  | Batch C | 与 `FetchLogValidationError` 对齐 DB 约束失败语义 |

C-C0-3 已在应用层领域化 timestamp；DB 约束仍属 Batch C 主 PR。

---

## C-C3 — Batch D 及以后（不变）

见 `REPAIR.plan.md` §4：安全 CI、coverage 95+、Orchestrator ResourceGuard 动作等。
