# R3H-10 BOOT — 入口旁路基线矩阵

> **切片：** S10-BOOT  
> **日期：** 2026-06-29 规划 · **Execute 复核：** 2026-06-29（`interface_probe.py` 仍直连 `interface_probe_fetch_ports`；`data_commands._service()` 经 service；`runners.guard_*` 在位）  
> **用途：** S10-01～05 的 RED 引用 SSOT

---

## 图例

| 经 service？ | 含义                                        |
| ------------ | ------------------------------------------- |
| ✅           | `DataSourceService.fetch` / `preview_route` |
| ⚠️           | 经 service 但 **注入** `ops/*_fetch_ports`  |
| ❌           | 可绕过 route/capability/guard 链            |

| 目标状态 @ R3H-10 CLOSE                                        |
| -------------------------------------------------------------- |
| 生产路径：**✅**                                               |
| Rehearsal：**⚠️ 允许**但 port 实现 ≡ `datasources/fetch_ports` |
| Probe：**✅ 委托 service** 或明确 rehearsal-only               |

---

## 矩阵

| #   | 入口                                                             | 模块   | 当前                                        | 风险         | 切片            |
| --- | ---------------------------------------------------------------- | ------ | ------------------------------------------- | ------------ | --------------- |
| 1   | `DataSyncOrchestrator.run_incremental(..., datasource_service=)` | D1, C2 | ✅                                          | —            | 保持            |
| 2   | `run_incremental(..., adapter=)` 无 service                      | D1     | ❌ 生产 fail-closed                         | 已测         | S10-01 复核     |
| 3   | `run_backfill` / `run_reconcile` 同上                            | D1     | ❌ 生产 fail-closed                         | 已测         | S10-01 复核     |
| 4   | `qmd data route-preview`                                         | E1, C2 | ✅ `_service()`                             | 低           | S10-02          |
| 5   | `qmd data sync-plan`                                             | E1, C2 | ✅ 经 route_preview                         | 低           | S10-02          |
| 6   | `run_staged_pilot_raw_only`                                      | E4     | ⚠️ service + SSOT `cn_rehearsal_live_ports` | 低（已收敛） | CLOSED          |
| 7   | `run_live_pilot_raw_only`                                        | E4     | ⚠️ service + SSOT re-export                 | 低           | CLOSED          |
| 8   | `run_interface_probe`                                            | E4     | ✅ 委托 `DataSourceService.fetch`           | 低           | CLOSED (S10-04) |
| 9   | `Layer1ObservationIngestionService` + fixture service            | G1     | ⚠️ staged 合法                              | 文档边界     | S10-03          |
| 10  | `sandbox_clean_write` gates                                      | E5     | ✅ `DataSourceService`                      | —            | 不动            |
| 11  | `datasource_service_contract.yaml`                               | C2     | **active** (S10-02)                         | —            | CLOSED          |
| 12  | `STAGED-PILOT-SSOT` audit 行                                     | 登记   | **CLOSED** (S10-05)                         | —            | CLOSED          |

---

## 已存在测试（勿重复发明）

```text
tests/test_sync_orchestrator.py::test_r3ySync001_*AdapterBypassInProductionProfile
tests/test_datasource_service.py::test_apiAndAgentCannotImportAdapterFactory
tests/test_datasource_service.py::test_serviceBuildsRouteBeforeFetch
tests/test_vendor_fetch_e2e.py::test_vendorFixtureFetch_e2eThroughDataSourceServicePath
tests/test_data_cli_contract.py::test_routePreviewContract_isReadOnly
```

---

## CLOSED @ R3H-10 Execute（2026-06-29）

全部 OPEN 项已于 S10-01..S10-05 闭合；保留本段作历史快照。

| 原 OPEN              | 闭合切片                                |
| -------------------- | --------------------------------------- |
| interface_probe 旁路 | S10-04 — 委托 `DataSourceService.fetch` |
| staged/live 双实现   | S10-05 — `cn_rehearsal_live_ports` SSOT |
| 契约 draft           | S10-02 — `status: active`               |
| STAGED-PILOT-SSOT    | S10-05/CLOSE — audit 行 CLOSED          |

---

## BOOT 完成命令（证据 `9.0-green.txt`）

```bash
uv run pytest -q
```

记录：commit SHA、pytest 摘要、本文件路径。
