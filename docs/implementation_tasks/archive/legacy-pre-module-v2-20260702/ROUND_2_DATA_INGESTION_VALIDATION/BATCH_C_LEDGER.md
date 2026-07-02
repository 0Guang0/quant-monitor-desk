# Batch C Ledger — 前置约定与未收口项

> 关联：GPT 审计严格口径补收口（2026-06-17）· Trellis `06-17-gpt-audit-remediation`

---

## C-C0 — 已关闭

| ID     | 项                                | 状态      | 说明                                                         |
| ------ | --------------------------------- | --------- | ------------------------------------------------------------ |
| C-C0-1 | `validation: "null"` 字符串       | **FIXED** | 仅接受 YAML `null`；字符串 `"null"` → `InvalidRegistryError` |
| C-C0-3 | `FetchLogWriter._parse_timestamp` | **FIXED** | 坏 timestamp → `FetchLogValidationError`                     |

---

## C-C1 — SourceRegistry.sync_to_db 原子性策略（文档化）

**决策：** 保持 **caller-owned transaction**（函数内部不 `BEGIN`/`COMMIT`）。

**Batch C/D 执行要求：** Orchestrator 或 CLI 调用方拥有事务边界；单测 `test_syncToDb_withinExplicitTransaction_rollsBackOnRollback` 已覆盖。

---

## C-C2 — fetch_log DB CHECK

| 项                       | 阶段                  | 内容                                                              |
| ------------------------ | --------------------- | ----------------------------------------------------------------- |
| validation 表约束        | Batch C migration 005 | 新表内联约束                                                      |
| `fetch_log` 004 表 CHECK | Batch D+（defer）     | 已应用 migration 不可 ALTER；**Batch D 仅 app 层**（MASTER §6.7） |

---

## C-C3 — Batch D 及以后

Orchestrator、安全 CI、coverage uplift 等 — 见 `DECISIONS.md` §9 延后台账。
