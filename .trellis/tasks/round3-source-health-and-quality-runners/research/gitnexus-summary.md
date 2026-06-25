# GitNexus Summary — B3F-SH

> Plan Phase 1b

## 符号与流程

| 符号 | 角色 | 变更预期 |
| ---- | ---- | -------- |
| `DataSyncOrchestrator.run_data_quality` | sync entry | SH-03 实现（当前 `raise_deferred_job_type`） |
| `DataSyncOrchestrator.run_revision_audit` | sync entry | SH-02 实现 |
| `data_health` 模块 | ops | SH-01/04/05 writer 扩展（非 DH2 profile 建表） |
| `raise_deferred_job_type` | contract | SH-02/03 后仍对其他 defer 类型生效 |

## 影响面（Plan 预估）

- **LOW–MEDIUM**：orchestrator 两方法 + 新 ops writer 模块
- **HIGH 禁止**：直接改 `backend/app/db/migrations/**` 无 MIG 协调

## 建议 Execute 顺序

1. impact(`run_data_quality`) / impact(`run_revision_audit`) 再改 orchestrator
2. 新 writer 符号独立模块，DH2 路径不 import migration DDL
