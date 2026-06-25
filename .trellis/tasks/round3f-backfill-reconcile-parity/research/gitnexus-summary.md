# GitNexus summary — B3F-BR

> Phase 1b · handler registry blast radius

## 符号

| 符号 | 文件 | 变更 |
|------|------|------|
| `OrchestratorJobHandler` | `orchestrator.py` | 新增 dataclass |
| `ORCHESTRATOR_HANDLER_REGISTRY` | `orchestrator.py` | 冻结映射 |
| `orchestrator_handler_registry()` | `orchestrator.py` | 返回副本 |
| `DataSyncOrchestrator.handler_registry()` | `orchestrator.py` | ops/CLI 暴露 |

## 上游

- `DataSyncOrchestrator.run_*` 仍直接调用 runner；registry 为文档化/矩阵用途，非动态派发（ponytail 最小）。
- `IMPLEMENTED_JOB_TYPES` / `RESERVED_JOB_TYPES` from `contract.py` — registry 须超集覆盖。

## 风险级别

**LOW** — 新增只读 registry + 测试；未改 runner 业务语义。

## 执行流

incremental/backfill/reconcile → 既有 `run_*` → runners；reserved → `raise_deferred_job_type`（B3V 已交付）。
