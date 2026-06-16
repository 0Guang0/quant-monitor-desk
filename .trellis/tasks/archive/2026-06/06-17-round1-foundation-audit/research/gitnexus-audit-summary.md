# GitNexus + CodeGraph Audit 摘要 — Round 1（7.pre · 2026-06-17）

> **7.pre 产出** · 双工具 CLI 已验证

## 工具状态

| 工具 | 命令 | 结果 |
|------|------|------|
| GitNexus | `npx gitnexus status` | ✅ up-to-date · 2136 nodes |
| GitNexus | `npx gitnexus query "WriteManager staging clean write audit"` | ✅ WriteManager class + smoke/raw_store tests |
| GitNexus | `npx gitnexus context WriteManager` | ✅ imports: test_write_manager, test_raw_store, test_foundation_smoke, file_registry |
| CodeGraph | `npx @colbymchenry/codegraph explore WriteManager` | ✅ 65 symbols · write→_execute_write→gate→audit 链 |
| CodeGraph | `npx @colbymchenry/codegraph node apply_migrations` | ✅ 13 test callers + init_db main |

## 污染隔离

- Execute DATA_ROOT：`data/`（禁止 Audit 写）
- Audit sandbox：`QMD_DATA_ROOT=.audit-sandbox/data` · **A7 已验证**：首次 applied `[001_foundation, 002_registry_hardening]`，第二次 `none (up to date)`

## 关键调用链（双工具一致）

```text
init_db → ConnectionManager.writer → apply_migrations
WriteManager.write → StubValidationGate → staging→clean → write_audit_log
RawStore → FileRegistry → WriteManager.write(own_transaction=False)
```

CodeGraph 标注：`_execute_write` / `_write_audit` ⚠️ 无直接单测（经 write() 集成覆盖）。

## 各维度 agent 提示

| 维 | GitNexus | CodeGraph |
|----|----------|-----------|
| A1 | query WriteManager→ValidationGate→migrate | explore db/ + DECISIONS 对照 |
| A2 | — | explore WriteManager 266 行 · ponytail |
| A3 | — | node apply_migrations · quote_ident 注入面 |
| A5 | AC-1..8 trace | node 链 + A7 sandbox 幂等 |
| A7 | — | init_db @ .audit-sandbox/data ×2 ✅ |
| A8 | — | pytest -k checksum / own_transaction @ basetemp |

## 初筛静态

- `rg password|secret|api_key backend/app/` → **0 match**

## 7.pre 完成

维度 agent：读本文件 + GitNexus query/context + CodeGraph explore/node → audit.report §3.x。
