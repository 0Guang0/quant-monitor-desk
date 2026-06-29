# Project Overview — R3H-10（GitNexus 1a · Execute 后刷新）

**Query：** DataSourceService SSOT · Sync fail-closed · staged/live fetch 双轨收敛

**Scope：** `backend/app/datasources/service.py` · `sync/runners.py` · `sync/orchestrator.py` · `fetch_ports/cn_rehearsal_live_ports.py` · ops shims

**Date：** 2026-06-29（R3H-10 CLOSED）

## Findings（Execute 后）

| 区域           | 现状                                                                                         |
| -------------- | -------------------------------------------------------------------------------------------- |
| **C2 service** | 契约 `status: active`；Sync incremental/backfill fail-closed（ADR-025）                      |
| **E4 双轨**    | staged/live shim → `cn_rehearsal_live_ports` SSOT；STAGED-PILOT-SSOT CLOSED                  |
| **旁路**       | `interface_probe` 网络 fetch 委托 `DataSourceService.fetch`                                  |
| **Reconcile**  | adapter fail-closed；`datasource_service=` 金路径 defer → R3H-08（ADR-025 §Reconcile defer） |

## Caveats

- 改 `service.py` / `runners.py` 前必须 GitNexus `impact` + 全量 pytest
- CRITICAL blast radius 见 `research/gitnexus-detect-changes-evidence.txt`
