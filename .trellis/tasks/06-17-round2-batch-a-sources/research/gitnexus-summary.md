# GitNexus 摘要 — Round 2 Batch A（011+012）

> Phase 1 产出 · Plan 阶段 · 2026-06-17

## 索引状态

- 仓库：**quant-monitor-desk**（GitNexus 已索引）
- Round 2 目标模块：**尚未存在**（`backend/app/datasources/` 仅空 `__init__.py`）
- Round 1 就绪触点：`migrate.py`、`ConnectionManager`、`WriteManager`、`StubValidationGate`、`FileRegistry`

## 与 Batch A 相关的现有符号

| 符号 | 路径 | Batch A 关系 |
|------|------|--------------|
| `apply_migrations` | `backend/app/db/migrate.py` | 003 migration 挂载点 |
| `ConnectionManager.writer/reader` | `backend/app/db/connection.py` | fetch_log / sync_to_db 写路径 |
| `WriteManager` | `backend/app/db/write_manager.py` | **Batch A 不得调用**（Adapter 不写 clean） |
| `StubValidationGate` | `backend/app/db/validation_gate.py` | Batch A 不修改；Batch C 替换 |
| `FileRegistry` | `backend/app/storage/file_registry.py` | 后续 adapter 写 raw 时复用（Batch B） |

## 执行流（GitNexus query: source registry adapter fetch）

当前无 ingestion 执行流；最近似流程为 **Write → _write_audit**（Round 1 WriteManager）。

Batch A 将新增 **跨 community** 流程：

```text
SourceRegistry.load → sync_to_db
BaseDataAdapter.fetch → FetchLogWriter.write
```

## 风险与约束

1. **路径漂移：** 任务文件写 `backend/sources/`，Round 1 DECISIONS 与 architecture 为 `backend/app/datasources/` — Plan 已冻结后者。
2. **缺失契约文件：** `source_registry.yaml` Plan 阶段已补 seed（原仓库缺失）。
3. **schema 增量：** `fetch_log` 仅在 module doc 定义，不在 `specs/schema/schema.sql` — migration 003 以 module doc §5.6 为准。
4. **测试基线：** Round 1 结束 **93** tests；Batch A 增量需全绿回归。

## Execute 6.pre 建议查询

- `impact({target: "apply_migrations", direction: "upstream"})` — 改 migration 前
- `context({name: "WriteManager"})` — 确认 Batch A 不接入 write 路径
- `query({query: "fetch_log source_registry adapter"})` — Execute 开始时再跑
