# R3H-10 BOOT — 入口旁路基线矩阵

> **切片：** S10-BOOT  
> **日期：** 2026-06-29（规划扫描；Execute S10-BOOT 时须 `git grep` 复核）  
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

| #   | 入口                                                             | 模块   | 当前                                    | 风险          | 切片           |
| --- | ---------------------------------------------------------------- | ------ | --------------------------------------- | ------------- | -------------- |
| 1   | `DataSyncOrchestrator.run_incremental(..., datasource_service=)` | D1, C2 | ✅                                      | —             | 保持           |
| 2   | `run_incremental(..., adapter=)` 无 service                      | D1     | ❌ 生产 fail-closed                     | 已测          | S10-01 复核    |
| 3   | `run_backfill` / `run_reconcile` 同上                            | D1     | ❌ 生产 fail-closed                     | 已测          | S10-01 复核    |
| 4   | `qmd data route-preview`                                         | E1, C2 | ✅ `_service()`                         | 低            | S10-02         |
| 5   | `qmd data sync-plan`                                             | E1, C2 | ✅ 经 route_preview                     | 低            | S10-02         |
| 6   | `run_staged_pilot_raw_only`                                      | E4     | ⚠️ service + `create_staged_fetch_port` | **双轨实现**  | S10-05         |
| 7   | `run_live_pilot_raw_only`                                        | E4     | ⚠️ service + `create_live_fetch_port`   | **双轨实现**  | S10-03, S10-05 |
| 8   | `run_interface_probe`                                            | E4     | ❌ `interface_probe_fetch_ports`        | **旁路**      | S10-04, S10-05 |
| 9   | `Layer1ObservationIngestionService` + fixture service            | G1     | ⚠️ staged 合法                          | 文档边界      | S10-03         |
| 10  | `sandbox_clean_write` gates                                      | E5     | ✅ `DataSourceService`                  | —             | 不动           |
| 11  | `datasource_service_contract.yaml`                               | C2     | draft                                   | 契约未 active | S10-02         |
| 12  | `STAGED-PILOT-SSOT` audit 行                                     | 登记   | PENDING                                 | PASS 阻塞     | S10-CLOSE      |

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

## OPEN 缺口（Execute 驱动）

1. **interface_probe** 未经 service — S10-04/05
2. **staged/live fetch_ports** 与 `datasources/fetch_ports` 双实现 — S10-05
3. **契约 draft** — S10-02
4. **STAGED-PILOT-SSOT** 登记 PENDING — S10-CLOSE

---

## BOOT 完成命令（证据 `9.0-green.txt`）

```bash
uv run pytest -q
```

记录：commit SHA、pytest 摘要、本文件路径。
