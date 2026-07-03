# M-DATA-03 Project Overview（GitNexus 1a）

> **Query：** Tier A live incremental data pipeline subsystems  
> **Date：** 2026-07-02

---

## 子系统地图

```text
CLI (E1)
  backend/app/cli/data_commands.py
    → product_live_gate (ADR-027)
    → DataSourceService (C2/C3)
      → fetch_ports/* (C3)
    → DataSyncOrchestrator.run_incremental (D1)
      → IncrementalJobRunner
      → validators (B2/B3) + WriteManager (B1)
      → clean tables (ADR-028)
    → ops inspect / data_health (E2/F0)
```

## 十一源入口

| 层   | 组件                                                                     |
| ---- | ------------------------------------------------------------------------ |
| 路由 | `sync/incremental_source_registry.py` · `data_commands sync --source-id` |
| 编排 | `sync/orchestrator.py` · `ops/*_incremental_run.py`                      |
| 抓取 | `datasources/fetch_ports/*_port.py`                                      |
| 验收 | `tests/test_*_incremental_e2e.py`                                        |

## 与 DCP-05 关系

DCP-05 在同一子系统上交付 **replay 闭合**；M-DATA-03 在同一图上切换 **live 验收面**，不新建平行管道。

## 关键执行流（GitNexus query 命中）

- `DataSyncOrchestrator.run_incremental` — 增量金路径
- `test_batch_d_orchestration_flow` — 幂等先例
- `test_r3h08_live_productization` — live 政策测

## Caveats

- GitNexus index 可能滞后；Execute 改符号前仍须 `impact()`
