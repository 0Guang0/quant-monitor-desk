# Project Overview — R3H-10（GitNexus 1a）

**Query：** DataSourceService SSOT · Sync fail-closed · staged/live fetch 双轨

**Scope：** `backend/app/datasources/service.py` · `backend/app/sync/runners.py` · `backend/app/sync/orchestrator.py` · `ops/staged_pilot_fetch_ports.py` · `ops/live_pilot_fetch_ports.py`

**Date：** 2026-06-29

## Findings

| 区域           | 现状                                                                                                   |
| -------------- | ------------------------------------------------------------------------------------------------------ |
| **C2 service** | `DataSourceService` 为产品 fetch 金路径；契约 `datasource_service_contract.yaml` 仍为 draft            |
| **Sync**       | `guard_production_adapter_bypass` 已存在；生产路径未传 `datasource_service=` 须 fail-closed（ADR-025） |
| **E4 双轨**    | staged/live 各有 `fetch_ports`；与 `datasources/fetch_ports/` 产品轨未完全收敛                         |
| **旁路**       | `interface_probe` 等 ops 路径仍可能 bypass service                                                     |

## Caveats

- 改 `service.py` / `runners.py` 前必须 GitNexus `impact` + 全量 pytest
- 参考项目只读，禁止 runtime import
